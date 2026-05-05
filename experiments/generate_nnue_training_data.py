"""Generate CSV training data for an NNUE-style board-feature evaluator."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import math
import os
from pathlib import Path
import random
import sys
from time import perf_counter, sleep
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.core import CANNON, KING, KNIGHT, RED, ROOK, Board, Move
from engine.evaluation import PIECE_VALUES
from engine.rules import game_over, generate_legal_moves, is_check
from engine.search import alpha_beta_search
from experiments.evaluator_registry import get_evaluator

SOURCE_RANDOM_PLAYOUT = "random_playout"
SOURCE_STATIC_SELF_PLAY = "static_self_play"
SOURCE_TACTICAL_CAPTURE = "tactical_capture"
SOURCE_TACTICAL_CHECK = "tactical_check"
SOURCE_ORDER = [
    SOURCE_RANDOM_PLAYOUT,
    SOURCE_STATIC_SELF_PLAY,
    SOURCE_TACTICAL_CAPTURE,
    SOURCE_TACTICAL_CHECK,
]
SOURCE_OFFSETS = {
    SOURCE_RANDOM_PLAYOUT: 11,
    SOURCE_STATIC_SELF_PLAY: 101,
    SOURCE_TACTICAL_CAPTURE: 1009,
    SOURCE_TACTICAL_CHECK: 10007,
}
TACTICAL_LOCAL_ATTEMPTS = 4
CHECKPOINT_VERSION = 1

FIELDNAMES = [
    "position_id",
    "fen",
    "position_key",
    "side_to_move",
    "phase",
    "source",
    "ply_count",
    "legal_move_count",
    "is_terminal",
    "target_score",
    "oracle_depth",
    "oracle_evaluator",
    "oracle_best_move",
    "nodes_visited",
    "leaf_nodes",
    "cutoffs",
    "elapsed_seconds",
]


@dataclass(frozen=True, slots=True)
class LabelResult:
    target_score: int
    oracle_best_move: str
    nodes_visited: int
    leaf_nodes: int
    cutoffs: int
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class CandidatePosition:
    fen: str
    source: str
    ply_count: int


@dataclass(frozen=True, slots=True)
class GenerationTask:
    source: str
    sample_index: int
    seed: int
    min_plies: int
    max_plies: int
    oracle_depth: int
    oracle_evaluator: str
    self_play_depth: int
    self_play_evaluator: str
    temperature: float
    self_play_top_k: int
    include_terminal: bool


@dataclass(frozen=True, slots=True)
class GenerationSummary:
    output: str
    new_rows_written: int
    total_rows: int
    source_counts: dict[str, int]
    duplicate_skipped: int
    terminal_skipped: int
    no_candidate: int
    error_count: int
    elapsed_seconds: float


@dataclass(slots=True)
class _RunState:
    source_targets: dict[str, int]
    written_by_source: Counter[str] = field(default_factory=Counter)
    duplicate_skipped: int = 0
    terminal_skipped: int = 0
    no_candidate: int = 0
    error_count: int = 0

    @property
    def new_rows_written(self) -> int:
        return sum(self.written_by_source.values())

    @property
    def total_requested(self) -> int:
        return sum(self.source_targets.values())


def classify_phase(board: Board, ply_count: int) -> str:
    """Classify a position as opening, middlegame, or endgame."""
    piece_count = len(board.piece_map())
    if piece_count >= 26 and ply_count <= 20:
        return "opening"
    if piece_count >= 14:
        return "middlegame"
    return "endgame"


def label_position(
    board: Board,
    oracle_depth: int,
    oracle_evaluator_name: str = "full_static",
) -> LabelResult:
    """Search one board and return a red-perspective label."""
    original_fen = board.fen()
    evaluator = get_evaluator(oracle_evaluator_name)
    result = alpha_beta_search(
        board,
        depth=oracle_depth,
        evaluator=evaluator,
        maximizing_color=RED,
    )
    if board.fen() != original_fen:
        raise RuntimeError("Oracle search modified board while generating labels.")
    return LabelResult(
        target_score=result.best_score,
        oracle_best_move=result.best_move.to_iccs() if result.best_move else "",
        nodes_visited=result.stats.nodes_visited,
        leaf_nodes=result.stats.leaf_nodes,
        cutoffs=result.stats.cutoffs,
        elapsed_seconds=result.stats.elapsed_seconds,
    )


def generate_random_playout_candidate(task: GenerationTask) -> CandidatePosition | None:
    """Generate one random legal playout candidate."""
    rng = random.Random(task.seed)
    board = Board()
    target_plies = rng.randint(task.min_plies, task.max_plies)
    plies_played = _play_random_plies(board, target_plies, rng)
    if not task.include_terminal and game_over(board):
        return None
    return CandidatePosition(board.fen(), SOURCE_RANDOM_PLAYOUT, plies_played)


def generate_static_self_play_candidate(
    task: GenerationTask,
) -> CandidatePosition | None:
    """Generate one candidate using shallow static self-play."""
    rng = random.Random(task.seed)
    board = Board()
    target_plies = rng.randint(task.min_plies, task.max_plies)
    positions: list[CandidatePosition] = [
        CandidatePosition(board.fen(), SOURCE_STATIC_SELF_PLAY, 0)
    ]

    evaluator = get_evaluator(task.self_play_evaluator)
    for ply in range(1, target_plies + 1):
        if game_over(board):
            break
        move = _select_self_play_move(board, task, evaluator, rng)
        if move is None:
            break
        board.make_move(move)
        positions.append(CandidatePosition(board.fen(), SOURCE_STATIC_SELF_PLAY, ply))

    candidates = [
        candidate
        for candidate in positions
        if task.include_terminal or not game_over(Board(candidate.fen))
    ]
    if not candidates:
        return None
    return rng.choice(candidates)


def generate_tactical_capture_candidate(
    task: GenerationTask,
) -> CandidatePosition | None:
    """Find a candidate position with at least one legal capture."""
    rng = random.Random(task.seed)
    best_low_value: CandidatePosition | None = None
    best_low_score = -1
    for attempt in range(TACTICAL_LOCAL_ATTEMPTS):
        candidate = _generate_tactical_base_candidate(task, rng, attempt)
        if candidate is None:
            continue
        board = Board(candidate.fen)
        best_capture = _best_capture_value(generate_legal_moves(board))
        if best_capture <= 0:
            continue
        tactical = CandidatePosition(
            candidate.fen,
            SOURCE_TACTICAL_CAPTURE,
            candidate.ply_count,
        )
        if _has_high_value_capture(board):
            return tactical
        if best_capture > best_low_score:
            best_low_score = best_capture
            best_low_value = tactical
    return best_low_value


def generate_tactical_check_candidate(task: GenerationTask) -> CandidatePosition | None:
    """Find a candidate position with at least one checking legal move."""
    rng = random.Random(task.seed)
    for attempt in range(TACTICAL_LOCAL_ATTEMPTS):
        candidate = _generate_tactical_base_candidate(task, rng, attempt)
        if candidate is None:
            continue
        board = Board(candidate.fen)
        if has_checking_move(board):
            return CandidatePosition(
                candidate.fen,
                SOURCE_TACTICAL_CHECK,
                candidate.ply_count,
            )
    return None


def has_checking_move(board: Board) -> bool:
    """Return whether the side to move has any legal move that gives check."""
    original_fen = board.fen()
    try:
        for move in generate_legal_moves(board):
            board.make_move(move)
            try:
                if is_check(board, board.side_to_move):
                    return True
            finally:
                board.undo_move()
        return False
    finally:
        if board.fen() != original_fen:
            raise RuntimeError("Checking-move filter did not restore board state.")


def has_capture_move(board: Board) -> bool:
    """Return whether the side to move has any legal capture."""
    original_fen = board.fen()
    try:
        return any(move.captured is not None for move in generate_legal_moves(board))
    finally:
        if board.fen() != original_fen:
            raise RuntimeError("Capture filter did not restore board state.")


def worker_generate_row(task: GenerationTask) -> dict[str, Any]:
    """Generate and label one candidate row. Workers never write CSV."""
    try:
        candidate = _generate_candidate(task)
        if candidate is None:
            if task.source == SOURCE_RANDOM_PLAYOUT:
                return _worker_result(task, "terminal_skipped")
            return _worker_result(task, "no_candidate")

        board = Board(candidate.fen)
        original_fen = board.fen()
        terminal = game_over(board)
        if terminal and not task.include_terminal:
            return _worker_result(task, "terminal_skipped")

        legal_moves = generate_legal_moves(board)
        label = label_position(board, task.oracle_depth, task.oracle_evaluator)
        if board.fen() != original_fen:
            raise RuntimeError("Generating row modified board state.")

        row: dict[str, Any] = {
            "position_id": "",
            "fen": original_fen,
            "position_key": board.position_key(),
            "side_to_move": board.side_to_move,
            "phase": classify_phase(board, candidate.ply_count),
            "source": candidate.source,
            "ply_count": candidate.ply_count,
            "legal_move_count": len(legal_moves),
            "is_terminal": terminal,
            "target_score": label.target_score,
            "oracle_depth": task.oracle_depth,
            "oracle_evaluator": task.oracle_evaluator,
            "oracle_best_move": label.oracle_best_move,
            "nodes_visited": label.nodes_visited,
            "leaf_nodes": label.leaf_nodes,
            "cutoffs": label.cutoffs,
            "elapsed_seconds": f"{label.elapsed_seconds:.6f}",
        }
        return _worker_result(task, "ok", row=row)
    except Exception as exc:  # pragma: no cover - exercised by integration paths.
        return _worker_result(task, "error", error=f"{type(exc).__name__}: {exc}")


def write_training_data(
    output: str,
    random_positions: int = 50000,
    self_play_positions: int = 30000,
    tactical_capture_positions: int = 10000,
    tactical_check_positions: int = 10000,
    min_plies: int = 0,
    max_plies: int = 100,
    oracle_depth: int = 3,
    oracle_evaluator: str = "full_static",
    self_play_depth: int = 2,
    self_play_evaluator: str = "weighted_static",
    temperature: float = 0.0,
    self_play_top_k: int = 4,
    seed: int = 0,
    workers: int = 15,
    chunk_size: int = 10,
    progress_every: int = 100,
    resume: bool = False,
    include_terminal: bool = False,
    max_attempts_multiplier: int = 20,
    max_errors: int = 100,
    checkpoint_path: str | None = None,
) -> GenerationSummary:
    """Generate NNUE-style training rows and write them from the main process."""
    _validate_counts(
        random_positions,
        self_play_positions,
        tactical_capture_positions,
        tactical_check_positions,
        min_plies,
        max_plies,
    )
    output_path = Path(output)
    active_checkpoint_path = (
        _default_checkpoint_path(output_path)
        if checkpoint_path is None
        else Path(checkpoint_path)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chunk_size = max(1, chunk_size)
    progress_every = max(1, progress_every)
    workers = max(1, workers)
    max_attempts_multiplier = max(1, max_attempts_multiplier)

    requested_by_source = {
        SOURCE_RANDOM_PLAYOUT: random_positions,
        SOURCE_STATIC_SELF_PLAY: self_play_positions,
        SOURCE_TACTICAL_CAPTURE: tactical_capture_positions,
        SOURCE_TACTICAL_CHECK: tactical_check_positions,
    }
    existing = _load_existing(output_path) if resume and output_path.exists() else None
    seen_keys: set[str] = set() if existing is None else set(existing["seen_keys"])
    existing_source_counts: Counter[str] = (
        Counter() if existing is None else Counter(existing["source_counts"])
    )
    next_position_id = 0 if existing is None else int(existing["next_position_id"])
    source_targets = {
        source: max(requested_by_source[source] - existing_source_counts[source], 0)
        for source in SOURCE_ORDER
    }
    generation_parameters = _checkpoint_parameters(
        seed=seed,
        min_plies=min_plies,
        max_plies=max_plies,
        oracle_depth=oracle_depth,
        oracle_evaluator=oracle_evaluator,
        self_play_depth=self_play_depth,
        self_play_evaluator=self_play_evaluator,
        temperature=temperature,
        self_play_top_k=self_play_top_k,
        include_terminal=include_terminal,
    )
    checkpoint, source_start_indices = _prepare_checkpoint(
        output_path=output_path,
        checkpoint_path=active_checkpoint_path,
        resume=resume,
        existing_source_counts=existing_source_counts,
        parameters=generation_parameters,
    )
    state = _RunState(source_targets)
    mode = "a" if resume and output_path.exists() else "w"
    write_header = mode == "w"
    start = perf_counter()
    processed_results = 0

    _save_checkpoint(
        active_checkpoint_path,
        checkpoint,
        existing_source_counts + state.written_by_source,
        next_position_id,
    )

    with output_path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        with ProcessPoolExecutor(max_workers=workers) as executor:
            for source in SOURCE_ORDER:
                target = source_targets[source]
                if target <= 0:
                    continue
                attempts = target * max_attempts_multiplier
                task_iter = _task_iter(
                    source=source,
                    attempts=attempts,
                    start_index=source_start_indices[source],
                    base_seed=seed,
                    min_plies=min_plies,
                    max_plies=max_plies,
                    oracle_depth=oracle_depth,
                    oracle_evaluator=oracle_evaluator,
                    self_play_depth=self_play_depth,
                    self_play_evaluator=self_play_evaluator,
                    temperature=temperature,
                    self_play_top_k=self_play_top_k,
                    include_terminal=include_terminal,
                )
                for result in executor.map(
                    worker_generate_row,
                    task_iter,
                    chunksize=chunk_size,
                ):
                    _handle_worker_result(
                        result,
                        source,
                        writer,
                        seen_keys,
                        state,
                        next_position_id,
                        start,
                        progress_every,
                    )
                    _advance_checkpoint(checkpoint, result)
                    if result.get("_wrote_row"):
                        next_position_id += 1
                    processed_results += 1
                    if (
                        result.get("_wrote_row")
                        or processed_results % progress_every == 0
                    ):
                        _save_checkpoint(
                            active_checkpoint_path,
                            checkpoint,
                            existing_source_counts + state.written_by_source,
                            next_position_id,
                        )
                    if state.error_count > max_errors:
                        _save_checkpoint(
                            active_checkpoint_path,
                            checkpoint,
                            existing_source_counts + state.written_by_source,
                            next_position_id,
                        )
                        raise RuntimeError(
                            f"Too many worker errors: {state.error_count}"
                        )
                    if state.written_by_source[source] >= target:
                        break

                if state.written_by_source[source] < target:
                    print(
                        "WARNING: source "
                        f"{source} requested {target} but only wrote "
                        f"{state.written_by_source[source]} after max attempts.",
                        flush=True,
                    )
                _save_checkpoint(
                    active_checkpoint_path,
                    checkpoint,
                    existing_source_counts + state.written_by_source,
                    next_position_id,
                )

    elapsed = perf_counter() - start
    total_rows = next_position_id
    _save_checkpoint(
        active_checkpoint_path,
        checkpoint,
        existing_source_counts + state.written_by_source,
        next_position_id,
    )
    return GenerationSummary(
        output=str(output_path),
        new_rows_written=state.new_rows_written,
        total_rows=total_rows,
        source_counts=dict(existing_source_counts + state.written_by_source),
        duplicate_skipped=state.duplicate_skipped,
        terminal_skipped=state.terminal_skipped,
        no_candidate=state.no_candidate,
        error_count=state.error_count,
        elapsed_seconds=elapsed,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--random-positions", type=int, default=50000)
    parser.add_argument("--self-play-positions", type=int, default=30000)
    parser.add_argument("--tactical-capture-positions", type=int, default=10000)
    parser.add_argument("--tactical-check-positions", type=int, default=10000)
    parser.add_argument("--min-plies", type=int, default=0)
    parser.add_argument("--max-plies", type=int, default=100)
    parser.add_argument("--oracle-depth", type=int, default=3)
    parser.add_argument("--oracle-evaluator", default="full_static")
    parser.add_argument("--self-play-depth", type=int, default=2)
    parser.add_argument("--self-play-evaluator", default="weighted_static")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--self-play-top-k", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=15)
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--include-terminal", action="store_true")
    parser.add_argument("--max-attempts-multiplier", type=int, default=20)
    parser.add_argument("--max-errors", type=int, default=100)
    parser.add_argument("--checkpoint-path")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    summary = write_training_data(
        output=args.output,
        random_positions=args.random_positions,
        self_play_positions=args.self_play_positions,
        tactical_capture_positions=args.tactical_capture_positions,
        tactical_check_positions=args.tactical_check_positions,
        min_plies=args.min_plies,
        max_plies=args.max_plies,
        oracle_depth=args.oracle_depth,
        oracle_evaluator=args.oracle_evaluator,
        self_play_depth=args.self_play_depth,
        self_play_evaluator=args.self_play_evaluator,
        temperature=args.temperature,
        self_play_top_k=args.self_play_top_k,
        seed=args.seed,
        workers=args.workers,
        chunk_size=args.chunk_size,
        progress_every=args.progress_every,
        resume=args.resume,
        include_terminal=args.include_terminal,
        max_attempts_multiplier=args.max_attempts_multiplier,
        max_errors=args.max_errors,
        checkpoint_path=args.checkpoint_path,
    )
    print(
        "Generation complete: "
        f"output={summary.output}, "
        f"new_rows={summary.new_rows_written}, "
        f"total_rows={summary.total_rows}, "
        f"source_counts={summary.source_counts}, "
        f"duplicate_skipped={summary.duplicate_skipped}, "
        f"terminal_skipped={summary.terminal_skipped}, "
        f"no_candidate={summary.no_candidate}, "
        f"errors={summary.error_count}, "
        f"elapsed={summary.elapsed_seconds:.2f}s",
        flush=True,
    )


def _generate_candidate(task: GenerationTask) -> CandidatePosition | None:
    if task.source == SOURCE_RANDOM_PLAYOUT:
        return generate_random_playout_candidate(task)
    if task.source == SOURCE_STATIC_SELF_PLAY:
        return generate_static_self_play_candidate(task)
    if task.source == SOURCE_TACTICAL_CAPTURE:
        return generate_tactical_capture_candidate(task)
    if task.source == SOURCE_TACTICAL_CHECK:
        return generate_tactical_check_candidate(task)
    raise ValueError(f"Unknown source: {task.source}")


def _play_random_plies(board: Board, target_plies: int, rng: random.Random) -> int:
    plies_played = 0
    for _ in range(target_plies):
        if game_over(board):
            break
        moves = generate_legal_moves(board)
        if not moves:
            break
        board.make_move(rng.choice(moves))
        plies_played += 1
    return plies_played


def _select_self_play_move(
    board: Board,
    task: GenerationTask,
    evaluator: Any,
    rng: random.Random,
) -> Move | None:
    moves = generate_legal_moves(board)
    if not moves:
        return None
    if task.temperature <= 0:
        result = alpha_beta_search(
            board,
            depth=task.self_play_depth,
            evaluator=evaluator,
            maximizing_color=board.side_to_move,
        )
        return result.best_move

    side = board.side_to_move
    scored: list[tuple[float, Move]] = []
    for move in moves:
        board.make_move(move)
        try:
            scored.append((float(evaluator(board, side)), move))
        finally:
            board.undo_move()
    scored.sort(key=lambda item: (item[0], item[1].to_iccs()), reverse=True)
    top = scored[: max(1, task.self_play_top_k)]
    return _softmax_choice(top, task.temperature, rng)


def _softmax_choice(
    scored_moves: list[tuple[float, Move]],
    temperature: float,
    rng: random.Random,
) -> Move:
    if len(scored_moves) == 1:
        return scored_moves[0][1]
    max_score = max(score for score, _ in scored_moves)
    weights = [
        math.exp((score - max_score) / max(temperature, 1e-9))
        for score, _ in scored_moves
    ]
    total = sum(weights)
    needle = rng.random() * total
    cumulative = 0.0
    for weight, (_, move) in zip(weights, scored_moves):
        cumulative += weight
        if needle <= cumulative:
            return move
    return scored_moves[-1][1]


def _generate_tactical_base_candidate(
    task: GenerationTask,
    rng: random.Random,
    attempt: int,
) -> CandidatePosition | None:
    seed = rng.randrange(0, 2**31 - 1) + attempt * 7919
    source = SOURCE_RANDOM_PLAYOUT if rng.random() < 0.5 else SOURCE_STATIC_SELF_PLAY
    base_task = GenerationTask(
        source=source,
        sample_index=task.sample_index,
        seed=seed,
        min_plies=task.min_plies,
        max_plies=task.max_plies,
        oracle_depth=task.oracle_depth,
        oracle_evaluator=task.oracle_evaluator,
        self_play_depth=task.self_play_depth,
        self_play_evaluator=task.self_play_evaluator,
        temperature=task.temperature,
        self_play_top_k=task.self_play_top_k,
        include_terminal=task.include_terminal,
    )
    if source == SOURCE_RANDOM_PLAYOUT:
        return generate_random_playout_candidate(base_task)
    return generate_static_self_play_candidate(base_task)


def _best_capture_value(moves: list[Move]) -> int:
    values = [
        PIECE_VALUES[move.captured.type]
        for move in moves
        if move.captured is not None and move.captured.type != KING
    ]
    return max(values, default=0)


def _has_high_value_capture(board: Board) -> bool:
    high_value_types = {ROOK, CANNON, KNIGHT}
    return any(
        move.captured is not None and move.captured.type in high_value_types
        for move in generate_legal_moves(board)
    )


def _validate_counts(
    random_positions: int,
    self_play_positions: int,
    tactical_capture_positions: int,
    tactical_check_positions: int,
    min_plies: int,
    max_plies: int,
) -> None:
    counts = [
        random_positions,
        self_play_positions,
        tactical_capture_positions,
        tactical_check_positions,
    ]
    if any(count < 0 for count in counts):
        raise ValueError("Requested position counts must be non-negative.")
    if min_plies < 0 or max_plies < min_plies:
        raise ValueError("--max-plies must be greater than or equal to --min-plies.")


def _load_existing(output_path: Path) -> dict[str, Any]:
    seen_keys: set[str] = set()
    source_counts: Counter[str] = Counter()
    max_position_id = -1
    with output_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = row.get("position_key")
            if key:
                seen_keys.add(key)
            source = row.get("source")
            if source:
                source_counts[source] += 1
            position_id = row.get("position_id")
            if position_id not in (None, ""):
                max_position_id = max(max_position_id, int(position_id))
    return {
        "seen_keys": seen_keys,
        "source_counts": source_counts,
        "next_position_id": max_position_id + 1,
    }


def _worker_result(
    task: GenerationTask,
    status: str,
    *,
    row: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": status,
        "source": task.source,
        "sample_index": task.sample_index,
    }
    if row is not None:
        result["row"] = row
    if error is not None:
        result["error"] = error
    return result


def _default_checkpoint_path(output_path: Path) -> Path:
    return Path(f"{output_path}.checkpoint.json")


def _checkpoint_parameters(
    seed: int,
    min_plies: int,
    max_plies: int,
    oracle_depth: int,
    oracle_evaluator: str,
    self_play_depth: int,
    self_play_evaluator: str,
    temperature: float,
    self_play_top_k: int,
    include_terminal: bool,
) -> dict[str, Any]:
    return {
        "seed": seed,
        "min_plies": min_plies,
        "max_plies": max_plies,
        "oracle_depth": oracle_depth,
        "oracle_evaluator": oracle_evaluator,
        "self_play_depth": self_play_depth,
        "self_play_evaluator": self_play_evaluator,
        "temperature": temperature,
        "self_play_top_k": self_play_top_k,
        "include_terminal": include_terminal,
    }


def _new_checkpoint(
    output_path: Path,
    parameters: dict[str, Any],
    source_start_indices: dict[str, int] | None = None,
) -> dict[str, Any]:
    starts = source_start_indices or {source: 0 for source in SOURCE_ORDER}
    return {
        "version": CHECKPOINT_VERSION,
        "output": str(output_path),
        "seed": parameters["seed"],
        "parameters": dict(parameters),
        "sources": {
            source: {"next_sample_index": int(starts.get(source, 0))}
            for source in SOURCE_ORDER
        },
    }


def _prepare_checkpoint(
    output_path: Path,
    checkpoint_path: Path,
    resume: bool,
    existing_source_counts: Counter[str],
    parameters: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    fallback_starts = {
        source: int(existing_source_counts[source]) for source in SOURCE_ORDER
    }
    if resume and checkpoint_path.exists():
        checkpoint = _load_checkpoint(checkpoint_path)
        _warn_checkpoint_mismatches(checkpoint, parameters)
        checkpoint["version"] = CHECKPOINT_VERSION
        checkpoint["output"] = str(output_path)
        checkpoint["seed"] = parameters["seed"]
        checkpoint["parameters"] = dict(parameters)
        starts = {
            source: int(
                checkpoint.get("sources", {})
                .get(source, {})
                .get("next_sample_index", fallback_starts[source])
            )
            for source in SOURCE_ORDER
        }
        for source in SOURCE_ORDER:
            checkpoint.setdefault("sources", {}).setdefault(source, {})
            checkpoint["sources"][source]["next_sample_index"] = starts[source]
        return checkpoint, starts

    if resume:
        print(
            "WARNING: checkpoint file not found; using existing CSV source counts "
            "as fallback sample start indices.",
            flush=True,
        )
        checkpoint = _new_checkpoint(output_path, parameters, fallback_starts)
        return checkpoint, fallback_starts

    checkpoint = _new_checkpoint(output_path, parameters)
    return checkpoint, {source: 0 for source in SOURCE_ORDER}


def _load_checkpoint(checkpoint_path: Path) -> dict[str, Any]:
    with checkpoint_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Checkpoint must contain a JSON object: {checkpoint_path}")
    return data


def _warn_checkpoint_mismatches(
    checkpoint: dict[str, Any],
    parameters: dict[str, Any],
) -> None:
    checkpoint_parameters = checkpoint.get("parameters", {})
    for key, value in parameters.items():
        checkpoint_value = checkpoint_parameters.get(key, checkpoint.get(key))
        if checkpoint_value != value:
            print(
                "WARNING: checkpoint parameter mismatch for "
                f"{key}: checkpoint={checkpoint_value!r}, current={value!r}",
                flush=True,
            )


def _advance_checkpoint(checkpoint: dict[str, Any], result: dict[str, Any]) -> None:
    source = result.get("source")
    sample_index = result.get("sample_index")
    if source not in SOURCE_ORDER or sample_index is None:
        return
    source_state = checkpoint.setdefault("sources", {}).setdefault(source, {})
    current = int(source_state.get("next_sample_index", 0))
    source_state["next_sample_index"] = max(current, int(sample_index) + 1)


def _save_checkpoint(
    checkpoint_path: Path,
    checkpoint: dict[str, Any],
    source_counts: Counter[str],
    next_position_id: int,
) -> None:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint["updated_at"] = datetime.now(UTC).isoformat()
    checkpoint["source_counts"] = {
        source: int(source_counts[source]) for source in SOURCE_ORDER
    }
    checkpoint["next_position_id"] = next_position_id
    payload = json.dumps(checkpoint, indent=2, sort_keys=True) + "\n"

    for attempt in range(5):
        temporary_path = checkpoint_path.with_name(
            f"{checkpoint_path.name}.tmp.{os.getpid()}.{attempt}"
        )
        try:
            temporary_path.write_text(payload, encoding="utf-8")
            os.replace(temporary_path, checkpoint_path)
            return
        except PermissionError:
            sleep(0.25 * (attempt + 1))
        except OSError as exc:
            print(
                f"WARNING: could not atomically save checkpoint: {exc}",
                flush=True,
            )
            break
        finally:
            try:
                if temporary_path.exists():
                    temporary_path.unlink()
            except OSError:
                pass

    try:
        checkpoint_path.write_text(payload, encoding="utf-8")
    except OSError as exc:
        print(
            "WARNING: failed to save checkpoint; CSV rows already written, "
            f"but resume position may be stale: {exc}",
            flush=True,
        )


def _task_iter(
    source: str,
    attempts: int,
    start_index: int,
    base_seed: int,
    min_plies: int,
    max_plies: int,
    oracle_depth: int,
    oracle_evaluator: str,
    self_play_depth: int,
    self_play_evaluator: str,
    temperature: float,
    self_play_top_k: int,
    include_terminal: bool,
) -> Any:
    for sample_index in range(start_index, start_index + attempts):
        task_seed = base_seed + sample_index * 1009 + SOURCE_OFFSETS[source]
        yield GenerationTask(
            source=source,
            sample_index=sample_index,
            seed=task_seed,
            min_plies=min_plies,
            max_plies=max_plies,
            oracle_depth=oracle_depth,
            oracle_evaluator=oracle_evaluator,
            self_play_depth=self_play_depth,
            self_play_evaluator=self_play_evaluator,
            temperature=temperature,
            self_play_top_k=self_play_top_k,
            include_terminal=include_terminal,
        )


def _handle_worker_result(
    result: dict[str, Any],
    expected_source: str,
    writer: csv.DictWriter,
    seen_keys: set[str],
    state: _RunState,
    next_position_id: int,
    start: float,
    progress_every: int,
) -> None:
    status = result.get("status")
    if status == "ok":
        row = dict(result["row"])
        position_key = row["position_key"]
        if position_key in seen_keys:
            state.duplicate_skipped += 1
            return
        row["position_id"] = next_position_id
        seen_keys.add(position_key)
        writer.writerow(row)
        result["_wrote_row"] = True
        state.written_by_source[expected_source] += 1
        if state.new_rows_written % progress_every == 0:
            _print_progress(state, start)
        return
    if status == "terminal_skipped":
        state.terminal_skipped += 1
        return
    if status == "no_candidate":
        state.no_candidate += 1
        return
    if status == "error":
        state.error_count += 1
        print(f"ERROR sample failed: {result.get('error', '')}", flush=True)
        return
    state.error_count += 1
    print(f"ERROR unknown worker status: {status}", flush=True)


def _print_progress(state: _RunState, start: float) -> None:
    elapsed = perf_counter() - start
    samples_per_second = state.new_rows_written / elapsed if elapsed > 0 else 0.0
    remaining = max(state.total_requested - state.new_rows_written, 0)
    estimated_remaining = (
        remaining / samples_per_second if samples_per_second > 0 else 0.0
    )
    print(
        "Progress: "
        f"{state.new_rows_written}/{state.total_requested} written, "
        f"source_counts={dict(state.written_by_source)}, "
        f"duplicate_skipped={state.duplicate_skipped}, "
        f"terminal_skipped={state.terminal_skipped}, "
        f"no_candidate={state.no_candidate}, "
        f"errors={state.error_count}, "
        f"elapsed={elapsed:.2f}s, "
        f"{samples_per_second:.2f} samples/s, "
        f"estimated_remaining={estimated_remaining:.2f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()

"""
在仓库根目录运行这个 PowerShell 命令，8 个 worker，带 `--resume`，并使用默认 checkpoint 路径 `data/nnue_training_data.csv.checkpoint.json`：


python experiments/generate_nnue_training_data.py `
  --output data/nnue_training_data.csv `
  --random-positions 50000 `
  --self-play-positions 30000 `
  --tactical-capture-positions 10000 `
  --tactical-check-positions 10000 `
  --min-plies 0 `
  --max-plies 100 `
  --oracle-depth 3 `
  --oracle-evaluator full_static `
  --self-play-depth 2 `
  --self-play-evaluator weighted_static `
  --temperature 0.0 `
  --self-play-top-k 4 `
  --workers 12 `
  --chunk-size 10 `
  --progress-every 100 `
  --seed 0 `
  --resume

"""

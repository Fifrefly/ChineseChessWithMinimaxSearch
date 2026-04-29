"""Generate CSV training data for the optional MLP evaluator."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from pathlib import Path
import random
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.core import RED, Board
from engine.evaluation import (
    evaluate_piece_value_position_mobility_king_safety_and_threats,
    extract_evaluation_features,
)
from engine.rules import generate_legal_moves

try:
    from engine.search import alpha_beta_search as search_position
except ImportError:  # pragma: no cover - compatibility fallback
    from engine.search import minimax_search as search_position


FIELDNAMES = [
    "fen",
    "side_to_move",
    "material",
    "position",
    "mobility",
    "king_safety",
    "threats",
    "target_score",
]


def random_position(max_plies: int, rng: random.Random) -> Board:
    board = Board()
    for _ in range(rng.randint(0, max_plies)):
        moves = generate_legal_moves(board)
        if not moves:
            break
        board.make_move(rng.choice(moves))
    return board


def label_position(board: Board, depth: int) -> int:
    original_fen = board.fen()
    result = search_position(
        board,
        depth=depth,
        evaluator=evaluate_piece_value_position_mobility_king_safety_and_threats,
        maximizing_color=RED,
    )
    if board.fen() != original_fen:
        raise RuntimeError("Search modified board while generating labels.")
    return result.best_score


def _generate_training_sample(
    sample_index: int,
    max_plies: int,
    label_depth: int,
    seed: int,
) -> dict[str, int | str]:
    sample_seed = seed + sample_index
    rng = random.Random(sample_seed)
    board = random_position(max_plies, rng)
    fen = board.fen()
    features = extract_evaluation_features(board, RED)
    target_score = label_position(board, label_depth)
    if board.fen() != fen:
        raise RuntimeError("Feature extraction or labeling modified board.")
    return {
        "fen": fen,
        "side_to_move": board.side_to_move,
        "material": features.material,
        "position": features.position,
        "mobility": features.mobility,
        "king_safety": features.king_safety,
        "threats": features.threats,
        "target_score": target_score,
    }


def _generate_training_sample_from_args(
    args: tuple[int, int, int, int],
) -> dict[str, int | str]:
    return _generate_training_sample(*args)


def _existing_row_count(output_path: Path) -> int:
    if not output_path.exists():
        return 0
    with output_path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _print_progress(
    completed: int,
    positions: int,
    generated: int,
    start: float,
) -> None:
    elapsed = perf_counter() - start
    samples_per_second = generated / elapsed if elapsed > 0 else 0.0
    remaining = max(positions - completed, 0)
    estimated_remaining = (
        remaining / samples_per_second if samples_per_second > 0 else 0.0
    )
    print(
        "Progress: "
        f"{completed}/{positions} completed, "
        f"elapsed {elapsed:.2f}s, "
        f"{samples_per_second:.2f} samples/s, "
        f"estimated remaining {estimated_remaining:.2f}s",
        flush=True,
    )


def write_training_data(
    output: str,
    positions: int,
    max_plies: int,
    label_depth: int,
    seed: int,
    workers: int = 1,
    chunk_size: int = 10,
    progress_every: int = 50,
    resume: bool = False,
) -> int:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_exists = output_path.exists()
    start_index = _existing_row_count(output_path) if resume and output_exists else 0
    chunk_size = max(1, chunk_size)
    progress_every = max(1, progress_every)
    mode = "a" if resume and output_exists else "w"
    write_header = not (resume and output_exists)
    generated = 0
    start = perf_counter()

    if start_index >= positions:
        _print_progress(positions, positions, generated, start)
        return generated

    with output_path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()

        if workers <= 1:
            for sample_index in range(start_index, positions):
                writer.writerow(
                    _generate_training_sample(
                        sample_index,
                        max_plies,
                        label_depth,
                        seed,
                    )
                )
                generated += 1
                completed = start_index + generated
                if generated % progress_every == 0 or completed == positions:
                    _print_progress(completed, positions, generated, start)
            return generated

        args_iter = (
            (sample_index, max_plies, label_depth, seed)
            for sample_index in range(start_index, positions)
        )
        with ProcessPoolExecutor(max_workers=workers) as executor:
            for row in executor.map(
                _generate_training_sample_from_args,
                args_iter,
                chunksize=chunk_size,
            ):
                writer.writerow(row)
                generated += 1
                completed = start_index + generated
                if generated % progress_every == 0 or completed == positions:
                    _print_progress(completed, positions, generated, start)
    return generated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--positions", type=int, default=1000)
    parser.add_argument("--max-plies", type=int, default=80)
    parser.add_argument("--label-depth", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--progress-every", type=int, default=50)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    written = write_training_data(
        args.output,
        args.positions,
        args.max_plies,
        args.label_depth,
        args.seed,
        workers=args.workers,
        chunk_size=args.chunk_size,
        progress_every=args.progress_every,
        resume=args.resume,
    )
    print(
        f"Wrote {written} new positions to {args.output} "
        f"({args.positions} total requested)",
        flush=True,
    )


if __name__ == "__main__":
    main()

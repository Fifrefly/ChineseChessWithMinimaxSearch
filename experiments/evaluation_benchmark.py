"""Benchmark named evaluators against a deeper oracle search."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.core import RED, Board, Move
from engine.move_ordering import static_move_orderer
from engine.rules import game_over
from engine.search import MoveOrderer, alpha_beta_search
from experiments.evaluator_registry import get_evaluator

DEFAULT_EVALUATORS = (
    "material",
    "position",
    "mobility",
    "king_safety",
    "full_static",
    "weighted_static",
)
MOVE_ORDERING_CHOICES = ("none", "static")

FIELDNAMES = [
    "position_id",
    "fen",
    "side_to_move",
    "evaluator",
    "static_score",
    "search_depth",
    "search_score",
    "best_move",
    "nodes_visited",
    "leaf_nodes",
    "cutoffs",
    "elapsed_seconds",
    "oracle_evaluator",
    "oracle_depth",
    "oracle_score",
    "oracle_best_move",
    "candidate_oracle_score",
    "oracle_delta",
    "decision_loss",
    "oracle_regret",
    "abs_oracle_regret",
    "score_error",
    "abs_score_error",
    "move_matches_oracle",
]


def _parse_evaluator_names(text: str) -> list[str]:
    names = [name.strip() for name in text.split(",") if name.strip()]
    if not names:
        raise ValueError("At least one evaluator must be provided.")
    return names


def _move_to_text(move: Move | None) -> str:
    return "" if move is None else move.to_iccs()


def _move_orderer_for_name(name: str) -> MoveOrderer | None:
    if name == "none":
        return None
    if name == "static":
        return static_move_orderer
    raise ValueError(
        f"move_ordering must be one of {', '.join(MOVE_ORDERING_CHOICES)}."
    )


def _percentile(values: list[int], percentile: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    if lower == upper:
        return float(ordered[lower])
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _candidate_oracle_score(
    board: Board,
    candidate_move: Move | None,
    oracle_evaluator,
    oracle_depth: int,
    move_orderer: MoveOrderer | None = None,
) -> int | None:
    if candidate_move is None:
        return None

    original_fen = board.fen()
    board.make_move(candidate_move)
    try:
        result = alpha_beta_search(
            board,
            depth=max(0, oracle_depth - 1),
            evaluator=oracle_evaluator,
            maximizing_color=RED,
            move_orderer=move_orderer,
        )
        return result.best_score
    finally:
        board.undo_move()
        if board.fen() != original_fen:
            raise RuntimeError("Candidate oracle evaluation modified board FEN.")


def _decision_loss_metrics(
    side_to_move: str,
    oracle_score: int,
    candidate_oracle_score: int | None,
) -> tuple[int | None, int | None]:
    """Return ``(oracle_delta, decision_loss)`` for one candidate move."""
    if candidate_oracle_score is None:
        return None, None

    oracle_delta = candidate_oracle_score - oracle_score
    if side_to_move == RED:
        raw_loss = oracle_score - candidate_oracle_score
    else:
        raw_loss = candidate_oracle_score - oracle_score
    return oracle_delta, max(0, raw_loss)


def _load_position_rows(path: str, limit: int | None, seed: int) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "fen" not in reader.fieldnames:
            raise ValueError("positions CSV must contain a fen column.")
        rows = list(reader)

    if limit is not None and limit < len(rows):
        rows = random.Random(seed).sample(rows, limit)
    return rows


def run_benchmark(
    positions: str,
    output: str,
    evaluator_names: list[str] | None = None,
    search_depth: int = 2,
    oracle_depth: int = 3,
    oracle_evaluator_name: str = "full_static",
    mlp_model: str | None = None,
    limit: int | None = None,
    seed: int = 0,
    skip_terminal: bool = True,
    move_ordering: str = "none",
) -> tuple[int, int]:
    """Run the benchmark and return ``(rows_written, terminal_skipped)``."""
    if search_depth < 0 or oracle_depth < 0:
        raise ValueError("search depths must be non-negative.")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative.")

    names = list(DEFAULT_EVALUATORS) if evaluator_names is None else evaluator_names
    evaluators = {name: get_evaluator(name, mlp_model) for name in names}
    oracle_evaluator = get_evaluator(oracle_evaluator_name, mlp_model)
    move_orderer = _move_orderer_for_name(move_ordering)
    position_rows = _load_position_rows(positions, limit, seed)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0
    terminal_skipped = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        abs_regrets_by_evaluator: dict[str, list[int]] = {
            name: [] for name in names
        }
        move_matches_by_evaluator: dict[str, list[bool]] = {
            name: [] for name in names
        }

        for position_id, row in enumerate(position_rows):
            board = Board(row["fen"])
            original_fen = board.fen()
            if skip_terminal and game_over(board):
                terminal_skipped += 1
                continue

            oracle_result = alpha_beta_search(
                board,
                depth=oracle_depth,
                evaluator=oracle_evaluator,
                maximizing_color=RED,
                move_orderer=move_orderer,
            )
            if board.fen() != original_fen:
                raise RuntimeError("Oracle search modified board FEN.")

            oracle_score = oracle_result.best_score
            oracle_best_move = _move_to_text(oracle_result.best_move)

            for evaluator_name, evaluator in evaluators.items():
                static_score = evaluator(board, RED)
                if board.fen() != original_fen:
                    raise RuntimeError(f"{evaluator_name} modified board FEN.")

                search_result = alpha_beta_search(
                    board,
                    depth=search_depth,
                    evaluator=evaluator,
                    maximizing_color=RED,
                    move_orderer=move_orderer,
                )
                if board.fen() != original_fen:
                    raise RuntimeError(f"{evaluator_name} search modified board FEN.")

                best_move = _move_to_text(search_result.best_move)
                candidate_oracle_score = _candidate_oracle_score(
                    board,
                    search_result.best_move,
                    oracle_evaluator,
                    oracle_depth,
                    move_orderer,
                )
                if candidate_oracle_score is None:
                    oracle_regret = None
                    abs_oracle_regret = None
                    oracle_delta = None
                    decision_loss = None
                else:
                    oracle_regret = oracle_score - candidate_oracle_score
                    abs_oracle_regret = abs(oracle_regret)
                    oracle_delta, decision_loss = _decision_loss_metrics(
                        board.side_to_move,
                        oracle_score,
                        candidate_oracle_score,
                    )
                    abs_regrets_by_evaluator[evaluator_name].append(abs_oracle_regret)

                score_error = search_result.best_score - oracle_score
                move_matches_oracle = best_move == oracle_best_move
                move_matches_by_evaluator[evaluator_name].append(move_matches_oracle)
                writer.writerow(
                    {
                        "position_id": position_id,
                        "fen": original_fen,
                        "side_to_move": board.side_to_move,
                        "evaluator": evaluator_name,
                        "static_score": static_score,
                        "search_depth": search_depth,
                        "search_score": search_result.best_score,
                        "best_move": best_move,
                        "nodes_visited": search_result.stats.nodes_visited,
                        "leaf_nodes": search_result.stats.leaf_nodes,
                        "cutoffs": search_result.stats.cutoffs,
                        "elapsed_seconds": f"{search_result.stats.elapsed_seconds:.6f}",
                        "oracle_evaluator": oracle_evaluator_name,
                        "oracle_depth": oracle_depth,
                        "oracle_score": oracle_score,
                        "oracle_best_move": oracle_best_move,
                        "candidate_oracle_score": candidate_oracle_score,
                        "oracle_delta": oracle_delta,
                        "decision_loss": decision_loss,
                        "oracle_regret": oracle_regret,
                        "abs_oracle_regret": abs_oracle_regret,
                        "score_error": score_error,
                        "abs_score_error": abs(score_error),
                        "move_matches_oracle": move_matches_oracle,
                    }
                )
                rows_written += 1

    print(f"Wrote {rows_written} benchmark rows to {output}")
    print(f"Skipped {terminal_skipped} terminal positions")
    print(f"Evaluators: {', '.join(names)}")
    print(f"Oracle: {oracle_evaluator_name} depth {oracle_depth}")
    print(f"Move ordering: {move_ordering}")
    regret_means = {
        name: sum(values) / len(values)
        for name, values in abs_regrets_by_evaluator.items()
        if values
    }
    if regret_means:
        best_regret = min(regret_means, key=regret_means.__getitem__)
        print(
            "Lowest mean abs_oracle_regret: "
            f"{best_regret} ({regret_means[best_regret]:.4f})"
        )
        p90_regrets = {
            name: _percentile(values, 0.9)
            for name, values in abs_regrets_by_evaluator.items()
            if values
        }
        max_regrets = {
            name: max(values)
            for name, values in abs_regrets_by_evaluator.items()
            if values
        }
        best_p90 = min(p90_regrets, key=p90_regrets.__getitem__)
        worst_max = max(max_regrets, key=max_regrets.__getitem__)
        print(
            "Lowest p90 abs_oracle_regret: "
            f"{best_p90} ({p90_regrets[best_p90]:.4f})"
        )
        print(
            "Highest max abs_oracle_regret: "
            f"{worst_max} ({max_regrets[worst_max]:.4f})"
        )
    match_rates = {
        name: sum(values) / len(values)
        for name, values in move_matches_by_evaluator.items()
        if values
    }
    if match_rates:
        best_match = max(match_rates, key=match_rates.__getitem__)
        print(
            "Highest move match rate: "
            f"{best_match} ({match_rates[best_match]:.4f})"
        )
    return rows_written, terminal_skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--positions", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--evaluators",
        default=",".join(DEFAULT_EVALUATORS),
        help="Comma-separated evaluator names.",
    )
    parser.add_argument("--search-depth", type=int, default=2)
    parser.add_argument("--oracle-depth", type=int, default=3)
    parser.add_argument("--oracle-evaluator", default="full_static")
    parser.add_argument("--mlp-model")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--skip-terminal",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--move-ordering",
        choices=MOVE_ORDERING_CHOICES,
        default="none",
        help="Move ordering heuristic for alpha-beta search.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_benchmark(
        positions=args.positions,
        output=args.output,
        evaluator_names=_parse_evaluator_names(args.evaluators),
        search_depth=args.search_depth,
        oracle_depth=args.oracle_depth,
        oracle_evaluator_name=args.oracle_evaluator,
        mlp_model=args.mlp_model,
        limit=args.limit,
        seed=args.seed,
        skip_terminal=args.skip_terminal,
        move_ordering=args.move_ordering,
    )


if __name__ == "__main__":
    main()

"""Run a small self-play tournament between named evaluators."""

from __future__ import annotations

import argparse
import csv
from itertools import combinations
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.core import BLACK, RED, Board, opponent
from engine.rules import (
    game_over,
    generate_legal_moves,
    is_checkmate,
    is_stalemate,
    is_threefold_repetition,
)
from engine.search import alpha_beta_search
from experiments.evaluator_registry import get_evaluator

DEFAULT_EVALUATORS = ("material", "full_static", "weighted_static")

FIELDNAMES = [
    "game_id",
    "red_evaluator",
    "black_evaluator",
    "winner",
    "result_reason",
    "plies",
    "final_fen",
    "red_total_time",
    "black_total_time",
    "red_avg_nodes",
    "black_avg_nodes",
    "red_total_nodes",
    "black_total_nodes",
    "red_total_cutoffs",
    "black_total_cutoffs",
    "red_moves",
    "black_moves",
    "depth",
    "max_plies",
    "opening_random_plies",
    "adjudicate_max_plies",
    "adjudicator_evaluator",
    "adjudication_threshold",
    "final_adjudication_score",
    "seed",
]


def _parse_evaluator_names(text: str) -> list[str]:
    names = [name.strip() for name in text.split(",") if name.strip()]
    if not names:
        raise ValueError("At least one evaluator must be provided.")
    return names


def _terminal_result(board: Board) -> tuple[str, str] | None:
    if is_checkmate(board):
        return ("RED" if opponent(board.side_to_move) == RED else "BLACK", "checkmate")
    if is_stalemate(board):
        return "DRAW", "stalemate"
    if is_threefold_repetition(board):
        return "DRAW", "threefold_repetition"
    return None


def _apply_opening_random_plies(
    board: Board,
    plies: int,
    rng: random.Random,
) -> int:
    applied = 0
    for _ in range(plies):
        if game_over(board):
            break
        moves = generate_legal_moves(board)
        if not moves:
            break
        board.make_move(rng.choice(moves))
        applied += 1
    return applied


def _avg(total: int, count: int) -> float:
    return total / count if count else 0.0


def _adjudicate_position(
    board: Board,
    adjudicator,
    threshold: int,
) -> tuple[str, str, int]:
    final_score = adjudicator(board, RED)
    if final_score > threshold:
        return "RED", "max_plies_adjudicated_red", final_score
    if final_score < -threshold:
        return "BLACK", "max_plies_adjudicated_black", final_score
    return "DRAW", "max_plies_adjudicated_draw", final_score


def _play_game(
    game_id: int,
    red_name: str,
    black_name: str,
    red_evaluator,
    black_evaluator,
    depth: int,
    max_plies: int,
    opening_random_plies: int,
    adjudicate_max_plies: bool,
    adjudicator_evaluator: str,
    adjudicator,
    adjudication_threshold: int,
    seed: int,
    rng: random.Random,
) -> dict[str, object]:
    board = Board()
    plies = _apply_opening_random_plies(board, opening_random_plies, rng)

    red_total_time = 0.0
    black_total_time = 0.0
    red_total_nodes = 0
    black_total_nodes = 0
    red_total_cutoffs = 0
    black_total_cutoffs = 0
    red_moves = 0
    black_moves = 0

    winner = "DRAW"
    result_reason = "draw_max_plies"
    final_adjudication_score: int | str = ""

    terminal = _terminal_result(board)
    if terminal is not None:
        winner, result_reason = terminal
    else:
        while plies < max_plies:
            if game_over(board):
                terminal = _terminal_result(board)
                if terminal is not None:
                    winner, result_reason = terminal
                break

            side = board.side_to_move
            current_evaluator = red_evaluator if side == RED else black_evaluator
            result = alpha_beta_search(
                board,
                depth=depth,
                evaluator=current_evaluator,
                maximizing_color=side,
            )

            if side == RED:
                red_total_time += result.stats.elapsed_seconds
                red_total_nodes += result.stats.nodes_visited
                red_total_cutoffs += result.stats.cutoffs
            else:
                black_total_time += result.stats.elapsed_seconds
                black_total_nodes += result.stats.nodes_visited
                black_total_cutoffs += result.stats.cutoffs

            if result.best_move is None:
                terminal = _terminal_result(board)
                if terminal is not None:
                    winner, result_reason = terminal
                else:
                    winner, result_reason = "DRAW", "draw_or_no_move"
                break

            board.make_move(result.best_move)
            plies += 1
            if side == RED:
                red_moves += 1
            else:
                black_moves += 1

            terminal = _terminal_result(board)
            if terminal is not None:
                winner, result_reason = terminal
                break
        else:
            if adjudicate_max_plies:
                (
                    winner,
                    result_reason,
                    final_adjudication_score,
                ) = _adjudicate_position(
                    board,
                    adjudicator,
                    adjudication_threshold,
                )
            else:
                winner, result_reason = "DRAW", "draw_max_plies"

    return {
        "game_id": game_id,
        "red_evaluator": red_name,
        "black_evaluator": black_name,
        "winner": winner,
        "result_reason": result_reason,
        "plies": plies,
        "final_fen": board.fen(),
        "red_total_time": f"{red_total_time:.6f}",
        "black_total_time": f"{black_total_time:.6f}",
        "red_avg_nodes": f"{_avg(red_total_nodes, red_moves):.2f}",
        "black_avg_nodes": f"{_avg(black_total_nodes, black_moves):.2f}",
        "red_total_nodes": red_total_nodes,
        "black_total_nodes": black_total_nodes,
        "red_total_cutoffs": red_total_cutoffs,
        "black_total_cutoffs": black_total_cutoffs,
        "red_moves": red_moves,
        "black_moves": black_moves,
        "depth": depth,
        "max_plies": max_plies,
        "opening_random_plies": opening_random_plies,
        "adjudicate_max_plies": adjudicate_max_plies,
        "adjudicator_evaluator": adjudicator_evaluator,
        "adjudication_threshold": adjudication_threshold,
        "final_adjudication_score": final_adjudication_score,
        "seed": seed,
    }


def _scheduled_games(
    evaluator_names: list[str],
    games_per_pair: int,
) -> list[tuple[str, str]]:
    games: list[tuple[str, str]] = []
    for first, second in combinations(evaluator_names, 2):
        for _ in range(games_per_pair):
            games.append((first, second))
            games.append((second, first))
    return games


def _print_summary(rows: list[dict[str, object]], evaluator_names: list[str]) -> None:
    summary = {name: {"wins": 0, "losses": 0, "draws": 0} for name in evaluator_names}
    results = {"RED": 0, "BLACK": 0, "DRAW": 0}
    adjudicated_decisive = 0
    for row in rows:
        red = str(row["red_evaluator"])
        black = str(row["black_evaluator"])
        winner = row["winner"]
        results[str(winner)] += 1
        if str(row["result_reason"]) in (
            "max_plies_adjudicated_red",
            "max_plies_adjudicated_black",
        ):
            adjudicated_decisive += 1
        if winner == "RED":
            summary[red]["wins"] += 1
            summary[black]["losses"] += 1
        elif winner == "BLACK":
            summary[black]["wins"] += 1
            summary[red]["losses"] += 1
        else:
            summary[red]["draws"] += 1
            summary[black]["draws"] += 1

    print(f"Total games: {len(rows)}")
    print(
        f"Results: RED {results['RED']}, "
        f"BLACK {results['BLACK']}, DRAW {results['DRAW']}"
    )
    for name in evaluator_names:
        record = summary[name]
        print(
            f"{name}: {record['wins']}W/"
            f"{record['losses']}L/{record['draws']}D"
        )
    print(f"Max-plies adjudicated decisive games: {adjudicated_decisive}")


def run_tournament(
    output: str,
    evaluator_names: list[str] | None = None,
    games_per_pair: int = 2,
    depth: int = 2,
    max_plies: int = 120,
    seed: int = 0,
    mlp_model: str | None = None,
    opening_random_plies: int = 0,
    adjudicate_max_plies: bool = False,
    adjudicator_evaluator: str = "full_static",
    adjudication_threshold: int = 200,
) -> list[dict[str, object]]:
    """Run the tournament and return per-game rows."""
    if games_per_pair < 0:
        raise ValueError("games_per_pair must be non-negative.")
    if depth < 0 or max_plies < 0 or opening_random_plies < 0:
        raise ValueError("depth, max_plies, and opening_random_plies must be non-negative.")
    if adjudication_threshold < 0:
        raise ValueError("adjudication_threshold must be non-negative.")

    names = list(DEFAULT_EVALUATORS) if evaluator_names is None else evaluator_names
    evaluators = {name: get_evaluator(name, mlp_model) for name in names}
    adjudicator = (
        evaluators[adjudicator_evaluator]
        if adjudicator_evaluator in evaluators
        else get_evaluator(adjudicator_evaluator, mlp_model)
    )
    rng = random.Random(seed)
    rows: list[dict[str, object]] = []

    for game_id, (red_name, black_name) in enumerate(
        _scheduled_games(names, games_per_pair)
    ):
        rows.append(
            _play_game(
                game_id=game_id,
                red_name=red_name,
                black_name=black_name,
                red_evaluator=evaluators[red_name],
                black_evaluator=evaluators[black_name],
                depth=depth,
                max_plies=max_plies,
                opening_random_plies=opening_random_plies,
                adjudicate_max_plies=adjudicate_max_plies,
                adjudicator_evaluator=adjudicator_evaluator,
                adjudicator=adjudicator,
                adjudication_threshold=adjudication_threshold,
                seed=seed,
                rng=rng,
            )
        )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    _print_summary(rows, names)
    print(f"Output: {output}")
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--evaluators",
        default=",".join(DEFAULT_EVALUATORS),
        help="Comma-separated evaluator names.",
    )
    parser.add_argument("--games-per-pair", type=int, default=2)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-plies", type=int, default=120)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--mlp-model")
    parser.add_argument("--opening-random-plies", type=int, default=0)
    parser.add_argument("--adjudicate-max-plies", action="store_true")
    parser.add_argument("--adjudicator-evaluator", default="full_static")
    parser.add_argument("--adjudication-threshold", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_tournament(
        output=args.output,
        evaluator_names=_parse_evaluator_names(args.evaluators),
        games_per_pair=args.games_per_pair,
        depth=args.depth,
        max_plies=args.max_plies,
        seed=args.seed,
        mlp_model=args.mlp_model,
        opening_random_plies=args.opening_random_plies,
        adjudicate_max_plies=args.adjudicate_max_plies,
        adjudicator_evaluator=args.adjudicator_evaluator,
        adjudication_threshold=args.adjudication_threshold,
    )


if __name__ == "__main__":
    main()

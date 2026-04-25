"""Generate CSV training data for the optional MLP evaluator."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import random
import sys

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


def write_training_data(
    output: str,
    positions: int,
    max_plies: int,
    label_depth: int,
    seed: int,
) -> None:
    rng = random.Random(seed)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for _ in range(positions):
            board = random_position(max_plies, rng)
            fen = board.fen()
            features = extract_evaluation_features(board, RED)
            target_score = label_position(board, label_depth)
            if board.fen() != fen:
                raise RuntimeError("Feature extraction or labeling modified board.")
            writer.writerow(
                {
                    "fen": fen,
                    "side_to_move": board.side_to_move,
                    "material": features.material,
                    "position": features.position,
                    "mobility": features.mobility,
                    "king_safety": features.king_safety,
                    "threats": features.threats,
                    "target_score": target_score,
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--positions", type=int, default=1000)
    parser.add_argument("--max-plies", type=int, default=80)
    parser.add_argument("--label-depth", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_training_data(
        args.output,
        args.positions,
        args.max_plies,
        args.label_depth,
        args.seed,
    )
    print(f"Wrote {args.positions} positions to {args.output}")


if __name__ == "__main__":
    main()

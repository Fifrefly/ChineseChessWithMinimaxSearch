"""Evaluate a trained MLP model on one FEN position."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.core import BLACK, RED, Board
from engine.evaluation import (
    evaluate_piece_value_position_mobility_king_safety_and_threats,
    evaluate_weighted_static,
    extract_evaluation_features,
)
from experiments.mlp_evaluator import load_model, predict_mlp_score
from experiments.mlp_evaluator import feature_vector_from_board


def parse_perspective(value: str) -> str:
    if value == "RED":
        return RED
    if value == "BLACK":
        return BLACK
    raise ValueError("perspective must be RED or BLACK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--fen", required=True)
    parser.add_argument("--perspective", choices=["RED", "BLACK"], default="RED")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    perspective = parse_perspective(args.perspective)
    board = Board(args.fen)
    model = load_model(args.model)
    features = extract_evaluation_features(board, perspective)
    input_vector = feature_vector_from_board(board, perspective)

    print(f"FEN: {board.fen()}")
    print(f"side_to_move: {board.side_to_move}")
    print(f"Input features: {input_vector}")
    print(f"Features: {features}")
    print(f"MLP predicted score: {predict_mlp_score(board, model, perspective)}")
    print(
        "Full static score: "
        f"{evaluate_piece_value_position_mobility_king_safety_and_threats(board, perspective)}"
    )
    print(f"Weighted static score: {evaluate_weighted_static(board, perspective)}")


if __name__ == "__main__":
    main()

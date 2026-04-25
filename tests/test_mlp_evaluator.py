"""Optional tests for the PyTorch MLP evaluator helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("torch")

from engine.core import BLACK, RED, Board
from experiments.mlp_evaluator import (
    FEATURE_DIM,
    StaticEvaluationMLP,
    feature_vector_from_board,
    side_to_move_feature,
)

MINIMAL_FEN_RED_TO_MOVE = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"
MINIMAL_FEN_BLACK_TO_MOVE = "4k4/9/9/9/9/9/9/9/9/4K4 b - - 0 1"


def test_mlp_uses_six_input_features() -> None:
    model = StaticEvaluationMLP()

    assert FEATURE_DIM == 6
    assert model.network[0].in_features == 6


def test_feature_vector_appends_side_to_move_from_perspective() -> None:
    red_to_move = Board(MINIMAL_FEN_RED_TO_MOVE)
    black_to_move = Board(MINIMAL_FEN_BLACK_TO_MOVE)

    assert len(feature_vector_from_board(red_to_move, RED)) == 6
    assert feature_vector_from_board(red_to_move, RED)[-1] == 1.0
    assert feature_vector_from_board(red_to_move, BLACK)[-1] == -1.0
    assert feature_vector_from_board(black_to_move, RED)[-1] == -1.0
    assert feature_vector_from_board(black_to_move, BLACK)[-1] == 1.0


def test_side_to_move_feature_rejects_invalid_values() -> None:
    assert side_to_move_feature(RED, RED) == 1.0
    assert side_to_move_feature(BLACK, RED) == -1.0
    with pytest.raises(ValueError):
        side_to_move_feature("x", RED)

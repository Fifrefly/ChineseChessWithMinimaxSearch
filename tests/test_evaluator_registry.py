"""Tests for named experiment evaluator lookup."""

from __future__ import annotations

import pytest

from engine.core import RED, Board
from engine.evaluation import (
    evaluate_material,
    evaluate_piece_value_position_mobility_king_safety_and_threats,
    evaluate_weighted_static,
)
from experiments.evaluator_registry import (
    available_evaluator_names,
    get_evaluator,
    get_static_evaluator,
)


def test_available_evaluator_names_can_include_mlp() -> None:
    names = available_evaluator_names()
    assert names == [
        "material",
        "position",
        "mobility",
        "king_safety",
        "full_static",
        "weighted_static",
    ]
    assert available_evaluator_names(include_mlp=True) == names + ["mlp"]


def test_static_evaluators_can_be_retrieved_by_name() -> None:
    board = Board()

    assert get_static_evaluator("material") is evaluate_material
    assert get_static_evaluator("full_static") is (
        evaluate_piece_value_position_mobility_king_safety_and_threats
    )
    assert get_static_evaluator("weighted_static") is evaluate_weighted_static
    assert get_evaluator("material")(board, RED) == evaluate_material(board, RED)


def test_unknown_evaluator_raises_value_error() -> None:
    with pytest.raises(ValueError):
        get_static_evaluator("unknown")
    with pytest.raises(ValueError):
        get_evaluator("unknown")


def test_mlp_evaluator_requires_model_path() -> None:
    with pytest.raises(ValueError):
        get_evaluator("mlp")

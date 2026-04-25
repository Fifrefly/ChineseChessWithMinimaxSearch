"""Named evaluator registry for experiment scripts."""

from __future__ import annotations

from collections.abc import Callable

from engine.core import Board
from engine.evaluation import (
    evaluate_material,
    evaluate_piece_value_and_position,
    evaluate_piece_value_position_and_mobility,
    evaluate_piece_value_position_mobility_and_king_safety,
    evaluate_piece_value_position_mobility_king_safety_and_threats,
    evaluate_weighted_static,
)

Evaluator = Callable[[Board, str], int]

_STATIC_EVALUATORS: dict[str, Evaluator] = {
    "material": evaluate_material,
    "position": evaluate_piece_value_and_position,
    "mobility": evaluate_piece_value_position_and_mobility,
    "king_safety": evaluate_piece_value_position_mobility_and_king_safety,
    "full_static": evaluate_piece_value_position_mobility_king_safety_and_threats,
    "weighted_static": evaluate_weighted_static,
}


def available_evaluator_names(include_mlp: bool = False) -> list[str]:
    """Return evaluator names supported by the experiment registry."""
    names = list(_STATIC_EVALUATORS)
    if include_mlp:
        names.append("mlp")
    return names


def get_static_evaluator(name: str) -> Evaluator:
    """Return a registered non-ML evaluator by name."""
    try:
        return _STATIC_EVALUATORS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown static evaluator: {name}") from exc


def get_mlp_evaluator(model_path: str) -> Evaluator:
    """Load one MLP model and return an evaluator closure."""
    from experiments.mlp_evaluator import load_model, predict_mlp_score

    model = load_model(model_path)

    def evaluator(board: Board, perspective: str) -> int:
        return predict_mlp_score(board, model, perspective)

    return evaluator


def get_evaluator(name: str, mlp_model: str | None = None) -> Evaluator:
    """Return any registered evaluator by name."""
    if name == "mlp":
        if mlp_model is None:
            raise ValueError("mlp evaluator requires mlp_model.")
        return get_mlp_evaluator(mlp_model)
    return get_static_evaluator(name)

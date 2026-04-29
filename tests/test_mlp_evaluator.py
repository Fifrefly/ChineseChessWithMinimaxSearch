"""Optional tests for the PyTorch MLP evaluator helpers."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

pytest.importorskip("torch")

from engine.core import BLACK, RED, Board
from experiments.train_mlp_evaluator import load_training_data, train
from experiments.mlp_evaluator import (
    FEATURE_DIM,
    SCORE_SCALE,
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


def _write_training_csv(path: Path, targets: list[int]) -> None:
    fieldnames = [
        "fen",
        "side_to_move",
        "material",
        "position",
        "mobility",
        "king_safety",
        "threats",
        "target_score",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, target in enumerate(targets):
            writer.writerow(
                {
                    "fen": MINIMAL_FEN_RED_TO_MOVE,
                    "side_to_move": RED if index % 2 == 0 else BLACK,
                    "material": 0,
                    "position": 0,
                    "mobility": index,
                    "king_safety": 0,
                    "threats": 0,
                    "target_score": target,
                }
            )


def test_load_training_data_clips_targets(tmp_path: Path) -> None:
    training_csv = tmp_path / "train.csv"
    _write_training_csv(training_csv, [-10000, 10000])

    _, y = load_training_data(str(training_csv), clip_target_score=5000)

    assert y.squeeze().tolist() == [-5000 / SCORE_SCALE, 5000 / SCORE_SCALE]


def test_train_with_validation_split_writes_metrics(tmp_path: Path) -> None:
    training_csv = tmp_path / "train.csv"
    model_path = tmp_path / "model.pt"
    metrics_path = tmp_path / "metrics.csv"
    _write_training_csv(training_csv, [-100, 0, 100, 200])

    result = train(
        input_path=str(training_csv),
        output_model=str(model_path),
        epochs=2,
        batch_size=2,
        learning_rate=0.001,
        seed=123,
        validation_split=0.5,
        loss_name="huber",
        clip_target_score=5000,
        output_metrics=str(metrics_path),
    )

    assert model_path.exists()
    assert metrics_path.exists()
    assert len(result.metrics) == 2
    assert result.final_val_loss is not None
    with metrics_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["epoch"] == "1"
    assert "val_mae" in rows[0]

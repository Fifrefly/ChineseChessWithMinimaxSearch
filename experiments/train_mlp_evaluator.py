"""Train the optional MLP evaluator from generated CSV features."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from torch import nn

from engine.evaluation import EvaluationFeatures
from experiments.mlp_evaluator import (
    SCORE_SCALE,
    StaticEvaluationMLP,
    normalize_features,
    save_model,
    side_to_move_feature,
)


@dataclass(frozen=True, slots=True)
class TrainingResult:
    final_train_loss: float
    final_val_loss: float | None
    final_train_mae: float
    final_val_mae: float | None
    final_train_rmse: float
    final_val_rmse: float | None
    metrics: list[dict[str, float | int | None]]


def _target_stats(targets: np.ndarray) -> dict[str, float | int]:
    return {
        "samples": int(targets.size),
        "min": float(targets.min()),
        "max": float(targets.max()),
        "mean": float(targets.mean()),
        "std": float(targets.std()),
        "abs_ge_100000": int(np.count_nonzero(np.abs(targets) >= 100000)),
        "abs_ge_500000": int(np.count_nonzero(np.abs(targets) >= 500000)),
        "abs_ge_900000": int(np.count_nonzero(np.abs(targets) >= 900000)),
    }


def _print_target_stats(targets: np.ndarray, prefix: str = "target_score") -> None:
    stats = _target_stats(targets)
    print(f"number of samples: {stats['samples']}")
    print(f"{prefix} min: {stats['min']:.6f}")
    print(f"{prefix} max: {stats['max']:.6f}")
    print(f"{prefix} mean: {stats['mean']:.6f}")
    print(f"{prefix} std: {stats['std']:.6f}")
    print(f"count of abs(target_score) >= 100000: {stats['abs_ge_100000']}")
    print(f"count of abs(target_score) >= 500000: {stats['abs_ge_500000']}")
    print(f"count of abs(target_score) >= 900000: {stats['abs_ge_900000']}")


def load_training_data(
    path: str,
    clip_target_score: float | None = None,
    report_target_stats: bool = False,
) -> tuple[torch.Tensor, torch.Tensor]:
    features: list[list[float]] = []
    targets: list[float] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            feature_values = EvaluationFeatures(
                material=int(row["material"]),
                position=int(row["position"]),
                mobility=int(row["mobility"]),
                king_safety=int(row["king_safety"]),
                threats=int(row["threats"]),
            )
            features.append(
                normalize_features(feature_values)
                + [side_to_move_feature(row["side_to_move"])]
            )
            targets.append(float(row["target_score"]))

    if not features:
        raise ValueError("Training CSV contains no rows.")

    target_array = np.array(targets, dtype=np.float32)
    if report_target_stats:
        _print_target_stats(target_array)
    if clip_target_score is not None:
        if clip_target_score <= 0:
            raise ValueError("clip_target_score must be positive.")
        clipped = np.clip(target_array, -clip_target_score, clip_target_score)
        if report_target_stats:
            print(
                "clipped target_score min/max: "
                f"{clipped.min():.6f}/{clipped.max():.6f}"
            )
        target_array = clipped

    x = torch.tensor(np.array(features, dtype=np.float32), dtype=torch.float32)
    y = torch.tensor(target_array / SCORE_SCALE, dtype=torch.float32).view(-1, 1)
    return x, y


def _split_indices(
    sample_count: int,
    validation_split: float,
    seed: int,
) -> tuple[torch.Tensor, torch.Tensor | None]:
    if validation_split < 0 or validation_split >= 1:
        raise ValueError("validation_split must be in the range [0, 1).")
    generator = torch.Generator().manual_seed(seed)
    permutation = torch.randperm(sample_count, generator=generator)
    if validation_split == 0 or sample_count < 2:
        return permutation, None
    val_count = max(1, int(round(sample_count * validation_split)))
    val_count = min(val_count, sample_count - 1)
    return permutation[val_count:], permutation[:val_count]


def _loss_function(loss_name: str) -> nn.Module:
    if loss_name == "mse":
        return nn.MSELoss()
    if loss_name == "huber":
        return nn.SmoothL1Loss()
    raise ValueError(f"Unsupported loss: {loss_name}")


def _dataset_loss(
    model: StaticEvaluationMLP,
    x: torch.Tensor,
    y: torch.Tensor,
    indices: torch.Tensor,
    loss_fn: nn.Module,
) -> float:
    if indices.numel() == 0:
        return 0.0
    with torch.no_grad():
        predictions = model(x[indices])
        loss = loss_fn(predictions, y[indices])
    return float(loss.item())


def _original_scale_metrics(
    model: StaticEvaluationMLP,
    x: torch.Tensor,
    y: torch.Tensor,
    indices: torch.Tensor,
) -> tuple[float, float]:
    if indices.numel() == 0:
        return 0.0, 0.0
    with torch.no_grad():
        predictions = model(x[indices]) * SCORE_SCALE
        targets = y[indices] * SCORE_SCALE
        errors = predictions - targets
        mae = torch.mean(torch.abs(errors)).item()
        rmse = torch.sqrt(torch.mean(errors * errors)).item()
    return float(mae), float(rmse)


def _write_metrics_csv(
    path: str,
    metrics: list[dict[str, float | int | None]],
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "epoch",
        "train_loss",
        "val_loss",
        "train_mae",
        "val_mae",
        "train_rmse",
        "val_rmse",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)


def train(
    input_path: str,
    output_model: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
    validation_split: float = 0.0,
    loss_name: str = "mse",
    clip_target_score: float | None = None,
    report_target_stats: bool = False,
    output_metrics: str | None = None,
) -> TrainingResult:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    x, y = load_training_data(
        input_path,
        clip_target_score=clip_target_score,
        report_target_stats=report_target_stats,
    )
    train_indices, val_indices = _split_indices(x.size(0), validation_split, seed)
    model = StaticEvaluationMLP()
    loss_fn = _loss_function(loss_name)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    metrics: list[dict[str, float | int | None]] = []
    for epoch in range(1, epochs + 1):
        permutation = train_indices[torch.randperm(train_indices.size(0))]
        for start in range(0, train_indices.size(0), batch_size):
            indices = permutation[start : start + batch_size]
            predictions = model(x[indices])
            loss = loss_fn(predictions, y[indices])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        train_loss = _dataset_loss(model, x, y, train_indices, loss_fn)
        val_loss = (
            _dataset_loss(model, x, y, val_indices, loss_fn)
            if val_indices is not None
            else None
        )
        train_mae, train_rmse = _original_scale_metrics(model, x, y, train_indices)
        if val_indices is not None:
            val_mae, val_rmse = _original_scale_metrics(model, x, y, val_indices)
        else:
            val_mae, val_rmse = None, None
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "train_mae": train_mae,
            "val_mae": val_mae,
            "train_rmse": train_rmse,
            "val_rmse": val_rmse,
        }
        metrics.append(row)
        val_loss_text = "n/a" if val_loss is None else f"{val_loss:.6f}"
        val_mae_text = "n/a" if val_mae is None else f"{val_mae:.6f}"
        val_rmse_text = "n/a" if val_rmse is None else f"{val_rmse:.6f}"
        print(
            f"Epoch {epoch}/{epochs} "
            f"train_loss: {train_loss:.6f} "
            f"val_loss: {val_loss_text} "
            f"train_mae_original_scale: {train_mae:.6f} "
            f"val_mae_original_scale: {val_mae_text} "
            f"train_rmse_original_scale: {train_rmse:.6f} "
            f"val_rmse_original_scale: {val_rmse_text}"
        )

    save_model(model, output_model)
    if output_metrics is not None:
        _write_metrics_csv(output_metrics, metrics)
    final = metrics[-1]
    return TrainingResult(
        final_train_loss=float(final["train_loss"]),
        final_val_loss=(
            None if final["val_loss"] is None else float(final["val_loss"])
        ),
        final_train_mae=float(final["train_mae"]),
        final_val_mae=None if final["val_mae"] is None else float(final["val_mae"]),
        final_train_rmse=float(final["train_rmse"]),
        final_val_rmse=None
        if final["val_rmse"] is None
        else float(final["val_rmse"]),
        metrics=metrics,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-model", required=True)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--validation-split", type=float, default=0.2)
    parser.add_argument("--loss", choices=("mse", "huber"), default="huber")
    parser.add_argument("--clip-target-score", type=float)
    parser.add_argument("--report-target-stats", action="store_true")
    parser.add_argument("--output-metrics")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = train(
        args.input,
        args.output_model,
        args.epochs,
        args.batch_size,
        args.learning_rate,
        args.seed,
        validation_split=args.validation_split,
        loss_name=args.loss,
        clip_target_score=args.clip_target_score,
        report_target_stats=args.report_target_stats,
        output_metrics=args.output_metrics,
    )
    print(f"Final train_loss: {result.final_train_loss:.6f}")
    if result.final_val_loss is not None:
        print(f"Final val_loss: {result.final_val_loss:.6f}")
    print(f"Final train_mae: {result.final_train_mae:.6f}")
    if result.final_val_mae is not None:
        print(f"Final val_mae: {result.final_val_mae:.6f}")
    print(f"Final train_rmse: {result.final_train_rmse:.6f}")
    if result.final_val_rmse is not None:
        print(f"Final val_rmse: {result.final_val_rmse:.6f}")
    print(f"Saved model to {args.output_model}")
    if args.output_metrics:
        print(f"Saved metrics to {args.output_metrics}")


if __name__ == "__main__":
    main()

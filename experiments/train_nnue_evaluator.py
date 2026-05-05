"""Train and compare an NNUE-style evaluator from generated Xiangqi data."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import json
import math
from pathlib import Path
import random
import sys
from time import perf_counter
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from engine.core import (
    ADVISER,
    BISHOP,
    BLACK,
    BOARD_COLS,
    BOARD_ROWS,
    CANNON,
    KING,
    KNIGHT,
    PAWN,
    RED,
    ROOK,
    Board,
)
from experiments.evaluator_registry import get_static_evaluator

PIECE_TYPES = (KING, ADVISER, BISHOP, KNIGHT, ROOK, CANNON, PAWN)
COLORS = (RED, BLACK)
PIECE_TYPE_INDEX = {piece_type: index for index, piece_type in enumerate(PIECE_TYPES)}
COLOR_INDEX = {color: index for index, color in enumerate(COLORS)}
SQUARE_COUNT = BOARD_ROWS * BOARD_COLS
BOARD_FEATURE_DIM = len(COLORS) * len(PIECE_TYPES) * SQUARE_COUNT
SIDE_TO_MOVE_INDEX = BOARD_FEATURE_DIM
FEATURE_DIM = BOARD_FEATURE_DIM + 1
DEFAULT_STATIC_EVALUATORS = (
    "material",
    "position",
    "mobility",
    "king_safety",
    "full_static",
    "weighted_static",
)


@dataclass(frozen=True, slots=True)
class DatasetBundle:
    rows: list[dict[str, str]]
    features: np.ndarray
    targets: np.ndarray
    train_indices: np.ndarray
    val_indices: np.ndarray
    test_indices: np.ndarray


class ClippedReLU(nn.Module):
    """ReLU clipped to [0, 1], matching the usual NNUE activation style."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.clamp(x, 0.0, 1.0)


class XiangqiNNUE(nn.Module):
    """Small NNUE-style evaluator over binary piece-square features."""

    def __init__(self, hidden_size: int = 256, bottleneck_size: int = 32) -> None:
        super().__init__()
        self.input = nn.Linear(FEATURE_DIM, hidden_size)
        self.network = nn.Sequential(
            ClippedReLU(),
            nn.Linear(hidden_size, bottleneck_size),
            ClippedReLU(),
            nn.Linear(bottleneck_size, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(self.input(features))


def feature_index(color: str, piece_type: str, row: int, col: int) -> int:
    return (
        COLOR_INDEX[color] * len(PIECE_TYPES) * SQUARE_COUNT
        + PIECE_TYPE_INDEX[piece_type] * SQUARE_COUNT
        + row * BOARD_COLS
        + col
    )


def encode_board(board: Board) -> np.ndarray:
    features = np.zeros(FEATURE_DIM, dtype=np.float32)
    for position, piece in board.piece_map().items():
        features[feature_index(piece.color, piece.type, position.row, position.col)] = 1.0
    features[SIDE_TO_MOVE_INDEX] = 1.0 if board.side_to_move == RED else -1.0
    return features


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        required = {"fen", "target_score"}
        missing = required.difference(reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def split_indices(
    sample_count: int,
    val_split: float,
    test_split: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if sample_count < 3:
        raise ValueError("Need at least 3 samples to create train/val/test splits.")
    if val_split <= 0 or test_split <= 0 or val_split + test_split >= 1:
        raise ValueError("val_split and test_split must be positive and sum below 1.")
    permutation = np.array(random.Random(seed).sample(range(sample_count), sample_count))
    test_count = max(1, round(sample_count * test_split))
    val_count = max(1, round(sample_count * val_split))
    if test_count + val_count >= sample_count:
        raise ValueError("Validation/test splits leave no training samples.")
    test_indices = permutation[:test_count]
    val_indices = permutation[test_count : test_count + val_count]
    train_indices = permutation[test_count + val_count :]
    return train_indices, val_indices, test_indices


def build_dataset(
    input_csv: Path,
    val_split: float,
    test_split: float,
    seed: int,
) -> DatasetBundle:
    rows = load_rows(input_csv)
    features = np.zeros((len(rows), FEATURE_DIM), dtype=np.float32)
    targets = np.zeros(len(rows), dtype=np.float32)
    for index, row in enumerate(rows):
        features[index] = encode_board(Board(row["fen"]))
        targets[index] = float(row["target_score"])
    train_indices, val_indices, test_indices = split_indices(
        len(rows),
        val_split,
        test_split,
        seed,
    )
    return DatasetBundle(rows, features, targets, train_indices, val_indices, test_indices)


def write_split_csv(rows: list[dict[str, str]], indices: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("Cannot write split CSV from an empty row set.")
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in indices:
            writer.writerow(rows[int(index)])


def make_loader(
    features: np.ndarray,
    targets: np.ndarray,
    indices: np.ndarray,
    batch_size: int,
    target_scale: float,
    clip_train_target: float | None,
    shuffle: bool,
    device: torch.device,
) -> DataLoader:
    active_targets = targets[indices].copy()
    if clip_train_target is not None:
        active_targets = np.clip(active_targets, -clip_train_target, clip_train_target)
    x = torch.tensor(features[indices], dtype=torch.float32)
    y = torch.tensor(active_targets / target_scale, dtype=torch.float32).view(-1, 1)
    dataset = TensorDataset(x, y)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        pin_memory=device.type == "cuda",
    )


def predict_model(
    model: nn.Module,
    features: np.ndarray,
    indices: np.ndarray,
    target_scale: float,
    device: torch.device,
    batch_size: int,
) -> np.ndarray:
    model.eval()
    predictions: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(indices), batch_size):
            batch_indices = indices[start : start + batch_size]
            x = torch.tensor(features[batch_indices], dtype=torch.float32, device=device)
            y_hat = model(x).detach().cpu().numpy().reshape(-1) * target_scale
            predictions.append(y_hat)
    if not predictions:
        return np.array([], dtype=np.float32)
    return np.concatenate(predictions).astype(np.float32)


def metrics_for_predictions(targets: np.ndarray, predictions: np.ndarray) -> dict[str, float | int]:
    if targets.shape != predictions.shape:
        raise ValueError("targets and predictions must have identical shapes.")
    errors = predictions - targets
    abs_errors = np.abs(errors)
    rmse = float(math.sqrt(float(np.mean(errors * errors)))) if len(errors) else 0.0
    target_mean = float(np.mean(targets)) if len(targets) else 0.0
    ss_res = float(np.sum(errors * errors))
    ss_tot = float(np.sum((targets - target_mean) ** 2))
    if len(targets) > 1 and float(np.std(predictions)) > 0 and float(np.std(targets)) > 0:
        corr = float(np.corrcoef(targets, predictions)[0, 1])
    else:
        corr = 0.0
    nonzero_mask = targets != 0
    if int(np.count_nonzero(nonzero_mask)) > 0:
        sign_accuracy = float(
            np.mean(np.sign(predictions[nonzero_mask]) == np.sign(targets[nonzero_mask]))
        )
    else:
        sign_accuracy = 0.0
    return {
        "samples": int(len(targets)),
        "mae": float(np.mean(abs_errors)) if len(abs_errors) else 0.0,
        "rmse": rmse,
        "bias": float(np.mean(errors)) if len(errors) else 0.0,
        "max_abs_error": float(np.max(abs_errors)) if len(abs_errors) else 0.0,
        "r2": 0.0 if ss_tot == 0 else float(1.0 - ss_res / ss_tot),
        "pearson": corr,
        "sign_accuracy": sign_accuracy,
    }


def summarize_subset_metrics(
    evaluator_name: str,
    targets: np.ndarray,
    predictions: np.ndarray,
    output_rows: list[dict[str, float | int | str]],
) -> None:
    all_metrics = metrics_for_predictions(targets, predictions)
    output_rows.append({"evaluator": evaluator_name, "subset": "all", **all_metrics})
    quiet_mask = np.abs(targets) < 900000
    if int(np.count_nonzero(quiet_mask)) > 0:
        quiet_metrics = metrics_for_predictions(targets[quiet_mask], predictions[quiet_mask])
        output_rows.append(
            {"evaluator": evaluator_name, "subset": "non_mate", **quiet_metrics}
        )


def evaluate_static_functions(
    rows: list[dict[str, str]],
    indices: np.ndarray,
    evaluator_names: tuple[str, ...],
) -> dict[str, np.ndarray]:
    evaluators: dict[str, Callable[[Board, str], int]] = {
        name: get_static_evaluator(name) for name in evaluator_names
    }
    predictions = {
        name: np.zeros(len(indices), dtype=np.float32) for name in evaluator_names
    }
    for output_index, row_index in enumerate(indices):
        board = Board(rows[int(row_index)]["fen"])
        original_fen = board.fen()
        for name, evaluator in evaluators.items():
            predictions[name][output_index] = float(evaluator(board, RED))
            if board.fen() != original_fen:
                raise RuntimeError(f"{name} modified board state.")
    return predictions


def evaluate_loss(
    model: nn.Module,
    loader: DataLoader,
    loss_fn: nn.Module,
    device: torch.device,
) -> float:
    model.eval()
    total_loss = 0.0
    total_samples = 0
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            loss = loss_fn(model(x), y)
            total_loss += float(loss.item()) * x.size(0)
            total_samples += x.size(0)
    return total_loss / max(1, total_samples)


def write_metrics_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(
    path: Path,
    args: argparse.Namespace,
    dataset: DatasetBundle,
    compare_rows: list[dict[str, float | int | str]],
    device: torch.device,
    elapsed_seconds: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    best_all = min(
        (row for row in compare_rows if row["subset"] == "all"),
        key=lambda row: float(row["mae"]),
    )
    best_non_mate = min(
        (row for row in compare_rows if row["subset"] == "non_mate"),
        key=lambda row: float(row["mae"]),
    )
    lines = [
        "# NNUE Training Report",
        "",
        "## Data split",
        "",
        f"- input: `{args.input}`",
        f"- train: {len(dataset.train_indices)}",
        f"- val: {len(dataset.val_indices)}",
        f"- test: {len(dataset.test_indices)}",
        f"- seed: {args.seed}",
        "",
        "## Model",
        "",
        f"- feature_dim: {FEATURE_DIM}",
        f"- hidden_size: {args.hidden_size}",
        f"- bottleneck_size: {args.bottleneck_size}",
        f"- target_scale: {args.target_scale}",
        f"- clip_train_target: {args.clip_train_target}",
        f"- device: {device}",
        f"- elapsed_seconds: {elapsed_seconds:.2f}",
        "",
        "## Test comparison",
        "",
        "| evaluator | subset | samples | MAE | RMSE | R2 | Pearson | sign_acc |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in compare_rows:
        lines.append(
            "| {evaluator} | {subset} | {samples} | {mae:.3f} | {rmse:.3f} | "
            "{r2:.4f} | {pearson:.4f} | {sign_accuracy:.4f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Best by MAE",
            "",
            f"- all test rows: {best_all['evaluator']} (MAE {float(best_all['mae']):.3f})",
            "- non_mate excludes rows with `abs(target_score) >= 900000`, because those "
            "are forced-mate search labels that dominate static-regression metrics.",
            f"- non_mate rows: {best_non_mate['evaluator']} "
            f"(MAE {float(best_non_mate['mae']):.3f})",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def train_and_compare(args: argparse.Namespace) -> None:
    start = perf_counter()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset(Path(args.input), args.val_split, args.test_split, args.seed)
    write_split_csv(dataset.rows, dataset.train_indices, output_dir / "nnue_train.csv")
    write_split_csv(dataset.rows, dataset.val_indices, output_dir / "nnue_val.csv")
    write_split_csv(dataset.rows, dataset.test_indices, output_dir / "nnue_test.csv")

    device = torch.device(
        "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    )
    if args.device == "auto" and device.type != "cuda":
        device = torch.device("cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    model = XiangqiNNUE(args.hidden_size, args.bottleneck_size).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    loss_fn: nn.Module = nn.SmoothL1Loss(beta=args.huber_beta)
    train_loader = make_loader(
        dataset.features,
        dataset.targets,
        dataset.train_indices,
        args.batch_size,
        args.target_scale,
        args.clip_train_target,
        True,
        device,
    )
    val_loader = make_loader(
        dataset.features,
        dataset.targets,
        dataset.val_indices,
        args.batch_size,
        args.target_scale,
        args.clip_train_target,
        False,
        device,
    )

    epoch_rows: list[dict[str, float | int | str]] = []
    best_val_loss = float("inf")
    best_state: dict[str, torch.Tensor] | None = None
    best_epoch = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss_sum = 0.0
        train_samples = 0
        for x, y in train_loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            loss = loss_fn(model(x), y)
            loss.backward()
            optimizer.step()
            train_loss_sum += float(loss.item()) * x.size(0)
            train_samples += x.size(0)

        train_loss = train_loss_sum / max(1, train_samples)
        val_loss = evaluate_loss(model, val_loader, loss_fn, device)
        val_predictions = predict_model(
            model,
            dataset.features,
            dataset.val_indices,
            args.target_scale,
            device,
            args.batch_size,
        )
        val_metrics = metrics_for_predictions(
            np.clip(dataset.targets[dataset.val_indices], -args.eval_clip, args.eval_clip)
            if args.eval_clip is not None
            else dataset.targets[dataset.val_indices],
            np.clip(val_predictions, -args.eval_clip, args.eval_clip)
            if args.eval_clip is not None
            else val_predictions,
        )
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_mae": val_metrics["mae"],
            "val_rmse": val_metrics["rmse"],
        }
        epoch_rows.append(row)
        print(
            f"Epoch {epoch}/{args.epochs} "
            f"train_loss={train_loss:.6f} "
            f"val_loss={val_loss:.6f} "
            f"val_mae={float(val_metrics['mae']):.3f} "
            f"val_rmse={float(val_metrics['rmse']):.3f}",
            flush=True,
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            best_state = {
                key: value.detach().cpu().clone()
                for key, value in model.state_dict().items()
            }

    if best_state is not None:
        model.load_state_dict(best_state)

    model_path = output_dir / "xiangqi_nnue.pt"
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "feature_dim": FEATURE_DIM,
        "hidden_size": args.hidden_size,
        "bottleneck_size": args.bottleneck_size,
        "target_scale": args.target_scale,
        "piece_types": PIECE_TYPES,
        "colors": COLORS,
        "side_to_move_index": SIDE_TO_MOVE_INDEX,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "seed": args.seed,
    }
    torch.save(checkpoint, model_path)
    write_metrics_csv(output_dir / "nnue_epoch_metrics.csv", epoch_rows)

    test_targets = dataset.targets[dataset.test_indices]
    nnue_predictions = predict_model(
        model,
        dataset.features,
        dataset.test_indices,
        args.target_scale,
        device,
        args.batch_size,
    )
    compare_rows: list[dict[str, float | int | str]] = []
    summarize_subset_metrics("nnue", test_targets, nnue_predictions, compare_rows)
    static_predictions = evaluate_static_functions(
        dataset.rows,
        dataset.test_indices,
        tuple(args.static_evaluators.split(",")),
    )
    for name, predictions in static_predictions.items():
        summarize_subset_metrics(name, test_targets, predictions, compare_rows)

    write_metrics_csv(output_dir / "nnue_test_comparison.csv", compare_rows)
    metadata = {
        "input": args.input,
        "output_dir": str(output_dir),
        "train_samples": int(len(dataset.train_indices)),
        "val_samples": int(len(dataset.val_indices)),
        "test_samples": int(len(dataset.test_indices)),
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "elapsed_seconds": perf_counter() - start,
    }
    (output_dir / "nnue_run_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_summary(
        output_dir / "nnue_training_report.md",
        args,
        dataset,
        compare_rows,
        device,
        perf_counter() - start,
    )
    print(f"Saved model: {model_path}")
    print(f"Saved comparison: {output_dir / 'nnue_test_comparison.csv'}")
    print(f"Saved report: {output_dir / 'nnue_training_report.md'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/nnue_training_data.csv")
    parser.add_argument("--output-dir", default="data/nnue")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=2048)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--hidden-size", type=int, default=256)
    parser.add_argument("--bottleneck-size", type=int, default=32)
    parser.add_argument("--target-scale", type=float, default=1000.0)
    parser.add_argument("--clip-train-target", type=float, default=5000.0)
    parser.add_argument("--huber-beta", type=float, default=1.0)
    parser.add_argument("--val-split", type=float, default=0.1)
    parser.add_argument("--test-split", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument(
        "--static-evaluators",
        default=",".join(DEFAULT_STATIC_EVALUATORS),
    )
    parser.add_argument(
        "--eval-clip",
        type=float,
        default=None,
        help="Optional clipping only for per-epoch validation display.",
    )
    return parser.parse_args()


def main() -> None:
    train_and_compare(parse_args())


if __name__ == "__main__":
    main()

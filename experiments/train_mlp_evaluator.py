"""Train the optional MLP evaluator from generated CSV features."""

from __future__ import annotations

import argparse
import csv
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


def load_training_data(path: str) -> tuple[torch.Tensor, torch.Tensor]:
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
            targets.append(float(row["target_score"]) / SCORE_SCALE)

    if not features:
        raise ValueError("Training CSV contains no rows.")

    x = torch.tensor(np.array(features, dtype=np.float32), dtype=torch.float32)
    y = torch.tensor(np.array(targets, dtype=np.float32), dtype=torch.float32).view(-1, 1)
    return x, y


def train(
    input_path: str,
    output_model: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    seed: int,
) -> float:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    x, y = load_training_data(input_path)
    model = StaticEvaluationMLP()
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    final_loss = 0.0
    for epoch in range(1, epochs + 1):
        permutation = torch.randperm(x.size(0))
        for start in range(0, x.size(0), batch_size):
            indices = permutation[start : start + batch_size]
            predictions = model(x[indices])
            loss = loss_fn(predictions, y[indices])
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            final_loss = loss.item()
        print(f"Epoch {epoch}/{epochs} loss: {final_loss:.6f}")

    save_model(model, output_model)
    return final_loss


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-model", required=True)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    final_loss = train(
        args.input,
        args.output_model,
        args.epochs,
        args.batch_size,
        args.learning_rate,
        args.seed,
    )
    print(f"Final training loss: {final_loss:.6f}")
    print(f"Saved model to {args.output_model}")


if __name__ == "__main__":
    main()

"""Optional PyTorch MLP evaluator for static Xiangqi evaluation features."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from torch import nn

from engine.core import BLACK, RED, Board
from engine.evaluation import EvaluationFeatures, extract_evaluation_features

FEATURE_DIM = 6
SCORE_SCALE = 1000.0


class StaticEvaluationMLP(nn.Module):
    """Small MLP that maps static features plus side-to-move to one score."""

    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(FEATURE_DIM, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)


def normalize_features(features: EvaluationFeatures) -> list[float]:
    material, position, mobility, king_safety, threats = features.as_tuple()
    return [
        material / 1000.0,
        position / 100.0,
        mobility / 100.0,
        king_safety / 100.0,
        threats / 100.0,
    ]


def side_to_move_feature(side_to_move: str, perspective: str = RED) -> float:
    if side_to_move not in (RED, BLACK):
        raise ValueError(f"Invalid side_to_move {side_to_move!r}.")
    if perspective not in (RED, BLACK):
        raise ValueError(f"Invalid perspective {perspective!r}.")
    return 1.0 if side_to_move == perspective else -1.0


def feature_vector_from_board(board: Board, perspective: str = RED) -> list[float]:
    vector = normalize_features(extract_evaluation_features(board, perspective))
    return vector + [side_to_move_feature(board.side_to_move, perspective)]


def predict_mlp_score(
    board: Board,
    model: StaticEvaluationMLP,
    perspective: str = RED,
) -> int:
    original_fen = board.fen()
    model.eval()
    device = next(model.parameters()).device
    with torch.no_grad():
        features = torch.tensor(
            [feature_vector_from_board(board, perspective)],
            dtype=torch.float32,
            device=device,
        )
        predicted_score = model(features).squeeze().item() * SCORE_SCALE
    if board.fen() != original_fen:
        raise RuntimeError("predict_mlp_score modified the board.")
    return int(round(predicted_score))


def save_model(model: StaticEvaluationMLP, path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)


def load_model(path: str, device: str = "cpu") -> StaticEvaluationMLP:
    model = StaticEvaluationMLP()
    state = torch.load(path, map_location=device)
    model.load_state_dict(state)
    model.to(device)
    model.eval()
    return model

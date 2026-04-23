"""Combined evaluation wrapper.

For the minimax baseline, this simply delegates to material evaluation. Later
phases can add piece-square, mobility, and king-safety terms behind the same
function signature.
"""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.game import Game
from eval.material import evaluate_material


def evaluate(game_or_board: Game | Board, perspective: str) -> int:
    """Return the current combined score from ``perspective``."""
    return evaluate_material(game_or_board, perspective)

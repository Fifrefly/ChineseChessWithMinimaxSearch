"""Unit tests for the baseline material evaluator."""

from __future__ import annotations

from chinese_chess.constants import BLACK, RED, ROOK
from chinese_chess.game import Game
from eval.material import PIECE_VALUES, evaluate_material


def test_default_position_is_materially_balanced() -> None:
    game = Game()

    assert evaluate_material(game, RED) == 0
    assert evaluate_material(game, BLACK) == 0


def test_extra_red_rook_scores_positive_for_red_and_negative_for_black() -> None:
    game = Game("4k4/9/9/9/9/9/9/9/9/R3K4 r - - 0 1")

    assert evaluate_material(game, RED) == PIECE_VALUES[ROOK]
    assert evaluate_material(game, BLACK) == -PIECE_VALUES[ROOK]


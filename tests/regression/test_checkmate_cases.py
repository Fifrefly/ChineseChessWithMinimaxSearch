"""Regression tests for simple checkmate positions."""

from __future__ import annotations

from chinese_chess.constants import RED
from chinese_chess.game import Game
from chinese_chess.rules.terminal import is_checkmate

CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"


def test_red_king_mated_by_pawn_with_escape_squares_covered() -> None:
    game = Game(CHECKMATE_FEN)

    assert game.get_legal_moves() == []
    assert game.is_check() is True
    assert game.is_checkmate() is True
    assert is_checkmate(game.board_obj, RED) is True


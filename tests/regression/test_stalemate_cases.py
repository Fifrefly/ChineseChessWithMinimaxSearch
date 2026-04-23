"""Regression tests for simple stalemate positions."""

from __future__ import annotations

from chinese_chess.game import Game

STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"


def test_red_king_stalemated_by_rook_coverage_and_pinned_advisor() -> None:
    game = Game(STALEMATE_FEN)

    assert game.is_check() is False
    assert game.get_legal_moves() == []
    assert game.is_stalemate() is True
    assert game.game_over() is True


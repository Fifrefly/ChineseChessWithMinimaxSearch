"""Regression tests for minimax behavior around terminal positions."""

from __future__ import annotations

from chinese_chess.game import Game
from search.minimax import MATE_SCORE, search_best_move

CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"


def test_checkmate_scores_as_bad_for_side_to_move() -> None:
    result = search_best_move(Game(CHECKMATE_FEN), depth=2)

    assert result.best_move is None
    assert result.best_score == -MATE_SCORE


def test_stalemate_scores_as_draw() -> None:
    result = search_best_move(Game(STALEMATE_FEN), depth=2)

    assert result.best_move is None
    assert result.best_score == 0


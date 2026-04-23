"""Unit tests for rule-level check helpers."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import BLACK, RED
from chinese_chess.rules.check import has_legal_moves, is_check

CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"


def test_is_check_wraps_attack_detection() -> None:
    board = Board(CHECKMATE_FEN)

    assert is_check(board, RED) is True
    assert is_check(board, BLACK) is False


def test_has_legal_moves_uses_legal_filtering() -> None:
    assert has_legal_moves(Board(), RED) is True
    assert has_legal_moves(Board(STALEMATE_FEN), RED) is False


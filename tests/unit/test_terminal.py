"""Unit tests for terminal-state helpers."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import RED
from chinese_chess.game import Game
from chinese_chess.rules.terminal import game_over, is_checkmate, is_stalemate

CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"


def test_checkmate_requires_check_and_no_legal_moves() -> None:
    board = Board(CHECKMATE_FEN)

    assert is_checkmate(board, RED) is True
    assert is_stalemate(board, RED) is False
    assert game_over(board, RED) is True


def test_stalemate_requires_no_check_and_no_legal_moves() -> None:
    board = Board(STALEMATE_FEN)

    assert is_checkmate(board, RED) is False
    assert is_stalemate(board, RED) is True
    assert game_over(board, RED) is True


def test_non_terminal_default_position_has_legal_moves() -> None:
    board = Board()

    assert is_checkmate(board, RED) is False
    assert is_stalemate(board, RED) is False
    assert game_over(board, RED) is False


def test_game_terminal_methods_match_rules() -> None:
    game = Game(CHECKMATE_FEN)

    assert game.is_check() is True
    assert game.is_checkmate() is True
    assert game.is_stalemate() is False
    assert game.game_over() is True


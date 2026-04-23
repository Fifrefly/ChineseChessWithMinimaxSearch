"""Regression tests for flying-general legality."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import RED
from chinese_chess.movegen.attack import is_in_check, is_square_attacked
from chinese_chess.movegen.legal import generate_legal_moves


def iccs(moves: list) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_kings_on_open_file_attack_each_other() -> None:
    board = Board("4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1")

    assert is_square_attacked(board, "e0", "b") is True
    assert is_in_check(board, RED) is True


def test_king_may_not_move_forward_if_generals_still_face() -> None:
    board = Board("4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1")

    moves = iccs(generate_legal_moves(board, RED))

    assert "e0e1" not in moves
    assert {"e0d0", "e0f0"}.issubset(moves)


def test_moving_screen_away_between_generals_is_illegal() -> None:
    board = Board("4k4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1")

    moves = iccs(generate_legal_moves(board, RED))

    assert "e1d1" not in moves
    assert "e1f1" not in moves
    assert "e1e2" in moves


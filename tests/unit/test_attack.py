"""Unit tests for attack and check detection."""

from __future__ import annotations

import pytest

from chinese_chess.board import Board
from chinese_chess.constants import ADVISER, BISHOP, BLACK, CANNON, KING, KNIGHT, PAWN, RED, ROOK
from chinese_chess.exceptions import BoardStateError
from chinese_chess.movegen.attack import find_king, is_in_check, is_square_attacked
from chinese_chess.types import Piece

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def test_find_king_returns_expected_position() -> None:
    board = Board(MINIMAL_FEN)

    assert str(find_king(board, RED)) == "e0"
    assert str(find_king(board, BLACK)) == "e9"


def test_flying_general_counts_as_attack() -> None:
    board = Board(MINIMAL_FEN)

    assert is_square_attacked(board, "e0", BLACK) is True
    assert is_in_check(board, RED) is True


def test_rook_attack_requires_clear_line() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("e5", Piece(ROOK, BLACK))

    assert is_square_attacked(board, "e0", BLACK) is True
    board.set_piece("e3", Piece(PAWN, RED))
    assert is_square_attacked(board, "e0", BLACK) is False


def test_cannon_attack_requires_exactly_one_screen() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("d9", board.clear_piece("e9"))
    board.set_piece("e4", Piece(CANNON, BLACK))

    assert is_square_attacked(board, "e0", BLACK) is False
    board.set_piece("e2", Piece(PAWN, RED))
    assert is_square_attacked(board, "e0", BLACK) is True
    board.set_piece("e1", Piece(PAWN, RED))
    assert is_square_attacked(board, "e0", BLACK) is False


def test_horse_attack_respects_horse_leg() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("d9", board.clear_piece("e9"))
    board.set_piece("d2", Piece(KNIGHT, BLACK))

    assert is_square_attacked(board, "e0", BLACK) is True
    board.set_piece("d1", Piece(PAWN, RED))
    assert is_square_attacked(board, "e0", BLACK) is False


def test_advisor_and_elephant_attacks_follow_piece_rules() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("d1", Piece(ADVISER, RED))
    board.set_piece("c4", Piece(BISHOP, RED))

    assert is_square_attacked(board, "e0", RED) is True
    board.clear_piece("d1")
    assert is_square_attacked(board, "e2", RED) is True
    board.set_piece("d3", Piece(PAWN, BLACK))
    assert is_square_attacked(board, "e2", RED) is False


def test_missing_king_raises_board_state_error() -> None:
    board = Board(MINIMAL_FEN)
    board.clear_piece("e0")

    with pytest.raises(BoardStateError):
        find_king(board, RED)

"""Unit tests for the mutable board state container."""

from __future__ import annotations

import pytest

from chinese_chess.board import Board
from chinese_chess.constants import BLACK, DEFAULT_FEN, KING, KNIGHT, RED, ROOK
from chinese_chess.exceptions import BoardStateError
from chinese_chess.types import Piece, Position


def test_board_starts_from_default_fen() -> None:
    board = Board()

    assert board.fen() == DEFAULT_FEN
    assert board.side_to_move == RED


def test_board_can_read_set_and_clear_pieces() -> None:
    board = Board()

    rook = board.get_piece("a9")
    assert rook == Piece(ROOK, BLACK)

    knight = Piece(KNIGHT, RED)
    board.set_piece(Position.from_algebraic("e4"), knight)
    assert board.get_piece((5, 4)) == knight

    removed = board.clear_piece("e4")
    assert removed == knight
    assert board.get_piece("e4") is None


def test_board_rejects_out_of_bounds_coordinates() -> None:
    board = Board()

    assert board.is_inside(Position(0, 0)) is True
    assert board.is_inside(Position(10, 0)) is False
    assert board.is_inside("z9") is False
    with pytest.raises(BoardStateError):
        board.get_piece(Position(10, 0))
    with pytest.raises(BoardStateError):
        board.get_piece("z9")


def test_board_loads_custom_fen_and_preserves_counters() -> None:
    fen = "4k4/9/9/9/9/9/9/9/9/4K4 b - - 3 7"
    board = Board(fen)

    assert board.get_piece("e9") == Piece(KING, BLACK)
    assert board.get_piece("e0") == Piece(KING, RED)
    assert board.side_to_move == BLACK
    assert board.halfmove_clock == 3
    assert board.fullmove_number == 7
    assert board.fen() == fen


def test_board_matrix_view_is_a_copy() -> None:
    board = Board()
    matrix = board.to_matrix()

    matrix[0][0] = None

    assert board.get_piece("a9") == Piece(ROOK, BLACK)

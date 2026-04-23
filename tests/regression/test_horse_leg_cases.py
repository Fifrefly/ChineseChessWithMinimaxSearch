"""Regression tests for horse-leg blocking."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import KNIGHT, PAWN, RED
from chinese_chess.movegen.pseudo_legal import generate_horse_moves
from chinese_chess.types import Move, Piece, Position

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def iccs(moves: list[Move]) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_horse_leg_blocks_two_moves_in_that_axis_only() -> None:
    board = Board(MINIMAL_FEN)
    horse = Piece(KNIGHT, RED)
    board.set_piece("e4", horse)
    board.set_piece("e5", Piece(PAWN, RED))

    moves = iccs(generate_horse_moves(board, Position.from_algebraic("e4"), horse))

    assert "e4d6" not in moves
    assert "e4f6" not in moves
    assert "e4d2" in moves
    assert "e4f2" in moves
    assert "e4c5" in moves
    assert "e4g5" in moves


def test_horizontal_horse_leg_blocks_left_l_shape_moves() -> None:
    board = Board(MINIMAL_FEN)
    horse = Piece(KNIGHT, RED)
    board.set_piece("e4", horse)
    board.set_piece("d4", Piece(PAWN, RED))

    moves = iccs(generate_horse_moves(board, Position.from_algebraic("e4"), horse))

    assert "e4c5" not in moves
    assert "e4c3" not in moves
    assert "e4g5" in moves
    assert "e4g3" in moves


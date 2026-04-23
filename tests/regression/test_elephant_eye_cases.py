"""Regression tests for elephant-eye blocking and river limits."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import BISHOP, PAWN, RED
from chinese_chess.movegen.pseudo_legal import generate_elephant_moves
from chinese_chess.types import Move, Piece, Position

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def iccs(moves: list[Move]) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_elephant_eye_blocks_only_the_corresponding_diagonal() -> None:
    board = Board(MINIMAL_FEN)
    elephant = Piece(BISHOP, RED)
    board.set_piece("e2", elephant)
    board.set_piece("d3", Piece(PAWN, RED))

    moves = iccs(generate_elephant_moves(board, Position.from_algebraic("e2"), elephant))

    assert "e2c4" not in moves
    assert "e2g4" in moves
    assert "e2c0" in moves
    assert "e2g0" in moves


def test_red_elephant_cannot_cross_to_black_side_of_river() -> None:
    board = Board(MINIMAL_FEN)
    elephant = Piece(BISHOP, RED)
    board.set_piece("e4", elephant)

    moves = iccs(generate_elephant_moves(board, Position.from_algebraic("e4"), elephant))

    assert "e4c6" not in moves
    assert "e4g6" not in moves
    assert "e4c2" in moves
    assert "e4g2" in moves


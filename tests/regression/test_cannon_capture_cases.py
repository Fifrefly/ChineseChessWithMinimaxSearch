"""Regression tests for cannon screen and capture behavior."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import BLACK, CANNON, PAWN, RED
from chinese_chess.movegen.pseudo_legal import generate_cannon_moves
from chinese_chess.types import Move, Piece, Position

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def iccs(moves: list[Move]) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_cannon_captures_only_with_exactly_one_screen() -> None:
    board = Board(MINIMAL_FEN)
    cannon = Piece(CANNON, RED)
    board.set_piece("e4", cannon)
    board.set_piece("e5", Piece(PAWN, RED))
    board.set_piece("e6", Piece(PAWN, BLACK))
    board.set_piece("e7", Piece(PAWN, BLACK))

    moves = iccs(generate_cannon_moves(board, Position.from_algebraic("e4"), cannon))

    assert "e4e5" not in moves
    assert "e4e6" in moves
    assert "e4e7" not in moves


def test_cannon_cannot_capture_without_screen() -> None:
    board = Board(MINIMAL_FEN)
    cannon = Piece(CANNON, RED)
    board.set_piece("e4", cannon)
    board.set_piece("e6", Piece(PAWN, BLACK))

    moves = iccs(generate_cannon_moves(board, Position.from_algebraic("e4"), cannon))

    assert "e4e5" in moves
    assert "e4e6" not in moves


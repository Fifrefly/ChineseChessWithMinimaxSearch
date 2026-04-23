"""Regression tests for red/black pawn movement orientation and river rules."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import BLACK, PAWN, RED
from chinese_chess.movegen.pseudo_legal import generate_pawn_moves
from chinese_chess.types import Move, Piece, Position

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def iccs(moves: list[Move]) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_red_pawn_moves_toward_higher_rank_numbers_before_crossing() -> None:
    board = Board(MINIMAL_FEN)
    pawn = Piece(PAWN, RED)

    assert iccs(generate_pawn_moves(board, Position.from_algebraic("e3"), pawn)) == {"e3e4"}


def test_red_pawn_can_move_sideways_after_crossing_but_never_backward() -> None:
    board = Board(MINIMAL_FEN)
    pawn = Piece(PAWN, RED)

    moves = iccs(generate_pawn_moves(board, Position.from_algebraic("e5"), pawn))

    assert moves == {"e5e6", "e5d5", "e5f5"}
    assert "e5e4" not in moves


def test_black_pawn_orientation_is_opposite_red() -> None:
    board = Board(MINIMAL_FEN)
    pawn = Piece(PAWN, BLACK)

    assert iccs(generate_pawn_moves(board, Position.from_algebraic("e6"), pawn)) == {"e6e5"}
    assert iccs(generate_pawn_moves(board, Position.from_algebraic("e4"), pawn)) == {"e4e3", "e4d4", "e4f4"}


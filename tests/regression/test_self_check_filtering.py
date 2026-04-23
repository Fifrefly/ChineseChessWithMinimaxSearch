"""Regression tests for filtering moves that leave own king in check."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import RED
from chinese_chess.movegen.legal import generate_legal_moves


def iccs(moves: list) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_pinned_rook_cannot_move_off_check_line() -> None:
    board = Board("3kr4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1")

    moves = iccs(generate_legal_moves(board, RED))

    assert "e1d1" not in moves
    assert "e1f1" not in moves
    assert "e1e9" in moves


def test_board_state_is_restored_after_filtering() -> None:
    fen = "3kr4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1"
    board = Board(fen)

    generate_legal_moves(board, RED)

    assert board.fen() == fen
    assert board.history_length == 0


"""Regression tests for legal moves while in check."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import RED
from chinese_chess.movegen.attack import is_in_check
from chinese_chess.movegen.legal import generate_legal_moves


def iccs(moves: list) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_when_checked_by_rook_only_evasion_moves_remain() -> None:
    board = Board("3kr4/9/9/9/9/9/9/9/9/4K4 r - - 0 1")

    assert is_in_check(board, RED) is True
    # d0 is still controlled by the black king on d9 via flying-general rules.
    assert iccs(generate_legal_moves(board, RED)) == {"e0f0"}


def test_king_cannot_evade_check_by_staying_on_attacked_file() -> None:
    board = Board("3kr4/9/9/9/9/9/9/9/9/4K4 r - - 0 1")

    moves = iccs(generate_legal_moves(board, RED))

    assert "e0e1" not in moves
    assert "e0d0" not in moves
    assert "e0f0" in moves

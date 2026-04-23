"""Rule-level check and legal-move availability helpers."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.movegen.attack import is_in_check
from chinese_chess.movegen.legal import generate_legal_moves


def is_check(board: Board, color: str) -> bool:
    """Return whether ``color`` is currently in check."""
    return is_in_check(board, color)


def has_legal_moves(board: Board, color: str) -> bool:
    """Return whether ``color`` has at least one legal move."""
    return bool(generate_legal_moves(board, color))

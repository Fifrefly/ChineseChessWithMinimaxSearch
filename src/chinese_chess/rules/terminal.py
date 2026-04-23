"""Checkmate, stalemate, and game-over helpers."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.rules.check import has_legal_moves, is_check
from chinese_chess.rules.repetition import is_threefold_repetition


def is_checkmate(board: Board, color: str) -> bool:
    """Return whether ``color`` is checkmated."""
    return is_check(board, color) and not has_legal_moves(board, color)


def is_stalemate(board: Board, color: str) -> bool:
    """Return whether ``color`` is stalemated."""
    return not is_check(board, color) and not has_legal_moves(board, color)


def game_over(board: Board, side_to_move: str | None = None, repetition_state: object | None = None) -> bool:
    """Return whether the current game is over.

    This phase intentionally combines only checkmate, stalemate, and the
    simplified xiangqi.js-style threefold repetition rule. More draw rules and
    result attribution can be layered on later.
    """
    _ = repetition_state
    side = board.side_to_move if side_to_move is None else side_to_move
    return is_checkmate(board, side) or is_stalemate(board, side) or is_threefold_repetition(board)

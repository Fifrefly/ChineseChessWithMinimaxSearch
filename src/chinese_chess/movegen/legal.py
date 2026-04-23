"""Legal move filtering that rejects self-check positions."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.movegen.attack import is_in_check
from chinese_chess.movegen.pseudo_legal import generate_pseudo_legal_moves
from chinese_chess.types import Move


def generate_legal_moves(board: Board, side_to_move: str | None = None) -> list[Move]:
    """Return pseudo-legal moves that do not leave ``side_to_move`` in check."""
    side = board.side_to_move if side_to_move is None else side_to_move
    original_side = board.side_to_move
    legal_moves: list[Move] = []

    board.side_to_move = side
    try:
        for move in generate_pseudo_legal_moves(board, side):
            applied_move = board.make_move(move)
            try:
                if not is_in_check(board, side):
                    legal_moves.append(applied_move)
            finally:
                board.undo_move()
    finally:
        board.side_to_move = original_side

    return legal_moves

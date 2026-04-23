"""Simplified repetition detection aligned with xiangqi.js behavior.

xiangqi.js detects threefold repetition by undoing all moves, replaying the
history, and counting FEN keys made from only the first two fields:
piece placement and side to move. This deliberately ignores halfmove/fullmove
counters and does not attempt full official Xiangqi long-check/long-chase
adjudication. We keep the same simplified behavior for parity with the
reference implementation.
"""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.types import Move


def position_key(board: Board) -> str:
    """Return the normalized repetition key for the current board."""
    return board.position_key()


def is_threefold_repetition(board: Board) -> bool:
    """Return whether any position key in the current history occurred 3 times.

    The board is restored before returning. This mirrors xiangqi.js rather than
    maintaining an incremental hash because clarity and parity matter more than
    performance at this stage.
    """
    undone_moves: list[Move] = []
    while True:
        move = board.undo_move()
        if move is None:
            break
        undone_moves.append(move)

    positions: dict[str, int] = {}
    repetition = False
    try:
        while True:
            key = position_key(board)
            positions[key] = positions.get(key, 0) + 1
            if positions[key] >= 3:
                repetition = True

            if not undone_moves:
                break
            board.make_move(undone_moves.pop())
    finally:
        while undone_moves:
            board.make_move(undone_moves.pop())

    return repetition

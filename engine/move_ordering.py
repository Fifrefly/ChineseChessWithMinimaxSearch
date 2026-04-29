"""Static move ordering heuristics for alpha-beta search."""

from __future__ import annotations

from engine.core import (
    BLACK,
    CANNON,
    KING,
    KNIGHT,
    PAWN,
    RED,
    ROOK,
    Board,
    Move,
    Piece,
    crossed_river,
)
from engine.evaluation import PIECE_VALUES
from engine.rules import is_check, is_checkmate

CHECKMATE_BONUS = 1_000_000_000
CAPTURE_BONUS = 100_000
CHECK_BONUS = 10_000
PAWN_FORWARD_BONUS = 300
PAWN_CROSSED_FORWARD_BONUS = 800
PAWN_CROSSED_LATERAL_BONUS = 200
ACTIVITY_CENTER_BONUS = 50
ACTIVITY_ENEMY_HALF_BONUS = 80

_ACTIVE_PIECES = frozenset({ROOK, CANNON, KNIGHT})
_CENTER_FILES = frozenset({3, 4, 5})


def static_move_orderer(board: Board, moves: list[Move]) -> list[Move]:
    """Return ``moves`` sorted by shallow tactical and activity heuristics.

    The returned list contains the same ``Move`` objects as the input. Sorting
    is stable, so equal-scoring moves keep their generator order.
    """
    original_fen = board.fen()
    try:
        return sorted(moves, key=lambda move: -_score_move(board, move))
    finally:
        if board.fen() != original_fen:
            raise RuntimeError("static_move_orderer did not restore board FEN.")


def _score_move(board: Board, move: Move) -> int:
    score = 0
    moving_piece = move.piece or board.get_piece(move.from_pos)
    captured_piece = move.captured or board.get_piece(move.to_pos)

    if moving_piece is None:
        return _tactical_score(board, move, captured_piece)

    if captured_piece is not None:
        score += (
            CAPTURE_BONUS
            + 16 * PIECE_VALUES[captured_piece.type]
            - PIECE_VALUES[moving_piece.type]
        )

    score += _pawn_activity_score(move, moving_piece)
    score += _piece_activity_score(move, moving_piece)
    score += _tactical_score(board, move, captured_piece)
    return score


def _tactical_score(
    board: Board, move: Move, captured_piece: Piece | None
) -> int:
    if captured_piece is not None and captured_piece.type == KING:
        return CHECKMATE_BONUS

    board.make_move(move)
    try:
        if is_check(board):
            return CHECKMATE_BONUS if is_checkmate(board) else CHECK_BONUS
        return 0
    finally:
        board.undo_move()


def _pawn_activity_score(move: Move, moving_piece: Piece) -> int:
    if moving_piece.type != PAWN:
        return 0

    forward_delta = -1 if moving_piece.color == RED else 1
    row_delta = move.to_pos.row - move.from_pos.row
    col_delta = move.to_pos.col - move.from_pos.col
    pawn_crossed = crossed_river(move.from_pos, moving_piece.color)

    if row_delta == forward_delta and col_delta == 0:
        return PAWN_CROSSED_FORWARD_BONUS if pawn_crossed else PAWN_FORWARD_BONUS
    if pawn_crossed and row_delta == 0 and abs(col_delta) == 1:
        return PAWN_CROSSED_LATERAL_BONUS
    return 0


def _piece_activity_score(move: Move, moving_piece: Piece) -> int:
    if moving_piece.type not in _ACTIVE_PIECES:
        return 0

    score = 0
    if move.to_pos.col in _CENTER_FILES:
        score += ACTIVITY_CENTER_BONUS
    if _in_enemy_half(move.to_pos.row, moving_piece.color):
        score += ACTIVITY_ENEMY_HALF_BONUS
    return score


def _in_enemy_half(row: int, color: str) -> bool:
    if color == RED:
        return row < 5
    if color == BLACK:
        return row > 4
    return False

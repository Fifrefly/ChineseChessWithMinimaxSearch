"""Attack detection helpers used for check and legal-move filtering."""

from __future__ import annotations

from chinese_chess.board import Board, PositionLike
from chinese_chess.constants import ADVISER, BISHOP, BLACK, CANNON, KING, KNIGHT, PAWN, RED, ROOK
from chinese_chess.exceptions import BoardStateError
from chinese_chess.types import Piece, Position


def find_king(board: Board, color: str) -> Position:
    """Return the king position for ``color``.

    A missing king indicates an invalid intermediate state for check
    detection, so this raises ``BoardStateError`` instead of returning
    ``None``.
    """
    for position, piece in board.piece_map().items():
        if piece.type == KING and piece.color == color:
            return position
    raise BoardStateError(f"Could not find {color!r} king.")


def is_in_check(board: Board, color: str) -> bool:
    """Return whether ``color``'s king is currently attacked."""
    return is_square_attacked(board, find_king(board, color), _opponent(color))


def is_square_attacked(board: Board, target_pos: PositionLike, by_color: str) -> bool:
    """Return whether ``target_pos`` is attacked by any piece of ``by_color``."""
    target = Board._coerce_position(target_pos)
    if not board.is_inside(target):
        raise BoardStateError(f"Target position {target!r} is outside the board.")

    for from_pos, piece in board.piece_map().items():
        if piece.color != by_color:
            continue
        if _piece_attacks(board, from_pos, piece, target):
            return True
    return False


def _piece_attacks(board: Board, from_pos: Position, piece: Piece, target: Position) -> bool:
    if from_pos == target:
        return False
    if piece.type == KING:
        return _king_attacks(board, from_pos, piece, target)
    if piece.type == ADVISER:
        return _advisor_attacks(from_pos, piece, target)
    if piece.type == BISHOP:
        return _elephant_attacks(board, from_pos, piece, target)
    if piece.type == KNIGHT:
        return _horse_attacks(board, from_pos, target)
    if piece.type == ROOK:
        return _same_line_no_blockers(board, from_pos, target)
    if piece.type == CANNON:
        return _same_line_blocker_count(board, from_pos, target) == 1
    if piece.type == PAWN:
        return _pawn_attacks(from_pos, piece, target)
    return False


def _king_attacks(board: Board, from_pos: Position, piece: Piece, target: Position) -> bool:
    # Flying-general attack: kings attack along an open file regardless of
    # distance. Legal move filtering uses this to reject exposing the kings.
    target_piece = board.get_piece(target)
    if (
        target_piece is not None
        and target_piece.type == KING
        and target_piece.color != piece.color
        and from_pos.col == target.col
        and _same_line_no_blockers(board, from_pos, target)
    ):
        return True

    row_delta = abs(from_pos.row - target.row)
    col_delta = abs(from_pos.col - target.col)
    return row_delta + col_delta == 1 and _in_palace(target, piece.color)


def _advisor_attacks(from_pos: Position, piece: Piece, target: Position) -> bool:
    return abs(from_pos.row - target.row) == 1 and abs(from_pos.col - target.col) == 1 and _in_palace(
        target, piece.color
    )


def _elephant_attacks(board: Board, from_pos: Position, piece: Piece, target: Position) -> bool:
    row_delta = target.row - from_pos.row
    col_delta = target.col - from_pos.col
    if abs(row_delta) != 2 or abs(col_delta) != 2:
        return False
    if _elephant_crosses_river(target, piece.color):
        return False

    eye = Position(from_pos.row + row_delta // 2, from_pos.col + col_delta // 2)
    return board.is_inside(eye) and board.get_piece(eye) is None


def _horse_attacks(board: Board, from_pos: Position, target: Position) -> bool:
    row_delta = target.row - from_pos.row
    col_delta = target.col - from_pos.col
    if sorted((abs(row_delta), abs(col_delta))) != [1, 2]:
        return False

    if abs(row_delta) == 2:
        leg = Position(from_pos.row + (1 if row_delta > 0 else -1), from_pos.col)
    else:
        leg = Position(from_pos.row, from_pos.col + (1 if col_delta > 0 else -1))
    return board.is_inside(leg) and board.get_piece(leg) is None


def _pawn_attacks(from_pos: Position, piece: Piece, target: Position) -> bool:
    forward = -1 if piece.color == RED else 1
    row_delta = target.row - from_pos.row
    col_delta = target.col - from_pos.col
    if (row_delta, col_delta) == (forward, 0):
        return True
    if _crossed_river(from_pos, piece.color) and row_delta == 0 and abs(col_delta) == 1:
        return True
    return False


def _same_line_no_blockers(board: Board, start: Position, end: Position) -> bool:
    if start.row != end.row and start.col != end.col:
        return False
    return _same_line_blocker_count(board, start, end) == 0


def _same_line_blocker_count(board: Board, start: Position, end: Position) -> int | None:
    if start.row == end.row:
        row_step = 0
        col_step = 1 if end.col > start.col else -1
    elif start.col == end.col:
        row_step = 1 if end.row > start.row else -1
        col_step = 0
    else:
        return None

    blockers = 0
    current = Position(start.row + row_step, start.col + col_step)
    while current != end:
        if board.get_piece(current) is not None:
            blockers += 1
        current = Position(current.row + row_step, current.col + col_step)
    return blockers


def _in_palace(position: Position, color: str) -> bool:
    if position.col < 3 or position.col > 5:
        return False
    if color == RED:
        return 7 <= position.row <= 9
    return 0 <= position.row <= 2


def _crossed_river(position: Position, color: str) -> bool:
    return position.row < 5 if color == RED else position.row > 4


def _elephant_crosses_river(position: Position, color: str) -> bool:
    return position.row < 5 if color == RED else position.row > 4


def _opponent(color: str) -> str:
    return BLACK if color == RED else RED

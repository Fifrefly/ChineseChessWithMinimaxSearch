"""Pseudo-legal move generation mirroring xiangqi.js piece rules.

Pseudo-legal moves obey piece movement, board bounds, river, palace, horse-leg,
elephant-eye, and occupancy rules. They intentionally do *not* filter out moves
that leave the moving side in check; that belongs to the legal-move layer.
"""

from __future__ import annotations

from collections.abc import Iterable

from chinese_chess.board import Board
from chinese_chess.constants import (
    ADVISER,
    BLACK,
    CANNON,
    CAPTURE_MOVE_FLAG,
    KING,
    KNIGHT,
    NORMAL_MOVE_FLAG,
    PAWN,
    RED,
    ROOK,
    BISHOP,
)
from chinese_chess.types import Move, Piece, Position

ORTHOGONAL_DIRECTIONS: tuple[tuple[int, int], ...] = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL_DIRECTIONS: tuple[tuple[int, int], ...] = ((-1, -1), (1, 1), (1, -1), (-1, 1))
HORSE_STEPS: tuple[tuple[int, int, int, int], ...] = (
    (-2, -1, -1, 0),
    (-2, 1, -1, 0),
    (2, -1, 1, 0),
    (2, 1, 1, 0),
    (-1, -2, 0, -1),
    (1, -2, 0, -1),
    (-1, 2, 0, 1),
    (1, 2, 0, 1),
)
ELEPHANT_STEPS: tuple[tuple[int, int, int, int], ...] = (
    (-2, -2, -1, -1),
    (2, 2, 1, 1),
    (2, -2, 1, -1),
    (-2, 2, -1, 1),
)


def generate_pseudo_legal_moves(board: Board, side_to_move: str | None = None) -> list[Move]:
    """Return all pseudo-legal moves for ``side_to_move``.

    When ``side_to_move`` is omitted, the board's current ``side_to_move`` is
    used. Move order follows board scan order from top-left to bottom-right,
    with per-piece offsets arranged to mirror xiangqi.js as closely as this
    row/column implementation allows.
    """
    side = board.side_to_move if side_to_move is None else side_to_move
    moves: list[Move] = []
    for position, piece in board.piece_map().items():
        if piece.color != side:
            continue
        moves.extend(generate_piece_moves(board, position, piece))
    return moves


def generate_piece_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Dispatch pseudo-legal generation for one piece."""
    if piece.type == KING:
        return generate_king_moves(board, from_pos, piece)
    if piece.type == ADVISER:
        return generate_advisor_moves(board, from_pos, piece)
    if piece.type == BISHOP:
        return generate_elephant_moves(board, from_pos, piece)
    if piece.type == KNIGHT:
        return generate_horse_moves(board, from_pos, piece)
    if piece.type == ROOK:
        return generate_rook_moves(board, from_pos, piece)
    if piece.type == CANNON:
        return generate_cannon_moves(board, from_pos, piece)
    if piece.type == PAWN:
        return generate_pawn_moves(board, from_pos, piece)
    return []


def generate_king_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate palace-confined king/admiral moves."""
    return [
        move
        for move in _step_moves(board, from_pos, piece, ORTHOGONAL_DIRECTIONS)
        if _in_palace(move.to_pos, piece.color)
    ]


def generate_advisor_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate palace-confined diagonal advisor moves."""
    return [
        move
        for move in _step_moves(board, from_pos, piece, DIAGONAL_DIRECTIONS)
        if _in_palace(move.to_pos, piece.color)
    ]


def generate_elephant_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate elephant/bishop moves, including river and eye blocking."""
    moves: list[Move] = []
    for row_delta, col_delta, eye_row_delta, eye_col_delta in ELEPHANT_STEPS:
        eye = Position(from_pos.row + eye_row_delta, from_pos.col + eye_col_delta)
        to_pos = Position(from_pos.row + row_delta, from_pos.col + col_delta)
        if not board.is_inside(to_pos) or not board.is_inside(eye):
            continue
        if board.get_piece(eye) is not None:
            continue
        if _elephant_crosses_river(to_pos, piece.color):
            continue
        move = _build_move_if_target_allowed(board, from_pos, to_pos, piece)
        if move is not None:
            moves.append(move)
    return moves


def generate_horse_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate horse/knight moves, including horse-leg blocking."""
    moves: list[Move] = []
    for row_delta, col_delta, leg_row_delta, leg_col_delta in HORSE_STEPS:
        leg = Position(from_pos.row + leg_row_delta, from_pos.col + leg_col_delta)
        to_pos = Position(from_pos.row + row_delta, from_pos.col + col_delta)
        if not board.is_inside(to_pos) or not board.is_inside(leg):
            continue
        if board.get_piece(leg) is not None:
            continue
        move = _build_move_if_target_allowed(board, from_pos, to_pos, piece)
        if move is not None:
            moves.append(move)
    return moves


def generate_rook_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate rook/chariot sliding moves."""
    return _sliding_moves(board, from_pos, piece, ORTHOGONAL_DIRECTIONS)


def generate_cannon_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate cannon moves with exactly one screen for captures."""
    moves: list[Move] = []
    for row_delta, col_delta in ORTHOGONAL_DIRECTIONS:
        screen_seen = False
        current = from_pos
        while True:
            current = Position(current.row + row_delta, current.col + col_delta)
            if not board.is_inside(current):
                break

            target = board.get_piece(current)
            if target is None:
                if not screen_seen:
                    moves.append(Move(from_pos, current, piece=piece, flags=NORMAL_MOVE_FLAG))
                continue

            if not screen_seen:
                screen_seen = True
                continue

            if target.color != piece.color:
                moves.append(Move(from_pos, current, piece=piece, captured=target, flags=CAPTURE_MOVE_FLAG))
            break
    return moves


def generate_pawn_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate soldier/pawn moves with river-dependent side movement."""
    forward = -1 if piece.color == RED else 1
    directions = [(forward, 0)]
    if _crossed_river(from_pos, piece.color):
        directions.extend([(0, -1), (0, 1)])
    return list(_step_moves(board, from_pos, piece, directions))


def _step_moves(
    board: Board,
    from_pos: Position,
    piece: Piece,
    directions: Iterable[tuple[int, int]],
) -> Iterable[Move]:
    for row_delta, col_delta in directions:
        to_pos = Position(from_pos.row + row_delta, from_pos.col + col_delta)
        if not board.is_inside(to_pos):
            continue
        move = _build_move_if_target_allowed(board, from_pos, to_pos, piece)
        if move is not None:
            yield move


def _sliding_moves(
    board: Board,
    from_pos: Position,
    piece: Piece,
    directions: Iterable[tuple[int, int]],
) -> list[Move]:
    moves: list[Move] = []
    for row_delta, col_delta in directions:
        current = from_pos
        while True:
            current = Position(current.row + row_delta, current.col + col_delta)
            if not board.is_inside(current):
                break
            target = board.get_piece(current)
            if target is None:
                moves.append(Move(from_pos, current, piece=piece, flags=NORMAL_MOVE_FLAG))
                continue
            if target.color != piece.color:
                moves.append(Move(from_pos, current, piece=piece, captured=target, flags=CAPTURE_MOVE_FLAG))
            break
    return moves


def _build_move_if_target_allowed(board: Board, from_pos: Position, to_pos: Position, piece: Piece) -> Move | None:
    target = board.get_piece(to_pos)
    if target is not None and target.color == piece.color:
        return None
    return Move(
        from_pos,
        to_pos,
        piece=piece,
        captured=target,
        flags=CAPTURE_MOVE_FLAG if target is not None else NORMAL_MOVE_FLAG,
    )


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

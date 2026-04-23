"""Move rules, attack detection, legal filtering, and terminal checks.

This file deliberately keeps the core rules together. Pseudo-legal generation
checks piece movement and occupancy. Legal generation then filters those moves
by making each move and rejecting positions where the moving side is in check.
"""

from __future__ import annotations

from collections.abc import Iterable

from engine.core import (
    ADVISER,
    BISHOP,
    BLACK,
    CANNON,
    CAPTURE_MOVE_FLAG,
    KING,
    KNIGHT,
    NORMAL_MOVE_FLAG,
    PAWN,
    RED,
    ROOK,
    Board,
    BoardStateError,
    Move,
    Piece,
    Position,
    PositionLike,
    crossed_river,
    elephant_crosses_river,
    in_palace,
    opponent,
)

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


# ---------------------------------------------------------------------------
# Pseudo-legal moves: piece rules only, not self-check filtering.
# ---------------------------------------------------------------------------


def generate_pseudo_legal_moves(
    board: Board, side_to_move: str | None = None
) -> list[Move]:
    """Return all moves that obey piece movement and occupancy rules."""
    side = board.side_to_move if side_to_move is None else side_to_move
    moves: list[Move] = []
    for position, piece in board.piece_map().items():
        if piece.color == side:
            moves.extend(generate_piece_moves(board, position, piece))
    return moves


def generate_piece_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    """Generate pseudo-legal moves for one piece."""
    if piece.type == KING:
        return _king_moves(board, from_pos, piece)
    if piece.type == ADVISER:
        return _advisor_moves(board, from_pos, piece)
    if piece.type == BISHOP:
        return _elephant_moves(board, from_pos, piece)
    if piece.type == KNIGHT:
        return _horse_moves(board, from_pos, piece)
    if piece.type == ROOK:
        return _rook_moves(board, from_pos, piece)
    if piece.type == CANNON:
        return _cannon_moves(board, from_pos, piece)
    if piece.type == PAWN:
        return _pawn_moves(board, from_pos, piece)
    return []


def _king_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    return [
        move
        for move in _step_moves(board, from_pos, piece, ORTHOGONAL_DIRECTIONS)
        if in_palace(move.to_pos, piece.color)
    ]


def _advisor_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    return [
        move
        for move in _step_moves(board, from_pos, piece, DIAGONAL_DIRECTIONS)
        if in_palace(move.to_pos, piece.color)
    ]


def _elephant_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    moves: list[Move] = []
    for row_delta, col_delta, eye_row_delta, eye_col_delta in ELEPHANT_STEPS:
        eye = Position(from_pos.row + eye_row_delta, from_pos.col + eye_col_delta)
        to_pos = Position(from_pos.row + row_delta, from_pos.col + col_delta)
        if not board.is_inside(to_pos) or not board.is_inside(eye):
            continue
        if board.get_piece(eye) is not None or elephant_crosses_river(
            to_pos, piece.color
        ):
            continue
        move = _target_move(board, from_pos, to_pos, piece)
        if move is not None:
            moves.append(move)
    return moves


def _horse_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    moves: list[Move] = []
    for row_delta, col_delta, leg_row_delta, leg_col_delta in HORSE_STEPS:
        leg = Position(from_pos.row + leg_row_delta, from_pos.col + leg_col_delta)
        to_pos = Position(from_pos.row + row_delta, from_pos.col + col_delta)
        if not board.is_inside(to_pos) or not board.is_inside(leg):
            continue
        if board.get_piece(leg) is not None:
            continue
        move = _target_move(board, from_pos, to_pos, piece)
        if move is not None:
            moves.append(move)
    return moves


def _rook_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    return _sliding_moves(board, from_pos, piece, ORTHOGONAL_DIRECTIONS)


def _cannon_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
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
                    moves.append(
                        Move(from_pos, current, piece=piece, flags=NORMAL_MOVE_FLAG)
                    )
                continue
            if not screen_seen:
                screen_seen = True
                continue
            if target.color != piece.color:
                moves.append(
                    Move(
                        from_pos,
                        current,
                        piece=piece,
                        captured=target,
                        flags=CAPTURE_MOVE_FLAG,
                    )
                )
            break
    return moves


def _pawn_moves(board: Board, from_pos: Position, piece: Piece) -> list[Move]:
    forward = -1 if piece.color == RED else 1
    directions = [(forward, 0)]
    if crossed_river(from_pos, piece.color):
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
        move = _target_move(board, from_pos, to_pos, piece)
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
                moves.append(
                    Move(from_pos, current, piece=piece, flags=NORMAL_MOVE_FLAG)
                )
                continue
            if target.color != piece.color:
                moves.append(
                    Move(
                        from_pos,
                        current,
                        piece=piece,
                        captured=target,
                        flags=CAPTURE_MOVE_FLAG,
                    )
                )
            break
    return moves


def _target_move(
    board: Board, from_pos: Position, to_pos: Position, piece: Piece
) -> Move | None:
    target = board.get_piece(to_pos)
    if target is not None and target.color == piece.color:
        return None
    return Move(
        from_pos,
        to_pos,
        piece=piece,
        captured=target,
        flags=CAPTURE_MOVE_FLAG if target else NORMAL_MOVE_FLAG,
    )


# ---------------------------------------------------------------------------
# Attack and check detection.
# ---------------------------------------------------------------------------


def find_king(board: Board, color: str) -> Position:
    """Return ``color``'s king square."""
    for position, piece in board.piece_map().items():
        if piece.type == KING and piece.color == color:
            return position
    raise BoardStateError(f"Could not find {color!r} king.")


def is_square_attacked(board: Board, target_pos: PositionLike, by_color: str) -> bool:
    """Return whether ``target_pos`` is attacked by ``by_color``."""
    target = Board._coerce_position(target_pos)
    if not board.is_inside(target):
        raise BoardStateError(f"Target position {target!r} is outside the board.")
    for from_pos, piece in board.piece_map().items():
        if piece.color == by_color and _piece_attacks(board, from_pos, piece, target):
            return True
    return False


def is_check(board: Board, color: str | None = None) -> bool:
    """Return whether ``color`` is in check. Defaults to side to move."""
    checked_color = board.side_to_move if color is None else color
    return is_square_attacked(
        board, find_king(board, checked_color), opponent(checked_color)
    )


def _piece_attacks(
    board: Board, from_pos: Position, piece: Piece, target: Position
) -> bool:
    if from_pos == target:
        return False
    if piece.type == KING:
        return _king_attacks(board, from_pos, piece, target)
    if piece.type == ADVISER:
        return (
            abs(from_pos.row - target.row) == 1
            and abs(from_pos.col - target.col) == 1
            and in_palace(target, piece.color)
        )
    if piece.type == BISHOP:
        return _elephant_attacks(board, from_pos, piece, target)
    if piece.type == KNIGHT:
        return _horse_attacks(board, from_pos, target)
    if piece.type == ROOK:
        return _same_line_blocker_count(board, from_pos, target) == 0
    if piece.type == CANNON:
        return _same_line_blocker_count(board, from_pos, target) == 1
    if piece.type == PAWN:
        return _pawn_attacks(from_pos, piece, target)
    return False


def _king_attacks(
    board: Board, from_pos: Position, piece: Piece, target: Position
) -> bool:
    target_piece = board.get_piece(target)
    if (
        target_piece is not None
        and target_piece.type == KING
        and target_piece.color != piece.color
        and from_pos.col == target.col
        and _same_line_blocker_count(board, from_pos, target) == 0
    ):
        return True
    return abs(from_pos.row - target.row) + abs(
        from_pos.col - target.col
    ) == 1 and in_palace(target, piece.color)


def _elephant_attacks(
    board: Board, from_pos: Position, piece: Piece, target: Position
) -> bool:
    row_delta = target.row - from_pos.row
    col_delta = target.col - from_pos.col
    if (
        abs(row_delta) != 2
        or abs(col_delta) != 2
        or elephant_crosses_river(target, piece.color)
    ):
        return False
    eye = Position(from_pos.row + row_delta // 2, from_pos.col + col_delta // 2)
    return board.is_inside(eye) and board.get_piece(eye) is None


def _horse_attacks(board: Board, from_pos: Position, target: Position) -> bool:
    row_delta = target.row - from_pos.row
    col_delta = target.col - from_pos.col
    if sorted((abs(row_delta), abs(col_delta))) != [1, 2]:
        return False
    leg = (
        Position(from_pos.row + (1 if row_delta > 0 else -1), from_pos.col)
        if abs(row_delta) == 2
        else Position(from_pos.row, from_pos.col + (1 if col_delta > 0 else -1))
    )
    return board.is_inside(leg) and board.get_piece(leg) is None


def _pawn_attacks(from_pos: Position, piece: Piece, target: Position) -> bool:
    forward = -1 if piece.color == RED else 1
    row_delta = target.row - from_pos.row
    col_delta = target.col - from_pos.col
    if (row_delta, col_delta) == (forward, 0):
        return True
    return (
        crossed_river(from_pos, piece.color) and row_delta == 0 and abs(col_delta) == 1
    )


def _same_line_blocker_count(
    board: Board, start: Position, end: Position
) -> int | None:
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


# ---------------------------------------------------------------------------
# Legal moves and terminal checks.
# ---------------------------------------------------------------------------


def generate_legal_moves(board: Board, side_to_move: str | None = None) -> list[Move]:
    """Return pseudo-legal moves that do not leave own king in check."""
    side = board.side_to_move if side_to_move is None else side_to_move
    original_side = board.side_to_move
    legal_moves: list[Move] = []
    board.side_to_move = side
    try:
        for move in generate_pseudo_legal_moves(board, side):
            applied = board.make_move(move)
            try:
                if not is_check(board, side):
                    legal_moves.append(applied)
            finally:
                board.undo_move()
    finally:
        board.side_to_move = original_side
    return legal_moves


def has_legal_moves(board: Board, color: str | None = None) -> bool:
    """Return whether ``color`` has at least one legal move."""
    return bool(
        generate_legal_moves(board, board.side_to_move if color is None else color)
    )


def is_checkmate(board: Board, color: str | None = None) -> bool:
    """Return whether ``color`` is checkmated."""
    side = board.side_to_move if color is None else color
    return is_check(board, side) and not has_legal_moves(board, side)


def is_stalemate(board: Board, color: str | None = None) -> bool:
    """Return whether ``color`` is stalemated."""
    side = board.side_to_move if color is None else color
    return not is_check(board, side) and not has_legal_moves(board, side)


def is_threefold_repetition(board: Board) -> bool:
    """Return whether the xiangqi.js simplified threefold rule triggers.

    This counts position keys made from FEN's first two fields only: piece
    placement and side to move. It intentionally does not implement official
    long-check or long-chase adjudication.
    """
    undone: list[Move] = []
    while True:
        move = board.undo_move()
        if move is None:
            break
        undone.append(move)

    counts: dict[str, int] = {}
    repeated = False
    try:
        while True:
            key = board.position_key()
            counts[key] = counts.get(key, 0) + 1
            if counts[key] >= 3:
                repeated = True
            if not undone:
                break
            board.make_move(undone.pop())
    finally:
        while undone:
            board.make_move(undone.pop())
    return repeated


def game_over(board: Board) -> bool:
    """Return whether the current board is terminal for this study engine."""
    return is_checkmate(board) or is_stalemate(board) or is_threefold_repetition(board)


def legal_move_from_iccs(board: Board, text: str) -> Move:
    """Find a legal move matching an ICCS string, useful for user input."""
    wanted = Move.from_iccs(text)
    for move in generate_legal_moves(board):
        if move.from_pos == wanted.from_pos and move.to_pos == wanted.to_pos:
            return move
    raise ValueError(f"Illegal move: {text}")

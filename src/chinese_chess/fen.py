"""FEN parsing, validation, and serialization helpers.

xiangqi.js uses six FEN fields:

``pieces side_to_move - - halfmove_clock fullmove_number``

There is no castling or en-passant in Xiangqi, but the reference keeps those
placeholder fields for chess.js compatibility. This module intentionally
preserves that shape so parity tests can compare strings directly.
"""

from __future__ import annotations

from dataclasses import dataclass

from chinese_chess.constants import (
    ADVISER,
    BISHOP,
    BLACK,
    BOARD_COLS,
    BOARD_ROWS,
    CANNON,
    DEFAULT_FEN,
    FEN_CASTLING_FIELD,
    FEN_EN_PASSANT_FIELD,
    FEN_PIECE_SYMBOLS,
    FEN_SIDE_TO_MOVE_SYMBOLS,
    KING,
    KNIGHT,
    MAX_PIECE_COUNTS,
    PAWN,
    RED,
    ROOK,
)
from chinese_chess.exceptions import BoardStateError, InvalidFENError
from chinese_chess.types import BoardState, Piece, Position


@dataclass(frozen=True, slots=True)
class ParsedFEN:
    """Fully parsed FEN information."""

    board_state: BoardState
    side_to_move: str
    halfmove_clock: int
    fullmove_number: int


def validate_fen(fen: str) -> tuple[bool, str | None]:
    """Validate a Xiangqi FEN string.

    The checks mirror the important constraints from xiangqi.js: six fields,
    10 rows of 9 files, valid piece counts, and palace/river placement for
    kings, advisers, bishops, and pawns.
    """
    try:
        _parse_fen_record(fen)
    except InvalidFENError as exc:
        return (False, str(exc))
    return (True, None)


def parse_fen(fen: str) -> BoardState:
    """Parse FEN and return only the 10x9 board state."""
    return parse_fen_record(fen).board_state


def parse_fen_record(fen: str = DEFAULT_FEN) -> ParsedFEN:
    """Parse FEN and return board state plus side/counter metadata."""
    return _parse_fen_record(fen)


def serialize_fen(
    board_state: BoardState,
    side_to_move: str,
    halfmove_clock: int | None = None,
    fullmove_number: int | None = None,
) -> str:
    """Serialize board state and counters to xiangqi.js-compatible FEN."""
    _validate_board_state(board_state)
    side = _normalize_side_to_move(side_to_move)
    halfmove = 0 if halfmove_clock is None else halfmove_clock
    fullmove = 1 if fullmove_number is None else fullmove_number

    if halfmove < 0:
        raise ValueError("halfmove_clock must be non-negative.")
    if fullmove <= 0:
        raise ValueError("fullmove_number must be positive.")

    rows: list[str] = []
    for row in board_state:
        empty = 0
        row_text = ""
        for piece in row:
            if piece is None:
                empty += 1
                continue
            if empty:
                row_text += str(empty)
                empty = 0
            row_text += piece.to_fen_symbol()
        if empty:
            row_text += str(empty)
        rows.append(row_text)

    placement = "/".join(rows)
    return f"{placement} {side} {FEN_CASTLING_FIELD} {FEN_EN_PASSANT_FIELD} {halfmove} {fullmove}"


def _parse_fen_record(fen: str) -> ParsedFEN:
    if not isinstance(fen, str) or not fen:
        raise InvalidFENError("FEN string must be a non-empty string.")

    tokens = fen.split()
    if len(tokens) != 6:
        raise InvalidFENError("FEN string must contain six space-delimited fields.")

    placement, side, castling, en_passant, halfmove_text, fullmove_text = tokens

    if castling != FEN_CASTLING_FIELD:
        raise InvalidFENError("3rd field (castling availability) should be '-'.")
    if en_passant != FEN_EN_PASSANT_FIELD:
        raise InvalidFENError("4th field (en-passant square) should be '-'.")
    if side not in FEN_SIDE_TO_MOVE_SYMBOLS:
        raise InvalidFENError("2nd field (side to move) is invalid.")
    if not halfmove_text.isdecimal() or int(halfmove_text) < 0:
        raise InvalidFENError("5th field (half move counter) must be a non-negative integer.")
    if not fullmove_text.isdecimal() or int(fullmove_text) <= 0:
        raise InvalidFENError("6th field (move number) must be a positive integer.")

    board_state = _parse_piece_placement(placement)
    _validate_piece_constraints(board_state)

    return ParsedFEN(
        board_state=board_state,
        side_to_move=_normalize_side_to_move(side),
        halfmove_clock=int(halfmove_text),
        fullmove_number=int(fullmove_text),
    )


def _parse_piece_placement(placement: str) -> BoardState:
    rows = placement.split("/")
    if len(rows) != BOARD_ROWS:
        raise InvalidFENError("1st field (piece positions) does not contain 10 '/'-delimited rows.")

    board_state: BoardState = []
    for row_text in rows:
        row: list[Piece | None] = []
        previous_was_number = False
        for symbol in row_text:
            if symbol.isdecimal():
                if previous_was_number:
                    raise InvalidFENError("1st field (piece positions) is invalid [consecutive numbers].")
                empty_count = int(symbol)
                if empty_count <= 0:
                    raise InvalidFENError("1st field (piece positions) is invalid [invalid empty count].")
                row.extend([None] * empty_count)
                previous_was_number = True
            else:
                if symbol not in FEN_PIECE_SYMBOLS:
                    raise InvalidFENError("1st field (piece positions) is invalid [invalid piece].")
                row.append(Piece.from_fen_symbol(symbol))
                previous_was_number = False

            if len(row) > BOARD_COLS:
                raise InvalidFENError("1st field (piece positions) is invalid [row too large].")

        if len(row) != BOARD_COLS:
            raise InvalidFENError("1st field (piece positions) is invalid [row must contain 9 files].")
        board_state.append(row)

    return board_state


def _validate_piece_constraints(board_state: BoardState) -> None:
    counts: dict[tuple[str, str], int] = {}
    positions: dict[tuple[str, str], list[Position]] = {}

    for row_index, row in enumerate(board_state):
        for col_index, piece in enumerate(row):
            if piece is None:
                continue
            key = (piece.color, piece.type)
            counts[key] = counts.get(key, 0) + 1
            positions.setdefault(key, []).append(Position(row_index, col_index))

    if counts.get((BLACK, KING), 0) != 1 or counts.get((RED, KING), 0) != 1:
        raise InvalidFENError("1st field (piece positions) is invalid [each side has one king].")

    for color in (BLACK, RED):
        for piece_type, limit in MAX_PIECE_COUNTS.items():
            if counts.get((color, piece_type), 0) > limit:
                raise InvalidFENError(
                    f"1st field (piece positions) is invalid [{color} has too many {piece_type} pieces]."
                )

    for color in (BLACK, RED):
        for position in positions.get((color, KING), []):
            if _out_of_place(KING, position, color):
                raise InvalidFENError("1st field (piece positions) is invalid [king should be in palace].")
        for position in positions.get((color, ADVISER), []):
            if _out_of_place(ADVISER, position, color):
                raise InvalidFENError("1st field (piece positions) is invalid [adviser should be in palace].")
        for position in positions.get((color, BISHOP), []):
            if _out_of_place(BISHOP, position, color):
                raise InvalidFENError("1st field (piece positions) is invalid [bishop should be on own side].")
        for position in positions.get((color, PAWN), []):
            if _out_of_place(PAWN, position, color):
                raise InvalidFENError("1st field (piece positions) is invalid [pawn should be on legal square].")


def _out_of_place(piece_type: str, position: Position, color: str) -> bool:
    row = position.row
    col = position.col

    if piece_type == PAWN:
        starting_files = {0, 2, 4, 6, 8}
        if color == RED:
            return row > 6 or (row > 4 and col not in starting_files)
        return row < 3 or (row < 5 and col not in starting_files)

    if piece_type == BISHOP:
        red_squares = {
            Position(9, 2),
            Position(9, 6),
            Position(7, 0),
            Position(7, 4),
            Position(7, 8),
            Position(5, 2),
            Position(5, 6),
        }
        black_squares = {
            Position(0, 2),
            Position(0, 6),
            Position(2, 0),
            Position(2, 4),
            Position(2, 8),
            Position(4, 2),
            Position(4, 6),
        }
        return position not in (red_squares if color == RED else black_squares)

    if piece_type == ADVISER:
        return not _in_palace(position, color)

    if piece_type == KING:
        return not _in_palace(position, color)

    # Rooks, knights, and cannons can appear anywhere on the board.
    return piece_type not in {ROOK, KNIGHT, CANNON}


def _in_palace(position: Position, color: str) -> bool:
    if position.col < 3 or position.col > 5:
        return False
    if color == RED:
        return 7 <= position.row <= 9
    return 0 <= position.row <= 2


def _normalize_side_to_move(side_to_move: str) -> str:
    # xiangqi.js validation accepts "w" but load() treats any non-black side
    # as red. Preserve that behavior for parity.
    return BLACK if side_to_move == BLACK else RED


def _validate_board_state(board_state: BoardState) -> None:
    if len(board_state) != BOARD_ROWS:
        raise BoardStateError(f"Board state must contain {BOARD_ROWS} rows.")
    for row in board_state:
        if len(row) != BOARD_COLS:
            raise BoardStateError(f"Each board row must contain {BOARD_COLS} columns.")
        for piece in row:
            if piece is not None and not isinstance(piece, Piece):
                raise BoardStateError("Board entries must be Piece instances or None.")


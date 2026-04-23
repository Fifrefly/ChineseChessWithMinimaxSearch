"""Core data structures and board state for the compact Xiangqi engine.

Read this file first if you want to understand how the engine represents a
position. It contains the board model, FEN parsing/serialization, ICCS move
parsing, and reversible ``make_move`` / ``undo_move`` state transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

BOARD_ROWS = 10
BOARD_COLS = 9

RED = "r"
BLACK = "b"
WHITE_ALIAS = "w"  # xiangqi.js accepts "w" in FEN and loads it as red.
COLORS = frozenset({RED, BLACK})
FEN_SIDE_TO_MOVE_SYMBOLS = frozenset({RED, BLACK, WHITE_ALIAS})

PAWN = "p"
CANNON = "c"
ROOK = "r"
KNIGHT = "n"
BISHOP = "b"  # xiangqi.js uses "b" for elephant/bishop.
ADVISER = "a"
KING = "k"

PIECE_TYPES = frozenset({PAWN, CANNON, ROOK, KNIGHT, BISHOP, ADVISER, KING})
FEN_PIECE_SYMBOLS = frozenset("pcrnbakPCRNBAK")
MAX_PIECE_COUNTS = {
    KING: 1,
    ADVISER: 2,
    BISHOP: 2,
    KNIGHT: 2,
    ROOK: 2,
    CANNON: 2,
    PAWN: 5,
}

DEFAULT_FEN = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR r - - 0 1"
ICCS_FILES = "abcdefghi"
ICCS_RANKS = "9876543210"
NORMAL_MOVE_FLAG = "n"
CAPTURE_MOVE_FLAG = "c"

BoardState: TypeAlias = list[list["Piece | None"]]
PositionLike: TypeAlias = "Position | str | tuple[int, int]"


class XiangqiError(Exception):
    """Base class for engine-specific errors."""


class InvalidFENError(XiangqiError):
    """Raised when a FEN string cannot be parsed or validated."""


class IllegalMoveError(XiangqiError):
    """Raised when a move cannot be applied to the current board."""


class BoardStateError(XiangqiError):
    """Raised when board coordinates or state are invalid."""


@dataclass(frozen=True, slots=True, order=True)
class Position:
    """A zero-based board coordinate.

    ``row=0`` is the top FEN row (black home side), and ``col=0`` is file
    ``a``. ICCS coordinates therefore run from ``a9`` at top-left to ``i0`` at
    bottom-right.
    """

    row: int
    col: int

    @classmethod
    def from_iccs(cls, square: str) -> "Position":
        """Create a position from an ICCS square such as ``e2``."""
        if len(square) != 2:
            raise ValueError(f"Invalid square {square!r}; expected forms like e2.")
        file_symbol = square[0].lower()
        rank_symbol = square[1]
        if file_symbol not in ICCS_FILES or rank_symbol not in ICCS_RANKS:
            raise ValueError(f"Invalid square {square!r}; expected a9 through i0.")
        return cls(ICCS_RANKS.index(rank_symbol), ICCS_FILES.index(file_symbol))

    def to_iccs(self) -> str:
        """Return this position as an ICCS square."""
        try:
            return f"{ICCS_FILES[self.col]}{ICCS_RANKS[self.row]}"
        except IndexError as exc:
            raise ValueError(f"Position is outside ICCS coordinates: {self!r}") from exc

    def __str__(self) -> str:
        return self.to_iccs()


@dataclass(frozen=True, slots=True)
class Piece:
    """A Xiangqi piece using xiangqi.js symbols."""

    type: str
    color: str

    def __post_init__(self) -> None:
        if self.type not in PIECE_TYPES:
            raise ValueError(f"Invalid piece type {self.type!r}.")
        if self.color not in COLORS:
            raise ValueError(f"Invalid piece color {self.color!r}.")

    @classmethod
    def from_fen_symbol(cls, symbol: str) -> "Piece":
        """Create a piece from one FEN placement character."""
        if len(symbol) != 1 or symbol not in FEN_PIECE_SYMBOLS:
            raise ValueError(f"Invalid FEN piece symbol {symbol!r}.")
        return cls(symbol.lower(), RED if symbol.isupper() else BLACK)

    def to_fen_symbol(self) -> str:
        """Return this piece as one FEN placement character."""
        return self.type.upper() if self.color == RED else self.type

    def to_dict(self) -> dict[str, str]:
        """Return a compact serializable representation."""
        return {"type": self.type, "color": self.color}


@dataclass(frozen=True, slots=True)
class Move:
    """A move value.

    ``piece`` and ``captured`` are optional when a move is parsed from text, but
    generated/applied moves fill them in so search and debugging can inspect
    captures without rereading the board.
    """

    from_pos: Position
    to_pos: Position
    piece: Piece | None = None
    captured: Piece | None = None
    flags: str = ""

    @classmethod
    def from_iccs(
        cls,
        text: str,
        *,
        piece: Piece | None = None,
        captured: Piece | None = None,
        flags: str = "",
    ) -> "Move":
        """Parse ``h2e2`` or ``h2-e2`` into a move."""
        clean = text.strip().replace("-", "")
        if len(clean) != 4:
            raise ValueError(f"Invalid ICCS move {text!r}; expected forms like h2e2.")
        return cls(
            Position.from_iccs(clean[:2]),
            Position.from_iccs(clean[2:]),
            piece=piece,
            captured=captured,
            flags=flags,
        )

    def to_iccs(self) -> str:
        """Return compact ICCS form, for example ``h2e2``."""
        return f"{self.from_pos}{self.to_pos}"

    def to_dict(self) -> dict[str, Any]:
        """Return a readable dictionary for tests and debugging."""
        data: dict[str, Any] = {
            "from": str(self.from_pos),
            "to": str(self.to_pos),
            "flags": self.flags,
        }
        if self.piece is not None:
            data["piece"] = self.piece.to_dict()
        if self.captured is not None:
            data["captured"] = self.captured.to_dict()
        return data

    def __str__(self) -> str:
        return self.to_iccs()


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """Enough information to undo one applied move exactly."""

    move: Move
    moved_piece: Piece
    captured_piece: Piece | None
    previous_side_to_move: str
    previous_halfmove_clock: int
    previous_fullmove_number: int


@dataclass(frozen=True, slots=True)
class ParsedFEN:
    """Parsed board and FEN metadata."""

    board_state: BoardState
    side_to_move: str
    halfmove_clock: int
    fullmove_number: int


def parse_iccs_move(text: str) -> Move:
    """Parse an ICCS move string without checking legality."""
    return Move.from_iccs(text)


def move_to_iccs(move: Move) -> str:
    """Return a move as compact ICCS text."""
    return move.to_iccs()


def validate_fen(fen: str) -> tuple[bool, str | None]:
    """Validate FEN and return ``(valid, error_message)``."""
    try:
        parse_fen_record(fen)
    except InvalidFENError as exc:
        return (False, str(exc))
    return (True, None)


def parse_fen(fen: str) -> BoardState:
    """Parse FEN and return only the 10x9 board matrix."""
    return parse_fen_record(fen).board_state


def parse_fen_record(fen: str = DEFAULT_FEN) -> ParsedFEN:
    """Parse xiangqi.js-style six-field FEN."""
    if not isinstance(fen, str) or not fen:
        raise InvalidFENError("FEN string must be a non-empty string.")

    tokens = fen.split()
    if len(tokens) != 6:
        raise InvalidFENError("FEN string must contain six space-delimited fields.")

    placement, side, castling, en_passant, halfmove_text, fullmove_text = tokens
    if side not in FEN_SIDE_TO_MOVE_SYMBOLS:
        raise InvalidFENError("2nd field (side to move) is invalid.")
    if castling != "-" or en_passant != "-":
        raise InvalidFENError("3rd and 4th FEN fields should both be '-'.")
    if not halfmove_text.isdecimal() or int(halfmove_text) < 0:
        raise InvalidFENError(
            "5th field (half move counter) must be a non-negative integer."
        )
    if not fullmove_text.isdecimal() or int(fullmove_text) <= 0:
        raise InvalidFENError("6th field (move number) must be a positive integer.")

    board_state = _parse_piece_placement(placement)
    _validate_piece_constraints(board_state)
    return ParsedFEN(
        board_state,
        BLACK if side == BLACK else RED,
        int(halfmove_text),
        int(fullmove_text),
    )


def serialize_fen(
    board_state: BoardState,
    side_to_move: str,
    halfmove_clock: int = 0,
    fullmove_number: int = 1,
) -> str:
    """Serialize board state to xiangqi.js-compatible FEN."""
    _validate_board_shape(board_state)
    if side_to_move not in COLORS:
        raise ValueError(f"Invalid side to move {side_to_move!r}.")
    if halfmove_clock < 0:
        raise ValueError("halfmove_clock must be non-negative.")
    if fullmove_number <= 0:
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
    return f"{'/'.join(rows)} {side_to_move} - - {halfmove_clock} {fullmove_number}"


class Board:
    """Mutable board state plus reversible move history.

    ``make_move`` is intentionally low-level: it applies a board-consistent
    move but does not check whether that move is legal. Use
    ``engine.rules.generate_legal_moves`` before applying user-facing moves.
    """

    def __init__(self, fen: str | None = None) -> None:
        self._state: BoardState = [
            [None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)
        ]
        self.side_to_move = RED
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self._history: list[HistoryEntry] = []
        self.load_fen(DEFAULT_FEN if fen is None else fen)

    def load_fen(self, fen: str) -> None:
        """Replace the current position and clear move history."""
        parsed = parse_fen_record(fen)
        self._state = [[piece for piece in row] for row in parsed.board_state]
        self.side_to_move = parsed.side_to_move
        self.halfmove_clock = parsed.halfmove_clock
        self.fullmove_number = parsed.fullmove_number
        self._history = []

    def fen(self) -> str:
        """Return the current position as FEN."""
        return serialize_fen(
            self._state, self.side_to_move, self.halfmove_clock, self.fullmove_number
        )

    def position_key(self) -> str:
        """Return the repetition key used by xiangqi.js: placement + side."""
        return " ".join(self.fen().split()[:2])

    def is_inside(self, position: PositionLike) -> bool:
        """Return whether ``position`` is on the 10x9 board."""
        try:
            pos = self._coerce_position(position)
        except BoardStateError:
            return False
        return 0 <= pos.row < BOARD_ROWS and 0 <= pos.col < BOARD_COLS

    def get_piece(self, position: PositionLike) -> Piece | None:
        """Return the piece at a square, or ``None``."""
        pos = self._require_inside(position)
        return self._state[pos.row][pos.col]

    def set_piece(self, position: PositionLike, piece: Piece | None) -> None:
        """Set or clear a square. Useful for tests and small experiments."""
        pos = self._require_inside(position)
        if piece is not None and not isinstance(piece, Piece):
            raise BoardStateError("set_piece expects a Piece or None.")
        self._state[pos.row][pos.col] = piece

    def clear_piece(self, position: PositionLike) -> Piece | None:
        """Remove and return the piece at a square."""
        pos = self._require_inside(position)
        piece = self._state[pos.row][pos.col]
        self._state[pos.row][pos.col] = None
        return piece

    def to_matrix(self) -> BoardState:
        """Return a shallow-copy board matrix."""
        return [[piece for piece in row] for row in self._state]

    def piece_map(self) -> dict[Position, Piece]:
        """Return occupied squares as ``Position -> Piece``."""
        result: dict[Position, Piece] = {}
        for row_index, row in enumerate(self._state):
            for col_index, piece in enumerate(row):
                if piece is not None:
                    result[Position(row_index, col_index)] = piece
        return result

    def make_move(self, move: Move | str) -> Move:
        """Apply a board-consistent move and return the filled-in move."""
        move = parse_iccs_move(move) if isinstance(move, str) else move
        from_pos = self._require_inside(move.from_pos)
        to_pos = self._require_inside(move.to_pos)
        moved_piece = self.get_piece(from_pos)
        if moved_piece is None:
            raise IllegalMoveError(f"No piece on source square {from_pos}.")
        captured_piece = self.get_piece(to_pos)
        if captured_piece is not None and captured_piece.color == moved_piece.color:
            raise IllegalMoveError(f"Cannot capture friendly piece at {to_pos}.")

        applied = Move(
            from_pos,
            to_pos,
            piece=moved_piece,
            captured=captured_piece,
            flags=(
                CAPTURE_MOVE_FLAG if captured_piece else move.flags or NORMAL_MOVE_FLAG
            ),
        )
        self._history.append(
            HistoryEntry(
                applied,
                moved_piece,
                captured_piece,
                self.side_to_move,
                self.halfmove_clock,
                self.fullmove_number,
            )
        )
        self._state[to_pos.row][to_pos.col] = moved_piece
        self._state[from_pos.row][from_pos.col] = None
        self.halfmove_clock = 0 if captured_piece else self.halfmove_clock + 1
        if self.side_to_move == BLACK:
            self.fullmove_number += 1
        self.side_to_move = opponent(self.side_to_move)
        return applied

    def undo_move(self) -> Move | None:
        """Undo the last applied move, returning it if one exists."""
        if not self._history:
            return None
        entry = self._history.pop()
        move = entry.move
        self._state[move.from_pos.row][move.from_pos.col] = entry.moved_piece
        self._state[move.to_pos.row][move.to_pos.col] = entry.captured_piece
        self.side_to_move = entry.previous_side_to_move
        self.halfmove_clock = entry.previous_halfmove_clock
        self.fullmove_number = entry.previous_fullmove_number
        return move

    @property
    def history_length(self) -> int:
        """Return number of applied moves currently in history."""
        return len(self._history)

    @property
    def history(self) -> tuple[HistoryEntry, ...]:
        """Immutable view of history, mainly for diagnostics."""
        return tuple(self._history)

    def _require_inside(self, position: PositionLike) -> Position:
        pos = self._coerce_position(position)
        if not (0 <= pos.row < BOARD_ROWS and 0 <= pos.col < BOARD_COLS):
            raise BoardStateError(f"Position {pos!r} is outside the board.")
        return pos

    @staticmethod
    def _coerce_position(position: PositionLike) -> Position:
        if isinstance(position, Position):
            return position
        if isinstance(position, str):
            try:
                return Position.from_iccs(position)
            except ValueError as exc:
                raise BoardStateError(str(exc)) from exc
        if isinstance(position, tuple) and len(position) == 2:
            return Position(position[0], position[1])
        raise BoardStateError(f"Unsupported position value: {position!r}")


def opponent(color: str) -> str:
    """Return the other side."""
    return BLACK if color == RED else RED


def _parse_piece_placement(placement: str) -> BoardState:
    rows = placement.split("/")
    if len(rows) != BOARD_ROWS:
        raise InvalidFENError("1st field must contain 10 '/'-delimited rows.")

    board_state: BoardState = []
    for row_text in rows:
        row: list[Piece | None] = []
        previous_was_number = False
        for symbol in row_text:
            if symbol.isdecimal():
                if previous_was_number:
                    raise InvalidFENError("Piece placement has consecutive numbers.")
                empty = int(symbol)
                if empty <= 0:
                    raise InvalidFENError("Empty counts must be positive.")
                row.extend([None] * empty)
                previous_was_number = True
            else:
                if symbol not in FEN_PIECE_SYMBOLS:
                    raise InvalidFENError(f"Invalid piece symbol {symbol!r}.")
                row.append(Piece.from_fen_symbol(symbol))
                previous_was_number = False
            if len(row) > BOARD_COLS:
                raise InvalidFENError("A FEN row contains more than 9 files.")
        if len(row) != BOARD_COLS:
            raise InvalidFENError("Each FEN row must contain exactly 9 files.")
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

    if counts.get((RED, KING), 0) != 1 or counts.get((BLACK, KING), 0) != 1:
        raise InvalidFENError("Each side must have exactly one king.")
    for color in (RED, BLACK):
        for piece_type, limit in MAX_PIECE_COUNTS.items():
            if counts.get((color, piece_type), 0) > limit:
                raise InvalidFENError(f"Too many {color} {piece_type} pieces.")
        for piece_type in (KING, ADVISER, BISHOP, PAWN):
            for position in positions.get((color, piece_type), []):
                if _out_of_place(piece_type, position, color):
                    raise InvalidFENError(
                        f"{color} {piece_type} is on an illegal square."
                    )


def _validate_board_shape(board_state: BoardState) -> None:
    if len(board_state) != BOARD_ROWS:
        raise BoardStateError(f"Board must have {BOARD_ROWS} rows.")
    for row in board_state:
        if len(row) != BOARD_COLS:
            raise BoardStateError(f"Every board row must have {BOARD_COLS} columns.")
        for piece in row:
            if piece is not None and not isinstance(piece, Piece):
                raise BoardStateError("Board entries must be Piece or None.")


def _out_of_place(piece_type: str, position: Position, color: str) -> bool:
    """FEN-time piece placement restrictions copied from xiangqi.js."""
    if piece_type == PAWN:
        starting_files = {0, 2, 4, 6, 8}
        if color == RED:
            return position.row > 6 or (
                position.row > 4 and position.col not in starting_files
            )
        return position.row < 3 or (
            position.row < 5 and position.col not in starting_files
        )
    if piece_type == BISHOP:
        red = {
            Position(9, 2),
            Position(9, 6),
            Position(7, 0),
            Position(7, 4),
            Position(7, 8),
            Position(5, 2),
            Position(5, 6),
        }
        black = {
            Position(0, 2),
            Position(0, 6),
            Position(2, 0),
            Position(2, 4),
            Position(2, 8),
            Position(4, 2),
            Position(4, 6),
        }
        return position not in (red if color == RED else black)
    if piece_type in {KING, ADVISER}:
        return not in_palace(position, color)
    return False


def in_palace(position: Position, color: str) -> bool:
    """Return whether a square is inside ``color``'s 3x3 palace."""
    if position.col < 3 or position.col > 5:
        return False
    return 7 <= position.row <= 9 if color == RED else 0 <= position.row <= 2


def crossed_river(position: Position, color: str) -> bool:
    """Return whether a pawn at ``position`` has crossed the river."""
    return position.row < 5 if color == RED else position.row > 4


def elephant_crosses_river(position: Position, color: str) -> bool:
    """Return whether an elephant destination would cross the river."""
    return position.row < 5 if color == RED else position.row > 4

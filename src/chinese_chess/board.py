"""Board representation and square-level state management."""

from __future__ import annotations

from typing import TypeAlias

from chinese_chess.constants import BLACK, BOARD_COLS, BOARD_ROWS, CAPTURE_MOVE_FLAG, DEFAULT_FEN, RED
from chinese_chess.exceptions import BoardStateError, IllegalMoveError
from chinese_chess.fen import parse_fen_record, serialize_fen
from chinese_chess.history import HistoryEntry
from chinese_chess.types import BoardState, Move, Piece, Position

PositionLike: TypeAlias = Position | str | tuple[int, int]


class Board:
    """Mutable Xiangqi board state without move-generation rules."""

    def __init__(self, fen: str | None = None) -> None:
        self._state: BoardState = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        self.side_to_move = "r"
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self._history: list[HistoryEntry] = []
        self.load_fen(DEFAULT_FEN if fen is None else fen)

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        """Create a board from FEN."""
        return cls(fen)

    def load_fen(self, fen: str) -> None:
        """Replace the current board state with a FEN position."""
        parsed = parse_fen_record(fen)
        self._state = [[piece for piece in row] for row in parsed.board_state]
        self.side_to_move = parsed.side_to_move
        self.halfmove_clock = parsed.halfmove_clock
        self.fullmove_number = parsed.fullmove_number
        self._history = []

    def fen(self) -> str:
        """Return the current board state as xiangqi.js-compatible FEN."""
        return serialize_fen(
            self._state,
            self.side_to_move,
            self.halfmove_clock,
            self.fullmove_number,
        )

    def position_key(self) -> str:
        """Return the repetition key used by xiangqi.js.

        The reference implementation compares only piece placement and side to
        move, ignoring castling/en-passant placeholders and move counters.
        """
        return " ".join(self.fen().split()[:2])

    def is_inside(self, position: PositionLike) -> bool:
        """Return whether a position lies inside the 10x9 board."""
        try:
            pos = self._coerce_position(position)
        except BoardStateError:
            return False
        return 0 <= pos.row < BOARD_ROWS and 0 <= pos.col < BOARD_COLS

    def get_piece(self, position: PositionLike) -> Piece | None:
        """Return the piece at a position, or ``None`` if the square is empty."""
        pos = self._require_inside(position)
        return self._state[pos.row][pos.col]

    def set_piece(self, position: PositionLike, piece: Piece | None) -> None:
        """Place a piece on a square, or clear it when ``piece`` is ``None``."""
        pos = self._require_inside(position)
        if piece is not None and not isinstance(piece, Piece):
            raise BoardStateError("set_piece expects a Piece instance or None.")
        self._state[pos.row][pos.col] = piece

    def clear_piece(self, position: PositionLike) -> Piece | None:
        """Remove and return the piece at a square, if any."""
        pos = self._require_inside(position)
        piece = self._state[pos.row][pos.col]
        self._state[pos.row][pos.col] = None
        return piece

    def to_matrix(self) -> BoardState:
        """Return a shallow-copy 10x9 matrix view of the board."""
        return [[piece for piece in row] for row in self._state]

    def piece_map(self) -> dict[Position, Piece]:
        """Return occupied squares as a mapping from position to piece."""
        result: dict[Position, Piece] = {}
        for row_index, row in enumerate(self._state):
            for col_index, piece in enumerate(row):
                if piece is not None:
                    result[Position(row_index, col_index)] = piece
        return result

    def make_move(self, move: Move) -> Move:
        """Apply a move without legal-move filtering.

        This method only enforces basic board consistency: source occupied,
        destination inside the board, and no capture of a friendly piece.
        Legal self-check filtering is handled by ``movegen.legal``.
        """
        from_pos = self._require_inside(move.from_pos)
        to_pos = self._require_inside(move.to_pos)
        moved_piece = self.get_piece(from_pos)
        if moved_piece is None:
            raise IllegalMoveError(f"No piece on source square {from_pos}.")

        captured_piece = self.get_piece(to_pos)
        if captured_piece is not None and captured_piece.color == moved_piece.color:
            raise IllegalMoveError(f"Cannot move onto friendly piece at {to_pos}.")

        applied_move = Move(
            from_pos=from_pos,
            to_pos=to_pos,
            piece=moved_piece,
            captured=captured_piece,
            flags=CAPTURE_MOVE_FLAG if captured_piece is not None else move.flags,
        )
        self._history.append(
            HistoryEntry(
                move=applied_move,
                moved_piece=moved_piece,
                captured_piece=captured_piece,
                previous_side_to_move=self.side_to_move,
                previous_halfmove_clock=self.halfmove_clock,
                previous_fullmove_number=self.fullmove_number,
            )
        )

        self._state[to_pos.row][to_pos.col] = moved_piece
        self._state[from_pos.row][from_pos.col] = None

        self.halfmove_clock = 0 if captured_piece is not None else self.halfmove_clock + 1
        if self.side_to_move == BLACK:
            self.fullmove_number += 1
        self.side_to_move = BLACK if self.side_to_move == RED else RED
        return applied_move

    def undo_move(self) -> Move | None:
        """Undo and return the last applied move, if one exists."""
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
        """Return the number of reversible moves in history."""
        return len(self._history)

    def history(self) -> tuple[HistoryEntry, ...]:
        """Return an immutable view of reversible history entries."""
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
                return Position.from_algebraic(position)
            except ValueError as exc:
                raise BoardStateError(str(exc)) from exc
        if isinstance(position, tuple) and len(position) == 2:
            return Position(row=position[0], col=position[1])
        raise BoardStateError(f"Unsupported position value: {position!r}")

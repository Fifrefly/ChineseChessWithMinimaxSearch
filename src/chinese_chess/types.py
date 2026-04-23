"""Typed domain objects for pieces, squares, moves, and validation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from chinese_chess.constants import (
    BLACK,
    COLORS,
    ICCS_FILES,
    ICCS_RANKS,
    PIECE_TYPES,
    RED,
)


BoardState: TypeAlias = list[list["Piece | None"]]


@dataclass(frozen=True, slots=True, order=True)
class Position:
    """A zero-based board coordinate.

    ``row=0`` is the top rank in FEN (black side), and ``col=0`` is file
    ``a``. Bounds checking is intentionally owned by ``Board`` so positions
    can be constructed while parsing or validating.
    """

    row: int
    col: int

    @classmethod
    def from_algebraic(cls, square: str) -> "Position":
        """Create a position from an ICCS coordinate such as ``e2``."""
        if len(square) != 2:
            raise ValueError(f"Invalid square {square!r}; expected file and rank.")

        file_symbol = square[0].lower()
        rank_symbol = square[1]
        if file_symbol not in ICCS_FILES or rank_symbol not in ICCS_RANKS:
            raise ValueError(f"Invalid square {square!r}; expected a9 through i0.")

        return cls(row=ICCS_RANKS.index(rank_symbol), col=ICCS_FILES.index(file_symbol))

    def to_algebraic(self) -> str:
        """Return this position in ICCS coordinate form."""
        try:
            return f"{ICCS_FILES[self.col]}{ICCS_RANKS[self.row]}"
        except IndexError as exc:
            raise ValueError(f"Position is outside ICCS coordinates: {self!r}") from exc

    def to_tuple(self) -> tuple[int, int]:
        """Return ``(row, col)`` for simple serialization and tests."""
        return (self.row, self.col)

    def __str__(self) -> str:
        return self.to_algebraic()


@dataclass(frozen=True, slots=True)
class Piece:
    """A Xiangqi piece using xiangqi.js type and color symbols."""

    type: str
    color: str

    def __post_init__(self) -> None:
        if self.type not in PIECE_TYPES:
            raise ValueError(f"Invalid piece type {self.type!r}.")
        if self.color not in COLORS:
            raise ValueError(f"Invalid piece color {self.color!r}.")

    @classmethod
    def from_fen_symbol(cls, symbol: str) -> "Piece":
        """Create a piece from a single FEN placement symbol."""
        if len(symbol) != 1:
            raise ValueError(f"Invalid FEN piece symbol {symbol!r}.")
        color = RED if symbol.isupper() else BLACK
        return cls(type=symbol.lower(), color=color)

    def to_fen_symbol(self) -> str:
        """Return the FEN placement symbol for this piece."""
        return self.type.upper() if self.color == RED else self.type

    def to_dict(self) -> dict[str, str]:
        """Return a xiangqi.js-like serializable piece object."""
        return {"type": self.type, "color": self.color}


@dataclass(frozen=True, slots=True)
class Move:
    """A reversible move value used by future state transitions.

    This stage does not implement legal move generation. The fields mirror the
    information xiangqi.js keeps in its internal move object so later
    ``make_move`` and ``undo_move`` work can build on the same shape.
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
        """Create a move from an ICCS coordinate string like ``h2e2``."""
        clean = text.strip().replace("-", "")
        if len(clean) != 4:
            raise ValueError(f"Invalid ICCS move {text!r}; expected forms like h2e2.")
        return cls(
            from_pos=Position.from_algebraic(clean[:2]),
            to_pos=Position.from_algebraic(clean[2:]),
            piece=piece,
            captured=captured,
            flags=flags,
        )

    def to_iccs(self) -> str:
        """Return the move in compact ICCS coordinate form."""
        return f"{self.from_pos}{self.to_pos}"

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable move dictionary for debugging and tests."""
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


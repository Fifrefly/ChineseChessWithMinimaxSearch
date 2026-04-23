"""Undo history snapshots for reversible board state."""

from __future__ import annotations

from dataclasses import dataclass

from chinese_chess.types import Move, Piece


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """State needed to undo one applied move."""

    move: Move
    moved_piece: Piece
    captured_piece: Piece | None
    previous_side_to_move: str
    previous_halfmove_clock: int
    previous_fullmove_number: int


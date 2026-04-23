"""Move models plus ICCS parsing and formatting helpers."""

from __future__ import annotations

from chinese_chess.types import Move, Piece

__all__ = ["Move", "parse_iccs_move", "move_to_iccs"]


def parse_iccs_move(
    text: str,
    *,
    piece: Piece | None = None,
    captured: Piece | None = None,
    flags: str = "",
) -> Move:
    """Parse a compact or hyphenated ICCS move string.

    Examples accepted by xiangqi.js include ``h2e2`` and ``h2-e2``. This
    helper deliberately stays format-only; it does not check whether the move
    is pseudo-legal or legal in a position.
    """
    return Move.from_iccs(text, piece=piece, captured=captured, flags=flags)


def move_to_iccs(move: Move) -> str:
    """Return a move in compact ICCS form."""
    return move.to_iccs()

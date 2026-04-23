"""Rule helpers for check, terminal states, and repetition."""

from chinese_chess.rules.check import has_legal_moves, is_check
from chinese_chess.rules.repetition import is_threefold_repetition, position_key
from chinese_chess.rules.terminal import game_over, is_checkmate, is_stalemate

__all__ = [
    "game_over",
    "has_legal_moves",
    "is_check",
    "is_checkmate",
    "is_stalemate",
    "is_threefold_repetition",
    "position_key",
]

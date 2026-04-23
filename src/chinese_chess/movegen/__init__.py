"""Move generation package."""

from chinese_chess.movegen.attack import find_king, is_in_check, is_square_attacked
from chinese_chess.movegen.legal import generate_legal_moves
from chinese_chess.movegen.pseudo_legal import (
    generate_advisor_moves,
    generate_cannon_moves,
    generate_elephant_moves,
    generate_horse_moves,
    generate_king_moves,
    generate_pawn_moves,
    generate_piece_moves,
    generate_pseudo_legal_moves,
    generate_rook_moves,
)

__all__ = [
    "find_king",
    "generate_advisor_moves",
    "generate_cannon_moves",
    "generate_elephant_moves",
    "generate_horse_moves",
    "generate_king_moves",
    "generate_legal_moves",
    "generate_pawn_moves",
    "generate_piece_moves",
    "generate_pseudo_legal_moves",
    "generate_rook_moves",
    "is_in_check",
    "is_square_attacked",
]

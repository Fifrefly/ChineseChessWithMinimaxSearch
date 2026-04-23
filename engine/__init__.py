"""Compact readable Xiangqi engine for course experiments."""

from engine.core import (
    BLACK,
    DEFAULT_FEN,
    RED,
    Board,
    BoardStateError,
    IllegalMoveError,
    InvalidFENError,
    Move,
    Piece,
    Position,
)
from engine.evaluation import PIECE_VALUES, evaluate, evaluate_material
from engine.rules import (
    game_over,
    generate_legal_moves,
    generate_pseudo_legal_moves,
    is_check,
    is_checkmate,
    is_stalemate,
    is_threefold_repetition,
)
from engine.search import SearchResult, SearchStats, minimax_search

__all__ = [
    "BLACK",
    "DEFAULT_FEN",
    "PIECE_VALUES",
    "RED",
    "Board",
    "BoardStateError",
    "IllegalMoveError",
    "InvalidFENError",
    "Move",
    "Piece",
    "Position",
    "SearchResult",
    "SearchStats",
    "evaluate",
    "evaluate_material",
    "game_over",
    "generate_legal_moves",
    "generate_pseudo_legal_moves",
    "is_check",
    "is_checkmate",
    "is_stalemate",
    "is_threefold_repetition",
    "minimax_search",
]


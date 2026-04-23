"""Small evaluation functions for minimax experiments.

The default score is pure material. Positive scores favor the requested
perspective. Later coursework experiments can add mobility, piece-square
tables, or king safety here without changing the search code.
"""

from __future__ import annotations

from engine.core import ADVISER, BISHOP, BLACK, CANNON, KING, KNIGHT, PAWN, RED, ROOK, Board

PIECE_VALUES: dict[str, int] = {
    KING: 10000,
    ROOK: 900,
    CANNON: 450,
    KNIGHT: 400,
    BISHOP: 200,
    ADVISER: 200,
    PAWN: 100,
}


def evaluate_material(board: Board, perspective: str = RED) -> int:
    """Return material balance from ``perspective``.

    Internally the score is red-centric: red pieces add, black pieces subtract.
    Passing ``perspective=BLACK`` flips the sign.
    """
    red_score = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.type]
        red_score += value if piece.color == RED else -value
    return red_score if perspective == RED else -red_score


def evaluate(board: Board, perspective: str = RED) -> int:
    """Default evaluator used by search."""
    return evaluate_material(board, perspective)


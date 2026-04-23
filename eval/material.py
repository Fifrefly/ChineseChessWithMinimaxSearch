"""Minimal material evaluation.

The raw material score is red-centric: positive values favor red, negative
values favor black. Callers can pass ``perspective`` to receive a score from
that side's point of view, which is what search code normally wants.
"""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import ADVISER, BISHOP, BLACK, CANNON, KING, KNIGHT, PAWN, RED, ROOK
from chinese_chess.game import Game

PIECE_VALUES: dict[str, int] = {
    KING: 10000,
    ROOK: 900,
    CANNON: 450,
    KNIGHT: 400,
    BISHOP: 200,
    ADVISER: 200,
    PAWN: 100,
}


def evaluate_material(game_or_board: Game | Board, perspective: str = RED) -> int:
    """Return material balance from ``perspective``.

    Positive means the requested perspective is better. Internally, material is
    first summed from red's point of view and then negated for black.
    """
    board = game_or_board.board_obj if isinstance(game_or_board, Game) else game_or_board
    red_score = 0
    for piece in board.piece_map().values():
        value = PIECE_VALUES[piece.type]
        red_score += value if piece.color == RED else -value
    return red_score if perspective == RED else -red_score

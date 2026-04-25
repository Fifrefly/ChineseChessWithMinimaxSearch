"""Small evaluation functions for minimax experiments.

The default score is pure material. Positive scores favor the requested
perspective. Later coursework experiments can add mobility, piece-square
tables, or king safety here without changing the search code.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.core import (
    ADVISER,
    BISHOP,
    BLACK,
    CANNON,
    KING,
    KNIGHT,
    PAWN,
    RED,
    ROOK,
    Board,
    Position,
)
from engine.rules import generate_pseudo_legal_moves, is_check, is_square_attacked

PIECE_VALUES: dict[str, int] = {
    KING: 10000,
    ROOK: 900,
    CANNON: 450,
    KNIGHT: 400,
    BISHOP: 200,
    ADVISER: 200,
    PAWN: 100,
}

MOBILITY_WEIGHTS: dict[str, int] = {
    ROOK: 4,
    CANNON: 3,
    KNIGHT: 5,
    PAWN: 2,
    ADVISER: 1,
    BISHOP: 1,
    KING: 0,
}

CHECK_PENALTY = 80
PALACE_ATTACK_PENALTY = 10
MISSING_ADVISER_PENALTY = 18
MISSING_BISHOP_PENALTY = 12
ADVANCED_PAWN_NEAR_KING_PENALTY = 12

CAPTURE_THREAT_SCALE = 20
HANGING_PIECE_SCALE = 12
ATTACKED_DEFENDED_PIECE_SCALE = 40


@dataclass(frozen=True, slots=True)
class EvaluationFeatures:
    material: int
    position: int
    mobility: int
    king_safety: int
    threats: int

    def as_tuple(self) -> tuple[int, int, int, int, int]:
        return (
            self.material,
            self.position,
            self.mobility,
            self.king_safety,
            self.threats,
        )


@dataclass(frozen=True, slots=True)
class EvaluationWeights:
    material: float = 1.0
    position: float = 1.0
    mobility: float = 0.8
    king_safety: float = 1.2
    threats: float = 0.9


DEFAULT_EVALUATION_WEIGHTS = EvaluationWeights()
UNIT_EVALUATION_WEIGHTS = EvaluationWeights(
    material=1.0,
    position=1.0,
    mobility=1.0,
    king_safety=1.0,
    threats=1.0,
)


KING_POSITION_BONUS_RED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 6, 6, 6, 0, 0, 0],
    [0, 0, 0, 4, 8, 4, 0, 0, 0],
]

ADVISER_POSITION_BONUS_RED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 8, 0, 8, 0, 0, 0],
    [0, 0, 0, 0, 14, 0, 0, 0, 0],
    [0, 0, 0, 6, 0, 6, 0, 0, 0],
]

BISHOP_POSITION_BONUS_RED = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 10, 0, 0, 0, 10, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [4, 0, 0, 0, 14, 0, 0, 0, 4],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 6, 0, 0, 0, 6, 0, 0],
]

KNIGHT_POSITION_BONUS_RED = [
    [18, 22, 26, 30, 34, 30, 26, 22, 18],
    [24, 28, 32, 36, 40, 36, 32, 28, 24],
    [30, 34, 38, 42, 46, 42, 38, 34, 30],
    [34, 38, 42, 46, 50, 46, 42, 38, 34],
    [32, 36, 40, 44, 48, 44, 40, 36, 32],
    [28, 32, 36, 40, 44, 40, 36, 32, 28],
    [20, 24, 28, 32, 36, 32, 28, 24, 20],
    [14, 18, 22, 26, 30, 26, 22, 18, 14],
    [6, 10, 14, 18, 22, 18, 14, 10, 6],
    [0, 4, 8, 12, 16, 12, 8, 4, 0],
]

ROOK_POSITION_BONUS_RED = [
    [24, 28, 32, 35, 38, 35, 32, 28, 24],
    [28, 32, 36, 39, 42, 39, 36, 32, 28],
    [26, 30, 34, 37, 40, 37, 34, 30, 26],
    [24, 28, 32, 35, 38, 35, 32, 28, 24],
    [22, 26, 30, 33, 36, 33, 30, 26, 22],
    [18, 22, 26, 29, 32, 29, 26, 22, 18],
    [14, 18, 22, 25, 28, 25, 22, 18, 14],
    [10, 14, 18, 21, 24, 21, 18, 14, 10],
    [6, 10, 14, 17, 20, 17, 14, 10, 6],
    [0, 4, 8, 11, 14, 11, 8, 4, 0],
]

CANNON_POSITION_BONUS_RED = [
    [16, 19, 22, 25, 28, 25, 22, 19, 16],
    [20, 23, 26, 29, 32, 29, 26, 23, 20],
    [24, 27, 30, 33, 36, 33, 30, 27, 24],
    [26, 29, 32, 35, 38, 35, 32, 29, 26],
    [24, 27, 30, 33, 36, 33, 30, 27, 24],
    [22, 25, 28, 31, 34, 31, 28, 25, 22],
    [24, 27, 30, 33, 36, 33, 30, 27, 24],
    [28, 31, 34, 37, 40, 37, 34, 31, 28],
    [12, 15, 18, 21, 24, 21, 18, 15, 12],
    [0, 3, 6, 9, 12, 9, 6, 3, 0],
]

PAWN_POSITION_BONUS_RED = [
    [70, 74, 78, 82, 86, 82, 78, 74, 70],
    [60, 64, 68, 72, 76, 72, 68, 64, 60],
    [50, 54, 58, 62, 66, 62, 58, 54, 50],
    [40, 44, 48, 52, 56, 52, 48, 44, 40],
    [30, 34, 38, 42, 46, 42, 38, 34, 30],
    [8, 12, 16, 20, 24, 20, 16, 12, 8],
    [0, 4, 8, 12, 16, 12, 8, 4, 0],
    [0, 4, 8, 12, 16, 12, 8, 4, 0],
    [0, 4, 8, 12, 16, 12, 8, 4, 0],
    [0, 4, 8, 12, 16, 12, 8, 4, 0],
]

POSITION_BONUS_RED: dict[str, list[list[int]]] = {
    KING: KING_POSITION_BONUS_RED,
    ADVISER: ADVISER_POSITION_BONUS_RED,
    BISHOP: BISHOP_POSITION_BONUS_RED,
    KNIGHT: KNIGHT_POSITION_BONUS_RED,
    ROOK: ROOK_POSITION_BONUS_RED,
    CANNON: CANNON_POSITION_BONUS_RED,
    PAWN: PAWN_POSITION_BONUS_RED,
}


def _position_bonus(piece_type: str, color: str, row: int, col: int) -> int:
    table = POSITION_BONUS_RED.get(piece_type)
    if table is None:
        return 0
    lookup_row = row if color == RED else 9 - row
    return table[lookup_row][col]


def _mobility_score(board: Board) -> int:
    red_mobility = 0
    black_mobility = 0

    for move in generate_pseudo_legal_moves(board, RED):
        if move.piece is not None:
            red_mobility += MOBILITY_WEIGHTS.get(move.piece.type, 0)

    for move in generate_pseudo_legal_moves(board, BLACK):
        if move.piece is not None:
            black_mobility += MOBILITY_WEIGHTS.get(move.piece.type, 0)

    return red_mobility - black_mobility


def _palace_squares(color: str) -> list[Position]:
    rows = range(7, 10) if color == RED else range(0, 3)
    return [Position(row, col) for row in rows for col in range(3, 6)]


def _defender_counts(board: Board, color: str) -> tuple[int, int]:
    adviser_count = 0
    bishop_count = 0
    for piece in board.piece_map().values():
        if piece.color != color:
            continue
        if piece.type == ADVISER:
            adviser_count += 1
        elif piece.type == BISHOP:
            bishop_count += 1
    return adviser_count, bishop_count


def _advanced_enemy_pawns_near_king(board: Board, color: str) -> int:
    center_row = 8 if color == RED else 1
    count = 0
    for position, piece in board.piece_map().items():
        if piece.type != PAWN or piece.color == color:
            continue
        crossed = (piece.color == BLACK and position.row > 4) or (
            piece.color == RED and position.row < 5
        )
        if not crossed:
            continue
        distance = abs(position.row - center_row) + abs(position.col - 4)
        if distance <= 3:
            count += 1
    return count


def _side_king_danger(board: Board, color: str) -> int:
    danger = 0
    enemy = BLACK if color == RED else RED

    if is_check(board, color):
        danger += CHECK_PENALTY

    for square in _palace_squares(color):
        if is_square_attacked(board, square, enemy):
            danger += PALACE_ATTACK_PENALTY

    adviser_count, bishop_count = _defender_counts(board, color)
    missing_advisers = max(0, 2 - adviser_count)
    missing_bishops = max(0, 2 - bishop_count)
    danger += missing_advisers * MISSING_ADVISER_PENALTY
    danger += missing_bishops * MISSING_BISHOP_PENALTY
    danger += (
        _advanced_enemy_pawns_near_king(board, color) * ADVANCED_PAWN_NEAR_KING_PENALTY
    )
    return danger


def _king_safety_score(board: Board) -> int:
    red_danger = _side_king_danger(board, RED)
    black_danger = _side_king_danger(board, BLACK)
    return black_danger - red_danger


def _capture_threat_score(board: Board) -> int:
    score = 0

    for move in generate_pseudo_legal_moves(board, RED):
        if move.captured is not None and move.captured.type != KING:
            score += PIECE_VALUES[move.captured.type] // CAPTURE_THREAT_SCALE

    for move in generate_pseudo_legal_moves(board, BLACK):
        if move.captured is not None and move.captured.type != KING:
            score -= PIECE_VALUES[move.captured.type] // CAPTURE_THREAT_SCALE

    return score


def _piece_pressure_score(board: Board) -> int:
    score = 0
    for position, piece in board.piece_map().items():
        if piece.type == KING:
            continue

        own_color = piece.color
        enemy_color = BLACK if own_color == RED else RED
        attacked_by_enemy = is_square_attacked(board, position, enemy_color)
        if not attacked_by_enemy:
            continue

        defended_by_own = is_square_attacked(board, position, own_color)
        scale = (
            ATTACKED_DEFENDED_PIECE_SCALE
            if defended_by_own
            else HANGING_PIECE_SCALE
        )
        pressure = PIECE_VALUES[piece.type] // scale
        score += pressure if piece.color == BLACK else -pressure

    return score


def _threats_and_protection_score(board: Board) -> int:
    return _capture_threat_score(board) + _piece_pressure_score(board)


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


def evaluate_piece_value_and_position(board: Board, perspective: str = RED) -> int:
    """Return material plus piece-square position bonus from ``perspective``."""
    red_score = 0
    for position, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.type] + _position_bonus(
            piece.type,
            piece.color,
            position.row,
            position.col,
        )
        red_score += value if piece.color == RED else -value
    return red_score if perspective == RED else -red_score


def evaluate_piece_value_position_and_mobility(
    board: Board,
    perspective: str = RED,
) -> int:
    """Return material, position bonus, and pseudo-legal mobility balance."""
    red_score = evaluate_piece_value_and_position(board, RED) + _mobility_score(board)
    return red_score if perspective == RED else -red_score


def evaluate_piece_value_position_mobility_and_king_safety(
    board: Board,
    perspective: str = RED,
) -> int:
    """Return material, position, mobility, and lightweight king safety score."""
    red_score = evaluate_piece_value_position_and_mobility(
        board, RED
    ) + _king_safety_score(board)
    return red_score if perspective == RED else -red_score


def evaluate_piece_value_position_mobility_king_safety_and_threats(
    board: Board,
    perspective: str = RED,
) -> int:
    """Return material, position, mobility, king safety, and threat pressure."""
    red_score = evaluate_piece_value_position_mobility_and_king_safety(
        board, RED
    ) + _threats_and_protection_score(board)
    return red_score if perspective == RED else -red_score


def extract_evaluation_features(
    board: Board,
    perspective: str = RED,
) -> EvaluationFeatures:
    """Return decomposed static evaluation features from ``perspective``."""
    material_red = evaluate_material(board, RED)
    position_red = evaluate_piece_value_and_position(board, RED) - material_red
    mobility_red = _mobility_score(board)
    king_safety_red = _king_safety_score(board)
    threats_red = _threats_and_protection_score(board)

    if perspective == RED:
        return EvaluationFeatures(
            material_red,
            position_red,
            mobility_red,
            king_safety_red,
            threats_red,
        )
    return EvaluationFeatures(
        -material_red,
        -position_red,
        -mobility_red,
        -king_safety_red,
        -threats_red,
    )


def evaluate_weighted_static(
    board: Board,
    perspective: str = RED,
    weights: EvaluationWeights | None = None,
) -> int:
    """Return a manually weighted score over decomposed evaluation features."""
    active_weights = DEFAULT_EVALUATION_WEIGHTS if weights is None else weights
    features = extract_evaluation_features(board, perspective)
    score = (
        features.material * active_weights.material
        + features.position * active_weights.position
        + features.mobility * active_weights.mobility
        + features.king_safety * active_weights.king_safety
        + features.threats * active_weights.threats
    )
    return int(round(score))


def evaluate(board: Board, perspective: str = RED) -> int:
    """Default evaluator used by search."""
    return evaluate_material(board, perspective)

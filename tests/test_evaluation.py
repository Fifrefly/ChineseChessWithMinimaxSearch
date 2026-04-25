"""Tests for material, position, mobility, and king-safety evaluation."""

from __future__ import annotations

from engine import evaluate_piece_value_and_position as exported_position_evaluator
from engine import (
    evaluate_piece_value_position_and_mobility as exported_mobility_evaluator,
)
from engine import (
    evaluate_piece_value_position_mobility_and_king_safety
    as exported_king_safety_evaluator,
)
from engine import (
    evaluate_piece_value_position_mobility_king_safety_and_threats
    as exported_threats_evaluator,
)
from engine.core import (
    ADVISER,
    BISHOP,
    BLACK,
    KING,
    KNIGHT,
    PAWN,
    RED,
    ROOK,
    Board,
    Piece,
    Position,
)
from engine.evaluation import (
    PIECE_VALUES,
    UNIT_EVALUATION_WEIGHTS,
    evaluate,
    evaluate_material,
    evaluate_piece_value_and_position,
    evaluate_piece_value_position_and_mobility,
    evaluate_piece_value_position_mobility_king_safety_and_threats,
    evaluate_piece_value_position_mobility_and_king_safety,
    evaluate_weighted_static,
    extract_evaluation_features,
)

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def board_with_piece(row: int, col: int, piece: Piece) -> Board:
    board = Board(MINIMAL_FEN)
    board.set_piece(Position(row, col), piece)
    return board


def board_with_file_blocker() -> Board:
    board = Board(MINIMAL_FEN)
    board.set_piece(Position(4, 4), Piece(PAWN, RED))
    return board


def king_safety_component(board: Board) -> int:
    return evaluate_piece_value_position_mobility_and_king_safety(
        board, RED
    ) - evaluate_piece_value_position_and_mobility(board, RED)


def threats_component(board: Board) -> int:
    return evaluate_piece_value_position_mobility_king_safety_and_threats(
        board, RED
    ) - evaluate_piece_value_position_mobility_and_king_safety(board, RED)


def test_initial_position_features_are_balanced() -> None:
    assert extract_evaluation_features(Board(), RED).as_tuple() == (0, 0, 0, 0, 0)
    assert extract_evaluation_features(Board(), BLACK).as_tuple() == (0, 0, 0, 0, 0)


def test_initial_position_is_balanced_for_material_and_position() -> None:
    board = Board()

    assert evaluate_material(board, RED) == 0
    assert evaluate_piece_value_and_position(board, RED) == 0
    assert evaluate_piece_value_and_position(board, BLACK) == 0
    assert exported_position_evaluator(board, RED) == 0
    assert evaluate_piece_value_position_and_mobility(board, RED) == 0
    assert evaluate_piece_value_position_and_mobility(board, BLACK) == 0
    assert exported_mobility_evaluator(board, RED) == 0
    assert evaluate_piece_value_position_mobility_and_king_safety(board, RED) == 0
    assert evaluate_piece_value_position_mobility_and_king_safety(board, BLACK) == 0
    assert exported_king_safety_evaluator(board, RED) == 0
    assert (
        evaluate_piece_value_position_mobility_king_safety_and_threats(board, RED)
        == 0
    )
    assert (
        evaluate_piece_value_position_mobility_king_safety_and_threats(board, BLACK)
        == 0
    )
    assert exported_threats_evaluator(board, RED) == 0


def test_red_pawn_scores_higher_when_closer_to_black_home_rank() -> None:
    starting_rank = board_with_piece(6, 4, Piece(PAWN, RED))
    advanced_rank = board_with_piece(3, 4, Piece(PAWN, RED))

    assert evaluate_piece_value_and_position(advanced_rank, RED) > (
        evaluate_piece_value_and_position(starting_rank, RED)
    )


def test_black_position_bonus_uses_vertical_mirror() -> None:
    red_pawn = board_with_piece(6, 4, Piece(PAWN, RED))
    black_pawn = board_with_piece(3, 4, Piece(PAWN, BLACK))

    assert evaluate_piece_value_and_position(black_pawn, RED) == -(
        evaluate_piece_value_and_position(red_pawn, RED)
    )


def test_perspective_scores_are_opposites_for_same_position() -> None:
    board = board_with_piece(5, 4, Piece(PAWN, RED))
    board.set_piece(Position(3, 4), Piece(PAWN, BLACK))

    red_score = evaluate_piece_value_and_position(board, RED)

    assert red_score != 0
    assert evaluate_piece_value_and_position(board, BLACK) == -red_score


def test_extracted_features_are_opposites_by_perspective() -> None:
    board = board_with_file_blocker()
    board.set_piece(Position(5, 0), Piece(ROOK, RED))
    board.set_piece(Position(5, 4), Piece(KNIGHT, BLACK))

    red_features = extract_evaluation_features(board, RED)
    black_features = extract_evaluation_features(board, BLACK)

    assert red_features.as_tuple() == tuple(-value for value in black_features.as_tuple())


def test_default_evaluate_remains_material_baseline() -> None:
    board = board_with_piece(3, 4, Piece(PAWN, RED))

    assert evaluate(board, RED) == evaluate_material(board, RED)
    assert evaluate(board, BLACK) == evaluate_material(board, BLACK)
    assert evaluate(board, RED) == PIECE_VALUES[PAWN]
    assert evaluate_piece_value_and_position(board, RED) > evaluate(board, RED)


def test_position_feature_does_not_repeat_material() -> None:
    board = board_with_piece(5, 0, Piece(ROOK, RED))
    features = extract_evaluation_features(board, RED)

    assert features.material == PIECE_VALUES[ROOK]
    assert features.position == (
        evaluate_piece_value_and_position(board, RED) - evaluate_material(board, RED)
    )
    assert features.position != evaluate_piece_value_and_position(board, RED)
    assert abs(features.position) < features.material


def test_position_evaluator_does_not_modify_board_fen() -> None:
    board = board_with_piece(3, 4, Piece(PAWN, RED))
    original_fen = board.fen()

    evaluate_piece_value_and_position(board, RED)
    evaluate_piece_value_and_position(board, BLACK)

    assert board.fen() == original_fen


def test_kings_only_minimal_position_is_balanced() -> None:
    board = Board(MINIMAL_FEN)

    assert evaluate_piece_value_and_position(board, RED) == 0
    assert evaluate_piece_value_and_position(board, BLACK) == 0
    assert board.get_piece(Position(0, 4)) == Piece(KING, BLACK)
    assert board.get_piece(Position(9, 4)) == Piece(KING, RED)


def test_mobility_evaluator_does_not_modify_board_fen() -> None:
    board = Board()
    original_fen = board.fen()

    evaluate_piece_value_position_and_mobility(board, RED)

    assert board.fen() == original_fen


def test_mobility_perspective_scores_are_opposites() -> None:
    board = board_with_piece(5, 4, Piece(KNIGHT, RED))
    board.set_piece(Position(3, 4), Piece(PAWN, BLACK))

    red_score = evaluate_piece_value_position_and_mobility(board, RED)

    assert red_score != 0
    assert evaluate_piece_value_position_and_mobility(board, BLACK) == -red_score


def test_free_knight_scores_higher_than_blocked_knight_with_equal_material() -> None:
    board_free = board_with_piece(5, 4, Piece(KNIGHT, RED))
    board_free.set_piece(Position(4, 3), Piece(PAWN, RED))
    board_free.set_piece(Position(4, 5), Piece(PAWN, RED))

    board_blocked = board_with_piece(5, 4, Piece(KNIGHT, RED))
    board_blocked.set_piece(Position(4, 4), Piece(PAWN, RED))
    board_blocked.set_piece(Position(5, 3), Piece(PAWN, RED))

    assert evaluate_piece_value_position_and_mobility(board_free, RED) > (
        evaluate_piece_value_position_and_mobility(board_blocked, RED)
    )


def test_open_rook_scores_higher_than_blocked_rook_with_equal_material() -> None:
    board_open = board_with_piece(5, 0, Piece(ROOK, RED))
    board_open.set_piece(Position(4, 2), Piece(PAWN, RED))
    board_open.set_piece(Position(4, 6), Piece(PAWN, RED))

    board_blocked = board_with_piece(5, 0, Piece(ROOK, RED))
    board_blocked.set_piece(Position(4, 0), Piece(PAWN, RED))
    board_blocked.set_piece(Position(5, 1), Piece(PAWN, RED))

    assert evaluate_piece_value_position_and_mobility(board_open, RED) > (
        evaluate_piece_value_position_and_mobility(board_blocked, RED)
    )


def test_mobility_changes_score_beyond_piece_value_and_position() -> None:
    board_open = board_with_piece(5, 0, Piece(ROOK, RED))
    board_blocked = board_with_piece(5, 0, Piece(ROOK, RED))
    board_blocked.set_piece(Position(4, 0), Piece(PAWN, BLACK))
    board_blocked.set_piece(Position(5, 1), Piece(PAWN, BLACK))

    position_delta = evaluate_piece_value_and_position(
        board_open, RED
    ) - evaluate_piece_value_and_position(board_blocked, RED)
    mobility_delta = evaluate_piece_value_position_and_mobility(
        board_open, RED
    ) - evaluate_piece_value_position_and_mobility(board_blocked, RED)

    assert mobility_delta != position_delta
    assert mobility_delta > position_delta


def test_king_safety_evaluator_does_not_modify_board_fen() -> None:
    board = Board()
    original_fen = board.fen()

    evaluate_piece_value_position_mobility_and_king_safety(board, RED)

    assert board.fen() == original_fen


def test_king_safety_perspective_scores_are_opposites() -> None:
    board = board_with_file_blocker()
    board.set_piece(Position(5, 4), Piece(KNIGHT, RED))
    board.set_piece(Position(6, 4), Piece(PAWN, BLACK))

    red_score = evaluate_piece_value_position_mobility_and_king_safety(board, RED)

    assert red_score != 0
    assert evaluate_piece_value_position_mobility_and_king_safety(
        board, BLACK
    ) == -red_score


def test_checked_red_king_scores_lower_than_unchecked_red_king() -> None:
    checked = board_with_file_blocker()
    checked.set_piece(Position(6, 4), Piece(ROOK, BLACK))

    unchecked = board_with_file_blocker()
    unchecked.set_piece(Position(6, 0), Piece(ROOK, BLACK))

    assert evaluate_piece_value_position_mobility_and_king_safety(checked, RED) < (
        evaluate_piece_value_position_mobility_and_king_safety(unchecked, RED)
    )
    assert king_safety_component(checked) < king_safety_component(unchecked)


def test_red_missing_advisers_and_bishops_scores_lower() -> None:
    defended = board_with_file_blocker()
    defended.set_piece(Position(9, 3), Piece(ADVISER, RED))
    defended.set_piece(Position(9, 5), Piece(ADVISER, RED))
    defended.set_piece(Position(9, 2), Piece(BISHOP, RED))
    defended.set_piece(Position(9, 6), Piece(BISHOP, RED))

    exposed = board_with_file_blocker()

    assert evaluate_piece_value_position_mobility_and_king_safety(defended, RED) > (
        evaluate_piece_value_position_mobility_and_king_safety(exposed, RED)
    )
    assert king_safety_component(defended) > king_safety_component(exposed)


def test_black_missing_advisers_and_bishops_improves_red_score() -> None:
    defended = board_with_file_blocker()
    defended.set_piece(Position(0, 3), Piece(ADVISER, BLACK))
    defended.set_piece(Position(0, 5), Piece(ADVISER, BLACK))
    defended.set_piece(Position(0, 2), Piece(BISHOP, BLACK))
    defended.set_piece(Position(0, 6), Piece(BISHOP, BLACK))

    exposed = board_with_file_blocker()

    assert evaluate_piece_value_position_mobility_and_king_safety(exposed, RED) > (
        evaluate_piece_value_position_mobility_and_king_safety(defended, RED)
    )
    assert king_safety_component(exposed) > king_safety_component(defended)


def test_advanced_enemy_pawn_near_palace_lowers_own_score() -> None:
    near = board_with_file_blocker()
    near.set_piece(Position(7, 4), Piece(PAWN, BLACK))

    far = board_with_file_blocker()
    far.set_piece(Position(5, 0), Piece(PAWN, BLACK))

    assert evaluate_piece_value_position_mobility_and_king_safety(near, RED) < (
        evaluate_piece_value_position_mobility_and_king_safety(far, RED)
    )
    assert king_safety_component(near) < king_safety_component(far)


def test_threats_evaluator_does_not_modify_board_fen() -> None:
    board = Board()
    original_fen = board.fen()

    evaluate_piece_value_position_mobility_king_safety_and_threats(board, RED)

    assert board.fen() == original_fen


def test_weighted_static_evaluator_does_not_modify_board_fen() -> None:
    board = Board()
    original_fen = board.fen()

    evaluate_weighted_static(board, RED)

    assert board.fen() == original_fen


def test_threats_perspective_scores_are_opposites() -> None:
    board = board_with_file_blocker()
    board.set_piece(Position(5, 0), Piece(ROOK, RED))
    board.set_piece(Position(5, 4), Piece(KNIGHT, BLACK))

    red_score = evaluate_piece_value_position_mobility_king_safety_and_threats(
        board, RED
    )

    assert red_score != 0
    assert evaluate_piece_value_position_mobility_king_safety_and_threats(
        board, BLACK
    ) == -red_score


def test_unit_weights_match_full_static_evaluator() -> None:
    board = board_with_file_blocker()
    board.set_piece(Position(5, 0), Piece(ROOK, RED))
    board.set_piece(Position(5, 4), Piece(KNIGHT, BLACK))

    assert evaluate_weighted_static(board, RED, UNIT_EVALUATION_WEIGHTS) == (
        evaluate_piece_value_position_mobility_king_safety_and_threats(board, RED)
    )
    assert evaluate_weighted_static(board, BLACK, UNIT_EVALUATION_WEIGHTS) == (
        evaluate_piece_value_position_mobility_king_safety_and_threats(board, BLACK)
    )


def test_default_weighted_static_returns_int() -> None:
    board = board_with_piece(5, 0, Piece(ROOK, RED))

    assert isinstance(evaluate_weighted_static(board, RED), int)


def test_direct_capture_threat_improves_red_score() -> None:
    threatened = board_with_file_blocker()
    threatened.set_piece(Position(5, 0), Piece(ROOK, RED))
    threatened.set_piece(Position(5, 4), Piece(KNIGHT, BLACK))
    threatened.set_piece(Position(5, 6), Piece(PAWN, BLACK))

    quiet = board_with_file_blocker()
    quiet.set_piece(Position(5, 0), Piece(ROOK, RED))
    quiet.set_piece(Position(5, 4), Piece(KNIGHT, BLACK))
    quiet.set_piece(Position(5, 2), Piece(PAWN, BLACK))

    assert evaluate_piece_value_position_mobility_king_safety_and_threats(
        threatened, RED
    ) > evaluate_piece_value_position_mobility_king_safety_and_threats(quiet, RED)
    assert threats_component(threatened) > threats_component(quiet)


def test_attacked_undefended_red_piece_scores_lower_than_defended_one() -> None:
    undefended = board_with_file_blocker()
    undefended.set_piece(Position(5, 4), Piece(ROOK, RED))
    undefended.set_piece(Position(5, 0), Piece(ROOK, BLACK))
    undefended.set_piece(Position(7, 1), Piece(KNIGHT, RED))

    defended = board_with_file_blocker()
    defended.set_piece(Position(5, 4), Piece(ROOK, RED))
    defended.set_piece(Position(5, 0), Piece(ROOK, BLACK))
    defended.set_piece(Position(7, 3), Piece(KNIGHT, RED))

    assert evaluate_piece_value_position_mobility_king_safety_and_threats(
        defended, RED
    ) > evaluate_piece_value_position_mobility_king_safety_and_threats(
        undefended, RED
    )
    assert threats_component(defended) > threats_component(undefended)


def test_attacked_undefended_black_piece_improves_red_score() -> None:
    undefended = board_with_file_blocker()
    undefended.set_piece(Position(5, 0), Piece(ROOK, RED))
    undefended.set_piece(Position(5, 4), Piece(ROOK, BLACK))
    undefended.set_piece(Position(3, 1), Piece(KNIGHT, BLACK))

    defended = board_with_file_blocker()
    defended.set_piece(Position(5, 0), Piece(ROOK, RED))
    defended.set_piece(Position(5, 4), Piece(ROOK, BLACK))
    defended.set_piece(Position(3, 3), Piece(KNIGHT, BLACK))

    assert evaluate_piece_value_position_mobility_king_safety_and_threats(
        undefended, RED
    ) > evaluate_piece_value_position_mobility_king_safety_and_threats(
        defended, RED
    )
    assert threats_component(undefended) > threats_component(defended)


def test_defended_attacked_piece_penalty_is_smaller_than_hanging_penalty() -> None:
    hanging = board_with_file_blocker()
    hanging.set_piece(Position(5, 4), Piece(ROOK, RED))
    hanging.set_piece(Position(5, 0), Piece(ROOK, BLACK))
    hanging.set_piece(Position(7, 1), Piece(KNIGHT, RED))

    defended = board_with_file_blocker()
    defended.set_piece(Position(5, 4), Piece(ROOK, RED))
    defended.set_piece(Position(5, 0), Piece(ROOK, BLACK))
    defended.set_piece(Position(7, 3), Piece(KNIGHT, RED))

    assert evaluate_piece_value_position_mobility_king_safety_and_threats(
        defended, RED
    ) > evaluate_piece_value_position_mobility_king_safety_and_threats(hanging, RED)
    assert threats_component(defended) > threats_component(hanging)

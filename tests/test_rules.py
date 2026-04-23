"""Tests for Xiangqi movement rules, legal filtering, and terminal states."""

from __future__ import annotations

from engine.core import (
    BLACK,
    RED,
    ADVISER,
    BISHOP,
    CANNON,
    KING,
    KNIGHT,
    PAWN,
    Board,
    Move,
    Piece,
    Position,
)
from engine.rules import (
    find_king,
    game_over,
    generate_legal_moves,
    generate_pseudo_legal_moves,
    is_check,
    is_checkmate,
    is_square_attacked,
    is_stalemate,
    is_threefold_repetition,
)

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"
CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"
REPEAT_SEQUENCE = ["a0a1", "a9a8", "a1a0", "a8a9", "a0a1", "a9a8", "a1a0", "a8a9"]


def iccs(moves: list[Move]) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_horse_leg_blocks_only_matching_axis() -> None:
    board = Board(MINIMAL_FEN)
    horse = Piece(KNIGHT, RED)
    board.set_piece("e4", horse)
    board.set_piece("e5", Piece(PAWN, RED))

    moves = iccs(generate_pseudo_legal_moves(board, RED))

    assert "e4d6" not in moves
    assert "e4f6" not in moves
    assert "e4d2" in moves
    assert "e4g3" in moves


def test_elephant_eye_and_river_rules() -> None:
    board = Board(MINIMAL_FEN)
    elephant = Piece(BISHOP, RED)
    board.set_piece("e2", elephant)
    board.set_piece("d3", Piece(PAWN, BLACK))

    moves = iccs(generate_pseudo_legal_moves(board, RED))

    assert "e2c4" not in moves
    assert "e2g4" in moves

    board = Board(MINIMAL_FEN)
    board.set_piece("e4", elephant)
    moves = iccs(generate_pseudo_legal_moves(board, RED))
    assert "e4c6" not in moves
    assert "e4g6" not in moves
    assert "e4c2" in moves


def test_king_and_advisor_stay_in_palace() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("e0", Piece(ADVISER, RED))

    moves = iccs(generate_pseudo_legal_moves(board, RED))

    assert "e0d1" in moves
    assert "e0f1" in moves
    assert "e0e1" not in moves

    board = Board(MINIMAL_FEN)
    moves = iccs(generate_pseudo_legal_moves(board, RED))
    assert {"e0e1", "e0d0", "e0f0"}.issubset(moves)
    assert "e0c0" not in moves


def test_cannon_capture_requires_exactly_one_screen() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("e4", Piece(CANNON, RED))
    board.set_piece("e5", Piece(PAWN, RED))
    board.set_piece("e6", Piece(PAWN, BLACK))
    board.set_piece("e7", Piece(PAWN, BLACK))

    moves = iccs(generate_pseudo_legal_moves(board, RED))

    assert "e4e5" not in moves
    assert "e4e6" in moves
    assert "e4e7" not in moves


def test_pawn_movement_before_and_after_river() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("e3", Piece(PAWN, RED))
    board.set_piece("a6", Piece(PAWN, BLACK))
    board.set_piece("e5", Piece(PAWN, RED))

    moves = iccs(generate_pseudo_legal_moves(board, RED))

    assert "e3e4" in moves
    assert "e3d3" not in moves
    assert {"e5e6", "e5d5", "e5f5"}.issubset(moves)


def test_self_check_and_flying_general_filtering() -> None:
    board = Board("4k4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1")

    assert is_check(board, RED) is False
    assert is_square_attacked(board, "e0", BLACK) is False
    moves = iccs(generate_legal_moves(board, RED))
    assert "e1d1" not in moves
    assert "e1f1" not in moves
    assert "e1e2" in moves


def test_check_checkmate_stalemate_and_game_over() -> None:
    checkmate = Board(CHECKMATE_FEN)
    stalemate = Board(STALEMATE_FEN)
    normal = Board()

    assert str(find_king(checkmate, RED)) == "e0"
    assert is_check(checkmate, RED) is True
    assert is_checkmate(checkmate, RED) is True
    assert game_over(checkmate) is True
    assert is_check(stalemate, RED) is False
    assert is_stalemate(stalemate, RED) is True
    assert game_over(stalemate) is True
    assert game_over(normal) is False


def test_threefold_repetition_uses_placement_and_side_to_move() -> None:
    board = Board()
    for move in REPEAT_SEQUENCE:
        board.make_move(move)
    fen_before = board.fen()

    assert is_threefold_repetition(board) is True
    assert game_over(board) is True
    assert board.fen() == fen_before
    assert board.history_length == len(REPEAT_SEQUENCE)

"""Tests for static move ordering heuristics."""

from __future__ import annotations

from collections import Counter

from engine.core import Board, Move
from engine.move_ordering import static_move_orderer
from engine.rules import generate_legal_moves

CAPTURE_FEN = "r3k4/9/9/9/9/2p6/2P1P4/9/9/R3K4 r - - 0 1"
CHECK_FEN = "4k4/9/9/9/9/9/9/9/R8/3K5 r - - 0 1"


def _move_by_iccs(moves: list[Move], text: str) -> Move:
    for move in moves:
        if move.to_iccs() == text:
            return move
    raise AssertionError(f"Expected move {text!r} not found.")


def test_static_move_orderer_does_not_change_board_fen() -> None:
    board = Board(CAPTURE_FEN)
    moves = generate_legal_moves(board)
    original_fen = board.fen()

    static_move_orderer(board, moves)

    assert board.fen() == original_fen


def test_static_move_orderer_returns_same_move_objects() -> None:
    board = Board(CAPTURE_FEN)
    moves = generate_legal_moves(board)

    ordered = static_move_orderer(board, moves)

    assert len(ordered) == len(moves)
    assert Counter(id(move) for move in ordered) == Counter(id(move) for move in moves)


def test_high_value_capture_orders_before_low_value_capture() -> None:
    board = Board(CAPTURE_FEN)
    moves = generate_legal_moves(board)
    low_capture = _move_by_iccs(moves, "c3c4")
    high_capture = _move_by_iccs(moves, "a0a9")

    ordered = static_move_orderer(board, [low_capture, high_capture])

    assert ordered == [high_capture, low_capture]


def test_check_orders_before_quiet_move() -> None:
    board = Board(CHECK_FEN)
    moves = generate_legal_moves(board)
    quiet = _move_by_iccs(moves, "a1a2")
    checking = _move_by_iccs(moves, "a1e1")

    ordered = static_move_orderer(board, [quiet, checking])

    assert ordered == [checking, quiet]


def test_equal_scores_keep_original_relative_order() -> None:
    board = Board(CHECK_FEN)
    moves = generate_legal_moves(board)
    quiet_a = _move_by_iccs(moves, "a1a2")
    quiet_b = _move_by_iccs(moves, "a1a3")

    ordered = static_move_orderer(board, [quiet_b, quiet_a])

    assert ordered == [quiet_b, quiet_a]

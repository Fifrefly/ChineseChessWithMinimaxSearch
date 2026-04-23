"""Tests for core board state, FEN, ICCS moves, and reversible moves."""

from __future__ import annotations

import pytest

from engine.core import (
    BLACK,
    DEFAULT_FEN,
    KNIGHT,
    RED,
    ROOK,
    Board,
    IllegalMoveError,
    InvalidFENError,
    Move,
    Piece,
    Position,
    parse_fen,
    parse_iccs_move,
    serialize_fen,
    validate_fen,
)
from engine.rules import generate_legal_moves


def test_default_fen_round_trips() -> None:
    board_state = parse_fen(DEFAULT_FEN)

    assert len(board_state) == 10
    assert all(len(row) == 9 for row in board_state)
    assert serialize_fen(board_state, RED) == DEFAULT_FEN
    assert Board().fen() == DEFAULT_FEN


def test_invalid_fen_reports_error_and_raises() -> None:
    valid, error = validate_fen("invalid")

    assert valid is False
    assert error is not None
    with pytest.raises(InvalidFENError):
        Board("invalid")


def test_iccs_position_and_move_helpers() -> None:
    position = Position.from_iccs("h2")
    move = parse_iccs_move("h2-e2")

    assert position == Position(7, 7)
    assert str(position) == "h2"
    assert move == Move.from_iccs("h2e2")
    assert move.to_iccs() == "h2e2"


def test_board_piece_read_write_and_friendly_capture_rejection() -> None:
    board = Board()
    knight = Piece(KNIGHT, RED)

    assert board.get_piece("a9") == Piece(ROOK, BLACK)
    board.set_piece("e4", knight)
    assert board.get_piece((5, 4)) == knight
    assert board.clear_piece("e4") == knight
    with pytest.raises(IllegalMoveError):
        board.make_move("a0b0")


def test_make_undo_restores_fen_for_many_legal_moves() -> None:
    positions = [
        DEFAULT_FEN,
        "3kr4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1",
        "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1",
    ]
    for fen in positions:
        board = Board(fen)
        original = board.fen()
        for move in generate_legal_moves(board):
            applied = board.make_move(move)
            assert applied.from_pos == move.from_pos
            board.undo_move()
            assert board.fen() == original
            assert board.history_length == 0

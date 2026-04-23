"""Unit tests for FEN parsing and serialization."""

from __future__ import annotations

import pytest

from chinese_chess.constants import BLACK, DEFAULT_FEN, KING, RED, ROOK
from chinese_chess.exceptions import InvalidFENError
from chinese_chess.fen import parse_fen, parse_fen_record, serialize_fen, validate_fen


def test_default_fen_parses_to_expected_board_state() -> None:
    board_state = parse_fen(DEFAULT_FEN)

    assert len(board_state) == 10
    assert all(len(row) == 9 for row in board_state)
    assert board_state[0][0] is not None
    assert board_state[0][0].type == ROOK
    assert board_state[0][0].color == BLACK
    assert board_state[9][4] is not None
    assert board_state[9][4].type == KING
    assert board_state[9][4].color == RED


def test_default_fen_round_trips() -> None:
    parsed = parse_fen_record(DEFAULT_FEN)

    assert serialize_fen(
        parsed.board_state,
        parsed.side_to_move,
        parsed.halfmove_clock,
        parsed.fullmove_number,
    ) == DEFAULT_FEN


def test_validate_fen_returns_clear_error_for_invalid_fen() -> None:
    valid, error = validate_fen("9/9/9/9/9/9/9/9/9/9 r - - 0 1")

    assert valid is False
    assert error is not None
    assert "king" in error


def test_parse_fen_raises_for_invalid_fen() -> None:
    with pytest.raises(InvalidFENError):
        parse_fen("invalid")


def test_side_to_move_w_alias_matches_xiangqi_js_load_behavior() -> None:
    fen = DEFAULT_FEN.replace(" r ", " w ")
    parsed = parse_fen_record(fen)

    assert parsed.side_to_move == RED


"""Unit tests for positions, pieces, and move values."""

from __future__ import annotations

import pytest

from chinese_chess.constants import CANNON, RED, ROOK
from chinese_chess.move import move_to_iccs, parse_iccs_move
from chinese_chess.types import Move, Piece, Position


def test_position_converts_to_and_from_iccs_square() -> None:
    position = Position.from_algebraic("h2")

    assert position == Position(7, 7)
    assert str(position) == "h2"
    assert position.to_tuple() == (7, 7)


def test_piece_converts_to_fen_symbol() -> None:
    assert Piece(ROOK, RED).to_fen_symbol() == "R"
    assert Piece.from_fen_symbol("c") == Piece(CANNON, "b")


def test_move_constructs_compares_and_serializes() -> None:
    piece = Piece(CANNON, RED)
    move = Move(Position.from_algebraic("h2"), Position.from_algebraic("e2"), piece=piece)

    assert move == Move.from_iccs("h2e2", piece=piece)
    assert str(move) == "h2e2"
    assert move.to_dict()["piece"] == {"type": CANNON, "color": RED}


def test_move_module_parses_hyphenated_iccs_move() -> None:
    move = parse_iccs_move("h2-e2")

    assert move_to_iccs(move) == "h2e2"


def test_invalid_iccs_move_raises_value_error() -> None:
    with pytest.raises(ValueError):
        parse_iccs_move("z9e2")


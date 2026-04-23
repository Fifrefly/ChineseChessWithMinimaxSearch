"""Unit tests for pseudo-legal move generation by piece category."""

from __future__ import annotations

import pytest

from chinese_chess.board import Board
from chinese_chess.constants import (
    ADVISER,
    BLACK,
    CANNON,
    CAPTURE_MOVE_FLAG,
    KING,
    KNIGHT,
    PAWN,
    RED,
    ROOK,
    BISHOP,
)
from chinese_chess.game import Game
from chinese_chess.movegen.pseudo_legal import (
    generate_advisor_moves,
    generate_cannon_moves,
    generate_elephant_moves,
    generate_horse_moves,
    generate_king_moves,
    generate_pawn_moves,
    generate_piece_moves,
    generate_pseudo_legal_moves,
    generate_rook_moves,
)
from chinese_chess.types import Move, Piece, Position

MINIMAL_FEN = "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"


def iccs(moves: list[Move]) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_king_moves_stay_inside_palace() -> None:
    board = Board(MINIMAL_FEN)
    king = board.get_piece("e0")
    assert king == Piece(KING, RED)

    moves = generate_king_moves(board, Position.from_algebraic("e0"), king)

    assert iccs(moves) == {"e0e1", "e0d0", "e0f0"}


def test_advisor_moves_stay_inside_palace() -> None:
    board = Board(MINIMAL_FEN)
    advisor = Piece(ADVISER, RED)
    board.set_piece("e0", advisor)

    moves = generate_advisor_moves(board, Position.from_algebraic("e0"), advisor)

    assert iccs(moves) == {"e0d1", "e0f1"}


def test_elephant_moves_respect_river_and_empty_eye() -> None:
    board = Board(MINIMAL_FEN)
    elephant = Piece(BISHOP, RED)
    board.set_piece("e2", elephant)

    moves = generate_elephant_moves(board, Position.from_algebraic("e2"), elephant)

    assert iccs(moves) == {"e2c4", "e2g4", "e2c0", "e2g0"}


def test_horse_moves_include_all_unblocked_destinations() -> None:
    board = Board(MINIMAL_FEN)
    horse = Piece(KNIGHT, RED)
    board.set_piece("e4", horse)

    moves = generate_horse_moves(board, Position.from_algebraic("e4"), horse)

    assert iccs(moves) == {"e4d6", "e4f6", "e4d2", "e4f2", "e4c5", "e4c3", "e4g5", "e4g3"}


def test_rook_slides_until_blocked_or_capture() -> None:
    board = Board(MINIMAL_FEN)
    rook = Piece(ROOK, RED)
    board.set_piece("e4", rook)
    board.set_piece("e6", Piece(PAWN, BLACK))
    board.set_piece("e2", Piece(PAWN, RED))

    moves = generate_rook_moves(board, Position.from_algebraic("e4"), rook)
    move_text = iccs(moves)

    assert "e4e5" in move_text
    assert "e4e6" in move_text
    assert "e4e7" not in move_text
    assert "e4e3" in move_text
    assert "e4e2" not in move_text


def test_cannon_moves_and_captures_after_one_screen() -> None:
    board = Board(MINIMAL_FEN)
    cannon = Piece(CANNON, RED)
    board.set_piece("e4", cannon)
    board.set_piece("e5", Piece(PAWN, RED))
    board.set_piece("e7", Piece(PAWN, BLACK))

    moves = generate_cannon_moves(board, Position.from_algebraic("e4"), cannon)
    move_text = iccs(moves)
    capture = next(move for move in moves if move.to_iccs() == "e4e7")

    assert "e4e5" not in move_text
    assert "e4e6" not in move_text
    assert "e4e7" in move_text
    assert capture.captured == Piece(PAWN, BLACK)
    assert capture.flags == CAPTURE_MOVE_FLAG


def test_pawn_moves_change_after_crossing_river() -> None:
    board = Board(MINIMAL_FEN)
    pawn = Piece(PAWN, RED)

    assert iccs(generate_pawn_moves(board, Position.from_algebraic("e3"), pawn)) == {"e3e4"}
    assert iccs(generate_pawn_moves(board, Position.from_algebraic("e5"), pawn)) == {"e5e6", "e5d5", "e5f5"}


def test_generate_piece_moves_dispatches_by_type() -> None:
    board = Board(MINIMAL_FEN)
    rook = Piece(ROOK, RED)
    board.set_piece("a4", rook)

    assert generate_piece_moves(board, Position.from_algebraic("a4"), rook)


def test_generate_pseudo_legal_moves_uses_requested_side() -> None:
    board = Board(MINIMAL_FEN)
    board.set_piece("a4", Piece(ROOK, RED))
    board.set_piece("i5", Piece(ROOK, BLACK))

    red_moves = iccs(generate_pseudo_legal_moves(board, RED))
    black_moves = iccs(generate_pseudo_legal_moves(board, BLACK))

    assert any(move.startswith("a4") for move in red_moves)
    assert any(move.startswith("i5") for move in black_moves)
    assert not any(move.startswith("i5") for move in red_moves)


def test_game_exposes_pseudo_legal_moves_but_not_legal_filtering() -> None:
    game = Game(MINIMAL_FEN)

    assert game.get_pseudo_legal_moves()
    assert game.get_legal_moves()

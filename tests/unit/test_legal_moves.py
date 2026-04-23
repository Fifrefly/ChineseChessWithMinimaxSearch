"""Unit tests for legal move filtering and reversible board moves."""

from __future__ import annotations

from chinese_chess.board import Board
from chinese_chess.constants import BLACK, RED
from chinese_chess.game import Game
from chinese_chess.movegen.legal import generate_legal_moves


def iccs(moves: list) -> set[str]:
    return {move.to_iccs() for move in moves}


def test_default_position_has_same_pseudo_and_legal_moves() -> None:
    game = Game()

    assert iccs(game.get_legal_moves()) == iccs(game.get_pseudo_legal_moves())


def test_legal_filter_rejects_move_that_exposes_rook_check() -> None:
    board = Board("3kr4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1")

    moves = iccs(generate_legal_moves(board, RED))

    assert "e1d1" not in moves
    assert "e1e2" in moves
    assert board.fen() == "3kr4/9/9/9/9/9/9/9/4R4/4K4 r - - 0 1"


def test_make_move_and_undo_move_restore_fen() -> None:
    game = Game()
    original = game.fen()

    applied = game.make_move("a0a1")
    assert applied.to_iccs() == "a0a1"
    assert game.turn == BLACK

    undone = game.undo_move()
    assert undone is not None
    assert undone.to_iccs() == "a0a1"
    assert game.fen() == original
    assert game.turn == RED


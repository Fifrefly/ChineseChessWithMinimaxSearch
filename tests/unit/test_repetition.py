"""Unit tests for simplified xiangqi.js-style repetition detection."""

from __future__ import annotations

from chinese_chess.game import Game
from chinese_chess.rules.repetition import is_threefold_repetition, position_key

REPEAT_SEQUENCE = ["a0a1", "a9a8", "a1a0", "a8a9", "a0a1", "a9a8", "a1a0", "a8a9"]


def test_position_key_includes_side_to_move_but_ignores_counters() -> None:
    game = Game()
    key = position_key(game.board_obj)

    assert key.endswith(" r")
    assert len(key.split()) == 2


def test_threefold_repetition_after_repeating_default_rook_cycle() -> None:
    game = Game()
    for move in REPEAT_SEQUENCE:
        game.make_move(move)

    assert game.is_threefold_repetition() is True
    assert is_threefold_repetition(game.board_obj) is True
    assert game.game_over() is True


def test_repetition_check_restores_board_and_history() -> None:
    game = Game()
    for move in REPEAT_SEQUENCE:
        game.make_move(move)
    fen_before = game.fen()
    history_before = game.board_obj.history_length

    assert game.is_threefold_repetition() is True

    assert game.fen() == fen_before
    assert game.board_obj.history_length == history_before
    for _ in REPEAT_SEQUENCE:
        game.undo_move()
    assert game.fen() == Game().fen()


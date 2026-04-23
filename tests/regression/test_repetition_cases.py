"""Regression tests for simplified repetition behavior."""

from __future__ import annotations

from chinese_chess.game import Game

REPEAT_SEQUENCE = ["a0a1", "a9a8", "a1a0", "a8a9", "a0a1", "a9a8", "a1a0", "a8a9"]


def test_repetition_uses_piece_placement_and_side_to_move() -> None:
    game = Game()
    for move in REPEAT_SEQUENCE[:-1]:
        game.make_move(move)

    assert game.is_threefold_repetition() is False

    game.make_move(REPEAT_SEQUENCE[-1])
    assert game.is_threefold_repetition() is True


def test_undo_after_repetition_removes_current_repeated_position() -> None:
    game = Game()
    for move in REPEAT_SEQUENCE:
        game.make_move(move)

    assert game.is_threefold_repetition() is True
    game.undo_move()
    assert game.is_threefold_repetition() is False


"""Smoke tests for the initial project skeleton."""

from __future__ import annotations


def test_core_package_imports() -> None:
    """The package should be importable before rule migration starts."""
    import chinese_chess

    assert "Game" in chinese_chess.__all__


def test_game_class_imports() -> None:
    """The future search-facing facade should be importable."""
    from chinese_chess.game import Game

    assert Game.__name__ == "Game"


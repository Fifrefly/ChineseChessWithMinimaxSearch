"""Unit tests for the fixed-depth minimax baseline."""

from __future__ import annotations

from chinese_chess.game import Game
from eval.combined import evaluate
from search.minimax import MATE_SCORE, SearchResult, SearchStats, search_best_move

CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
ONLY_EVASION_FEN = "3kr4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"
CAPTURE_ROOK_FEN = "r3k4/9/9/9/9/9/9/9/4A4/R3K4 r - - 0 1"


def test_search_result_dataclasses_are_clear_values() -> None:
    stats = SearchStats(nodes_visited=1, leaf_nodes=1, elapsed_seconds=0.0, depth=0)
    result = SearchResult(best_move=None, best_score=0, stats=stats)

    assert result.stats.depth == 0
    assert result.best_move is None


def test_depth_zero_search_evaluates_without_best_move() -> None:
    game = Game()

    result = search_best_move(game, 0, evaluate)

    assert result.best_move is None
    assert result.best_score == 0
    assert result.stats.nodes_visited == 1
    assert result.stats.leaf_nodes == 1


def test_terminal_position_does_not_expand_children() -> None:
    game = Game(CHECKMATE_FEN)

    result = search_best_move(game, 3, evaluate)

    assert result.best_move is None
    assert result.best_score <= -MATE_SCORE + 1
    assert result.stats.nodes_visited == 1
    assert result.stats.leaf_nodes == 1


def test_search_selects_only_legal_check_evasion() -> None:
    game = Game(ONLY_EVASION_FEN)

    result = search_best_move(game, 1, evaluate)

    assert result.best_move is not None
    assert result.best_move.to_iccs() == "e0f0"


def test_depth_one_prefers_obvious_high_value_capture() -> None:
    game = Game(CAPTURE_ROOK_FEN)

    result = search_best_move(game, 1, evaluate)

    assert result.best_move is not None
    assert result.best_move.to_iccs() == "a0a9"
    assert result.best_score > 0


def test_search_restores_original_position() -> None:
    game = Game(CAPTURE_ROOK_FEN)
    original = game.fen()

    search_best_move(game, 2, evaluate)

    assert game.fen() == original
    assert game.board_obj.history_length == 0


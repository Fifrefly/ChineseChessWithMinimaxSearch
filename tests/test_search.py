"""Tests for material evaluation and minimax search."""

from __future__ import annotations

from engine.core import BLACK, RED, ROOK, Board
from engine.evaluation import PIECE_VALUES, evaluate, evaluate_material
from engine.search import MATE_SCORE, SearchResult, SearchStats, minimax_search

CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"
ONLY_EVASION_FEN = "3kr4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"
CAPTURE_ROOK_FEN = "r3k4/9/9/9/9/9/9/9/4A4/R3K4 r - - 0 1"


def test_material_evaluation_balance_and_extra_piece() -> None:
    assert evaluate_material(Board(), RED) == 0
    assert evaluate_material(Board(), BLACK) == 0

    board = Board("4k4/9/9/9/9/9/9/9/9/R3K4 r - - 0 1")
    assert evaluate_material(board, RED) == PIECE_VALUES[ROOK]
    assert evaluate_material(board, BLACK) == -PIECE_VALUES[ROOK]


def test_search_result_values_are_simple_dataclasses() -> None:
    stats = SearchStats(nodes_visited=1, leaf_nodes=1, elapsed_seconds=0.0, depth=0)
    result = SearchResult(best_move=None, best_score=0, stats=stats)

    assert result.stats.depth == 0
    assert result.best_move is None


def test_terminal_positions_do_not_expand_children() -> None:
    mate = minimax_search(Board(CHECKMATE_FEN), depth=3, evaluator=evaluate)
    stale = minimax_search(Board(STALEMATE_FEN), depth=3, evaluator=evaluate)

    assert mate.best_move is None
    assert mate.best_score == -MATE_SCORE
    assert mate.stats.nodes_visited == 1
    assert stale.best_move is None
    assert stale.best_score == 0


def test_minimax_finds_only_check_evasion() -> None:
    result = minimax_search(Board(ONLY_EVASION_FEN), depth=1)

    assert result.best_move is not None
    assert result.best_move.to_iccs() == "e0f0"


def test_minimax_prefers_obvious_capture_at_depth_one() -> None:
    result = minimax_search(Board(CAPTURE_ROOK_FEN), depth=1)

    assert result.best_move is not None
    assert result.best_move.to_iccs() == "a0a9"
    assert result.best_score > 0


def test_minimax_does_not_pollute_board_state() -> None:
    board = Board(CAPTURE_ROOK_FEN)
    original = board.fen()

    minimax_search(board, depth=2)

    assert board.fen() == original
    assert board.history_length == 0

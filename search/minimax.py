"""Fixed-depth minimax baseline without pruning or move ordering."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

from chinese_chess.constants import BLACK, RED
from chinese_chess.game import Game
from chinese_chess.types import Move
from eval.combined import evaluate

Evaluator = Callable[[Game, str], int]

MATE_SCORE = 1_000_000


@dataclass(frozen=True, slots=True)
class SearchStats:
    """Basic search statistics for experiments and benchmarks."""

    nodes_visited: int
    leaf_nodes: int
    elapsed_seconds: float
    depth: int


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Best move, score, and statistics from a search call."""

    best_move: Move | None
    best_score: int
    stats: SearchStats


@dataclass(slots=True)
class _MutableStats:
    nodes_visited: int = 0
    leaf_nodes: int = 0


def search_best_move(
    game: Game,
    depth: int,
    evaluator: Evaluator = evaluate,
    maximizing_color: str | None = None,
) -> SearchResult:
    """Search the best move for the current position using minimax.

    Scores are returned from ``maximizing_color``'s perspective. If omitted,
    the side to move at the root is the maximizing side.
    """
    if depth < 0:
        raise ValueError("depth must be non-negative.")

    root_color = game.turn if maximizing_color is None else maximizing_color
    stats = _MutableStats()
    start = perf_counter()
    original_fen = game.fen()

    try:
        if depth == 0 or game.game_over():
            stats.nodes_visited += 1
            score = _score_position(game, depth, root_color, evaluator, stats, ply=0)
            return SearchResult(
                best_move=None,
                best_score=score,
                stats=SearchStats(
                    stats.nodes_visited, stats.leaf_nodes, perf_counter() - start, depth
                ),
            )

        legal_moves = game.get_legal_moves()
        if not legal_moves:
            stats.nodes_visited += 1
            score = _score_position(game, depth, root_color, evaluator, stats, ply=0)
            return SearchResult(
                best_move=None,
                best_score=score,
                stats=SearchStats(
                    stats.nodes_visited, stats.leaf_nodes, perf_counter() - start, depth
                ),
            )

        root_is_maximizing = game.turn == root_color
        best_move: Move | None = None
        best_score = -MATE_SCORE * 2 if root_is_maximizing else MATE_SCORE * 2

        # Count the root node once; child nodes are counted in _minimax.
        stats.nodes_visited += 1
        for move in legal_moves:
            game.make_move(move)
            try:
                score = _minimax(game, depth - 1, root_color, evaluator, stats, ply=1)
            finally:
                game.undo_move()

            if root_is_maximizing:
                if score > best_score:
                    best_score = score
                    best_move = move
            elif score < best_score:
                best_score = score
                best_move = move

        return SearchResult(
            best_move=best_move,
            best_score=best_score,
            stats=SearchStats(
                stats.nodes_visited, stats.leaf_nodes, perf_counter() - start, depth
            ),
        )
    finally:
        if game.fen() != original_fen:
            raise RuntimeError(
                "Minimax search did not restore the original game state."
            )


def _minimax(
    game: Game,
    depth: int,
    maximizing_color: str,
    evaluator: Evaluator,
    stats: _MutableStats,
    ply: int,
) -> int:
    stats.nodes_visited += 1
    if depth == 0 or game.game_over():
        return _score_position(game, depth, maximizing_color, evaluator, stats, ply)

    legal_moves = game.get_legal_moves()
    if not legal_moves:
        return _score_position(game, depth, maximizing_color, evaluator, stats, ply)

    if game.turn == maximizing_color:
        best_score = -MATE_SCORE * 2
        for move in legal_moves:
            game.make_move(move)
            try:
                best_score = max(
                    best_score,
                    _minimax(
                        game, depth - 1, maximizing_color, evaluator, stats, ply + 1
                    ),
                )
            finally:
                game.undo_move()
        return best_score

    best_score = MATE_SCORE * 2
    for move in legal_moves:
        game.make_move(move)
        try:
            best_score = min(
                best_score,
                _minimax(game, depth - 1, maximizing_color, evaluator, stats, ply + 1),
            )
        finally:
            game.undo_move()
    return best_score


def _score_position(
    game: Game,
    depth: int,
    maximizing_color: str,
    evaluator: Evaluator,
    stats: _MutableStats,
    ply: int,
) -> int:
    """Return evaluator or terminal score from maximizing side's perspective."""
    _ = depth
    stats.leaf_nodes += 1

    if game.is_checkmate(game.turn):
        return -MATE_SCORE + ply if game.turn == maximizing_color else MATE_SCORE - ply
    if game.is_stalemate(game.turn) or game.is_threefold_repetition():
        return 0

    return evaluator(game, maximizing_color)


def opponent(color: str) -> str:
    """Return the opposite side color."""
    return BLACK if color == RED else RED

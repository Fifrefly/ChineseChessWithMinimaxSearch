"""Search algorithms for the compact Xiangqi engine.

The plain fixed-depth minimax implementation is kept as an unpruned baseline.
Alpha-beta pruning uses the same scoring path so experiment results remain
comparable. A light ``move_orderer`` hook is included for ordering experiments.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from time import perf_counter

from engine.core import BLACK, RED, Board, Move, opponent
from engine.evaluation import evaluate
from engine.rules import (
    game_over,
    generate_legal_moves,
    is_checkmate,
    is_stalemate,
    is_threefold_repetition,
)

Evaluator = Callable[[Board, str], int]
MoveOrderer = Callable[[Board, list[Move]], Iterable[Move]]
MATE_SCORE = 1_000_000


@dataclass(frozen=True, slots=True)
class SearchStats:
    """Basic search statistics."""

    nodes_visited: int
    leaf_nodes: int
    elapsed_seconds: float
    depth: int
    cutoffs: int = 0


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Best move, score, and statistics."""

    best_move: Move | None
    best_score: int
    stats: SearchStats


@dataclass(slots=True)
class _Counter:
    nodes_visited: int = 0
    leaf_nodes: int = 0
    cutoffs: int = 0


def minimax_search(
    board: Board,
    depth: int,
    evaluator: Evaluator = evaluate,
    maximizing_color: str | None = None,
    move_orderer: MoveOrderer | None = None,
) -> SearchResult:
    """Search for the best move from the current board.

    Scores are from ``maximizing_color``'s perspective; by default that is the
    side to move at the root.
    """
    if depth < 0:
        raise ValueError("depth must be non-negative.")

    root_color = board.side_to_move if maximizing_color is None else maximizing_color
    original_fen = board.fen()
    counter = _Counter()
    start = perf_counter()

    try:
        if depth == 0 or game_over(board):
            counter.nodes_visited += 1
            score = _score_position(board, root_color, evaluator, counter, ply=0)
            return _result(None, score, counter, start, depth)

        moves = generate_legal_moves(board)
        if not moves:
            counter.nodes_visited += 1
            score = _score_position(board, root_color, evaluator, counter, ply=0)
            return _result(None, score, counter, start, depth)

        counter.nodes_visited += 1  # root node
        ordered_moves = list(move_orderer(board, moves)) if move_orderer else moves
        root_is_max = board.side_to_move == root_color
        best_move: Move | None = None
        best_score = -MATE_SCORE * 2 if root_is_max else MATE_SCORE * 2

        for move in ordered_moves:
            board.make_move(move)
            try:
                score = _minimax(
                    board,
                    depth - 1,
                    root_color,
                    evaluator,
                    move_orderer,
                    counter,
                    ply=1,
                )
            finally:
                board.undo_move()
            if root_is_max and score > best_score:
                best_move, best_score = move, score
            elif not root_is_max and score < best_score:
                best_move, best_score = move, score

        return _result(best_move, best_score, counter, start, depth)
    finally:
        if board.fen() != original_fen:
            raise RuntimeError(
                "minimax_search did not restore the original board state."
            )


def alpha_beta_search(
    board: Board,
    depth: int,
    evaluator: Evaluator = evaluate,
    maximizing_color: str | None = None,
    move_orderer: MoveOrderer | None = None,
) -> SearchResult:
    """Search for the best move using alpha-beta pruning.

    Scores are from ``maximizing_color``'s perspective; by default that is the
    side to move at the root. The terminal and leaf scoring semantics match
    ``minimax_search`` exactly.
    """
    if depth < 0:
        raise ValueError("depth must be non-negative.")

    root_color = board.side_to_move if maximizing_color is None else maximizing_color
    original_fen = board.fen()
    counter = _Counter()
    start = perf_counter()

    try:
        if depth == 0 or game_over(board):
            counter.nodes_visited += 1
            score = _score_position(board, root_color, evaluator, counter, ply=0)
            return _result(None, score, counter, start, depth)

        moves = generate_legal_moves(board)
        if not moves:
            counter.nodes_visited += 1
            score = _score_position(board, root_color, evaluator, counter, ply=0)
            return _result(None, score, counter, start, depth)

        counter.nodes_visited += 1  # root node
        ordered_moves = list(move_orderer(board, moves)) if move_orderer else moves
        root_is_max = board.side_to_move == root_color
        alpha = -MATE_SCORE * 2
        beta = MATE_SCORE * 2
        best_move: Move | None = None
        best_score = alpha if root_is_max else beta

        for move in ordered_moves:
            board.make_move(move)
            try:
                score = _alpha_beta(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    root_color,
                    evaluator,
                    move_orderer,
                    counter,
                    ply=1,
                )
            finally:
                board.undo_move()

            if root_is_max:
                if score > best_score:
                    best_move, best_score = move, score
                alpha = max(alpha, best_score)
                if best_score >= beta:
                    counter.cutoffs += 1
                    break
            else:
                if score < best_score:
                    best_move, best_score = move, score
                beta = min(beta, best_score)
                if best_score <= alpha:
                    counter.cutoffs += 1
                    break

        return _result(best_move, best_score, counter, start, depth)
    finally:
        if board.fen() != original_fen:
            raise RuntimeError(
                "alpha_beta_search did not restore the original board state."
            )


def _minimax(
    board: Board,
    depth: int,
    maximizing_color: str,
    evaluator: Evaluator,
    move_orderer: MoveOrderer | None,
    counter: _Counter,
    ply: int,
) -> int:
    counter.nodes_visited += 1
    if depth == 0 or game_over(board):
        return _score_position(board, maximizing_color, evaluator, counter, ply)

    moves = generate_legal_moves(board)
    if not moves:
        return _score_position(board, maximizing_color, evaluator, counter, ply)

    ordered_moves = list(move_orderer(board, moves)) if move_orderer else moves
    if board.side_to_move == maximizing_color:
        best = -MATE_SCORE * 2
        for move in ordered_moves:
            board.make_move(move)
            try:
                best = max(
                    best,
                    _minimax(
                        board,
                        depth - 1,
                        maximizing_color,
                        evaluator,
                        move_orderer,
                        counter,
                        ply + 1,
                    ),
                )
            finally:
                board.undo_move()
        return best

    best = MATE_SCORE * 2
    for move in ordered_moves:
        board.make_move(move)
        try:
            best = min(
                best,
                _minimax(
                    board,
                    depth - 1,
                    maximizing_color,
                    evaluator,
                    move_orderer,
                    counter,
                    ply + 1,
                ),
            )
        finally:
            board.undo_move()
    return best


def _alpha_beta(
    board: Board,
    depth: int,
    alpha: int,
    beta: int,
    maximizing_color: str,
    evaluator: Evaluator,
    move_orderer: MoveOrderer | None,
    counter: _Counter,
    ply: int,
) -> int:
    counter.nodes_visited += 1
    if depth == 0 or game_over(board):
        return _score_position(board, maximizing_color, evaluator, counter, ply)

    moves = generate_legal_moves(board)
    if not moves:
        return _score_position(board, maximizing_color, evaluator, counter, ply)

    ordered_moves = list(move_orderer(board, moves)) if move_orderer else moves
    if board.side_to_move == maximizing_color:
        value = -MATE_SCORE * 2
        for move in ordered_moves:
            board.make_move(move)
            try:
                child_score = _alpha_beta(
                    board,
                    depth - 1,
                    alpha,
                    beta,
                    maximizing_color,
                    evaluator,
                    move_orderer,
                    counter,
                    ply + 1,
                )
            finally:
                board.undo_move()
            value = max(value, child_score)
            if value >= beta:
                counter.cutoffs += 1
                return value
            alpha = max(alpha, value)
        return value

    value = MATE_SCORE * 2
    for move in ordered_moves:
        board.make_move(move)
        try:
            child_score = _alpha_beta(
                board,
                depth - 1,
                alpha,
                beta,
                maximizing_color,
                evaluator,
                move_orderer,
                counter,
                ply + 1,
            )
        finally:
            board.undo_move()
        value = min(value, child_score)
        if value <= alpha:
            counter.cutoffs += 1
            return value
        beta = min(beta, value)
    return value


def _score_position(
    board: Board,
    maximizing_color: str,
    evaluator: Evaluator,
    counter: _Counter,
    ply: int,
) -> int:
    """Return terminal score or evaluator score from maximizing side's view."""
    counter.leaf_nodes += 1
    if is_checkmate(board):
        return (
            -MATE_SCORE + ply
            if board.side_to_move == maximizing_color
            else MATE_SCORE - ply
        )
    if is_stalemate(board) or is_threefold_repetition(board):
        return 0
    return evaluator(board, maximizing_color)


def _result(
    best_move: Move | None, score: int, counter: _Counter, start: float, depth: int
) -> SearchResult:
    return SearchResult(
        best_move,
        score,
        SearchStats(
            counter.nodes_visited,
            counter.leaf_nodes,
            perf_counter() - start,
            depth,
            counter.cutoffs,
        ),
    )


def other_side(color: str) -> str:
    """Small public helper for experiments."""
    return opponent(color)

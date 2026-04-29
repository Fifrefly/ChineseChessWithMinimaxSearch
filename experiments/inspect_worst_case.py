"""Inspect one benchmark worst-case position and candidate moves."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.core import BLACK, RED, Board, Move
from engine.rules import generate_legal_moves, is_check, is_checkmate
from engine.search import alpha_beta_search
from experiments.evaluator_registry import get_evaluator


def _perspective(value: str) -> str:
    normalized = value.upper()
    if normalized in ("RED", "R"):
        return RED
    if normalized in ("BLACK", "B"):
        return BLACK
    raise ValueError("perspective must be RED or BLACK.")


def _board_to_ascii(board: Board) -> str:
    lines = ["    a b c d e f g h i"]
    for row_index, row in enumerate(board.to_matrix()):
        cells = [piece.to_fen_symbol() if piece is not None else "." for piece in row]
        lines.append(f"{row_index:>2}  " + " ".join(cells))
    return "\n".join(lines)


def _find_legal_move(board: Board, move_text: str) -> Move:
    for move in generate_legal_moves(board):
        if move.to_iccs() == move_text:
            return move
    raise ValueError(f"Move {move_text!r} is not legal in the given position.")


def _score_position(
    board: Board,
    oracle_evaluator,
    oracle_depth: int,
    perspective: str,
) -> int:
    result = alpha_beta_search(
        board,
        depth=oracle_depth,
        evaluator=oracle_evaluator,
        maximizing_color=perspective,
    )
    return result.best_score


def _inspect_successor(
    board: Board,
    label: str,
    move: Move,
    oracle_evaluator,
    oracle_depth: int,
    perspective: str,
) -> tuple[list[str], int]:
    original_fen = board.fen()
    applied = board.make_move(move)
    try:
        score = _score_position(
            board,
            oracle_evaluator,
            max(0, oracle_depth - 1),
            perspective,
        )
        lines = [
            f"{label}: {applied.to_iccs()}",
            f"successor FEN: {board.fen()}",
            f"is check: {is_check(board)}",
            f"is checkmate: {is_checkmate(board)}",
            f"oracle continuation score: {score}",
            _board_to_ascii(board),
        ]
        return lines, score
    finally:
        board.undo_move()
        if board.fen() != original_fen:
            raise RuntimeError("inspect_worst_case modified board state.")


def inspect_worst_case(
    fen: str,
    best_move: str,
    oracle_best_move: str,
    oracle_evaluator_name: str = "full_static",
    oracle_depth: int = 3,
    mlp_model: str | None = None,
    perspective: str = RED,
) -> str:
    board = Board(fen)
    original_fen = board.fen()
    oracle_evaluator = get_evaluator(oracle_evaluator_name, mlp_model)
    candidate = _find_legal_move(board, best_move)
    oracle_move = _find_legal_move(board, oracle_best_move)
    original_score = _score_position(
        board,
        oracle_evaluator,
        oracle_depth,
        perspective,
    )

    lines = [
        f"Original FEN: {original_fen}",
        f"side_to_move: {board.side_to_move}",
        "Original board:",
        _board_to_ascii(board),
        f"best_move: {best_move}",
        f"oracle_best_move: {oracle_best_move}",
        f"original oracle score: {original_score}",
        "",
    ]
    best_lines, best_score = _inspect_successor(
        board,
        "Tested best_move",
        candidate,
        oracle_evaluator,
        oracle_depth,
        perspective,
    )
    oracle_lines, oracle_score = _inspect_successor(
        board,
        "Oracle best_move",
        oracle_move,
        oracle_evaluator,
        oracle_depth,
        perspective,
    )
    lines.extend(best_lines)
    lines.append("")
    lines.extend(oracle_lines)
    lines.extend(
        [
            "",
            f"successor score difference best_minus_oracle: {best_score - oracle_score}",
        ]
    )
    if board.fen() != original_fen:
        raise RuntimeError("inspect_worst_case modified board state.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", required=True)
    parser.add_argument("--best-move", required=True)
    parser.add_argument("--oracle-best-move", required=True)
    parser.add_argument("--oracle-evaluator", default="full_static")
    parser.add_argument("--oracle-depth", type=int, default=3)
    parser.add_argument("--mlp-model")
    parser.add_argument("--perspective", default="RED", choices=("RED", "BLACK"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        inspect_worst_case(
            fen=args.fen,
            best_move=args.best_move,
            oracle_best_move=args.oracle_best_move,
            oracle_evaluator_name=args.oracle_evaluator,
            oracle_depth=args.oracle_depth,
            mlp_model=args.mlp_model,
            perspective=_perspective(args.perspective),
        )
    )


if __name__ == "__main__":
    main()

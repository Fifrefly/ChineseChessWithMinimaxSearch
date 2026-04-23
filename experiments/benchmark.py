"""Minimal benchmark entry point for fixed-depth minimax."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chinese_chess.constants import DEFAULT_FEN  # noqa: E402
from chinese_chess.game import Game  # noqa: E402
from eval.combined import evaluate  # noqa: E402
from search.minimax import search_best_move  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Run a minimax benchmark for one position."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", default=DEFAULT_FEN, help="FEN position to search.")
    parser.add_argument("--depth", type=int, default=1, help="Fixed minimax depth.")
    args = parser.parse_args(argv)

    game = Game(args.fen)
    result = search_best_move(game, args.depth, evaluate)
    print(f"best_move={result.best_move.to_iccs() if result.best_move else None}")
    print(f"score={result.best_score}")
    print(f"nodes={result.stats.nodes_visited}")
    print(f"leaf_nodes={result.stats.leaf_nodes}")
    print(f"elapsed_seconds={result.stats.elapsed_seconds:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

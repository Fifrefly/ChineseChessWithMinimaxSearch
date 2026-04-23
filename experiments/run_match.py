"""Minimal self-play driver using minimax and material evaluation."""

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
    """Run a short minimax self-play match."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fen", default=DEFAULT_FEN, help="Starting FEN.")
    parser.add_argument("--depth", type=int, default=1, help="Fixed minimax depth for both sides.")
    parser.add_argument("--max-plies", type=int, default=20, help="Maximum half-moves to play.")
    args = parser.parse_args(argv)

    game = Game(args.fen)
    for ply in range(1, args.max_plies + 1):
        if game.game_over():
            print(f"game_over before ply {ply}: fen={game.fen()}")
            break
        side = game.turn
        result = search_best_move(game, args.depth, evaluate, maximizing_color=side)
        if result.best_move is None:
            print(f"no move for {side}: score={result.best_score}")
            break
        game.make_move(result.best_move)
        print(
            f"ply={ply} side={side} move={result.best_move.to_iccs()} "
            f"score={result.best_score} nodes={result.stats.nodes_visited} "
            f"time={result.stats.elapsed_seconds:.6f}"
        )
    print(f"final_fen={game.fen()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

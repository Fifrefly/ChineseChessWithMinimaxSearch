# Minimal Xiangqi Engine

This repository is a compact, readable Python Xiangqi engine for adversarial
search coursework. The priority is being able to read and understand almost
all core code quickly, not building a large framework.

## Structure

- `engine/core.py`: board state, FEN parsing/serialization, ICCS moves, and
  reversible `make_move` / `undo_move`.
- `engine/rules.py`: pseudo-legal moves, attack detection, legal move filtering,
  check/checkmate/stalemate, simplified threefold repetition, and `game_over`.
- `engine/evaluation.py`: minimal material evaluation.
- `engine/search.py`: fixed-depth minimax baseline with basic search stats.
- `vendor/xiangqi.js`: JavaScript reference implementation used for parity
  checks and behavior guidance.

## Basic Usage

```python
from engine.core import Board
from engine.rules import generate_legal_moves, game_over
from engine.search import minimax_search

board = Board()
moves = generate_legal_moves(board)
result = minimax_search(board, depth=1)

if result.best_move is not None:
    board.make_move(result.best_move)

print(board.fen())
print(game_over(board))
```

`Board.make_move()` is intentionally low-level: it applies a board-consistent
move and records undo state. For user-facing move choice, first obtain moves
from `generate_legal_moves(board)`.

## Run Tests

```bash
conda activate chess
pytest
```

## Current Scope

Implemented:

- FEN load/export
- ICCS move parsing
- pseudo-legal and legal move generation
- self-check filtering, including flying-general exposure
- check, checkmate, stalemate, simplified threefold repetition, and game over
- material evaluation
- fixed-depth minimax baseline

Intentionally not implemented yet:

- alpha-beta pruning
- move ordering experiments
- transposition tables
- piece-square tables, mobility, or king-safety evaluation
- official complex Xiangqi repetition adjudication such as long-check/long-chase


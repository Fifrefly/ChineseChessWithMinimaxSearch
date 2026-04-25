# Minimal ChineseChess Engine

This repository is a compact, readable Python Xiangqi engine for adversarial
search coursework. The priority is being able to read and understand almost
all core code quickly, not building a large framework.

## Structure

- `engine/core.py`: board state, FEN parsing/serialization, ICCS moves, and
  reversible `make_move` / `undo_move`.
- `engine/rules.py`: pseudo-legal moves, attack detection, legal move filtering,
  check/checkmate/stalemate, simplified threefold repetition, and `game_over`.
- `engine/evaluation.py`: material baseline plus optional static evaluation
  layers for position, mobility, king safety, threats, and weighted features.
- `engine/search.py`: fixed-depth minimax baseline and alpha-beta search with
  basic search stats.
- `vendor/xiangqi.js`: JavaScript reference implementation used for parity
  checks and behavior guidance.

## Basic Usage

```python
from engine.core import Board
from engine.rules import generate_legal_moves, game_over
from engine.search import alpha_beta_search, minimax_search

board = Board()
moves = generate_legal_moves(board)
result = minimax_search(board, depth=1)
pruned = alpha_beta_search(board, depth=2)

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

## Evaluation Functions

`evaluate(board, perspective)` intentionally remains a pure material baseline
for experiments. Additional evaluators are available when you want richer
static scoring:

- `evaluate_material`
- `evaluate_piece_value_and_position`
- `evaluate_piece_value_position_and_mobility`
- `evaluate_piece_value_position_mobility_and_king_safety`
- `evaluate_piece_value_position_mobility_king_safety_and_threats`
- `extract_evaluation_features`
- `evaluate_weighted_static`

`extract_evaluation_features` returns the five red/black-relative components
`material`, `position`, `mobility`, `king_safety`, and `threats`.
`evaluate_weighted_static` combines those features with configurable manual
weights; unit weights match the full static evaluator with threats.

## Optional MLP Evaluator

The MLP evaluator is an optional experiment and is not used by default search
or `evaluate`. It uses six input features:

- `material`
- `position`
- `mobility`
- `king_safety`
- `threats`
- `side_to_move`

The `side_to_move` feature is encoded from the requested perspective: `1.0`
when the perspective side is to move, and `-1.0` when the opponent is to move.

Install the optional ML dependencies before running these tools:

```bash
conda activate chess
pip install -e ".[ml]"
```

If the shell cannot activate conda directly, run the same install through
`conda run`:

```bash
conda run -n chess python -m pip install -e ".[ml]"
```

Generate labeled positions:

```bash
python experiments/generate_mlp_training_data.py --output data/mlp_train.csv --positions 1000 --max-plies 80 --label-depth 2 --seed 0
```

Train a small PyTorch MLP:

```bash
python experiments/train_mlp_evaluator.py --input data/mlp_train.csv --output-model data/mlp_eval.pt --epochs 50 --batch-size 64 --learning-rate 0.001 --seed 0
```

Evaluate one FEN:

```bash
python experiments/evaluate_mlp_model.py --model data/mlp_eval.pt --fen "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"
```

Small conda smoke-test workflow:

```bash
conda run -n chess python experiments/generate_mlp_training_data.py --output data/mlp_train_smoke.csv --positions 50 --max-plies 30 --label-depth 1 --seed 0
conda run -n chess python experiments/train_mlp_evaluator.py --input data/mlp_train_smoke.csv --output-model data/mlp_eval_smoke.pt --epochs 5 --batch-size 8 --learning-rate 0.001 --seed 0
conda run -n chess python experiments/evaluate_mlp_model.py --model data/mlp_eval_smoke.pt --fen "4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1" --perspective RED
```

## Current Scope

Implemented:

- FEN load/export
- ICCS move parsing
- pseudo-legal and legal move generation
- self-check filtering, including flying-general exposure
- check, checkmate, stalemate, simplified threefold repetition, and game over
- material evaluation and optional richer static evaluators
- explainable evaluation feature extraction and manual weighted scoring
- fixed-depth minimax baseline
- alpha-beta pruning via `alpha_beta_search`
- optional `move_orderer` hook for alpha-beta node-ordering experiments
- optional PyTorch MLP training/inference scripts for evaluation experiments

Intentionally not implemented yet:

- move ordering experiments
- transposition tables
- official complex Xiangqi repetition adjudication such as long-check/long-chase
- complex tactical evaluation such as long combinations, pins, and specialized
  cannon-screen threat scoring


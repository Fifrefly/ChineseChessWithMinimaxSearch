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

## Experiment Pipeline

The evaluation pipeline separates four kinds of checks:

- static sanity tests: unit tests that verify evaluator invariants, feature
  decomposition, and board-state restoration.
- oracle benchmark: compare evaluator search scores against deeper labels from
  a chosen oracle evaluator.
- search decision benchmark: compare each evaluator's best move with the oracle
  best move, measure oracle regret, and record search efficiency.
- self-play tournament: let evaluators play both colors and summarize results,
  nodes, cutoffs, and time.

The benchmark reports oracle regret because different evaluators can use
different score scales. Directly comparing an evaluator's `search_score` to the
oracle score can be misleading: a score may look numerically close while the
chosen move is poor. Oracle regret instead applies the tested evaluator's move,
then uses the same oracle evaluator to score the continuation. Lower
`mean_abs_oracle_regret` is therefore the main decision-quality metric;
`mean_abs_score_error` is kept only as a supporting diagnostic.
The summary also reports `p90_abs_oracle_regret` and
`max_abs_oracle_regret`: p90 helps judge how stable an evaluator is in bad
cases, while max regret is a quick way to find catastrophic moves. The analyzer
can write a worst-case CSV for manual position review, which is useful for
checking where material, position, or MLP evaluators are making qualitatively
different mistakes.

Shallow self-play often reaches the move limit without a tactical result. Use
`--adjudicate-max-plies` to score the final position with an adjudicator
evaluator, typically `full_static`, and award RED/BLACK wins only when the score
exceeds the threshold. A threshold around `200` is a reasonable starting point.
This is an experimental adjudication rule, not an official Xiangqi result rule.
When reading tournament results, compare both total win rate and red/black
color splits, because first-move advantage can otherwise look like evaluator
strength.

Recommended end-to-end workflow:

```bash
conda run -n chess python experiments/generate_mlp_training_data.py --output data/mlp_train.csv --positions 5000 --max-plies 80 --label-depth 2 --seed 0

conda run -n chess python experiments/train_mlp_evaluator.py --input data/mlp_train.csv --output-model data/mlp_eval.pt --epochs 50 --batch-size 64 --learning-rate 0.001 --seed 0

conda run -n chess python experiments/generate_mlp_training_data.py --output data/eval_positions.csv --positions 500 --max-plies 80 --label-depth 1 --seed 999

conda run -n chess python experiments/evaluation_benchmark.py --positions data/eval_positions.csv --output data/evaluation_benchmark.csv --evaluators material,position,mobility,king_safety,full_static,weighted_static,mlp --search-depth 2 --oracle-depth 3 --oracle-evaluator full_static --mlp-model data/mlp_eval.pt --limit 200

conda run -n chess python experiments/self_play_tournament.py --output data/self_play_results.csv --evaluators material,full_static,weighted_static,mlp --games-per-pair 2 --depth 2 --max-plies 120 --mlp-model data/mlp_eval.pt --opening-random-plies 2 --adjudicate-max-plies --adjudicator-evaluator full_static --adjudication-threshold 200 --seed 42

conda run -n chess python experiments/analyze_benchmark.py --benchmark data/evaluation_benchmark.csv --self-play data/self_play_results.csv --output-report data/experiment_summary.md --output-summary-csv data/experiment_summary.csv --output-worst-cases data/worst_cases.csv --worst-cases-per-evaluator 3
```

Small smoke tests only verify that the full pipeline runs and that metrics are
being recorded. Strong conclusions need more positions, a deeper oracle, deeper
tested searches, and many more self-play games. Current stalemate handling and
repetition adjudication are simplified to match this study engine's `search.py`
semantics: stalemate and simplified threefold repetition are treated as draws.

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
- evaluator registry, oracle benchmark, self-play tournament, and benchmark
  summary scripts under `experiments/`

Intentionally not implemented yet:

- move ordering experiments
- transposition tables
- official complex Xiangqi repetition adjudication such as long-check/long-chase
- complex tactical evaluation such as long combinations, pins, and specialized
  cannon-screen threat scoring

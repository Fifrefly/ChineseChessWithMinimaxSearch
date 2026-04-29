# Medium Experiment Summary: Decision-Loss View

## Data Availability

This summary updates the interpretation of the preserved medium experiment outputs. The logs show that the original run wrote:

- `data/evaluation_benchmark_medium.csv`
- `data/self_play_results_medium.csv`
- `data/experiment_summary_medium.csv`
- `data/worst_cases_medium.csv`

Those CSV files are not present in the current working tree, so the full analyzer could not be rerun on the original medium benchmark rows. The table below is reconstructed from the preserved `data/experiment_summary_medium.md` using the legacy `abs_oracle_regret` values as the non-negative decision-loss proxy. The current `experiments/evaluation_benchmark.py` and `experiments/analyze_benchmark.py` now write and summarize `decision_loss` directly.

## Benchmark Settings

- benchmark positions: 500 non-terminal/terminal-patched medium positions, inferred from 3500 rows across 7 evaluators
- search_depth: 2
- oracle_depth: 3
- oracle_evaluator: `full_static`
- tested evaluators: `material`, `position`, `mobility`, `king_safety`, `full_static`, `weighted_static`, `mlp`
- primary metric for new analysis: `decision_loss`
- legacy compatibility metric: `mean_abs_oracle_regret`

## Evaluator Decision Quality vs Oracle

| evaluator | mean_decision_loss | p90_decision_loss | max_decision_loss | zero_decision_loss_rate | move_match_rate | mean_abs_oracle_regret | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 4085.3818 | 193.6000 | 997859.0000 | 0.5859 | 0.5840 | 4085.3818 | 1.5494 |
| king_safety | 4096.5293 | 266.6000 | 997859.0000 | 0.5717 | 0.5720 | 4096.5293 | 1.2323 |
| material | 2093.4263 | 266.6000 | 997802.0000 | 0.5212 | 0.5240 | 2093.4263 | 0.7789 |
| mlp | 327.1596 | 841.2000 | 2306.0000 | 0.2505 | 0.2620 | 327.1596 | 1.8061 |
| mobility | 4096.9455 | 266.0000 | 997859.0000 | 0.5677 | 0.5680 | 4096.9455 | 1.0082 |
| position | 2084.0586 | 242.4000 | 997802.0000 | 0.5515 | 0.5520 | 2084.0586 | 0.8988 |
| weighted_static | 2070.1313 | 193.6000 | 997802.0000 | 0.5838 | 0.5840 | 2070.1313 | 1.5608 |

## Supporting Score Accuracy vs Oracle

| evaluator | mean_abs_score_error | root_mean_squared_error | avg_nodes_visited |
| --- | ---: | ---: | ---: |
| full_static | 4304.6040 | 63426.3864 | 523.9860 |
| king_safety | 4317.9520 | 63426.4161 | 549.9920 |
| material | 4304.6500 | 44848.1223 | 468.7920 |
| mlp | 35486.7600 | 490.4471 | 589.6180 |
| mobility | 4308.5280 | 63426.4159 | 549.0640 |
| position | 4306.6520 | 44848.0765 | 544.5980 |
| weighted_static | 4307.0520 | 44848.0298 | 526.2420 |

## Self-Play Tournament

| evaluator | wins | losses | draws | adjudicated_wins | adjudicated_losses | adjudicated_draws | win_rate | avg_game_plies |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 94 | 11 | 15 | 6 | 2 | 1 | 0.7833 | 66.6917 |
| material | 37 | 75 | 8 | 30 | 4 | 0 | 0.3083 | 82.5000 |
| mlp | 4 | 115 | 1 | 0 | 29 | 0 | 0.0333 | 72.3000 |
| weighted_static | 84 | 18 | 18 | 4 | 5 | 1 | 0.7000 | 66.3917 |

## Self-Play Color Split

| evaluator | red_wins | red_losses | red_draws | red_win_rate | black_wins | black_losses | black_draws | black_win_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 49 | 5 | 6 | 0.8167 | 45 | 6 | 9 | 0.7500 |
| material | 18 | 34 | 8 | 0.3000 | 19 | 41 | 0 | 0.3167 |
| mlp | 1 | 59 | 0 | 0.0167 | 3 | 56 | 1 | 0.0500 |
| weighted_static | 46 | 7 | 7 | 0.7667 | 38 | 11 | 11 | 0.6333 |

## Metric Notes

- `decision_loss` is the preferred move-quality metric because it is always non-negative and is computed from the side-to-move perspective.
- `oracle_regret = oracle_score - candidate_oracle_score` changes sign depending on whether RED or BLACK is to move, because scores are stored from RED's perspective.
- `abs_oracle_regret` removes the sign, but it is a legacy compatibility metric. It is less explicit than `decision_loss` and can obscure whether a value came from a RED maximizing or BLACK minimizing position.
- `move_match_rate` measures exact agreement with the oracle best move. It is stricter than `decision_loss`, because multiple moves can be nearly equivalent under the oracle.
- Self-play win rate is a separate playing-strength test, not the same thing as offline oracle agreement.

## Initial Interpretation

- `full_static` and `weighted_static` are the most reliable practical evaluators in self-play: 78.33% and 70.00% win rate, respectively.
- `weighted_static` matches `full_static` on move agreement in the preserved medium benchmark, but it is weaker than `full_static` in actual play, especially as BLACK.
- The MLP has the lowest preserved average oracle-regret value, but this is not evidence that it is the strongest evaluator. Its move-match rate is only 26.20%, its p90 decision loss is worse than the static evaluators, and its self-play win rate is only 3.33%.
- Mate-scale worst cases around positions 472 and 233 dominate the mean for several static evaluators. These cases need manual inspection and deeper oracle checks before being treated as definitive evaluator rankings.

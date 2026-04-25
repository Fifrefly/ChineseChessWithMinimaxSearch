# Experiment Summary

## Benchmark Settings
- search_depth: 1
- oracle_depth: 2
- oracle_evaluator: full_static

## Evaluator Accuracy vs Oracle
| evaluator | mean_abs_oracle_regret | oracle_regret_rmse | zero_regret_rate | move_match_rate | mean_abs_score_error | avg_nodes | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 46.1400 | 105.9084 | 0.6000 | 0.6200 | 276.7600 | 38.6600 | 0.0761 |
| king_safety | 95.6600 | 176.6935 | 0.5000 | 0.5200 | 290.2600 | 38.6600 | 0.0570 |
| material | 20106.9800 | 141413.1686 | 0.5000 | 0.5200 | 272.6600 | 38.6600 | 0.0415 |
| mlp | 231.8600 | 416.1876 | 0.3600 | 0.3800 | 381.5200 | 38.6600 | 0.0784 |
| mobility | 73.8400 | 146.7625 | 0.5600 | 0.5800 | 282.8400 | 38.6600 | 0.0463 |
| position | 20088.9200 | 141413.1188 | 0.5000 | 0.5200 | 276.2200 | 38.6600 | 0.0416 |
| weighted_static | 45.2000 | 105.7525 | 0.6400 | 0.6600 | 277.3600 | 38.6600 | 0.0765 |

## Self-Play Tournament
| evaluator | wins | losses | draws | adjudicated_wins | adjudicated_losses | adjudicated_draws | win_rate | avg_game_plies |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 4 | 2 | 0 | 3 | 2 | 0 | 0.6667 | 39.8333 |
| material | 3 | 3 | 0 | 3 | 2 | 0 | 0.5000 | 35.1667 |
| mlp | 2 | 3 | 1 | 1 | 2 | 1 | 0.3333 | 35.0000 |
| weighted_static | 2 | 3 | 1 | 2 | 3 | 1 | 0.3333 | 40.0000 |

## Initial Interpretation
- weighted_static has the lowest mean_abs_oracle_regret in this run.
- weighted_static has the highest move_match_rate in this run.
- MLP mean_abs_oracle_regret is 185.7200 higher than full_static.
- MLP mean_abs_oracle_regret is 186.6600 higher than weighted_static.
- full_static has the highest self-play win_rate in this run.
- If the sample is small, treat this as a smoke test rather than a final playing-strength conclusion.

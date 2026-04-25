# Experiment Summary

## Benchmark Settings
- search_depth: 1
- oracle_depth: 2
- oracle_evaluator: full_static

## Evaluator Accuracy vs Oracle
| evaluator | mean_abs_score_error | rmse | move_match_rate | avg_nodes | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: |
| full_static | 322.3800 | 375.1971 | 0.6200 | 38.6000 | 0.0756 |
| king_safety | 330.5000 | 403.9087 | 0.5600 | 38.6000 | 0.0561 |
| material | 304.5400 | 382.4155 | 0.5800 | 38.6000 | 0.0404 |
| mlp | 413.2200 | 530.6062 | 0.3600 | 38.6000 | 0.0780 |
| mobility | 321.8400 | 395.9062 | 0.5400 | 38.6000 | 0.0453 |
| position | 310.6600 | 388.8635 | 0.4800 | 38.6000 | 0.0406 |
| weighted_static | 320.6600 | 376.3695 | 0.6200 | 38.6000 | 0.0760 |

## Self-Play Tournament
| evaluator | wins | losses | draws | win_rate | avg_game_plies |
| --- | ---: | ---: | ---: | ---: | ---: |
| full_static | 0 | 0 | 6 | 0.0000 | 40.0000 |
| material | 0 | 0 | 6 | 0.0000 | 40.0000 |
| mlp | 0 | 0 | 6 | 0.0000 | 40.0000 |
| weighted_static | 0 | 0 | 6 | 0.0000 | 40.0000 |

## Initial Interpretation
- material has the lowest mean_abs_score_error in this run.
- full_static, weighted_static have the highest move_match_rate in this run.
- MLP mean_abs_score_error is 90.8400 higher than full_static.
- MLP mean_abs_score_error is 92.5600 higher than weighted_static.
- full_static, material, mlp, weighted_static have the highest self-play win_rate in this run.
- If the sample is small, treat this as a smoke test rather than a final playing-strength conclusion.

# Experiment Summary

## Benchmark Settings
- search_depth: 1
- oracle_depth: 2
- oracle_evaluator: full_static

## Evaluator Accuracy vs Oracle
| evaluator | mean_abs_oracle_regret | p90_abs_oracle_regret | max_abs_oracle_regret | oracle_regret_rmse | zero_regret_rate | move_match_rate | mean_abs_score_error | avg_nodes | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 46.1400 | 134.9000 | 387.0000 | 105.9084 | 0.6000 | 0.6200 | 276.7600 | 38.6600 | 0.0761 |
| king_safety | 95.6600 | 360.0000 | 519.0000 | 176.6935 | 0.5000 | 0.5200 | 290.2600 | 38.6600 | 0.0570 |
| material | 20106.9800 | 417.0000 | 999941.0000 | 141413.1686 | 0.5000 | 0.5200 | 272.6600 | 38.6600 | 0.0415 |
| mlp | 231.8600 | 704.4000 | 1599.0000 | 416.1876 | 0.3600 | 0.3800 | 381.5200 | 38.6600 | 0.0784 |
| mobility | 73.8400 | 323.1000 | 415.0000 | 146.7625 | 0.5600 | 0.5800 | 282.8400 | 38.6600 | 0.0463 |
| position | 20088.9200 | 389.5000 | 999941.0000 | 141413.1188 | 0.5000 | 0.5200 | 276.2200 | 38.6600 | 0.0416 |
| weighted_static | 45.2000 | 134.9000 | 387.0000 | 105.7525 | 0.6400 | 0.6600 | 277.3600 | 38.6600 | 0.0765 |

## Worst Regret Cases
| evaluator | rank | position_id | oracle_regret | best_move | oracle_best_move | fen |
| --- | ---: | ---: | ---: | --- | --- | --- |
| full_static | 1 | 6 | 387 | e4e5 | a6a9 | 2b1kabn1/9/8r/C7p/p1r1p4/2B1P1p2/P1Pc2N1P/R2A2R1C/9/1N1AK1B2 r - - 10 31 |
| full_static | 2 | 5 | -352 | d5e3 | b7c7 | r1ba1abnr/4k3c/1c7/p3p4/3n2p1p/P6C1/R1P1P1P1P/2N1B4/9/2BAKA1NR b - - 5 13 |
| full_static | 3 | 27 | -324 | g7f5 | g7h9 | r1b1ka2r/1c7/2n2an2/p1p1p4/2bC3cp/9/P1P1P1P1P/3AB1C2/N8/2RK1ABNR b - - 26 25 |
| king_safety | 1 | 19 | -519 | d2d0 | i9i5 | 2bakacnr/9/n3b4/p1p1p1pc1/8P/C8/P1P1P1P2/3r5/8N/RNBAKABR1 b - - 3 14 |
| king_safety | 2 | 27 | -479 | b8b0 | g7h9 | r1b1ka2r/1c7/2n2an2/p1p1p4/2bC3cp/9/P1P1P1P1P/3AB1C2/N8/2RK1ABNR b - - 26 25 |
| king_safety | 3 | 48 | 415 | a2a5 | i1f1 | rnbaka1nr/9/6ccb/2p1p1p1p/p8/4P4/P1P3P1P/C8/1C2K3R/RNBA1ABN1 r - - 10 6 |
| material | 1 | 3 | 999941 | i5i6 | c2c6 | rnbaka1nr/9/8b/p1p1p3p/1c4p1P/4P4/P1c3P2/2C2C3/4A4/RNBAK1BNR r - - 2 10 |
| material | 2 | 11 | 770 | f4e2 | e1d3 | 2bakabnr/5r3/9/p3p4/2p3p2/4PN2p/P1P1c3P/5R1c1/4NC3/2BAKAB1R r - - 22 21 |
| material | 3 | 19 | -519 | d2d0 | i9i5 | 2bakacnr/9/n3b4/p1p1p1pc1/8P/C8/P1P1P1P2/3r5/8N/RNBAKABR1 b - - 3 14 |
| mlp | 1 | 0 | 1599 | g9f9 | g9i9 | r1bakaR1r/7C1/2n5b/pcC1pnp1p/3c5/9/P1P1P1P1P/9/4K4/1RB2ABN1 r - - 9 21 |
| mlp | 2 | 17 | -1223 | g0f0 | d7d6 | 2bk1ab2/5C3/3r5/3R5/2P1pNp1P/Rp7/3cc1P2/4B4/4A4/1NB1KAr2 b - - 4 29 |
| mlp | 3 | 18 | -884 | h7h1 | c5a7 | 6r2/4k4/C2a3c1/p1p1ncp2/2b1p3p/2P3P1P/P3P4/2R1BC3/4KR3/2NA1ABN1 b - - 20 21 |
| mobility | 1 | 48 | 415 | a2a5 | i1f1 | rnbaka1nr/9/6ccb/2p1p1p1p/p8/4P4/P1P3P1P/C8/1C2K3R/RNBA1ABN1 r - - 10 6 |
| mobility | 2 | 13 | 412 | c1c6 | b6g6 | 1n1aknb2/r3a4/3cb3r/pCp3pc1/4p3p/P5P2/2P1P3P/4B3N/1RC6/1NBAKA2R r - - 46 24 |
| mobility | 3 | 6 | 387 | e4e5 | a6a9 | 2b1kabn1/9/8r/C7p/p1r1p4/2B1P1p2/P1Pc2N1P/R2A2R1C/9/1N1AK1B2 r - - 10 31 |
| position | 1 | 3 | 999941 | i5i6 | c2c6 | rnbaka1nr/9/8b/p1p1p3p/1c4p1P/4P4/P1c3P2/2C2C3/4A4/RNBAK1BNR r - - 2 10 |
| position | 2 | 19 | -519 | d2d0 | i9i5 | 2bakacnr/9/n3b4/p1p1p1pc1/8P/C8/P1P1P1P2/3r5/8N/RNBAKABR1 b - - 3 14 |
| position | 3 | 30 | -435 | e7g5 | a3e3 | rn1a5/c3k4/3ab1n1b/prp1p2R1/6P1p/8P/c1P1P4/B3BNC2/4KN1R1/3A1A3 b - - 15 23 |
| weighted_static | 1 | 6 | 387 | e4e5 | a6a9 | 2b1kabn1/9/8r/C7p/p1r1p4/2B1P1p2/P1Pc2N1P/R2A2R1C/9/1N1AK1B2 r - - 10 31 |
| weighted_static | 2 | 5 | -352 | d5e3 | b7c7 | r1ba1abnr/4k3c/1c7/p3p4/3n2p1p/P6C1/R1P1P1P1P/2N1B4/9/2BAKA1NR b - - 5 13 |
| weighted_static | 3 | 27 | -324 | g7f5 | g7h9 | r1b1ka2r/1c7/2n2an2/p1p1p4/2bC3cp/9/P1P1P1P1P/3AB1C2/N8/2RK1ABNR b - - 26 25 |

## Self-Play Tournament
| evaluator | wins | losses | draws | adjudicated_wins | adjudicated_losses | adjudicated_draws | win_rate | avg_game_plies |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 4 | 2 | 0 | 3 | 2 | 0 | 0.6667 | 39.8333 |
| material | 3 | 3 | 0 | 3 | 2 | 0 | 0.5000 | 35.1667 |
| mlp | 2 | 3 | 1 | 1 | 2 | 1 | 0.3333 | 35.0000 |
| weighted_static | 2 | 3 | 1 | 2 | 3 | 1 | 0.3333 | 40.0000 |

## Self-Play Color Split
| evaluator | red_wins | red_losses | red_draws | red_win_rate | black_wins | black_losses | black_draws | black_win_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 2 | 1 | 0 | 0.6667 | 2 | 1 | 0 | 0.6667 |
| material | 2 | 1 | 0 | 0.6667 | 1 | 2 | 0 | 0.3333 |
| mlp | 1 | 2 | 0 | 0.3333 | 1 | 1 | 1 | 0.3333 |
| weighted_static | 1 | 1 | 1 | 0.3333 | 1 | 2 | 0 | 0.3333 |

## Metric Notes
- mean_abs_oracle_regret measures average decision loss under the shared oracle.
- p90_abs_oracle_regret measures stability in poor but non-maximum cases.
- max_abs_oracle_regret highlights catastrophic moves worth inspecting manually.
- move_match_rate measures how often the evaluator chooses the same best move as the oracle.
- self-play color statistics help check red/black first-move bias.

## Initial Interpretation
- weighted_static has the lowest mean_abs_oracle_regret in this run.
- weighted_static has the highest move_match_rate in this run.
- MLP mean_abs_oracle_regret is 185.7200 higher than full_static.
- MLP mean_abs_oracle_regret is 186.6600 higher than weighted_static.
- full_static has the highest self-play win_rate in this run.
- If the sample is small, treat this as a smoke test rather than a final playing-strength conclusion.

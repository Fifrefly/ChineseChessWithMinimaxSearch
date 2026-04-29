# Experiment Summary

## Benchmark Settings
- search_depth: 2
- oracle_depth: 3
- oracle_evaluator: full_static

## Evaluator Accuracy vs Oracle
| evaluator | mean_abs_oracle_regret | p90_abs_oracle_regret | max_abs_oracle_regret | oracle_regret_rmse | zero_regret_rate | move_match_rate | mean_abs_score_error | avg_nodes | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 4085.3818 | 193.6000 | 997859.0000 | 63426.3864 | 0.5859 | 0.5840 | 4304.6040 | 523.9860 | 1.5494 |
| king_safety | 4096.5293 | 266.6000 | 997859.0000 | 63426.4161 | 0.5717 | 0.5720 | 4317.9520 | 549.9920 | 1.2323 |
| material | 2093.4263 | 266.6000 | 997802.0000 | 44848.1223 | 0.5212 | 0.5240 | 4304.6500 | 468.7920 | 0.7789 |
| mlp | 327.1596 | 841.2000 | 2306.0000 | 490.4471 | 0.2505 | 0.2620 | 35486.7600 | 589.6180 | 1.8061 |
| mobility | 4096.9455 | 266.0000 | 997859.0000 | 63426.4159 | 0.5677 | 0.5680 | 4308.5280 | 549.0640 | 1.0082 |
| position | 2084.0586 | 242.4000 | 997802.0000 | 44848.0765 | 0.5515 | 0.5520 | 4306.6520 | 544.5980 | 0.8988 |
| weighted_static | 2070.1313 | 193.6000 | 997802.0000 | 44848.0298 | 0.5838 | 0.5840 | 4307.0520 | 526.2420 | 1.5608 |

## Worst Regret Cases
| evaluator | rank | position_id | oracle_regret | best_move | oracle_best_move | fen |
| --- | ---: | ---: | ---: | --- | --- | --- |
| full_static | 1 | 472 | -997859 | g3e3 | b7e7 | 2bak1bn1/4a4/1c6r/2p3p1p/p8/P3p3C/2N3r1P/4K4/9/2cA1ABNR b - - 1 30 |
| full_static | 2 | 233 | -997802 | b1e1 | c3c2 | 1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38 |
| full_static | 3 | 89 | 799 | a7a8 | g1g9 | C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27 |
| full_static | 4 | 227 | 643 | g7f7 | b4b8 | 3a1a3/4k4/b3brR2/2C2nC1P/2pcp4/pRP6/P3P4/3NBA3/5n3/1N1AK1B2 r - - 2 40 |
| full_static | 5 | 5 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| king_safety | 1 | 472 | -997859 | g3e3 | b7e7 | 2bak1bn1/4a4/1c6r/2p3p1p/p8/P3p3C/2N3r1P/4K4/9/2cA1ABNR b - - 1 30 |
| king_safety | 2 | 233 | -997802 | b1e1 | c3c2 | 1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38 |
| king_safety | 3 | 196 | -736 | i5i4 | h9h1 | 3ak1br1/2n1a4/9/p5p2/2P1p3p/4c1P1P/Pr7/8C/R3K4/2BA1ABNR b - - 0 25 |
| king_safety | 4 | 236 | -657 | b9b0 | h0i0 | 1rb2ab2/4k4/n2a2n2/4p2Cp/p1p4c1/4P1P2/P1P5P/2N1B4/6N2/1R1AKABrR b - - 0 28 |
| king_safety | 5 | 5 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| material | 1 | 233 | -997802 | b1e1 | c3c2 | 1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38 |
| material | 2 | 227 | 947 | g7g8 | b4b8 | 3a1a3/4k4/b3brR2/2C2nC1P/2pcp4/pRP6/P3P4/3NBA3/5n3/1N1AK1B2 r - - 2 40 |
| material | 3 | 196 | -736 | i5i4 | h9h1 | 3ak1br1/2n1a4/9/p5p2/2P1p3p/4c1P1P/Pr7/8C/R3K4/2BA1ABNR b - - 0 25 |
| material | 4 | 236 | -657 | b9b0 | h0i0 | 1rb2ab2/4k4/n2a2n2/4p2Cp/p1p4c1/4P1P2/P1P5P/2N1B4/6N2/1R1AKABrR b - - 0 28 |
| material | 5 | 5 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| mlp | 1 | 401 | -2306 | c7d7 | d2h2 | 1Cbak4/4a4/1cc1b1n1r/p1p1p1p1p/7C1/2B3P1P/P1P1P4/3r3RB/2N1A3R/4KA1N1 b - - 2 20 |
| mlp | 2 | 54 | 2027 | h0h7 | b8b7 | 2bk2b2/1Rcna4/1rna5/p1p1p3p/6p2/4r1P1P/P1P6/4NA2B/2N5c/2BAK2R1 r - - 18 32 |
| mlp | 3 | 334 | 1806 | c0e2 | h3h7 | 2bak4/4a4/2n4rb/2p2P3/4r1p1p/6B1P/2P3PR1/R2A1CN2/c8/C1BA1K3 r - - 17 37 |
| mlp | 4 | 89 | 1788 | f2f7 | g1g9 | C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27 |
| mlp | 5 | 187 | -1523 | e8f9 | h3g3 | r1b1k1b2/4a3C/5a2n/4n3p/p5p2/1pP1p1P1P/P1R1c1Rr1/4BA3/3KA4/2c1C1BN1 b - - 7 38 |
| mobility | 1 | 472 | -997859 | g3e3 | b7e7 | 2bak1bn1/4a4/1c6r/2p3p1p/p8/P3p3C/2N3r1P/4K4/9/2cA1ABNR b - - 1 30 |
| mobility | 2 | 233 | -997802 | b1e1 | c3c2 | 1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38 |
| mobility | 3 | 196 | -736 | i5i4 | h9h1 | 3ak1br1/2n1a4/9/p5p2/2P1p3p/4c1P1P/Pr7/8C/R3K4/2BA1ABNR b - - 0 25 |
| mobility | 4 | 236 | -657 | b9b0 | h0i0 | 1rb2ab2/4k4/n2a2n2/4p2Cp/p1p4c1/4P1P2/P1P5P/2N1B4/6N2/1R1AKABrR b - - 0 28 |
| mobility | 5 | 5 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| position | 1 | 233 | -997802 | b1e1 | c3c2 | 1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38 |
| position | 2 | 196 | -736 | i5i4 | h9h1 | 3ak1br1/2n1a4/9/p5p2/2P1p3p/4c1P1P/Pr7/8C/R3K4/2BA1ABNR b - - 0 25 |
| position | 3 | 236 | -657 | b9b0 | h0i0 | 1rb2ab2/4k4/n2a2n2/4p2Cp/p1p4c1/4P1P2/P1P5P/2N1B4/6N2/1R1AKABrR b - - 0 28 |
| position | 4 | 5 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| position | 5 | 2 | -562 | i5i4 | i9h9 | 1nCa1ab1r/r1c6/4k3n/p3p4/6p1p/3cP3P/P1P3P2/B6CB/9/RN1AKA1NR b - - 10 13 |
| weighted_static | 1 | 233 | -997802 | b1e1 | c3c2 | 1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38 |
| weighted_static | 2 | 89 | 799 | a7a8 | g1g9 | C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27 |
| weighted_static | 3 | 227 | 643 | g7f7 | b4b8 | 3a1a3/4k4/b3brR2/2C2nC1P/2pcp4/pRP6/P3P4/3NBA3/5n3/1N1AK1B2 r - - 2 40 |
| weighted_static | 4 | 5 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| weighted_static | 5 | 319 | 499 | d1d2 | h6h9 | 2bak1b2/r1C5n/2n2a3/4p2Cp/9/4P3P/p1P3P2/3c1AR1N/N2K5/R1B2AB2 r - - 1 36 |

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
- mean_abs_oracle_regret measures average decision loss under the shared oracle.
- p90_abs_oracle_regret measures stability in poor but non-maximum cases.
- max_abs_oracle_regret highlights catastrophic moves worth inspecting manually.
- move_match_rate measures how often the evaluator chooses the same best move as the oracle.
- self-play color statistics help check red/black first-move bias.

## Initial Interpretation
- mlp has the lowest mean_abs_oracle_regret in this run.
- full_static, weighted_static have the highest move_match_rate in this run.
- MLP mean_abs_oracle_regret is 3758.2222 lower than full_static.
- MLP mean_abs_oracle_regret is 1742.9717 lower than weighted_static.
- full_static has the highest self-play win_rate in this run.
- If the sample is small, treat this as a smoke test rather than a final playing-strength conclusion.

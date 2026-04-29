# Experiment Summary

## Benchmark Settings
- search_depth: 2
- oracle_depth: 3
- oracle_evaluator: full_static
- decision_loss_source: decision_loss

## Evaluator Decision Quality vs Oracle
| evaluator | mean_decision_loss | p90_decision_loss | max_decision_loss | zero_decision_loss_rate | move_match_rate | mean_abs_oracle_regret | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 57.0764 | 201.9000 | 799.0000 | 0.6042 | 0.5972 | 57.0764 | 1.5145 |
| material | 75.5417 | 259.1000 | 587.0000 | 0.5347 | 0.5347 | 75.5417 | 0.7667 |
| mlp | 354.5486 | 810.3000 | 2027.0000 | 0.2153 | 0.2153 | 354.5486 | 1.7914 |
| weighted_static | 55.0972 | 201.9000 | 799.0000 | 0.6181 | 0.6111 | 55.0972 | 1.5260 |

## Evaluator Accuracy vs Oracle
| evaluator | mean_abs_oracle_regret | p90_abs_oracle_regret | max_abs_oracle_regret | oracle_regret_rmse | zero_regret_rate | move_match_rate | mean_abs_score_error | avg_nodes | avg_time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 57.0764 | 201.9000 | 799.0000 | 137.1499 | 0.6042 | 0.5972 | 323.4514 | 522.5694 | 1.5145 |
| material | 75.5417 | 259.1000 | 587.0000 | 149.5887 | 0.5347 | 0.5347 | 315.1250 | 470.2917 | 0.7667 |
| mlp | 354.5486 | 810.3000 | 2027.0000 | 524.0032 | 0.2153 | 0.2153 | 29867.8889 | 595.9097 | 1.7914 |
| weighted_static | 55.0972 | 201.9000 | 799.0000 | 133.3184 | 0.6181 | 0.6111 | 325.4514 | 525.0833 | 1.5260 |

## Worst Regret Cases
| evaluator | rank | position_id | decision_loss | oracle_delta | oracle_regret | best_move | oracle_best_move | fen |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| full_static | 1 | 89 | 799 | -799 | 799 | a7a8 | g1g9 | C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27 |
| full_static | 2 | 5 | 587 | -587 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| full_static | 3 | 2 | 501 | 501 | -501 | f9e8 | i9h9 | 1nCa1ab1r/r1c6/4k3n/p3p4/6p1p/3cP3P/P1P3P2/B6CB/9/RN1AKA1NR b - - 10 13 |
| full_static | 4 | 109 | 429 | 429 | -429 | b4a4 | d1f1 | 1n1akabn1/7C1/b8/6p2/p3pC2p/Prp6/2P1P1P1P/Nr6B/R2cKN3/2BA1A2R b - - 14 27 |
| full_static | 5 | 1 | 425 | 425 | -425 | e5e4 | i9h9 | 1nba1a2r/4k3c/r3b3n/p1pc2p1p/4p4/4P4/P1P3P1P/C6CR/4R4/1NBAKABN1 b - - 23 12 |
| material | 1 | 5 | 587 | -587 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| material | 2 | 2 | 562 | 562 | -562 | i5i4 | i9h9 | 1nCa1ab1r/r1c6/4k3n/p3p4/6p1p/3cP3P/P1P3P2/B6CB/9/RN1AKA1NR b - - 10 13 |
| material | 3 | 111 | 560 | -560 | 560 | a2b0 | a2c3 | rn1akabCr/9/4b2C1/p5p1p/2p1p4/9/P1c1P1P1P/N8/9/RcBAKABNR r - - 3 12 |
| material | 4 | 4 | 441 | 441 | -441 | e9e8 | c8b8 | 2b1kabnr/2r6/nC1a5/p1p3pcp/4p4/P2C4P/2P1P1P2/R3B4/9/1N1AKABNR b - - 10 15 |
| material | 5 | 109 | 429 | 429 | -429 | b4a4 | d1f1 | 1n1akabn1/7C1/b8/6p2/p3pC2p/Prp6/2P1P1P1P/Nr6B/R2cKN3/2BA1A2R b - - 14 27 |
| mlp | 1 | 54 | 2027 | -2027 | 2027 | h0h7 | b8b7 | 2bk2b2/1Rcna4/1rna5/p1p1p3p/6p2/4r1P1P/P1P6/4NA2B/2N5c/2BAK2R1 r - - 18 32 |
| mlp | 2 | 89 | 1788 | -1788 | 1788 | f2f7 | g1g9 | C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27 |
| mlp | 3 | 95 | 1452 | -1452 | 1452 | h7e7 | h7i7 | 2ba5/4kn3/n2ab2Rr/9/2prp3p/4Pp3/1CP5P/5A2B/7c1/1N2K1BN1 r - - 5 41 |
| mlp | 4 | 99 | 1411 | 1411 | -1411 | h9g7 | d8d1 | rnbakabnr/3c5/3c5/p1p1p1p1p/9/8P/P1P1P1P2/2C3C2/3R5/1NBAKABNR b - - 15 8 |
| mlp | 5 | 139 | 1402 | -1402 | 1402 | h2h7 | h8g8 | rnb1ka1n1/4a2C1/6c1r/p1p1p3p/2b3p2/2C3P1P/P1P1P4/2NcB2R1/4K4/3A1ABN1 r - - 14 29 |
| weighted_static | 1 | 89 | 799 | -799 | 799 | a7a8 | g1g9 | C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27 |
| weighted_static | 2 | 5 | 587 | -587 | 587 | i4e4 | b1b9 | 1n1ak1b2/8r/3ab3n/1c2p4/p1PR3Pp/P3r3R/4P1P1N/B4C3/1C2A4/1N2KA3 r - - 21 41 |
| weighted_static | 3 | 109 | 429 | 429 | -429 | b4a4 | d1f1 | 1n1akabn1/7C1/b8/6p2/p3pC2p/Prp6/2P1P1P1P/Nr6B/R2cKN3/2BA1A2R b - - 14 27 |
| weighted_static | 4 | 1 | 425 | 425 | -425 | e5e4 | i9h9 | 1nba1a2r/4k3c/r3b3n/p1pc2p1p/4p4/4P4/P1P3P1P/C6CR/4R4/1NBAKABN1 b - - 23 12 |
| weighted_static | 5 | 36 | 397 | -397 | 397 | g9i9 | i2f2 | 3a2Cnr/5k1C1/r1n1b3b/p1p1p4/7cp/P1P3p2/4P1P1P/5c2R/4N1R2/2BAKABN1 r - - 33 26 |

## Self-Play Tournament
Self-play data was not provided.

## Self-Play Color Split
Self-play data was not provided.

## Metric Notes
- decision_loss is the primary move-quality metric. It is always non-negative and measures how much worse the tested move is than the oracle move from the side-to-move perspective.
- mean_abs_oracle_regret is retained as a legacy metric, but its signed source can be hard to interpret when the side to move changes.
- p90_abs_oracle_regret measures stability in poor but non-maximum cases.
- max_abs_oracle_regret highlights catastrophic moves worth inspecting manually.
- move_match_rate measures how often the evaluator chooses the same best move as the oracle.
- self-play color statistics help check red/black first-move bias.

## Initial Interpretation
- weighted_static has the lowest mean_decision_loss in this run.
- weighted_static has the highest move_match_rate in this run.
- MLP mean_decision_loss is 297.4722 higher than full_static.
- MLP mean_decision_loss is 299.4514 higher than weighted_static.
- If the sample is small, treat this as a smoke test rather than a final playing-strength conclusion.

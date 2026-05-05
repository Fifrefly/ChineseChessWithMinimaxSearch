# NNUE Training Report

## Data split

- input: `data/nnue_training_data.csv`
- train: 26453
- val: 3306
- test: 3306
- seed: 2026

## Model

- feature_dim: 1261
- hidden_size: 256
- bottleneck_size: 32
- target_scale: 1000.0
- clip_train_target: 5000.0
- device: cuda
- elapsed_seconds: 82.77

## Test comparison

| evaluator | subset | samples | MAE | RMSE | R2 | Pearson | sign_acc |
|---|---:|---:|---:|---:|---:|---:|---:|
| nnue | all | 3306 | 20525.764 | 142231.861 | 0.0005 | 0.1553 | 0.8929 |
| nnue | non_mate | 3239 | 283.548 | 362.402 | 0.8358 | 0.9146 | 0.8941 |
| material | all | 3306 | 20733.977 | 142309.962 | -0.0006 | 0.0834 | 0.5604 |
| material | non_mate | 3239 | 484.838 | 603.744 | 0.5443 | 0.7388 | 0.5593 |
| position | all | 3306 | 20731.652 | 142307.407 | -0.0005 | 0.0845 | 0.6835 |
| position | non_mate | 3239 | 482.834 | 599.377 | 0.5509 | 0.7424 | 0.6841 |
| mobility | all | 3306 | 20730.361 | 142304.148 | -0.0005 | 0.0868 | 0.6856 |
| mobility | non_mate | 3239 | 481.990 | 597.901 | 0.5531 | 0.7437 | 0.6862 |
| king_safety | all | 3306 | 20731.508 | 142302.744 | -0.0005 | 0.0880 | 0.6865 |
| king_safety | non_mate | 3239 | 483.368 | 599.252 | 0.5511 | 0.7425 | 0.6872 |
| full_static | all | 3306 | 20726.322 | 142300.593 | -0.0004 | 0.0904 | 0.6799 |
| full_static | non_mate | 3239 | 478.372 | 576.498 | 0.5845 | 0.7645 | 0.6804 |
| weighted_static | all | 3306 | 20726.758 | 142301.176 | -0.0005 | 0.0900 | 0.6820 |
| weighted_static | non_mate | 3239 | 478.732 | 578.688 | 0.5813 | 0.7625 | 0.6825 |

## Best by MAE

- all test rows: nnue (MAE 20525.764)
- non_mate excludes rows with `abs(target_score) >= 900000`, because those are forced-mate search labels that dominate static-regression metrics.
- non_mate rows: nnue (MAE 283.548)

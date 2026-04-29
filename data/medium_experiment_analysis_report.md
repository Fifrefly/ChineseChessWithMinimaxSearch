# 中型实验分析报告：Xiangqi Evaluator Benchmark

## 1. 实验设置

本项目实现了一个轻量级中国象棋 / Xiangqi 引擎，包含可逆棋盘状态、合法走法生成、固定深度 minimax、alpha-beta 搜索、多个手工静态评估函数，以及一个可选的 MLP 评估器。中型实验主要比较两类结果：

- 离线 oracle benchmark：每个 tested evaluator 使用 depth 2 搜索，和 `full_static` depth 3 oracle 进行比较；
- self-play tournament：不同 evaluator 互相对弈，用总胜率和红黑方 split 评估实际下棋强度。

当前工作区缺少原始 medium CSV 文件。日志显示这些文件曾经生成过，包括 `data/evaluation_benchmark_medium.csv`、`data/self_play_results_medium.csv`、`data/experiment_summary_medium.csv` 和 `data/worst_cases_medium.csv`，但现在不在 `data/` 目录中。因此本报告使用保留下来的 medium summary markdown、self-play summary 和 worst-case inspection logs 进行分析。当前 `experiments/evaluation_benchmark.py` 和 `experiments/analyze_benchmark.py` 已支持直接输出和汇总 `decision_loss`，但若要完全逐行复现 medium summary，需要重新生成缺失的 CSV。

## 2. 比较的 Evaluators

| evaluator | 含义 |
| --- | --- |
| `material` | 只使用子力价值的基线 |
| `position` | 子力价值 + 位置表 |
| `mobility` | 加入 mobility 特征 |
| `king_safety` | 加入 king-safety 特征 |
| `full_static` | 完整手工静态评估，包含 threats |
| `weighted_static` | 手工加权的 feature combination |
| `mlp` | 使用手工特征输入的学习型 MLP evaluator |

benchmark 包含以上七个 evaluator；self-play summary 中包含 `material`、`full_static`、`weighted_static` 和 `mlp`。

## 3. Benchmark Methodology

每个 benchmark FEN 上，oracle 使用 `full_static` evaluator 搜索到 depth 3。tested evaluator 搜索到 depth 2 并选择一个 best move。随后 benchmark 将 tested move 应用到棋盘上，再用同一个 oracle 评估该 successor position。核心比较是：

```text
oracle best move 的 oracle score
vs.
tested evaluator move 之后 successor 的 oracle continuation score
```

这衡量的是 move quality under oracle，而不是实际棋力。实际棋力仍需要 self-play 验证，因为一个 evaluator 可能在某个离线 score metric 上表现不错，但在对抗式 self-play 中暴露严重弱点。

## 4. 为什么 `decision_loss` 是主要指标

引擎中的搜索分数以 RED perspective 存储。这会让 signed `oracle_regret` 在混合 RED/BLACK side-to-move 的 benchmark 中难以直接比较：

- RED to move 时，较差走法通常表现为 `oracle_score - candidate_score > 0`；
- BLACK to move 时，BLACK 希望 RED-perspective score 更低，所以较差走法通常表现为 `oracle_score - candidate_score < 0`。

`abs_oracle_regret` 可以消除符号，但它仍然是旧版兼容指标，并没有直接表达“当前行棋方损失了多少”。`decision_loss` 更清晰：它按照 side-to-move perspective 计算非负损失。`0` 表示 tested move 在当前 oracle depth 下与 oracle move 等价；值越大，说明 tested evaluator 选择的 move 在 oracle 看来越差。

因此，本报告优先分析：

- `mean_decision_loss`
- `p90_decision_loss`
- `max_decision_loss`
- `zero_decision_loss_rate`
- `move_match_rate`

`mean_abs_oracle_regret` 只作为旧版兼容和辅助诊断指标保留。

## 5. Benchmark Results

保留下来的 medium summary 主要记录旧版非负 regret 指标。下表将这些值作为 decision-loss 口径来解释；严格来说，若要获得完全 row-derived 的新版表格，需要重新生成 medium benchmark CSV。

| evaluator | mean_decision_loss | p90_decision_loss | max_decision_loss | zero_decision_loss_rate | move_match_rate | mean_abs_oracle_regret |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 4085.3818 | 193.6000 | 997859.0000 | 0.5859 | 0.5840 | 4085.3818 |
| king_safety | 4096.5293 | 266.6000 | 997859.0000 | 0.5717 | 0.5720 | 4096.5293 |
| material | 2093.4263 | 266.6000 | 997802.0000 | 0.5212 | 0.5240 | 2093.4263 |
| mlp | 327.1596 | 841.2000 | 2306.0000 | 0.2505 | 0.2620 | 327.1596 |
| mobility | 4096.9455 | 266.0000 | 997859.0000 | 0.5677 | 0.5680 | 4096.9455 |
| position | 2084.0586 | 242.4000 | 997802.0000 | 0.5515 | 0.5520 | 2084.0586 |
| weighted_static | 2070.1313 | 193.6000 | 997802.0000 | 0.5838 | 0.5840 | 2070.1313 |

这张表不能解释为 “MLP 最强”。MLP 的平均 regret 最低，主要是因为它没有出现几个接近 mate-scale 的极端 outlier；但它的 `p90_decision_loss` 是所有 evaluator 中最差之一，`move_match_rate` 也只有 26.20%。相比之下，`full_static` 和 `weighted_static` 的 move-match rate 都是 58.40%，p90 loss 也明显更低。

## 6. Self-Play Results

| evaluator | wins | losses | draws | win_rate | adjudicated_wins | adjudicated_losses | avg_game_plies |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 94 | 11 | 15 | 0.7833 | 6 | 2 | 66.6917 |
| weighted_static | 84 | 18 | 18 | 0.7000 | 4 | 5 | 66.3917 |
| material | 37 | 75 | 8 | 0.3083 | 30 | 4 | 82.5000 |
| mlp | 4 | 115 | 1 | 0.0333 | 0 | 29 | 72.3000 |

self-play 是本实验中最接近实际 playing strength 的证据。根据该结果，`full_static` 是最可靠的 evaluator，`weighted_static` 次之。`material` 明显较弱，而 `mlp` 在实际对弈中几乎完全失效。

## 7. Color-Split Discussion

| evaluator | red_wins | red_losses | red_draws | red_win_rate | black_wins | black_losses | black_draws | black_win_rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full_static | 49 | 5 | 6 | 0.8167 | 45 | 6 | 9 | 0.7500 |
| weighted_static | 46 | 7 | 7 | 0.7667 | 38 | 11 | 11 | 0.6333 |
| material | 18 | 34 | 8 | 0.3000 | 19 | 41 | 0 | 0.3167 |
| mlp | 1 | 59 | 0 | 0.0167 | 3 | 56 | 1 | 0.0500 |

全部 240 局中，RED 获胜 114 局，BLACK 获胜 105 局，DRAW 21 局，存在轻微红方优势，但不足以解释 evaluator 排名。`full_static` 红黑两边都稳定；`weighted_static` 作为 RED 表现很强，但 BLACK win rate 降到 63.33%，说明其防守或最小化 RED score 的能力可能不如 `full_static` 稳定。MLP 红黑两边都很差，因此它的失败不是颜色偏置造成的。

## 8. Catastrophic Worst-Case Analysis

### Position 472

FEN: `2bak1bn1/4a4/1c6r/2p3p1p/p8/P3p3C/2N3r1P/4K4/9/2cA1ABNR b - - 1 30`

BLACK to move。tested move 是 `g3e3`，oracle best move 是 `b7e7`。两个 successor 都是 check，但都不是 immediate checkmate。tested continuation score 为 `-2138`，oracle continuation score 为 `-999998`。因为 BLACK 希望 RED-perspective score 更低，所以 tested move 几乎放弃了一个 mate-scale 优势。

分类：horizon effect、search-depth limitation、possible evaluator feature limitation。当前证据不足以断定是 checkmate detection 或 propagation bug，因为 inspected successor 并非立即将死。下一步应使用 oracle depth 4 或 5 复查。

### Position 233

FEN: `1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38`

BLACK to move。tested move 是 `b1e1`，oracle best move 是 `c3c2`。tested move 给出 immediate check，但 continuation score 只有 `-2195`；oracle move 不是 immediate check，却达到 `-999998`。这说明 shallow tested search 可能偏好表面强迫性的 check，而没有看到更深的 winning continuation。

分类：horizon effect、search-depth limitation、possible evaluator feature limitation。它也可能涉及 mate-scale propagation 的边界情况，但目前没有足够证据下结论。

### Position 89

FEN: `C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27`

RED to move。tested move `a7a8` 是 quiet move，successor continuation score 为 `1312`；oracle move `g1g9` 给 check，并保持 `2111` 的分数。decision loss 为 `799`，较大但不是 mate-scale。

分类：evaluator feature limitation、search-depth limitation。这个 case 很有信息量，因为它不是由 mate-score constant 主导的极端值，而是一个普通但明显的 tactical miss。

## 9. MLP Diagnostic Negative Result

MLP 结果应被视为有意义的 negative result，而不是强行包装成最佳模型。它在 preserved medium benchmark 中拥有最低的平均 oracle regret，但 self-play 表现极差：

- benchmark 平均 preserved regret：`327.1596`，低于手工 static evaluators；
- benchmark `move_match_rate`：只有 `0.2620`；
- benchmark `p90_decision_loss`：`841.2000`，比手工 evaluator 更差；
- self-play：`4W / 115L / 1D`，win rate 只有 `0.0333`；
- color split：RED win rate `0.0167`，BLACK win rate `0.0500`。

这个矛盾说明，低平均 score regret 不等于强 move-selection，也不等于实际棋力。可能原因包括：label search depth 太浅、训练数据不足、mate-scale target score 导致 scale instability、输入 handcrafted features 表达能力有限、benchmark positions 到 self-play positions 的泛化能力差，以及 score prediction objective 和 move-selection quality 之间存在 mismatch。

可以将该发现总结为：学习型 evaluator 降低了一个离线 regret 指标，但在实际 self-play 中失败，说明基于有限特征的 learned static evaluation 对对抗式下棋不够 robust。

## 10. Limitations

- oracle depth 只有 3，并且 oracle 本身也是 `full_static`，不是完美真值。
- benchmark 大约 500 个 positions，self-play 240 局，样本规模仍然有限。
- mate-scale rows 会强烈影响 mean，因此必须同时报告 p90、max、zero rate 和人工 worst-case inspection。
- 原始 medium CSV 当前缺失，所以本报告不能逐行重新计算所有 medium aggregate。
- max-plies adjudication 是实验规则，依赖 adjudicator evaluator 和 threshold。
- MLP 使用浅层 label 和很小的 handcrafted feature vector，不代表完整神经象棋引擎的上限。

## 11. Next Steps

- 用当前 `experiments/evaluation_benchmark.py` 重新生成 `data/evaluation_benchmark_medium.csv`，确保 CSV 直接包含 `decision_loss`。
- 用 `experiments/analyze_benchmark.py` 重新生成 medium summary、summary CSV 和 worst-case CSV。
- 对 positions 472 和 233 使用 oracle depth 4 或 5 复查 mate-scale 分数是否稳定。
- 对 catastrophic FEN 枚举所有合法走法并记录 oracle continuation score，判断是单步 outlier 还是 evaluator 系统性偏好问题。
- 将 ordinary tactical losses 和 mate-scale losses 分开报告。
- 如果继续 MLP 实验，应增加训练 positions、使用更深 labels、采用 target clipping 或 Huber loss、扩展输入特征，并以 move-selection metrics 和 self-play 而不是单纯 score error 作为主要目标。

## 12. Conclusion

基于当前 self-play 证据，`full_static` 和 `weighted_static` 是最可靠的实用 evaluators，其中 `full_static` 综合最强。MLP 是一个 diagnostic negative result：它降低了一个离线平均 regret 指标，但没有转化为 robust adversarial play。接近 mate-scale regret 的 catastrophic failures 需要人工检查和更深 oracle 验证；它们很可能反映 horizon effects 或 tactical blind spots，而不能只用一个平均 regret 数字简单排名。

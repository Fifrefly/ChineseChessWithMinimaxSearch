# Medium Worst-Case Inspection Notes

These notes summarize manual inspections of the most severe medium benchmark cases. The preserved logs include full inspections for positions 472 and 233. Position 89 was re-inspected with `experiments/inspect_worst_case.py` using the bundled Python 3.11 runtime.

## Position 472

- FEN: `2bak1bn1/4a4/1c6r/2p3p1p/p8/P3p3C/2N3r1P/4K4/9/2cA1ABNR b - - 1 30`
- side to move: BLACK
- tested best move: `g3e3`
- oracle best move: `b7e7`
- original oracle score: `-999997`
- tested successor FEN: `2bak1bn1/4a4/1c6r/2p3p1p/p8/P3p3C/2N1r3P/4K4/9/2cA1ABNR r - - 2 31`
- tested successor is check: `True`
- tested successor is checkmate: `False`
- tested oracle continuation score: `-2138`
- oracle successor FEN: `2bak1bn1/4a4/4c3r/2p3p1p/p8/P3p3C/2N3r1P/4K4/9/2cA1ABNR r - - 2 31`
- oracle successor is check: `True`
- oracle successor is checkmate: `False`
- oracle continuation score: `-999998`
- successor score difference, tested minus oracle: `997860`

Original board:

```text
    a b c d e f g h i
 0  . . b a k . b n .
 1  . . . . a . . . .
 2  . c . . . . . . r
 3  . . p . . . p . p
 4  p . . . . . . . .
 5  P . . . p . . . C
 6  . . N . . . r . P
 7  . . . . K . . . .
 8  . . . . . . . . .
 9  . . c A . A B N R
```

Interpretation: both moves give check, but the oracle move preserves a near mate-scale advantage for BLACK while the tested move only leaves a large ordinary advantage. This is consistent with a horizon effect or search-depth limitation: the shallow tested search appears to prefer an immediate check without seeing the forcing continuation behind `b7e7`. Because the successor is not immediate checkmate, this is not enough evidence by itself to call it a checkmate-detection bug. A depth-4 oracle check would be the next confirmation step.

## Position 233

- FEN: `1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/rc1KR4/1NBA1AB2 b - - 17 38`
- side to move: BLACK
- tested best move: `b1e1`
- oracle best move: `c3c2`
- original oracle score: `-999997`
- tested successor FEN: `1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P1r1RNP2/2C6/r2Kc4/1NBA1AB2 r - - 0 39`
- tested successor is check: `True`
- tested successor is checkmate: `False`
- tested oracle continuation score: `-2195`
- oracle successor FEN: `1nba1k1n1/9/3a4b/p3P1p2/5c2p/2P5P/P3RNP2/2r6/rc1KR4/1NBA1AB2 r - - 0 39`
- oracle successor is check: `False`
- oracle successor is checkmate: `False`
- oracle continuation score: `-999998`
- successor score difference, tested minus oracle: `997803`

Original board:

```text
    a b c d e f g h i
 0  . n b a . k . n .
 1  . . . . . . . . .
 2  . . . a . . . . b
 3  p . . . P . p . .
 4  . . . . . c . . p
 5  . . P . . . . . P
 6  P . r . R N P . .
 7  . . C . . . . . .
 8  r c . K R . . . .
 9  . N B A . A B . .
```

Interpretation: the tested move gives an immediate check, while the oracle move does not. However, the oracle continuation score is near mate-scale for BLACK. This strongly suggests a tactical blind spot in the shallow tested search rather than a simple static-evaluation preference. The evidence also fits horizon effect and search-depth limitation. It is not conclusive proof of a mate/checkmate propagation issue, because neither successor is immediate checkmate under the rules checker.

## Position 89

- FEN: `C1bakar2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 r - - 5 27`
- side to move: RED
- tested best move: `a7a8`
- oracle best move: `g1g9`
- original oracle score: `2111`
- tested successor FEN: `C1bakar2/R8/2c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA1C2/4KABN1 b - - 0 27`
- tested successor is check: `False`
- tested successor is checkmate: `False`
- tested oracle continuation score: `1312`
- oracle successor FEN: `C1bakaC2/r8/R1c5n/4n1p1p/p8/4p4/P1PpP4/5R3/3NA4/4KABN1 b - - 0 27`
- oracle successor is check: `True`
- oracle successor is checkmate: `False`
- oracle continuation score: `2111`
- successor score difference, tested minus oracle: `-799`

Original board:

```text
    a b c d e f g h i
 0  C . b a k a r . .
 1  r . . . . . . . .
 2  R . c . . . . . n
 3  . . . . n . p . p
 4  p . . . . . . . .
 5  . . . . p . . . .
 6  P . P p P . . . .
 7  . . . . . R . . .
 8  . . . N A . C . .
 9  . . . . K A B N .
```

Interpretation: this is a high-information non-mate-scale case. The oracle chooses a checking cannon move that preserves a score of `2111`; the tested move is quieter and drops to `1312`. This points more toward evaluator feature limitation and search-depth limitation than toward a mate propagation bug. It is useful because the decision loss is large but not dominated by the mate-score constant.

## Cross-Case Classification

| position | likely causes | notes |
| ---: | --- | --- |
| 472 | horizon effect; search-depth limitation; possible tactical feature limitation | Immediate check was not enough; oracle finds a near mate-scale continuation. Needs depth-4 confirmation. |
| 233 | horizon effect; search-depth limitation; possible tactical feature limitation | Tested move gives check but loses a near forced win. Not enough evidence for a rules/checkmate bug. |
| 89 | evaluator feature limitation; search-depth limitation | Large ordinary tactical loss; oracle checking move is preferred without mate-scale scoring. |

## Extra Checks Needed

- Re-run these same FENs with oracle depth 4 or 5 if runtime permits.
- Compare several tested evaluators on each FEN, not only the evaluator that produced the preserved worst row.
- Record all legal candidate moves and oracle continuation scores to see whether the loss is from one tactical outlier or from a broad evaluator preference.
- Keep mate-scale rows separate from ordinary tactical rows when reporting means, because one near-checkmate error can dominate average regret.

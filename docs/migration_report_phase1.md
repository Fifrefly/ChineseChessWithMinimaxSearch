# Phase 1 Migration Report

## Source Layout Observed

The reference implementation currently available in this workspace is a single-file JavaScript build at `vender/xiangqi.js`. To match the requested project layout, `vendor/xiangqi.js` has been added as a compatibility symlink pointing to that file. The JavaScript source should remain read-only reference material for the Python port.

The implementation exposes a `Xiangqi(fen)` constructor. It keeps the complete mutable game state inside the constructor closure and returns an object with public methods.

## Most Critical Reference Modules and Behaviors

Because the JavaScript reference is one file, the critical pieces are logical sections rather than separate modules:

- Board model: a 256-element mailbox-style array using 0x9a coordinates, plus `SQUARES`, `rank`, `file`, and `algebraic` helpers.
- Position state: `board`, `kings`, `turn`, `half_moves`, `move_number`, `history`, `futures`, and `header`.
- FEN support: `load`, `validate_fen`, and `generate_fen`.
- Move generation: `generate_moves`, `build_move`, piece offsets, river/palace constraints, horse-leg blocking, elephant-eye blocking, cannon screen logic, and legal-move filtering.
- Attack/check logic: `king_attacked`, `in_check`, `in_checkmate`, and `in_stalemate`.
- State transitions: `make_move`, `undo_move`, `redo_move`, `move`, and `history`.
- Terminal/draw logic: `game_over`, `in_draw`, `insufficient_material`, and `in_threefold_repetition`.

## Public APIs to Prioritize

The Python version should first match the APIs needed by later search experiments:

- `load_fen(fen: str) -> None` and `fen() -> str`
- `get_legal_moves() -> list[Move]`
- `get_pseudo_legal_moves() -> list[Move]`
- `make_move(move: Move | str) -> Move`
- `undo_move() -> Move | None`
- `is_check() -> bool`
- `is_checkmate() -> bool`
- `is_stalemate() -> bool`
- `game_over() -> bool`
- `turn`, `board`, and lightweight square/piece accessors for evaluators

For parity with xiangqi.js, string moves should use ICCS coordinates such as `h2e2`, and verbose move objects should preserve `from`, `to`, `piece`, `captured`, `color`, and `flags` information.

## Rules with Ambiguity or Simplification Risk

- FEN side-to-move accepts `r`, `w`, or `b` in validation, but `load` normalizes any non-`b` value to red. The Python port should document and test whether it intentionally preserves this behavior.
- Draw handling is simplified: `in_draw` and `game_over` include a 120 half-move threshold, threefold repetition, and a limited `insufficient_material` heuristic.
- `insufficient_material` is explicitly marked `TODO: more cases` in xiangqi.js. The Python port should initially match this simplified behavior rather than expand it.
- Threefold repetition is implemented by undoing and replaying move history while comparing only the first two FEN fields. This is acceptable for parity, but later search code may want a faster hash-based tracker.
- Legal move filtering is based on whether the moving side's king is attacked after `make_move`. The flying-general rule is therefore enforced through rook/king line attack detection, not as a separate generator rule.
- `game_over` also checks whether the opponent king was captured (`kings[swap_color(turn)] === EMPTY`). Normal legal moves should not capture kings, but this branch exists in the reference and should be noted in tests.

## Proposed Python Module Mapping

- `constants.py`: colors, piece symbols, default FEN, offsets, square maps, move flags.
- `types.py`: `Color`, `PieceType`, `Piece`, `Square`, `MoveFlag`, and result/value dataclasses.
- `fen.py`: FEN validation, parsing, and serialization.
- `board.py`: mailbox board representation, square helpers, placement/removal, king tracking.
- `move.py`: internal and public move models, ICCS parsing/formatting.
- `history.py`: undo/redo snapshots.
- `movegen/pseudo_legal.py`: piece movement and pseudo-legal generation.
- `movegen/legal.py`: self-check filtering.
- `movegen/attack.py`: attack detection, especially knight, rook/cannon/king files, and pawns.
- `rules/check.py`: user-facing check helpers.
- `rules/terminal.py`: checkmate, stalemate, draw, and game-over helpers.
- `rules/repetition.py`: parity-first repetition logic.
- `game.py`: high-level facade for search algorithms and tests.

## Phase 1 Status

Completed:

- Scanned the reference implementation and identified public APIs, core mutable state, and rule hotspots.
- Created the requested Python project skeleton.
- Added a `vendor/xiangqi.js` compatibility symlink to the existing `vender/xiangqi.js` file.
- Added a minimal pytest import test so the skeleton remains importable while implementation proceeds.

Remaining:

- Implement constants, typed domain objects, FEN parsing/serialization, board representation, move model, and the first `Game` facade.
- Add parity runner and Node helper in a later phase.
- Add unit, parity, regression, and fixture coverage as rules are migrated.

Risks:

- The local reference is a single built JS file rather than the full repository, so package metadata and upstream tests are not available here.
- The workspace is not currently a Git repository, so phase-by-phase commits cannot be made until a repository is initialized or this work is copied into one.


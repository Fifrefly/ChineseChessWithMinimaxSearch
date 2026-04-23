"""Limited parity checks for terminal behavior against vendor/xiangqi.js."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from chinese_chess.game import Game

ROOT = Path(__file__).resolve().parents[2]
CHECKMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4p4/4K4 r - - 0 1"
STALEMATE_FEN = "3rkr3/9/9/9/9/9/9/9/4A4/4K4 r - - 0 1"
REPEAT_SEQUENCE = ["a0a1", "a9a8", "a1a0", "a8a9", "a0a1", "a9a8", "a1a0", "a8a9"]


def js_state(fen: str | None = None, moves: list[str] | None = None) -> dict[str, Any]:
    script = """
const { Xiangqi } = require('./vendor/xiangqi.js');
const fen = process.argv[1] === '__DEFAULT__' ? undefined : process.argv[1];
const moves = JSON.parse(process.argv[2]);
const game = fen === undefined ? new Xiangqi() : new Xiangqi(fen);
for (const move of moves) {
  const result = game.move(move);
  if (result === null) {
    throw new Error(`illegal JS move: ${move}`);
  }
}
console.log(JSON.stringify({
  fen: game.fen(),
  in_checkmate: game.in_checkmate(),
  in_stalemate: game.in_stalemate(),
  in_threefold_repetition: game.in_threefold_repetition(),
  game_over: game.game_over()
}));
"""
    completed = subprocess.run(
        ["node", "-e", script, "__DEFAULT__" if fen is None else fen, json.dumps(moves or [])],
        cwd=ROOT,
        text=True,
        check=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


def py_state(fen: str | None = None, moves: list[str] | None = None) -> dict[str, Any]:
    game = Game(fen)
    for move in moves or []:
        game.make_move(move)
    return {
        "fen": game.fen(),
        "in_checkmate": game.is_checkmate(),
        "in_stalemate": game.is_stalemate(),
        "in_threefold_repetition": game.is_threefold_repetition(),
        "game_over": game.game_over(),
    }


def test_default_position_terminal_parity() -> None:
    assert py_state() == js_state()


def test_checkmate_position_terminal_parity() -> None:
    assert py_state(CHECKMATE_FEN) == js_state(CHECKMATE_FEN)


def test_stalemate_position_terminal_parity() -> None:
    assert py_state(STALEMATE_FEN) == js_state(STALEMATE_FEN)


def test_threefold_repetition_terminal_parity() -> None:
    assert py_state(moves=REPEAT_SEQUENCE) == js_state(moves=REPEAT_SEQUENCE)

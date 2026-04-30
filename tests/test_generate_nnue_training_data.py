from __future__ import annotations

import csv
from pathlib import Path

from engine.core import Board
from experiments.generate_nnue_training_data import (
    FIELDNAMES,
    SOURCE_RANDOM_PLAYOUT,
    SOURCE_TACTICAL_CAPTURE,
    SOURCE_TACTICAL_CHECK,
    GenerationTask,
    classify_phase,
    generate_tactical_capture_candidate,
    generate_tactical_check_candidate,
    has_capture_move,
    has_checking_move,
    label_position,
    parse_args,
    worker_generate_row,
    write_training_data,
)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _task(source: str, seed: int = 123, min_plies: int = 8) -> GenerationTask:
    return GenerationTask(
        source=source,
        sample_index=0,
        seed=seed,
        min_plies=min_plies,
        max_plies=30,
        oracle_depth=0,
        oracle_evaluator="full_static",
        self_play_depth=1,
        self_play_evaluator="weighted_static",
        temperature=1.0,
        self_play_top_k=4,
        include_terminal=False,
    )


def test_generate_tiny_dataset_writes_csv_with_required_fields(tmp_path: Path) -> None:
    output = tmp_path / "nnue.csv"

    summary = write_training_data(
        output=str(output),
        random_positions=2,
        self_play_positions=2,
        tactical_capture_positions=2,
        tactical_check_positions=2,
        min_plies=8,
        max_plies=40,
        oracle_depth=0,
        self_play_depth=1,
        temperature=1.0,
        workers=2,
        chunk_size=1,
        progress_every=1,
        seed=7,
        max_attempts_multiplier=100,
    )

    rows = _read_csv_rows(output)
    assert summary.new_rows_written == 8
    assert len(rows) == 8
    assert list(rows[0].keys()) == FIELDNAMES
    assert {row["source"] for row in rows} == {
        "random_playout",
        "static_self_play",
        "tactical_capture",
        "tactical_check",
    }


def test_csv_values_are_typed_and_position_keys_are_unique(tmp_path: Path) -> None:
    output = tmp_path / "nnue_types.csv"

    write_training_data(
        output=str(output),
        random_positions=3,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        min_plies=0,
        max_plies=4,
        oracle_depth=0,
        workers=1,
        seed=1,
        max_attempts_multiplier=10,
    )

    rows = _read_csv_rows(output)
    assert rows
    assert all(isinstance(int(row["target_score"]), int) for row in rows)
    keys = [row["position_key"] for row in rows]
    assert len(keys) == len(set(keys))


def test_label_position_does_not_modify_board_fen() -> None:
    board = Board()
    original = board.fen()

    label = label_position(board, oracle_depth=1, oracle_evaluator_name="full_static")

    assert isinstance(label.target_score, int)
    assert board.fen() == original


def test_tactical_filters_do_not_modify_board_fen() -> None:
    capture_board = Board("r3k4/9/9/9/9/9/9/9/4A4/R3K4 r - - 0 1")
    capture_fen = capture_board.fen()
    check_board = Board("4k4/9/9/9/4P4/9/9/9/9/R3K4 r - - 0 1")
    check_fen = check_board.fen()

    assert has_capture_move(capture_board)
    assert capture_board.fen() == capture_fen
    assert has_checking_move(check_board)
    assert check_board.fen() == check_fen


def test_tactical_candidate_generation_does_not_modify_source_board() -> None:
    board = Board()
    original = board.fen()

    generate_tactical_capture_candidate(_task(SOURCE_TACTICAL_CAPTURE, seed=20))
    generate_tactical_check_candidate(_task(SOURCE_TACTICAL_CHECK, seed=30))

    assert board.fen() == original


def test_resume_does_not_duplicate_existing_position_keys(tmp_path: Path) -> None:
    output = tmp_path / "resume.csv"

    first = write_training_data(
        output=str(output),
        random_positions=2,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        min_plies=0,
        max_plies=4,
        oracle_depth=0,
        workers=1,
        seed=99,
        max_attempts_multiplier=20,
    )
    second = write_training_data(
        output=str(output),
        random_positions=4,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        min_plies=0,
        max_plies=4,
        oracle_depth=0,
        workers=1,
        seed=99,
        resume=True,
        max_attempts_multiplier=20,
    )

    rows = _read_csv_rows(output)
    keys = [row["position_key"] for row in rows]
    assert first.new_rows_written == 2
    assert second.new_rows_written == 2
    assert len(rows) == 4
    assert len(keys) == len(set(keys))


def test_classify_phase_basic_cases() -> None:
    assert classify_phase(Board(), ply_count=0) == "opening"
    assert classify_phase(Board(), ply_count=30) == "middlegame"
    assert (
        classify_phase(Board("4k4/9/9/9/9/9/9/9/9/4K4 r - - 0 1"), ply_count=80)
        == "endgame"
    )


def test_worker_ok_row_contains_required_fields() -> None:
    result = worker_generate_row(_task(SOURCE_RANDOM_PLAYOUT, min_plies=0))

    assert result["status"] == "ok"
    assert set(FIELDNAMES) <= set(result["row"])


def test_workers_argument_default_is_15() -> None:
    args = parse_args(["--output", "out.csv"])

    assert args.workers == 15

from __future__ import annotations

import csv
import json
from pathlib import Path

from engine.core import Board
import experiments.generate_nnue_training_data as gen
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


class _InlineProcessPoolExecutor:
    def __init__(self, max_workers: int) -> None:
        self.max_workers = max_workers

    def __enter__(self) -> "_InlineProcessPoolExecutor":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def map(self, func, iterable, chunksize: int = 1):
        for item in iterable:
            yield func(item)


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


def _csv_row(position_id: int, source: str, position_key: str) -> dict[str, str | int | bool]:
    return {
        "position_id": position_id,
        "fen": f"{position_key} r - - 0 1",
        "position_key": position_key,
        "side_to_move": "r",
        "phase": "opening",
        "source": source,
        "ply_count": 0,
        "legal_move_count": 1,
        "is_terminal": False,
        "target_score": 0,
        "oracle_depth": 0,
        "oracle_evaluator": "full_static",
        "oracle_best_move": "",
        "nodes_visited": 1,
        "leaf_nodes": 1,
        "cutoffs": 0,
        "elapsed_seconds": "0.000001",
    }


def _write_existing_rows(path: Path, rows: list[dict[str, str | int | bool]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def _fake_ok_result(task: GenerationTask, position_key: str | None = None) -> dict:
    key = position_key or f"key-{task.source}-{task.sample_index}"
    return {
        "status": "ok",
        "source": task.source,
        "sample_index": task.sample_index,
        "row": _csv_row("", task.source, key),
    }


def _patch_inline_generation(monkeypatch, worker) -> None:
    monkeypatch.setattr(gen, "ProcessPoolExecutor", _InlineProcessPoolExecutor)
    monkeypatch.setattr(gen, "worker_generate_row", worker)


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


def test_task_iter_uses_start_index() -> None:
    tasks = list(
        gen._task_iter(
            source=SOURCE_RANDOM_PLAYOUT,
            attempts=3,
            start_index=7,
            base_seed=5,
            min_plies=0,
            max_plies=1,
            oracle_depth=0,
            oracle_evaluator="full_static",
            self_play_depth=1,
            self_play_evaluator="weighted_static",
            temperature=0.0,
            self_play_top_k=4,
            include_terminal=False,
        )
    )

    assert [task.sample_index for task in tasks] == [7, 8, 9]
    assert tasks[0].seed == 5 + 7 * 1009 + gen.SOURCE_OFFSETS[SOURCE_RANDOM_PLAYOUT]


def test_non_resume_creates_checkpoint_from_zero(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "checkpoint_new.csv"
    calls: list[int] = []

    def worker(task: GenerationTask) -> dict:
        calls.append(task.sample_index)
        return _fake_ok_result(task)

    _patch_inline_generation(monkeypatch, worker)

    write_training_data(
        output=str(output),
        random_positions=2,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        oracle_depth=0,
        workers=2,
        progress_every=1,
    )

    checkpoint = json.loads(Path(f"{output}.checkpoint.json").read_text())
    assert calls == [0, 1]
    assert checkpoint["sources"][SOURCE_RANDOM_PLAYOUT]["next_sample_index"] == 2


def test_resume_uses_checkpoint_start_index(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "checkpoint_resume.csv"
    checkpoint_path = Path(f"{output}.checkpoint.json")
    _write_existing_rows(output, [_csv_row(0, SOURCE_RANDOM_PLAYOUT, "old")])
    checkpoint_path.write_text(
        json.dumps(
            {
                "version": 1,
                "output": str(output),
                "seed": 0,
                "parameters": {
                    "seed": 0,
                    "min_plies": 0,
                    "max_plies": 100,
                    "oracle_depth": 0,
                    "oracle_evaluator": "full_static",
                    "self_play_depth": 2,
                    "self_play_evaluator": "weighted_static",
                    "temperature": 0.0,
                    "self_play_top_k": 4,
                    "include_terminal": False,
                },
                "sources": {
                    source: {"next_sample_index": 0} for source in gen.SOURCE_ORDER
                },
            }
            | {"sources": {SOURCE_RANDOM_PLAYOUT: {"next_sample_index": 5}}},
        ),
        encoding="utf-8",
    )
    calls: list[int] = []

    def worker(task: GenerationTask) -> dict:
        calls.append(task.sample_index)
        return _fake_ok_result(task)

    _patch_inline_generation(monkeypatch, worker)

    write_training_data(
        output=str(output),
        random_positions=2,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        oracle_depth=0,
        workers=2,
        resume=True,
    )

    checkpoint = json.loads(checkpoint_path.read_text())
    assert calls == [5]
    assert checkpoint["sources"][SOURCE_RANDOM_PLAYOUT]["next_sample_index"] == 6


def test_resume_without_checkpoint_uses_existing_count_fallback(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    output = tmp_path / "checkpoint_missing.csv"
    _write_existing_rows(output, [_csv_row(0, SOURCE_RANDOM_PLAYOUT, "old")])
    calls: list[int] = []

    def worker(task: GenerationTask) -> dict:
        calls.append(task.sample_index)
        return _fake_ok_result(task)

    _patch_inline_generation(monkeypatch, worker)

    write_training_data(
        output=str(output),
        random_positions=2,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        oracle_depth=0,
        workers=2,
        resume=True,
    )

    assert calls == [1]
    assert "checkpoint file not found" in capsys.readouterr().out
    checkpoint = json.loads(Path(f"{output}.checkpoint.json").read_text())
    assert checkpoint["sources"][SOURCE_RANDOM_PLAYOUT]["next_sample_index"] == 2


def test_checkpoint_resume_still_deduplicates_position_keys(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "checkpoint_duplicate.csv"
    checkpoint_path = Path(f"{output}.checkpoint.json")
    _write_existing_rows(output, [_csv_row(0, SOURCE_RANDOM_PLAYOUT, "dup")])
    checkpoint_path.write_text(
        json.dumps(
            {
                "version": 1,
                "output": str(output),
                "seed": 0,
                "parameters": {},
                "sources": {
                    SOURCE_RANDOM_PLAYOUT: {"next_sample_index": 0},
                },
            }
        ),
        encoding="utf-8",
    )

    def worker(task: GenerationTask) -> dict:
        return _fake_ok_result(task, "dup" if task.sample_index == 0 else "new")

    _patch_inline_generation(monkeypatch, worker)

    summary = write_training_data(
        output=str(output),
        random_positions=2,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        oracle_depth=0,
        workers=2,
        resume=True,
        max_attempts_multiplier=3,
    )

    rows = _read_csv_rows(output)
    checkpoint = json.loads(checkpoint_path.read_text())
    assert summary.duplicate_skipped == 1
    assert [row["position_key"] for row in rows] == ["dup", "new"]
    assert checkpoint["sources"][SOURCE_RANDOM_PLAYOUT]["next_sample_index"] == 2


def test_skipped_and_error_results_advance_checkpoint(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "checkpoint_skips.csv"

    def worker(task: GenerationTask) -> dict:
        if task.sample_index == 0:
            return {
                "status": "terminal_skipped",
                "source": task.source,
                "sample_index": task.sample_index,
            }
        if task.sample_index == 1:
            return {
                "status": "no_candidate",
                "source": task.source,
                "sample_index": task.sample_index,
            }
        if task.sample_index == 2:
            return {
                "status": "error",
                "source": task.source,
                "sample_index": task.sample_index,
                "error": "synthetic",
            }
        return _fake_ok_result(task)

    _patch_inline_generation(monkeypatch, worker)

    summary = write_training_data(
        output=str(output),
        random_positions=1,
        self_play_positions=0,
        tactical_capture_positions=0,
        tactical_check_positions=0,
        oracle_depth=0,
        workers=2,
        max_attempts_multiplier=4,
        max_errors=5,
    )

    checkpoint = json.loads(Path(f"{output}.checkpoint.json").read_text())
    assert summary.terminal_skipped == 1
    assert summary.no_candidate == 1
    assert summary.error_count == 1
    assert checkpoint["sources"][SOURCE_RANDOM_PLAYOUT]["next_sample_index"] == 4


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

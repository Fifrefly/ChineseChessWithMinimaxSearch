"""Smoke tests for experiment scripts."""

from __future__ import annotations

import csv
from pathlib import Path

from engine.core import Board
from experiments.analyze_benchmark import analyze
from experiments.evaluation_benchmark import FIELDNAMES as BENCHMARK_FIELDS
from experiments.evaluation_benchmark import run_benchmark
from experiments.self_play_tournament import FIELDNAMES as SELF_PLAY_FIELDS
from experiments.self_play_tournament import run_tournament


def test_evaluation_benchmark_runs_on_tiny_csv(tmp_path: Path) -> None:
    positions = tmp_path / "positions.csv"
    output = tmp_path / "benchmark.csv"
    board = Board()
    original_fen = board.fen()
    with positions.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["fen"])
        writer.writeheader()
        writer.writerow({"fen": original_fen})

    rows_written, skipped = run_benchmark(
        positions=str(positions),
        output=str(output),
        evaluator_names=["material", "full_static"],
        search_depth=1,
        oracle_depth=1,
        oracle_evaluator_name="full_static",
    )

    assert skipped == 0
    assert rows_written == 2
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    assert set(BENCHMARK_FIELDS).issubset(rows[0])
    assert "candidate_oracle_score" in rows[0]
    assert "oracle_regret" in rows[0]
    assert "abs_oracle_regret" in rows[0]
    assert "move_matches_oracle" in rows[0]
    assert {row["evaluator"] for row in rows} == {"material", "full_static"}
    assert board.fen() == original_fen


def test_self_play_tournament_writes_expected_fields(tmp_path: Path) -> None:
    output = tmp_path / "self_play.csv"

    rows = run_tournament(
        output=str(output),
        evaluator_names=["material", "full_static"],
        games_per_pair=1,
        depth=1,
        max_plies=4,
        seed=123,
        adjudicate_max_plies=True,
        adjudicator_evaluator="full_static",
        adjudication_threshold=200,
    )

    assert len(rows) == 2
    with output.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 2
    assert set(SELF_PLAY_FIELDS).issubset(csv_rows[0])
    assert "adjudicate_max_plies" in csv_rows[0]
    assert "adjudicator_evaluator" in csv_rows[0]
    assert "adjudication_threshold" in csv_rows[0]
    assert "final_adjudication_score" in csv_rows[0]
    assert csv_rows[0]["winner"] in {"RED", "BLACK", "DRAW"}


def test_analyze_benchmark_generates_markdown_and_summary_csv(
    tmp_path: Path,
) -> None:
    benchmark = tmp_path / "benchmark.csv"
    self_play = tmp_path / "self_play.csv"
    report = tmp_path / "summary.md"
    summary_csv = tmp_path / "summary.csv"
    worst_cases = tmp_path / "worst_cases.csv"

    with benchmark.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BENCHMARK_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "position_id": 0,
                "fen": Board().fen(),
                "side_to_move": "r",
                "evaluator": "material",
                "static_score": 0,
                "search_depth": 1,
                "search_score": 10,
                "best_move": "a0a1",
                "nodes_visited": 2,
                "leaf_nodes": 1,
                "cutoffs": 0,
                "elapsed_seconds": 0.01,
                "oracle_evaluator": "full_static",
                "oracle_depth": 2,
                "oracle_score": 12,
                "oracle_best_move": "a0a1",
                "candidate_oracle_score": 12,
                "oracle_regret": 0,
                "abs_oracle_regret": 0,
                "score_error": -2,
                "abs_score_error": 2,
                "move_matches_oracle": True,
            }
        )
        writer.writerow(
            {
                "position_id": 1,
                "fen": Board().fen(),
                "side_to_move": "b",
                "evaluator": "material",
                "static_score": -50,
                "search_depth": 1,
                "search_score": -10,
                "best_move": "b0b1",
                "nodes_visited": 3,
                "leaf_nodes": 2,
                "cutoffs": 0,
                "elapsed_seconds": 0.02,
                "oracle_evaluator": "full_static",
                "oracle_depth": 2,
                "oracle_score": 20,
                "oracle_best_move": "c0c1",
                "candidate_oracle_score": 5,
                "oracle_regret": 15,
                "abs_oracle_regret": 15,
                "score_error": -30,
                "abs_score_error": 30,
                "move_matches_oracle": False,
            }
        )

    with self_play.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SELF_PLAY_FIELDS)
        writer.writeheader()
        writer.writerow(
            {
                "game_id": 0,
                "red_evaluator": "material",
                "black_evaluator": "full_static",
                "winner": "RED",
                "result_reason": "checkmate",
                "plies": 12,
                "final_fen": Board().fen(),
                "red_total_time": 0.1,
                "black_total_time": 0.2,
                "red_avg_nodes": 3,
                "black_avg_nodes": 4,
                "red_total_nodes": 30,
                "black_total_nodes": 40,
                "red_total_cutoffs": 1,
                "black_total_cutoffs": 2,
                "red_moves": 10,
                "black_moves": 10,
                "depth": 1,
                "max_plies": 20,
                "opening_random_plies": 0,
                "adjudicate_max_plies": True,
                "adjudicator_evaluator": "full_static",
                "adjudication_threshold": 200,
                "final_adjudication_score": 250,
                "seed": 0,
            }
        )

    markdown = analyze(
        benchmark=str(benchmark),
        self_play=str(self_play),
        output_report=str(report),
        output_summary_csv=str(summary_csv),
        output_worst_cases=str(worst_cases),
        worst_cases_per_evaluator=1,
    )

    assert report.exists()
    assert summary_csv.exists()
    assert worst_cases.exists()
    assert "# Experiment Summary" in markdown
    assert "mean_abs_oracle_regret" in markdown
    assert "p90_abs_oracle_regret" in markdown
    assert "max_abs_oracle_regret" in markdown
    assert "Worst Regret Cases" in markdown
    assert "material" in report.read_text(encoding="utf-8")
    with worst_cases.open(newline="", encoding="utf-8") as handle:
        worst_rows = list(csv.DictReader(handle))
    assert len(worst_rows) == 1
    assert worst_rows[0]["position_id"] == "1"
    with summary_csv.open(newline="", encoding="utf-8") as handle:
        summary_rows = list(csv.DictReader(handle))
        summary_fields = summary_rows[0].keys()
    assert "red_wins" in summary_fields
    assert "black_losses" in summary_fields
    assert "red_win_rate" in summary_fields
    assert "black_win_rate" in summary_fields

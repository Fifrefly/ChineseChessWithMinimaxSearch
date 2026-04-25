"""Summarize benchmark and self-play CSV outputs."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
import math
import statistics

BENCHMARK_SUMMARY_FIELDS = [
    "rows",
    "mean_abs_oracle_regret",
    "median_abs_oracle_regret",
    "oracle_regret_rmse",
    "zero_regret_rate",
    "mean_abs_score_error",
    "median_abs_score_error",
    "root_mean_squared_error",
    "move_match_rate",
    "avg_nodes_visited",
    "avg_leaf_nodes",
    "avg_cutoffs",
    "avg_elapsed_seconds",
]

SELF_PLAY_SUMMARY_FIELDS = [
    "games_as_red",
    "games_as_black",
    "wins",
    "losses",
    "draws",
    "adjudicated_wins",
    "adjudicated_losses",
    "adjudicated_draws",
    "win_rate",
    "non_draw_win_rate",
    "avg_game_plies",
    "avg_nodes_per_move",
    "avg_time_per_game",
]

SUMMARY_FIELDNAMES = [
    "source",
    "evaluator",
    *BENCHMARK_SUMMARY_FIELDS,
    *SELF_PLAY_SUMMARY_FIELDS,
]


def _read_csv(path: str) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key)
    if value in (None, ""):
        return default
    return float(value)


def _int(row: dict[str, str], key: str, default: int = 0) -> int:
    value = row.get(key)
    if value in (None, ""):
        return default
    return int(float(value))


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def summarize_benchmark(path: str) -> tuple[dict[str, dict[str, float]], dict[str, str]]:
    rows = _read_csv(path)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["evaluator"]].append(row)

    summary: dict[str, dict[str, float]] = {}
    for evaluator, evaluator_rows in grouped.items():
        abs_errors = [_float(row, "abs_score_error") for row in evaluator_rows]
        score_errors = [_float(row, "score_error") for row in evaluator_rows]
        regret_rows = [
            row
            for row in evaluator_rows
            if row.get("oracle_regret") not in (None, "")
        ]
        abs_oracle_regrets = [
            _float(row, "abs_oracle_regret") for row in regret_rows
        ]
        oracle_regrets = [_float(row, "oracle_regret") for row in regret_rows]
        zero_regrets = [
            1.0 if _float(row, "oracle_regret") == 0.0 else 0.0
            for row in regret_rows
        ]
        move_matches = [
            1.0 if row.get("move_matches_oracle") == "True" else 0.0
            for row in evaluator_rows
        ]
        summary[evaluator] = {
            "rows": float(len(evaluator_rows)),
            "mean_abs_oracle_regret": _mean(abs_oracle_regrets),
            "median_abs_oracle_regret": statistics.median(abs_oracle_regrets)
            if abs_oracle_regrets
            else 0.0,
            "oracle_regret_rmse": math.sqrt(
                _mean([regret * regret for regret in oracle_regrets])
            ),
            "zero_regret_rate": _mean(zero_regrets),
            "mean_abs_score_error": _mean(abs_errors),
            "median_abs_score_error": statistics.median(abs_errors)
            if abs_errors
            else 0.0,
            "root_mean_squared_error": math.sqrt(
                _mean([error * error for error in score_errors])
            ),
            "move_match_rate": _mean(move_matches),
            "avg_nodes_visited": _mean(
                [_float(row, "nodes_visited") for row in evaluator_rows]
            ),
            "avg_leaf_nodes": _mean(
                [_float(row, "leaf_nodes") for row in evaluator_rows]
            ),
            "avg_cutoffs": _mean([_float(row, "cutoffs") for row in evaluator_rows]),
            "avg_elapsed_seconds": _mean(
                [_float(row, "elapsed_seconds") for row in evaluator_rows]
            ),
        }

    settings = {}
    if rows:
        first = rows[0]
        settings = {
            "search_depth": first.get("search_depth", ""),
            "oracle_depth": first.get("oracle_depth", ""),
            "oracle_evaluator": first.get("oracle_evaluator", ""),
        }
    return summary, settings


def _ensure_self_play_record(
    summary: dict[str, dict[str, float]],
    evaluator: str,
) -> dict[str, float]:
    if evaluator not in summary:
        summary[evaluator] = {
            "games_as_red": 0.0,
            "games_as_black": 0.0,
            "wins": 0.0,
            "losses": 0.0,
            "draws": 0.0,
            "adjudicated_wins": 0.0,
            "adjudicated_losses": 0.0,
            "adjudicated_draws": 0.0,
            "game_plies_total": 0.0,
            "game_count": 0.0,
            "nodes_total": 0.0,
            "move_count": 0.0,
            "time_total": 0.0,
        }
    return summary[evaluator]


def _add_self_play_side(
    summary: dict[str, dict[str, float]],
    row: dict[str, str],
    evaluator: str,
    side: str,
) -> None:
    record = _ensure_self_play_record(summary, evaluator)
    record["game_count"] += 1
    record["game_plies_total"] += _float(row, "plies")
    if side == "red":
        record["games_as_red"] += 1
        record["nodes_total"] += _float(row, "red_total_nodes")
        record["move_count"] += _float(row, "red_moves")
        record["time_total"] += _float(row, "red_total_time")
    else:
        record["games_as_black"] += 1
        record["nodes_total"] += _float(row, "black_total_nodes")
        record["move_count"] += _float(row, "black_moves")
        record["time_total"] += _float(row, "black_total_time")


def summarize_self_play(path: str) -> dict[str, dict[str, float]]:
    rows = _read_csv(path)
    working: dict[str, dict[str, float]] = {}
    for row in rows:
        red = row["red_evaluator"]
        black = row["black_evaluator"]
        _add_self_play_side(working, row, red, "red")
        _add_self_play_side(working, row, black, "black")

        winner = row.get("winner")
        reason = row.get("result_reason", "")
        red_record = _ensure_self_play_record(working, red)
        black_record = _ensure_self_play_record(working, black)
        if winner == "RED":
            red_record["wins"] += 1
            black_record["losses"] += 1
            if reason == "max_plies_adjudicated_red":
                red_record["adjudicated_wins"] += 1
                black_record["adjudicated_losses"] += 1
        elif winner == "BLACK":
            black_record["wins"] += 1
            red_record["losses"] += 1
            if reason == "max_plies_adjudicated_black":
                black_record["adjudicated_wins"] += 1
                red_record["adjudicated_losses"] += 1
        else:
            red_record["draws"] += 1
            black_record["draws"] += 1
            if reason == "max_plies_adjudicated_draw":
                red_record["adjudicated_draws"] += 1
                black_record["adjudicated_draws"] += 1

    summary: dict[str, dict[str, float]] = {}
    for evaluator, record in working.items():
        games = record["wins"] + record["losses"] + record["draws"]
        decisive = record["wins"] + record["losses"]
        summary[evaluator] = {
            "games_as_red": record["games_as_red"],
            "games_as_black": record["games_as_black"],
            "wins": record["wins"],
            "losses": record["losses"],
            "draws": record["draws"],
            "adjudicated_wins": record["adjudicated_wins"],
            "adjudicated_losses": record["adjudicated_losses"],
            "adjudicated_draws": record["adjudicated_draws"],
            "win_rate": record["wins"] / games if games else 0.0,
            "non_draw_win_rate": record["wins"] / decisive if decisive else 0.0,
            "avg_game_plies": record["game_plies_total"] / record["game_count"]
            if record["game_count"]
            else 0.0,
            "avg_nodes_per_move": record["nodes_total"] / record["move_count"]
            if record["move_count"]
            else 0.0,
            "avg_time_per_game": record["time_total"] / record["game_count"]
            if record["game_count"]
            else 0.0,
        }
    return summary


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def _benchmark_table(summary: dict[str, dict[str, float]]) -> list[str]:
    lines = [
        "| evaluator | mean_abs_oracle_regret | oracle_regret_rmse | zero_regret_rate | move_match_rate | mean_abs_score_error | avg_nodes | avg_time |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for evaluator in sorted(summary):
        row = summary[evaluator]
        lines.append(
            f"| {evaluator} | {_fmt(row['mean_abs_oracle_regret'])} | "
            f"{_fmt(row['oracle_regret_rmse'])} | "
            f"{_fmt(row['zero_regret_rate'])} | "
            f"{_fmt(row['move_match_rate'])} | "
            f"{_fmt(row['mean_abs_score_error'])} | "
            f"{_fmt(row['avg_nodes_visited'])} | "
            f"{_fmt(row['avg_elapsed_seconds'])} |"
        )
    return lines


def _self_play_table(summary: dict[str, dict[str, float]]) -> list[str]:
    lines = [
        "| evaluator | wins | losses | draws | adjudicated_wins | adjudicated_losses | adjudicated_draws | win_rate | avg_game_plies |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for evaluator in sorted(summary):
        row = summary[evaluator]
        lines.append(
            f"| {evaluator} | {int(row['wins'])} | {int(row['losses'])} | "
            f"{int(row['draws'])} | {int(row['adjudicated_wins'])} | "
            f"{int(row['adjudicated_losses'])} | "
            f"{int(row['adjudicated_draws'])} | {_fmt(row['win_rate'])} | "
            f"{_fmt(row['avg_game_plies'])} |"
        )
    return lines


def _best_by(
    summary: dict[str, dict[str, float]],
    metric: str,
    reverse: bool = False,
) -> str | None:
    if not summary:
        return None
    return sorted(summary, key=lambda name: summary[name][metric], reverse=reverse)[0]


def _best_names_by(
    summary: dict[str, dict[str, float]],
    metric: str,
    reverse: bool = False,
) -> list[str]:
    if not summary:
        return []
    target = (
        max(row[metric] for row in summary.values())
        if reverse
        else min(row[metric] for row in summary.values())
    )
    return [
        name
        for name in sorted(summary)
        if math.isclose(summary[name][metric], target, rel_tol=1e-9, abs_tol=1e-9)
    ]


def _mlp_comparison(summary: dict[str, dict[str, float]]) -> list[str]:
    if "mlp" not in summary:
        return []
    lines = []
    mlp_regret = summary["mlp"]["mean_abs_oracle_regret"]
    for baseline in ("full_static", "weighted_static"):
        if baseline in summary:
            delta = mlp_regret - summary[baseline]["mean_abs_oracle_regret"]
            relation = "lower" if delta < 0 else "higher"
            lines.append(
                f"MLP mean_abs_oracle_regret is {abs(delta):.4f} "
                f"{relation} than {baseline}."
            )
    return lines


def _verb_for(names: list[str]) -> str:
    return "has" if len(names) == 1 else "have"


def build_markdown_report(
    benchmark_summary: dict[str, dict[str, float]] | None,
    benchmark_settings: dict[str, str] | None,
    self_play_summary: dict[str, dict[str, float]] | None,
) -> str:
    lines = ["# Experiment Summary", ""]
    lines.append("## Benchmark Settings")
    if benchmark_settings:
        lines.extend(
            [
                f"- search_depth: {benchmark_settings.get('search_depth', '')}",
                f"- oracle_depth: {benchmark_settings.get('oracle_depth', '')}",
                f"- oracle_evaluator: {benchmark_settings.get('oracle_evaluator', '')}",
            ]
        )
    else:
        lines.append("- benchmark CSV not provided")
    lines.append("")

    lines.append("## Evaluator Accuracy vs Oracle")
    if benchmark_summary:
        lines.extend(_benchmark_table(benchmark_summary))
    else:
        lines.append("Benchmark data was not provided.")
    lines.append("")

    lines.append("## Self-Play Tournament")
    if self_play_summary:
        lines.extend(_self_play_table(self_play_summary))
    else:
        lines.append("Self-play data was not provided.")
    lines.append("")

    lines.append("## Initial Interpretation")
    interpretation: list[str] = []
    if benchmark_summary:
        best_regret = _best_names_by(benchmark_summary, "mean_abs_oracle_regret")
        best_match = _best_names_by(
            benchmark_summary, "move_match_rate", reverse=True
        )
        if best_regret:
            interpretation.append(
                f"{', '.join(best_regret)} {_verb_for(best_regret)} "
                "the lowest mean_abs_oracle_regret "
                "in this run."
            )
        if best_match:
            interpretation.append(
                f"{', '.join(best_match)} {_verb_for(best_match)} "
                "the highest move_match_rate "
                "in this run."
            )
        interpretation.extend(_mlp_comparison(benchmark_summary))
    if self_play_summary:
        best_self_play = _best_names_by(self_play_summary, "win_rate", reverse=True)
        if best_self_play:
            interpretation.append(
                f"{', '.join(best_self_play)} {_verb_for(best_self_play)} "
                "the highest self-play win_rate "
                "in this run."
            )
    interpretation.append(
        "If the sample is small, treat this as a smoke test rather than a final "
        "playing-strength conclusion."
    )
    lines.extend(f"- {item}" for item in interpretation)
    lines.append("")
    return "\n".join(lines)


def _summary_rows(
    benchmark_summary: dict[str, dict[str, float]] | None,
    self_play_summary: dict[str, dict[str, float]] | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if benchmark_summary:
        for evaluator, summary in sorted(benchmark_summary.items()):
            row = {field: "" for field in SUMMARY_FIELDNAMES}
            row["source"] = "benchmark"
            row["evaluator"] = evaluator
            row.update(summary)
            rows.append(row)
    if self_play_summary:
        for evaluator, summary in sorted(self_play_summary.items()):
            row = {field: "" for field in SUMMARY_FIELDNAMES}
            row["source"] = "self_play"
            row["evaluator"] = evaluator
            row.update(summary)
            rows.append(row)
    return rows


def write_summary_csv(
    path: str,
    benchmark_summary: dict[str, dict[str, float]] | None,
    self_play_summary: dict[str, dict[str, float]] | None,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDNAMES)
        writer.writeheader()
        writer.writerows(_summary_rows(benchmark_summary, self_play_summary))


def analyze(
    benchmark: str | None = None,
    self_play: str | None = None,
    output_report: str = "data/experiment_summary.md",
    output_summary_csv: str = "data/experiment_summary.csv",
) -> str:
    benchmark_summary = None
    benchmark_settings = None
    self_play_summary = None
    if benchmark is not None:
        benchmark_summary, benchmark_settings = summarize_benchmark(benchmark)
    if self_play is not None:
        self_play_summary = summarize_self_play(self_play)

    report = build_markdown_report(
        benchmark_summary,
        benchmark_settings,
        self_play_summary,
    )

    report_path = Path(output_report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    write_summary_csv(output_summary_csv, benchmark_summary, self_play_summary)
    print(f"Wrote report to {output_report}")
    print(f"Wrote summary CSV to {output_summary_csv}")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark")
    parser.add_argument("--self-play")
    parser.add_argument("--output-report", default="data/experiment_summary.md")
    parser.add_argument("--output-summary-csv", default="data/experiment_summary.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analyze(
        benchmark=args.benchmark,
        self_play=args.self_play,
        output_report=args.output_report,
        output_summary_csv=args.output_summary_csv,
    )


if __name__ == "__main__":
    main()

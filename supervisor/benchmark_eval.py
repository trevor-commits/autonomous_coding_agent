from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence


DEFAULT_COMPLEX_RUN_IDS = ("benchmark-002", "benchmark-003")


@dataclass(frozen=True)
class BenchmarkRunGrade:
    run_id: str
    strategy_name: str
    run_state: str
    readiness_verdict: str | None
    builder_turns: int
    run_duration_seconds: float
    total_cost_dollars: float
    queue_exit_reason: str | None
    unresolved_blockers: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.run_state == "COMPLETE" and self.readiness_verdict == "READY"

    @property
    def review_caught_issue(self) -> bool:
        return (self.queue_exit_reason or "") in {
            "blocked by strategy review",
            "blocked by final gate",
        }


@dataclass(frozen=True)
class StrategyBenchmarkSummary:
    strategy_name: str
    total_runs: int
    ready_runs: int
    complex_runs: int
    complex_ready_runs: int
    average_iterations: float
    average_cost_dollars: float
    average_time_seconds: float
    review_catch_rate: float


@dataclass(frozen=True)
class BenchmarkComparison:
    strategies: tuple[StrategyBenchmarkSummary, ...]
    claude_only_wins: tuple[str, ...]
    simple_only_wins: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["strategies"] = [asdict(strategy) for strategy in self.strategies]
        return payload


def load_benchmark_grade(report_path: Path | str) -> BenchmarkRunGrade:
    payload = json.loads(Path(report_path).read_text())
    return BenchmarkRunGrade(
        run_id=str(payload["run_id"]),
        strategy_name=str(payload.get("strategy_name", "unknown")),
        run_state=str(payload["run_state"]),
        readiness_verdict=payload.get("readiness_verdict"),
        builder_turns=int(payload.get("builder_turns", 0)),
        run_duration_seconds=float(payload.get("run_duration_seconds", 0.0)),
        total_cost_dollars=float(payload.get("total_cost_dollars", 0.0)),
        queue_exit_reason=payload.get("queue_exit_reason"),
        unresolved_blockers=tuple(payload.get("unresolved_blockers", ())),
    )


def compare_benchmark_reports(
    report_paths: Sequence[Path | str],
    *,
    complex_run_ids: Sequence[str] = DEFAULT_COMPLEX_RUN_IDS,
) -> BenchmarkComparison:
    grades = [load_benchmark_grade(path) for path in report_paths]
    grouped: dict[str, list[BenchmarkRunGrade]] = {}
    for grade in grades:
        grouped.setdefault(grade.strategy_name, []).append(grade)

    summaries = tuple(
        _build_summary(strategy_name, grouped[strategy_name], complex_run_ids=complex_run_ids)
        for strategy_name in sorted(grouped)
    )
    paired = _pair_by_run_id(grades)
    claude_only_wins = tuple(
        sorted(
            run_id
            for run_id, pair in paired.items()
            if pair.get("claude") and pair.get("claude").ready
            and pair.get("simple") and not pair.get("simple").ready
        )
    )
    simple_only_wins = tuple(
        sorted(
            run_id
            for run_id, pair in paired.items()
            if pair.get("simple") and pair.get("simple").ready
            and pair.get("claude") and not pair.get("claude").ready
        )
    )
    return BenchmarkComparison(
        strategies=summaries,
        claude_only_wins=claude_only_wins,
        simple_only_wins=simple_only_wins,
    )


def render_markdown(comparison: BenchmarkComparison) -> str:
    lines = [
        "# Benchmark Comparison",
        "",
        "| Metric | " + " | ".join(strategy.strategy_name for strategy in comparison.strategies) + " |",
        "|---|" + "|".join("---" for _ in comparison.strategies) + "|",
        "| Completion rate | "
        + " | ".join(_percent(strategy.ready_runs, strategy.total_runs) for strategy in comparison.strategies)
        + " |",
        "| Complex-task completion | "
        + " | ".join(
            _percent(strategy.complex_ready_runs, strategy.complex_runs) for strategy in comparison.strategies
        )
        + " |",
        "| Average iterations | "
        + " | ".join(f"{strategy.average_iterations:.2f}" for strategy in comparison.strategies)
        + " |",
        "| Average cost ($) | "
        + " | ".join(f"{strategy.average_cost_dollars:.6f}" for strategy in comparison.strategies)
        + " |",
        "| Average time (s) | "
        + " | ".join(f"{strategy.average_time_seconds:.2f}" for strategy in comparison.strategies)
        + " |",
        "| Review catch rate | "
        + " | ".join(f"{strategy.review_catch_rate:.2%}" for strategy in comparison.strategies)
        + " |",
        "",
        f"- Claude-only wins: {', '.join(comparison.claude_only_wins) or 'none'}",
        f"- Simple-only wins: {', '.join(comparison.simple_only_wins) or 'none'}",
        "",
    ]
    return "\n".join(lines)


def _build_summary(
    strategy_name: str,
    grades: Sequence[BenchmarkRunGrade],
    *,
    complex_run_ids: Sequence[str],
) -> StrategyBenchmarkSummary:
    complex_set = set(complex_run_ids)
    ready_runs = [grade for grade in grades if grade.ready]
    complex_runs = [grade for grade in grades if grade.run_id in complex_set]
    complex_ready_runs = [grade for grade in complex_runs if grade.ready]
    return StrategyBenchmarkSummary(
        strategy_name=strategy_name,
        total_runs=len(grades),
        ready_runs=len(ready_runs),
        complex_runs=len(complex_runs),
        complex_ready_runs=len(complex_ready_runs),
        average_iterations=_average(grade.builder_turns for grade in grades),
        average_cost_dollars=_average(grade.total_cost_dollars for grade in grades),
        average_time_seconds=_average(grade.run_duration_seconds for grade in grades),
        review_catch_rate=_rate(sum(1 for grade in grades if grade.review_caught_issue), len(grades)),
    )


def _pair_by_run_id(grades: Sequence[BenchmarkRunGrade]) -> dict[str, dict[str, BenchmarkRunGrade]]:
    pairs: dict[str, dict[str, BenchmarkRunGrade]] = {}
    for grade in grades:
        pairs.setdefault(grade.run_id, {})[grade.strategy_name] = grade
    return pairs


def _average(values: Iterable[float]) -> float:
    materialized = tuple(values)
    if not materialized:
        return 0.0
    return float(mean(materialized))


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _percent(numerator: int, denominator: int) -> str:
    return f"{_rate(numerator, denominator):.0%}"


def _collect_report_paths(report_paths: Sequence[str], report_dirs: Sequence[str]) -> list[Path]:
    collected = [Path(path) for path in report_paths]
    for directory in report_dirs:
        collected.extend(sorted(Path(directory).rglob("final-report.json")))
    return collected


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare supervisor benchmark reports by strategy.")
    parser.add_argument("--report", action="append", default=[], help="Path to a final-report.json file.")
    parser.add_argument(
        "--report-dir",
        action="append",
        default=[],
        help="Directory to scan recursively for final-report.json files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    args = parser.parse_args(argv)

    report_paths = _collect_report_paths(args.report, args.report_dir)
    if not report_paths:
        parser.error("Provide at least one --report or --report-dir.")

    comparison = compare_benchmark_reports(report_paths)
    if args.json:
        print(json.dumps(comparison.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_markdown(comparison))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

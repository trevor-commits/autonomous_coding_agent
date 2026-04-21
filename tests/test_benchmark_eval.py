import json
import tempfile
import unittest
from pathlib import Path

from supervisor.benchmark_eval import compare_benchmark_reports, load_benchmark_grade, render_markdown


def _write_report(root: Path, name: str, payload: dict) -> Path:
    path = root / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class BenchmarkEvalTests(unittest.TestCase):
    def test_load_benchmark_grade_tolerates_historical_reports_without_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = _write_report(
                Path(tmpdir),
                "final-report.json",
                {
                    "run_id": "benchmark-001",
                    "claim_id": "claim-1",
                    "run_trace_id": "trace-1",
                    "run_state": "COMPLETE",
                    "readiness_verdict": "READY",
                    "phases_completed": ["INTAKE", "BUILD", "FINAL_GATE"],
                    "commands_run": [],
                    "failures": [],
                    "changed_files": [],
                    "artifact_manifest": [],
                    "unresolved_blockers": [],
                    "queue_entry_reason": "manual",
                    "queue_exit_reason": "final gate ready",
                },
            )

            grade = load_benchmark_grade(report_path)

            self.assertEqual("unknown", grade.strategy_name)
            self.assertEqual(0, grade.builder_turns)
            self.assertEqual(0.0, grade.run_duration_seconds)
            self.assertEqual(0.0, grade.total_cost_dollars)

    def test_compare_benchmark_reports_calculates_strategy_summary_and_wins(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            simple_one = _write_report(
                root,
                "simple-001.json",
                {
                    "run_id": "benchmark-001",
                    "claim_id": "claim-1",
                    "run_trace_id": "trace-simple-1",
                    "strategy_name": "simple",
                    "run_state": "COMPLETE",
                    "readiness_verdict": "READY",
                    "builder_turns": 2,
                    "run_duration_seconds": 20.0,
                    "total_cost_dollars": 0.0,
                    "phases_completed": ["INTAKE", "BUILD", "FINAL_GATE"],
                    "commands_run": [],
                    "failures": [],
                    "changed_files": [],
                    "artifact_manifest": [],
                    "unresolved_blockers": [],
                    "queue_entry_reason": "manual",
                    "queue_exit_reason": "final gate ready",
                },
            )
            simple_two = _write_report(
                root,
                "simple-002.json",
                {
                    "run_id": "benchmark-002",
                    "claim_id": "claim-2",
                    "run_trace_id": "trace-simple-2",
                    "strategy_name": "simple",
                    "run_state": "BLOCKED",
                    "readiness_verdict": "NOT_READY",
                    "builder_turns": 4,
                    "run_duration_seconds": 50.0,
                    "total_cost_dollars": 0.0,
                    "phases_completed": ["INTAKE", "BUILD", "AUDIT_READY", "FINAL_GATE"],
                    "commands_run": [],
                    "failures": ["lint-failed"],
                    "changed_files": [],
                    "artifact_manifest": [],
                    "unresolved_blockers": ["final audit finding"],
                    "queue_entry_reason": "manual",
                    "queue_exit_reason": "blocked by final gate",
                },
            )
            claude_one = _write_report(
                root,
                "claude-001.json",
                {
                    "run_id": "benchmark-001",
                    "claim_id": "claim-3",
                    "run_trace_id": "trace-claude-1",
                    "strategy_name": "claude",
                    "run_state": "COMPLETE",
                    "readiness_verdict": "READY",
                    "builder_turns": 1,
                    "run_duration_seconds": 15.0,
                    "total_cost_dollars": 0.11,
                    "phases_completed": ["INTAKE", "BUILD", "FINAL_GATE"],
                    "commands_run": [],
                    "failures": [],
                    "changed_files": [],
                    "artifact_manifest": [],
                    "unresolved_blockers": [],
                    "queue_entry_reason": "manual",
                    "queue_exit_reason": "final gate ready",
                },
            )
            claude_two = _write_report(
                root,
                "claude-002.json",
                {
                    "run_id": "benchmark-002",
                    "claim_id": "claim-4",
                    "run_trace_id": "trace-claude-2",
                    "strategy_name": "claude",
                    "run_state": "COMPLETE",
                    "readiness_verdict": "READY",
                    "builder_turns": 3,
                    "run_duration_seconds": 42.0,
                    "total_cost_dollars": 0.22,
                    "phases_completed": ["INTAKE", "BUILD", "AUDIT_READY", "FINAL_GATE"],
                    "commands_run": [],
                    "failures": [],
                    "changed_files": [],
                    "artifact_manifest": [],
                    "unresolved_blockers": [],
                    "queue_entry_reason": "manual",
                    "queue_exit_reason": "final gate ready",
                },
            )

            comparison = compare_benchmark_reports((simple_one, simple_two, claude_one, claude_two))

            self.assertEqual(("benchmark-002",), comparison.claude_only_wins)
            self.assertEqual((), comparison.simple_only_wins)
            self.assertEqual(("claude", "simple"), tuple(row.strategy_name for row in comparison.strategies))
            claude_summary = comparison.strategies[0]
            simple_summary = comparison.strategies[1]
            self.assertEqual(0.0, claude_summary.review_catch_rate)
            self.assertEqual(0.5, simple_summary.review_catch_rate)
            self.assertEqual(1.0, claude_summary.complex_ready_runs / claude_summary.complex_runs)
            self.assertEqual(0.0, simple_summary.complex_ready_runs / simple_summary.complex_runs)
            self.assertEqual(0.165, claude_summary.average_cost_dollars)

            markdown = render_markdown(comparison)

            self.assertIn("| Completion rate | 100% | 50% |", markdown)
            self.assertIn("Claude-only wins: benchmark-002", markdown)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from supervisor.contracts import (
    QueueMetadata,
    RunAcceptance,
    RunConstraints,
    RunContract,
    RunScope,
)
from supervisor.models import Phase, ReadinessVerdict
from supervisor.reports import build_readiness_report, write_readiness_reports
from supervisor.run_store import RunStore
from supervisor.state_machine import StateMachine
from supervisor.verifier import CommandExecutionResult


def _make_run_contract(repo_root: Path) -> RunContract:
    return RunContract(
        run_id="run-report",
        repo_path=str(repo_root),
        objective="Write readiness report",
        scope=RunScope(allowed_paths=("src", "tests"), forbidden_paths=(".env",)),
        acceptance=RunAcceptance(
            functional=("report written",),
            quality_gates=("tests pass",),
            ui_checks=(),
        ),
        constraints=RunConstraints(
            single_writer=True,
            max_repair_loops=2,
            max_iterations=5,
            max_cost_dollars=5.0,
            hard_timeout_seconds=300,
        ),
        queue=QueueMetadata(
            claim_id="claim-report",
            run_trace_id="trace-report-123",
            queue_entry_reason="Ready for Build queue claim",
        ),
    )


class ReadinessReportTests(unittest.TestCase):
    def test_build_and_write_readiness_report_without_checkpoint_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract={}, run_contract=run_contract)
            machine = StateMachine(run_contract.run_id)
            machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
            machine.transition_to(Phase.BUILD, "builder start")
            machine.transition_to(Phase.LOCAL_VERIFY, "candidate ready")
            machine.transition_to(Phase.FINAL_GATE, "authoritative checks")
            machine.record_final_gate_evidence(
                required_artifacts_present=True,
                authoritative_checks_passed=True,
                unresolved_high_severity_findings=False,
            )
            machine.apply_final_gate_outcome(ReadinessVerdict.READY, "all checks passed")

            command_results = (
                CommandExecutionResult(
                    name="test",
                    command="pnpm test",
                    exit_code=0,
                    stdout="all tests passed",
                    stderr="",
                    duration_seconds=1.23,
                    scope="full",
                    run_trace_id="trace-report-123",
                ),
            )
            report = build_readiness_report(
                snapshot=machine.snapshot,
                run_contract=run_contract,
                command_results=command_results,
                changed_files=("src/app.ts",),
                artifact_manifest=("artifacts/logs/test.stdout.log", "reports/final-summary.md"),
                unresolved_blockers=(),
                queue_exit_reason="final gate ready",
            )

            report_path, summary_path = write_readiness_reports(run_store, report)

            payload = json.loads(report_path.read_text())
            self.assertEqual("claim-report", payload["claim_id"])
            self.assertEqual("trace-report-123", payload["run_trace_id"])
            self.assertNotIn("checkpoint_refs", payload)
            self.assertEqual(0, payload["commands_run"][0]["exit_code"])
            self.assertIn("Run state: `COMPLETE`", summary_path.read_text())

    def test_report_includes_failures_and_checkpoint_refs_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract = _make_run_contract(repo_root)
            machine = StateMachine(run_contract.run_id)
            machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
            machine.transition_to(Phase.BUILD, "builder start")
            machine.transition_to(Phase.LOCAL_VERIFY, "candidate ready")
            machine.transition_to(Phase.FINAL_GATE, "authoritative checks")
            machine.block("lint failed", readiness_verdict=ReadinessVerdict.NOT_READY)

            command_results = (
                CommandExecutionResult(
                    name="lint",
                    command="pnpm lint",
                    exit_code=1,
                    stdout="",
                    stderr="lint failed",
                    duration_seconds=0.5,
                    scope="targeted",
                    run_trace_id="trace-report-123",
                    failure_fingerprint="local-verify-lint-lint-failed-src-app-ts",
                ),
            )
            report = build_readiness_report(
                snapshot=machine.snapshot,
                run_contract=run_contract,
                command_results=command_results,
                changed_files=("src/app.ts",),
                artifact_manifest=("artifacts/logs/lint.stderr.log",),
                unresolved_blockers=("Lint still failing",),
                queue_exit_reason="blocked by deterministic gate",
                checkpoint_refs=("checkpoint-001",),
            )

            self.assertEqual(("local-verify-lint-lint-failed-src-app-ts",), report.failures)
            self.assertEqual(("checkpoint-001",), report.checkpoint_refs)


if __name__ == "__main__":
    unittest.main()

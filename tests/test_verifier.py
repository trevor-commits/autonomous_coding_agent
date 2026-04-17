import json
import tempfile
import unittest
from pathlib import Path

from supervisor.contracts import (
    QueueMetadata,
    RepoCommands,
    RepoContract,
    RepoEnvConfig,
    RepoUIConfig,
    RunAcceptance,
    RunConstraints,
    RunContract,
    RunScope,
)
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.run_store import RunStore
from supervisor.verifier import VerificationMode, Verifier


def _make_run_contract(repo_root: Path) -> RunContract:
    return RunContract(
        run_id="run-verify",
        repo_path=str(repo_root),
        objective="Verify deterministic checks",
        scope=RunScope(allowed_paths=("src", "tests", "scripts"), forbidden_paths=(".env",)),
        acceptance=RunAcceptance(
            functional=("verification passes",),
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
            claim_id="claim-123",
            run_trace_id="trace-verify-123",
            queue_entry_reason="Ready for Build queue claim",
        ),
    )


class VerifierTests(unittest.TestCase):
    def test_targeted_mode_passes_scope_metadata_to_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            runner_script = scripts_dir / "runner.py"
            runner_script.write_text(
                """
import json
import os
import sys

name = sys.argv[1]
print(json.dumps({
    "name": name,
    "mode": os.environ["AUTOCLAW_VERIFICATION_MODE"],
    "paths": json.loads(os.environ["AUTOCLAW_TARGETED_PATHS_JSON"]),
    "trace": os.environ["AUTOCLAW_RUN_TRACE_ID"],
}))
""".strip()
            )
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup=f"python3 {runner_script} setup",
                    test=f"python3 {runner_script} test",
                    app_up="pnpm dev",
                    app_health="http://127.0.0.1:3000/health",
                ),
                ui=RepoUIConfig(),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            summary = Verifier(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-verify-123",
            ).run(
                mode=VerificationMode.TARGETED,
                changed_files=("src/app.ts", "tests/app.test.ts"),
            )

            self.assertTrue(summary.all_passed)
            self.assertEqual(2, len(summary.commands))
            payload = json.loads(summary.commands[0].stdout)
            self.assertEqual("targeted", payload["mode"])
            self.assertEqual(["src/app.ts", "tests/app.test.ts"], payload["paths"])
            self.assertEqual("trace-verify-123", payload["trace"])

    def test_failure_records_fingerprint_and_stops_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            runner_script = scripts_dir / "runner.py"
            runner_script.write_text(
                """
import sys

name = sys.argv[1]
if name == "lint":
    sys.stderr.write("Missing semicolon in src/app.ts\\n")
    raise SystemExit(1)
print(name + " ok")
""".strip()
            )
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup=f"python3 {runner_script} setup",
                    test=f"python3 {runner_script} test",
                    lint=f"python3 {runner_script} lint",
                    app_up="pnpm dev",
                    app_health="http://127.0.0.1:3000/health",
                ),
                ui=RepoUIConfig(),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)
            fingerprint_store = FailureFingerprintStore(run_store)

            summary = Verifier(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-verify-123",
                fingerprint_store=fingerprint_store,
            ).run(mode=VerificationMode.FULL, changed_files=("src/app.ts",))

            self.assertFalse(summary.all_passed)
            self.assertEqual(("setup", "lint"), tuple(result.name for result in summary.commands))
            self.assertTrue(summary.commands[-1].failure_fingerprint)
            self.assertTrue((run_store.logs_dir / "lint.stderr.log").exists())
            persisted = json.loads((run_store.reports_dir / "failure-fingerprints.json").read_text())
            self.assertEqual(1, len(persisted))
            self.assertEqual(summary.commands[-1].failure_fingerprint, persisted[0]["fingerprint"])


if __name__ == "__main__":
    unittest.main()

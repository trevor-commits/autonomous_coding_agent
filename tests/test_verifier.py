import json
import os
import platform
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
        scope=RunScope(
            allowed_paths=("src", "tests", "scripts"), forbidden_paths=(".env",)
        ),
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
    def test_verifier_rejects_absolute_denied_repo_command_before_execution(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            for name in ("src", "tests", "scripts"):
                (repo_root / name).mkdir()
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="printf ok && git push origin main",
                    test="python3 -c 'print(\"ok\")'",
                    app_up="pnpm dev",
                    app_health="http://127.0.0.1:3000/health",
                ),
                ui=RepoUIConfig(),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            with self.assertRaisesRegex(ValueError, "absolute shell policy"):
                Verifier(
                    repo_root=repo_root,
                    repo_contract=repo_contract,
                    run_contract=run_contract,
                    run_store=run_store,
                    run_trace_id="trace-verify-123",
                )

    @unittest.skipUnless(platform.system() == "Darwin", "macOS Seatbelt boundary test")
    def test_partner_verifier_uses_scrubbed_confined_command_sandbox(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory(dir="/private/tmp") as outside_tmp,
        ):
            repo_root = Path(tmpdir)
            (repo_root / "scripts").mkdir()
            (repo_root / "src").mkdir()
            (repo_root / "tests").mkdir()
            outside = Path(outside_tmp) / "sentinel.txt"
            outside.write_text("verifier-outside-secret\n")
            probe = repo_root / "scripts" / "secure_probe.py"
            probe.write_text(
                "\n".join(
                    (
                        "import os",
                        "from pathlib import Path",
                        "print('HOST_ENV=' + str(os.environ.get('ACA_VERIFIER_HOST_SECRET')))",
                        f"outside = Path({str(outside)!r})",
                        "try:",
                        "    print('READ=UNEXPECTED:' + outside.read_text())",
                        "except Exception as exc:",
                        "    print('READ=' + type(exc).__name__)",
                        "try:",
                        "    Path('outside.txt').write_text('no')",
                        "    print('WRITE=UNEXPECTED')",
                        "except Exception as exc:",
                        "    print('WRITE=' + type(exc).__name__)",
                        "Path('src/verified.txt').write_text('ok\\n')",
                    )
                )
                + "\n"
            )
            (repo_root / "scripts" / "test_probe.py").write_text('print("test ok")\n')
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 scripts/secure_probe.py",
                    test="python3 scripts/test_probe.py",
                    app_up="pnpm dev",
                    app_health="http://127.0.0.1:3000/health",
                ),
                ui=RepoUIConfig(),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)
            original = os.environ.get("ACA_VERIFIER_HOST_SECRET")
            os.environ["ACA_VERIFIER_HOST_SECRET"] = "verifier-host-secret"
            try:
                summary = Verifier(
                    repo_root=repo_root,
                    repo_contract=repo_contract,
                    run_contract=run_contract,
                    run_store=run_store,
                    run_trace_id="trace-verify-123",
                    partner_sandbox=True,
                ).run()
            finally:
                if original is None:
                    os.environ.pop("ACA_VERIFIER_HOST_SECRET", None)
                else:
                    os.environ["ACA_VERIFIER_HOST_SECRET"] = original

            output = "\n".join(
                result.stdout + result.stderr for result in summary.commands
            )
            self.assertTrue(summary.all_passed, output)
            self.assertIn("HOST_ENV=None", output)
            self.assertIn("READ=PermissionError", output)
            self.assertIn("WRITE=PermissionError", output)
            self.assertNotIn("verifier-host-secret", output)
            self.assertNotIn("verifier-outside-secret", output)
            self.assertTrue((repo_root / "src" / "verified.txt").is_file())
            self.assertFalse((repo_root / "outside.txt").exists())

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
            self.assertEqual(
                ("setup", "lint"), tuple(result.name for result in summary.commands)
            )
            self.assertTrue(summary.commands[-1].failure_fingerprint)
            self.assertTrue((run_store.logs_dir / "lint.stderr.log").exists())
            persisted = json.loads(
                (run_store.reports_dir / "failure-fingerprints.json").read_text()
            )
            self.assertEqual(1, len(persisted))
            self.assertEqual(
                summary.commands[-1].failure_fingerprint, persisted[0]["fingerprint"]
            )


if __name__ == "__main__":
    unittest.main()

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
from supervisor.run_store import RunStore
from supervisor.ui_verifier import UIVerifier


def _make_run_contract(
    repo_root: Path,
    *,
    ui_checks: tuple[str, ...] = ("Settings form saves without console errors",),
) -> RunContract:
    return RunContract(
        run_id="run-ui-verify",
        repo_path=str(repo_root),
        objective="Verify the UI smoke suite",
        scope=RunScope(allowed_paths=("src", "tests", "scripts"), forbidden_paths=(".env",)),
        acceptance=RunAcceptance(
            functional=("settings save works",),
            quality_gates=("tests pass",),
            ui_checks=ui_checks,
        ),
        constraints=RunConstraints(
            single_writer=True,
            max_repair_loops=2,
            max_iterations=5,
            max_cost_dollars=5.0,
            hard_timeout_seconds=300,
        ),
        queue=QueueMetadata(
            claim_id="claim-ui-123",
            run_trace_id="trace-ui-123",
            queue_entry_reason="Ready for Build queue claim",
        ),
    )


class UIVerifierTests(unittest.TestCase):
    def test_ui_smoke_passes_base_url_breakpoints_and_profile_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            runner_script = scripts_dir / "ui_runner.py"
            runner_script.write_text(
                "\n".join(
                    [
                        "import json",
                        "import os",
                        "from pathlib import Path",
                        "payload = {",
                        "    'base_url': os.environ['AUTOCLAW_UI_BASE_URL'],",
                        "    'breakpoints': json.loads(os.environ['AUTOCLAW_UI_BREAKPOINTS_JSON']),",
                        "    'profile_dir': os.environ['AUTOCLAW_BROWSER_PROFILE_DIR'],",
                        "}",
                        "Path(os.environ['AUTOCLAW_UI_TRACES_DIR']).mkdir(parents=True, exist_ok=True)",
                        "print(json.dumps(payload))",
                    ]
                )
            )
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up="python3 -c \"print('app ok')\"",
                    app_health="http://127.0.0.1:3000/health",
                    ui_smoke=f"python3 {runner_script}",
                ),
                ui=RepoUIConfig(
                    base_url="http://127.0.0.1:3000",
                    breakpoints=("390x844", "1440x900"),
                ),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            summary = UIVerifier(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-ui-123",
            ).run(changed_files=("src/settings.tsx",))

            self.assertTrue(summary.passed)
            self.assertEqual(("ui_smoke",), tuple(result.name for result in summary.command_results))
            payload = json.loads(summary.command_results[0].stdout)
            self.assertEqual("http://127.0.0.1:3000", payload["base_url"])
            self.assertEqual(["390x844", "1440x900"], payload["breakpoints"])
            self.assertTrue(payload["profile_dir"].endswith("browser-profile"))
            self.assertEqual((), summary.defect_packets)

    def test_ui_failure_writes_defect_packet_and_artifact_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            runner_script = scripts_dir / "ui_runner.py"
            runner_script.write_text(
                "\n".join(
                    [
                        "import os",
                        "from pathlib import Path",
                        "Path(os.environ['AUTOCLAW_UI_SCREENSHOTS_DIR']).mkdir(parents=True, exist_ok=True)",
                        "Path(os.environ['AUTOCLAW_UI_TRACES_DIR']).mkdir(parents=True, exist_ok=True)",
                        "Path(os.environ['AUTOCLAW_UI_SCREENSHOTS_DIR'], 'settings-save-disabled.png').write_text('png')",
                        "Path(os.environ['AUTOCLAW_UI_TRACES_DIR'], 'settings-flow.zip').write_text('zip')",
                        "raise SystemExit('Save button disabled after valid input')",
                    ]
                )
            )
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up="python3 -c \"print('app ok')\"",
                    app_health="http://127.0.0.1:3000/health",
                    ui_smoke=f"python3 {runner_script}",
                ),
                ui=RepoUIConfig(
                    base_url="http://127.0.0.1:3000",
                    breakpoints=("390x844",),
                    critical_flows=(),
                ),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            summary = UIVerifier(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-ui-123",
            ).run(changed_files=("src/components/SettingsForm.tsx",))

            self.assertFalse(summary.passed)
            self.assertEqual(1, len(summary.defect_packets))
            defect = summary.defect_packets[0]
            self.assertEqual("ui-functional", defect["type"])
            self.assertEqual(
                ["src/components/SettingsForm.tsx"],
                defect["suspected_scope"],
            )
            self.assertIn("artifacts/screenshots/settings-save-disabled.png", summary.artifact_manifest)
            self.assertIn("artifacts/traces/settings-flow.zip", summary.artifact_manifest)
            self.assertTrue((run_store.defects_dir / f"{defect['defect_id']}.json").exists())
            self.assertEqual("ui_smoke", summary.command_results[0].name)
            self.assertTrue(summary.command_results[0].failure_fingerprint)

    def test_ui_failure_emits_packet_per_failure_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            runner_script = scripts_dir / "ui_runner.py"
            runner_script.write_text(
                "\n".join(
                    [
                        "import os",
                        "import sys",
                        "from pathlib import Path",
                        "screenshots = Path(os.environ['AUTOCLAW_UI_SCREENSHOTS_DIR'])",
                        "traces = Path(os.environ['AUTOCLAW_UI_TRACES_DIR'])",
                        "screenshots.mkdir(parents=True, exist_ok=True)",
                        "traces.mkdir(parents=True, exist_ok=True)",
                        "(screenshots / 'first.png').write_text('png')",
                        "(screenshots / 'second.png').write_text('png')",
                        "(traces / 'trace-one.zip').write_text('zip')",
                        "(traces / 'trace-two.zip').write_text('zip')",
                        "sys.stderr.write('first failure\\nsecond failure\\n')",
                        "raise SystemExit(1)",
                    ]
                )
            )
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up="python3 -c \"print('app ok')\"",
                    app_health="http://127.0.0.1:3000/health",
                    ui_smoke=f"python3 {runner_script}",
                ),
                ui=RepoUIConfig(
                    base_url="http://127.0.0.1:3000",
                    breakpoints=("390x844",),
                    critical_flows=(),
                ),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(
                repo_root,
                ui_checks=("check one", "check two"),
            )
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            summary = UIVerifier(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-ui-123",
            ).run(changed_files=("src/components/SettingsForm.tsx",))

            self.assertFalse(summary.passed)
            self.assertEqual(2, len(summary.defect_packets))
            self.assertEqual("first failure", summary.defect_packets[0]["summary"])
            self.assertEqual("check one", summary.defect_packets[0]["expected"])
            self.assertEqual("second failure", summary.defect_packets[1]["summary"])
            self.assertEqual("check two", summary.defect_packets[1]["expected"])
            self.assertTrue((run_store.defects_dir / f"{summary.defect_packets[0]['defect_id']}.json").exists())
            self.assertTrue((run_store.defects_dir / f"{summary.defect_packets[1]['defect_id']}.json").exists())


if __name__ == "__main__":
    unittest.main()

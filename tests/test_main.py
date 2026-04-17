import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from supervisor.app_supervisor import AppLaunchSummary, AppSession
from supervisor.builder_adapter import BuilderAdapter, BuilderResult, BuilderSession
from supervisor.main import execute_run
from supervisor.ui_verifier import UIVerificationSummary
from supervisor.strategy_simple import SimpleStrategy
from supervisor.verifier import CommandExecutionResult


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_target_repo(repo_root: Path, *, with_ui: bool = False) -> Path:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "Codex")
    _git(repo_root, "config", "user.email", "codex@example.com")
    (repo_root / ".agent").mkdir()
    (repo_root / "scripts").mkdir()
    (repo_root / "src").mkdir()
    (repo_root / ".gitignore").write_text(".autoclaw/\nworktrees/\n")
    contract_payload = {
        "version": 1,
        "stack": "fullstack-web",
        "commands": {
            "setup": "python3 scripts/setup.py",
            "test": "python3 scripts/test.py",
            "app_up": "python3 -m http.server 3000",
            "app_health": "http://127.0.0.1:3000/health",
        },
    }
    if with_ui:
        contract_payload["commands"]["ui_smoke"] = "python3 scripts/ui_smoke.py"
        contract_payload["ui"] = {"base_url": "http://127.0.0.1:3000", "breakpoints": ["390x844"]}
        (repo_root / "scripts" / "ui_smoke.py").write_text("print('ui smoke placeholder')\n")
    (repo_root / ".agent" / "contract.yml").write_text(yaml.safe_dump(contract_payload))
    (repo_root / "scripts" / "setup.py").write_text("print('setup ok')\n")
    (repo_root / "scripts" / "test.py").write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "target = Path('src/task.txt')",
                "value = target.read_text().strip() if target.exists() else ''",
                "if value == 'fixed':",
                "    print('tests passed')",
                "else:",
                "    print('tests failed')",
                "    raise SystemExit(1)",
            ]
        )
    )
    (repo_root / "README.md").write_text("# target repo\n")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "init")

    run_contract_path = repo_root / "run-contract.json"
    run_contract_path.write_text(
        json.dumps(
            {
                "run_id": "benchmark-001",
                "repo_path": str(repo_root),
                "objective": "Fix the failing task fixture",
                "scope": {
                    "allowed_paths": ["src/", "tests/"],
                    "forbidden_paths": [".env", "infra/"],
                },
                "acceptance": {
                    "functional": ["task file fixed"],
                    "quality_gates": ["tests pass"],
                    "ui_checks": [],
                },
                "constraints": {
                    "single_writer": True,
                    "max_repair_loops": 2,
                    "max_iterations": 5,
                    "max_cost_dollars": 5.0,
                    "hard_timeout_seconds": 600,
                },
                "claim_id": "claim-123",
                "run_trace_id": "trace-123",
                "queue_entry_reason": "Ready for Build queue claim",
            }
        )
    )
    return run_contract_path


class FakeBuilderAdapter(BuilderAdapter):
    def __init__(self, writes: list[str], commands_per_turn: list[tuple[str, ...]] | None = None) -> None:
        self.writes = writes
        self.commands_per_turn = commands_per_turn or [tuple() for _ in writes]
        self.prompts: list[str] = []

    def start_session(self, worktree_path: Path, run_context: dict) -> BuilderSession:
        return BuilderSession(worktree_path=Path(worktree_path), run_context=run_context, session_id="fake")

    def send_task(self, session: BuilderSession, prompt: str, timeout: int) -> BuilderResult:
        turn = session.turn_count
        session.turn_count += 1
        self.prompts.append(prompt)
        target = session.worktree_path / "src" / "task.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.writes[turn])
        return BuilderResult(
            session_id=session.session_id,
            status="completed",
            final_message="done",
            files_changed=("src/task.txt",),
            commands_run=self.commands_per_turn[turn],
            duration_seconds=0.01,
            raw_events=tuple(),
        )

    def close_session(self, session: BuilderSession) -> None:
        return None


class FakeAppSupervisor:
    def __init__(self, launches: list[AppLaunchSummary]) -> None:
        self.launches = launches
        self.stopped_sessions: list[AppSession] = []

    def launch(self) -> AppLaunchSummary:
        return self.launches.pop(0)

    def stop(self, session: AppSession | None) -> None:
        if session is not None:
            self.stopped_sessions.append(session)


class FakeUIVerifier:
    def __init__(self, summaries: list[UIVerificationSummary]) -> None:
        self.summaries = summaries

    def run(self, *, changed_files: tuple[str, ...]) -> UIVerificationSummary:
        return self.summaries.pop(0)


def _healthy_launch() -> AppLaunchSummary:
    return AppLaunchSummary(
        healthy=True,
        session=AppSession(
            process=None,
            health_url="http://127.0.0.1:3000/health",
            stdout_log_path=Path("/tmp/app.stdout.log"),
            stderr_log_path=Path("/tmp/app.stderr.log"),
        ),
        base_url="http://127.0.0.1:3000",
        command_results=(
            CommandExecutionResult(
                name="app_up",
                command="pnpm dev",
                exit_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.1,
                scope="full",
                run_trace_id="trace-123",
            ),
            CommandExecutionResult(
                name="app_health",
                command="http://127.0.0.1:3000/health",
                exit_code=0,
                stdout="ok",
                stderr="",
                duration_seconds=0.1,
                scope="full",
                run_trace_id="trace-123",
            ),
        ),
        artifact_manifest=("artifacts/logs/app_up.stdout.log", "artifacts/logs/app_up.stderr.log"),
    )


def _failed_launch() -> AppLaunchSummary:
    return AppLaunchSummary(
        healthy=False,
        session=None,
        base_url="http://127.0.0.1:3000",
        command_results=(
            CommandExecutionResult(
                name="app_up",
                command="pnpm dev",
                exit_code=0,
                stdout="",
                stderr="",
                duration_seconds=0.1,
                scope="full",
                run_trace_id="trace-123",
            ),
            CommandExecutionResult(
                name="app_health",
                command="http://127.0.0.1:3000/health",
                exit_code=1,
                stdout="",
                stderr="timeout waiting for health",
                duration_seconds=0.2,
                scope="full",
                run_trace_id="trace-123",
                failure_fingerprint="app-launch-app-health-timeout",
            ),
        ),
        artifact_manifest=("artifacts/logs/app_up.stdout.log", "artifacts/logs/app_up.stderr.log"),
        failure_fingerprint="app-launch-app-health-timeout",
        failure_reason="timeout waiting for health",
    )


def _ui_pass() -> UIVerificationSummary:
    return UIVerificationSummary(
        passed=True,
        command_results=(
            CommandExecutionResult(
                name="ui_smoke",
                command="npx playwright test",
                exit_code=0,
                stdout="all ui smoke checks passed",
                stderr="",
                duration_seconds=0.4,
                scope="full",
                run_trace_id="trace-123",
            ),
        ),
        defect_packets=(),
        artifact_manifest=("artifacts/logs/ui_smoke.stdout.log",),
    )


def _ui_failure() -> UIVerificationSummary:
    return UIVerificationSummary(
        passed=False,
        command_results=(
            CommandExecutionResult(
                name="ui_smoke",
                command="npx playwright test",
                exit_code=1,
                stdout="",
                stderr="Save button disabled after valid input",
                duration_seconds=0.4,
                scope="full",
                run_trace_id="trace-123",
                failure_fingerprint="ui-verify-ui-smoke-save-disabled",
            ),
        ),
        defect_packets=(
            {
                "defect_id": "defect-001",
                "severity": "P1",
                "type": "ui-functional",
                "summary": "Save button disabled after valid input",
                "repro_steps": ["Open /settings", "Fill valid data", "Observe save button"],
                "expected": "Save button enabled",
                "observed": "Button remained disabled",
                "evidence": {"console_log": "artifacts/logs/ui_smoke.stderr.log"},
                "suspected_scope": ["src/components/SettingsForm.tsx"],
                "failure_fingerprint": "ui-verify-ui-smoke-save-disabled",
            },
        ),
        artifact_manifest=(
            "artifacts/logs/ui_smoke.stderr.log",
            "artifacts/screenshots/settings-save-disabled.png",
        ),
    )


class SupervisorMainTests(unittest.TestCase):
    def test_execute_run_completes_after_single_builder_turn(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract_path = _init_target_repo(repo_root)
            adapter = FakeBuilderAdapter(["fixed"])

            outcome = execute_run(
                repo_root=repo_root,
                run_contract_path=run_contract_path,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                cleanup_worktree=False,
            )

            self.assertEqual("COMPLETE", outcome.snapshot.run_state.value)
            self.assertTrue(outcome.report_path.exists())
            self.assertTrue(outcome.summary_path.exists())
            self.assertEqual(1, len(adapter.prompts))

    def test_execute_run_retries_with_failure_fingerprint_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract_path = _init_target_repo(repo_root)
            adapter = FakeBuilderAdapter(["broken", "fixed"])

            outcome = execute_run(
                repo_root=repo_root,
                run_contract_path=run_contract_path,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                cleanup_worktree=False,
            )

            self.assertEqual("COMPLETE", outcome.snapshot.run_state.value)
            self.assertEqual(2, len(adapter.prompts))
            self.assertIn("Prior failure fingerprints", adapter.prompts[1])
            self.assertIn("local-verify-test", adapter.prompts[1])

    def test_execute_run_blocks_on_high_risk_builder_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract_path = _init_target_repo(repo_root)
            adapter = FakeBuilderAdapter(
                ["fixed"],
                commands_per_turn=[("/bin/zsh -lc git push origin main",)],
            )

            outcome = execute_run(
                repo_root=repo_root,
                run_contract_path=run_contract_path,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                cleanup_worktree=False,
            )

            self.assertEqual("BLOCKED", outcome.snapshot.run_state.value)
            self.assertIn("git push", "\n".join(outcome.report.unresolved_blockers))

    def test_execute_run_retries_after_app_launch_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract_path = _init_target_repo(repo_root, with_ui=True)
            adapter = FakeBuilderAdapter(["fixed", "fixed"])
            app_supervisor = FakeAppSupervisor([_failed_launch(), _healthy_launch()])
            ui_verifier = FakeUIVerifier([_ui_pass()])

            outcome = execute_run(
                repo_root=repo_root,
                run_contract_path=run_contract_path,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                app_supervisor=app_supervisor,
                ui_verifier=ui_verifier,
                cleanup_worktree=False,
            )

            self.assertEqual("COMPLETE", outcome.snapshot.run_state.value)
            self.assertEqual(2, len(adapter.prompts))
            self.assertIn("app-launch-app-health-timeout", adapter.prompts[1])
            self.assertIn("APP_LAUNCH", outcome.report.phases_completed)
            self.assertIn("UI_VERIFY", outcome.report.phases_completed)

    def test_execute_run_routes_ui_defects_back_to_builder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            run_contract_path = _init_target_repo(repo_root, with_ui=True)
            adapter = FakeBuilderAdapter(["fixed", "fixed"])
            app_supervisor = FakeAppSupervisor([_healthy_launch(), _healthy_launch()])
            ui_verifier = FakeUIVerifier([_ui_failure(), _ui_pass()])

            outcome = execute_run(
                repo_root=repo_root,
                run_contract_path=run_contract_path,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                app_supervisor=app_supervisor,
                ui_verifier=ui_verifier,
                cleanup_worktree=False,
            )

            self.assertEqual("COMPLETE", outcome.snapshot.run_state.value)
            self.assertEqual(2, len(adapter.prompts))
            self.assertIn("Save button disabled after valid input", adapter.prompts[1])
            self.assertIn("src/components/SettingsForm.tsx", adapter.prompts[1])
            self.assertIn("ui-verify-ui-smoke-save-disabled", adapter.prompts[1])


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from supervisor.builder_adapter import BuilderAdapter, BuilderResult, BuilderSession
from supervisor.main import execute_run
from supervisor.strategy_simple import SimpleStrategy


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_target_repo(repo_root: Path) -> Path:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "Codex")
    _git(repo_root, "config", "user.email", "codex@example.com")
    (repo_root / ".agent").mkdir()
    (repo_root / "scripts").mkdir()
    (repo_root / "src").mkdir()
    (repo_root / ".gitignore").write_text(".autoclaw/\nworktrees/\n")
    (repo_root / ".agent" / "contract.yml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "stack": "fullstack-web",
                "commands": {
                    "setup": "python3 scripts/setup.py",
                    "test": "python3 scripts/test.py",
                    "app_up": "python3 -m http.server 3000",
                    "app_health": "http://127.0.0.1:3000/health",
                },
            }
        )
    )
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


if __name__ == "__main__":
    unittest.main()

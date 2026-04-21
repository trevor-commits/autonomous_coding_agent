import subprocess
import shutil
import tempfile
import unittest
from pathlib import Path

from supervisor.builder_adapter import CodexBuilderAdapter, build_builder_prompt


def _git(repo_root: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo_root: Path) -> None:
    _git(repo_root, "init")
    _git(repo_root, "config", "user.name", "Codex")
    _git(repo_root, "config", "user.email", "codex@example.com")
    (repo_root / "README.md").write_text("# temp repo\n")
    _git(repo_root, "add", "README.md")
    _git(repo_root, "commit", "-m", "init")


class CodexBuilderAdapterTests(unittest.TestCase):
    def test_build_builder_prompt_includes_scope_commands_and_failures(self) -> None:
        prompt = build_builder_prompt(
            {
                "objective": "Add login validation",
                "allowed_paths": ("src", "tests"),
                "forbidden_paths": (".env", "infra"),
                "repo_commands": {
                    "lint": "pnpm lint",
                    "test": "pnpm test",
                },
            },
            "Implement the login validation change.",
            prior_failure_fingerprints=("local-verify-test-login-failed",),
        )

        self.assertIn("Add login validation", prompt)
        self.assertIn("Implement the login validation change.", prompt)
        self.assertIn("src", prompt)
        self.assertIn("pnpm test", prompt)
        self.assertIn("local-verify-test-login-failed", prompt)
        self.assertIn("Do not commit, push, switch branches, or control a browser.", prompt)

    def test_adapter_parses_json_events_and_reuses_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_git_repo(repo_root)
            calls: list[list[str]] = []

            def runner(
                args: list[str],
                *,
                cwd: str | Path | None,
                capture_output: bool,
                text: bool,
                timeout: int | None,
                check: bool,
            ) -> subprocess.CompletedProcess[str]:
                calls.append(list(args))
                worktree = Path(cwd)
                (worktree / "src").mkdir(exist_ok=True)
                if len(calls) == 1:
                    (worktree / "src" / "feature.txt").write_text("first turn\n")
                    stdout = "\n".join(
                        [
                            '{"type":"thread.started","thread_id":"session-123"}',
                            '{"type":"item.completed","item":{"id":"item_0","type":"command_execution","command":"/bin/zsh -lc pwd","aggregated_output":"/tmp\\n","exit_code":0,"status":"completed"}}',
                            '{"type":"item.completed","item":{"id":"item_1","type":"agent_message","text":"done"}}',
                            '{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}',
                        ]
                    )
                else:
                    (worktree / "src" / "feature.txt").write_text("second turn\n")
                    stdout = "\n".join(
                        [
                            '{"type":"item.completed","item":{"id":"item_2","type":"agent_message","text":"done again"}}',
                            '{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}',
                        ]
                    )
                return subprocess.CompletedProcess(args=args, returncode=0, stdout=stdout, stderr="")

            adapter = CodexBuilderAdapter(runner=runner)
            session = adapter.start_session(repo_root, {"objective": "Add feature"})

            first = adapter.send_task(session, "Do the first task.", timeout=30)
            second = adapter.send_task(session, "Do the second task.", timeout=30)

            self.assertEqual("session-123", session.session_id)
            self.assertEqual(("src/feature.txt",), first.files_changed)
            self.assertEqual(("/bin/zsh -lc pwd",), first.commands_run)
            self.assertEqual("done", first.final_message)
            self.assertEqual("session-123", second.session_id)
            self.assertEqual("done again", second.final_message)
            self.assertEqual(["codex", "exec"], calls[0][:2])
            self.assertEqual(["codex", "exec", "resume", "session-123"], calls[1][:4])

    def test_adapter_handles_timeout_stdout_as_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_git_repo(repo_root)

            def runner(
                args: list[str],
                *,
                cwd: str | Path | None,
                capture_output: bool,
                text: bool,
                timeout: int | None,
                check: bool,
            ) -> subprocess.CompletedProcess[str]:
                raise subprocess.TimeoutExpired(
                    cmd=args,
                    timeout=timeout or 0,
                    output=b'{"type":"thread.started","thread_id":"session-timeout"}\n',
                )

            adapter = CodexBuilderAdapter(runner=runner)
            session = adapter.start_session(repo_root, {"objective": "Add feature"})

            result = adapter.send_task(session, "Do the task.", timeout=1)

            self.assertEqual("timed_out", result.status)
            self.assertEqual("session-timeout", result.session_id)
            self.assertEqual("session-timeout", session.session_id)

    def test_adapter_handles_missing_worktree_after_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()
            _init_git_repo(repo_root)

            def runner(
                args: list[str],
                *,
                cwd: str | Path | None,
                capture_output: bool,
                text: bool,
                timeout: int | None,
                check: bool,
            ) -> subprocess.CompletedProcess[str]:
                shutil.rmtree(repo_root)
                raise subprocess.TimeoutExpired(
                    cmd=args,
                    timeout=timeout or 0,
                    output='{"type":"thread.started","thread_id":"session-missing"}\n',
                )

            adapter = CodexBuilderAdapter(runner=runner)
            session = adapter.start_session(repo_root, {"objective": "Add feature"})

            result = adapter.send_task(session, "Do the task.", timeout=1)

            self.assertEqual("timed_out", result.status)
            self.assertEqual("session-missing", result.session_id)
            self.assertEqual((), result.files_changed)


if __name__ == "__main__":
    unittest.main()

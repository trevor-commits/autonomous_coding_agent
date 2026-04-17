import subprocess
import tempfile
import unittest
from pathlib import Path

from supervisor.worktree_manager import WorktreeError, WorktreeManager


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


class WorktreeManagerTests(unittest.TestCase):
    def test_create_and_remove_builder_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_git_repo(repo_root)

            manager = WorktreeManager(repo_root)
            workspace = manager.create_builder_worktree(
                run_id="run-001",
                task_slug="Implement login fixes",
            )

            self.assertTrue(workspace.worktree_path.exists())
            self.assertTrue(workspace.lease_path.exists())
            self.assertIn("run/implement-login-fixes/run-001", workspace.branch_name)

            manager.remove_builder_worktree(workspace)

            self.assertFalse(workspace.lease_path.exists())
            self.assertFalse(workspace.worktree_path.exists())

    def test_second_lease_for_same_run_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_git_repo(repo_root)

            manager = WorktreeManager(repo_root)
            workspace = manager.create_builder_worktree(
                run_id="run-002",
                task_slug="Add dashboard",
            )

            try:
                with self.assertRaises(WorktreeError):
                    manager.acquire_lease("run-002", workspace.worktree_path, workspace.branch_name)
            finally:
                manager.remove_builder_worktree(workspace)


if __name__ == "__main__":
    unittest.main()

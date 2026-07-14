import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
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
                    manager.acquire_lease(
                        "run-002", workspace.worktree_path, workspace.branch_name
                    )
            finally:
                manager.remove_builder_worktree(workspace)

    def test_long_objective_uses_bounded_stable_branch_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_git_repo(repo_root)
            manager = WorktreeManager(repo_root)
            objective = "Create a useful retained-worktree artifact " * 20

            workspace = manager.create_builder_worktree(
                run_id="partner-run-long-objective-001",
                task_slug=objective,
            )
            try:
                slug_component = workspace.branch_name.split("/")[1]
                self.assertLessEqual(len(slug_component), 80)
                self.assertRegex(slug_component, r"-[0-9a-f]{12}$")
            finally:
                manager.remove_builder_worktree(workspace)

    def test_concurrent_builder_worktree_creation_allows_one_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_git_repo(repo_root)
            manager = WorktreeManager(repo_root)

            def create_workspace() -> object:
                try:
                    return manager.create_builder_worktree(
                        run_id="run-003",
                        task_slug="Concurrent edit",
                    )
                except WorktreeError as exc:
                    return exc

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: create_workspace(), range(2)))

            successes = [
                result for result in results if not isinstance(result, Exception)
            ]
            failures = [
                result for result in results if isinstance(result, WorktreeError)
            ]

            self.assertEqual(1, len(successes))
            self.assertEqual(1, len(failures))
            self.assertIn("Single-writer lease already exists", str(failures[0]))

            manager.remove_builder_worktree(successes[0])

    def test_creation_rejects_symlinked_worktree_and_lease_roots(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            repo_root = Path(tmpdir)
            outside = Path(outside_tmp)
            _init_git_repo(repo_root)
            (repo_root / "worktrees").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(WorktreeError, "symlink"):
                WorktreeManager(repo_root).create_builder_worktree(
                    run_id="run-symlink",
                    task_slug="Reject symlink root",
                )
            self.assertEqual([], list(outside.iterdir()))

            (repo_root / "worktrees").unlink()
            (repo_root / ".autoclaw").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(WorktreeError, "symlink"):
                WorktreeManager(repo_root).acquire_lease(
                    "run-lease-symlink",
                    repo_root / "worktrees" / "run-lease-symlink" / "builder",
                    "run/reject/run-lease-symlink",
                )
            self.assertEqual([], list(outside.iterdir()))

    def test_creation_and_release_reject_linked_leaf_collisions(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            repo_root = Path(tmpdir)
            outside = Path(outside_tmp)
            _init_git_repo(repo_root)
            manager = WorktreeManager(repo_root)
            manager.worktrees_root.mkdir()
            run_root = manager.worktrees_root / "run-leaf"
            run_root.mkdir()
            worktree_leaf = run_root / "builder"
            worktree_leaf.symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(WorktreeError, "symlink"):
                manager.create_builder_worktree(
                    run_id="run-leaf",
                    task_slug="Reject leaf collision",
                )

            worktree_leaf.unlink()
            manager.leases_root.mkdir(parents=True)
            outside_lease = outside / "outside-lease.json"
            outside_lease.write_text("outside\n")
            (manager.leases_root / "run-linked.json").hardlink_to(outside_lease)
            with self.assertRaisesRegex(WorktreeError, "single-link"):
                manager.release_lease("run-linked")
            self.assertTrue((manager.leases_root / "run-linked.json").exists())
            self.assertEqual("outside\n", outside_lease.read_text())

            (manager.leases_root / "run-symlink.json").symlink_to(outside_lease)
            with self.assertRaisesRegex(WorktreeError, "regular file"):
                manager.acquire_lease(
                    "run-symlink",
                    repo_root / "worktrees" / "run-symlink" / "builder",
                    "run/reject/run-symlink",
                )
            self.assertEqual("outside\n", outside_lease.read_text())

            with self.assertRaisesRegex(WorktreeError, "traversal"):
                manager.acquire_lease(
                    "../../escaped",
                    repo_root / "worktrees" / "escaped" / "builder",
                    "run/reject/escaped",
                )
            self.assertFalse((repo_root / "escaped.json").exists())


if __name__ == "__main__":
    unittest.main()

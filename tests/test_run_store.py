import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from supervisor.run_store import RunStore, RunStoreError
from supervisor.state_machine import StateMachine


class RunStoreTests(unittest.TestCase):
    def test_initialize_creates_expected_runtime_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            store = RunStore(repo_root, "run-001")
            machine = StateMachine("run-001")

            store.initialize(
                repo_contract={"version": 1, "stack": "fullstack-web"},
                run_contract={"run_id": "run-001"},
                initial_state=machine.snapshot,
            )

            self.assertTrue((store.root / "defects").is_dir())
            self.assertTrue((store.root / "artifacts" / "logs").is_dir())
            self.assertTrue((store.root / "reports").is_dir())
            self.assertTrue(store.contract_path.exists())
            self.assertTrue(store.state_path.exists())
            self.assertTrue(store.execution_log_path.exists())

            payload = json.loads(store.contract_path.read_text())
            self.assertEqual(1, payload["repo_contract"]["version"])
            self.assertEqual("run-001", payload["run_contract"]["run_id"])

    def test_write_state_and_report_update_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            store = RunStore(repo_root, "run-002")
            store.initialize(repo_contract={}, run_contract={})

            machine = StateMachine("run-002")
            machine.transition_to(machine.snapshot.phase.PREPARE_WORKSPACE, "setup")
            store.write_state(machine.snapshot)
            report_path = store.write_report(
                "summary.json", {"run_state": "IN_PROGRESS"}
            )
            store.append_execution_log("phase started")

            self.assertIn("PREPARE_WORKSPACE", store.state_path.read_text())
            self.assertEqual(
                "IN_PROGRESS", json.loads(report_path.read_text())["run_state"]
            )
            self.assertIn("phase started", store.execution_log_path.read_text())

    def test_interrupted_json_write_preserves_last_valid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            store = RunStore(repo_root, "run-003")
            target = store.state_path
            store.write_json(target, {"generation": 1})
            original_payload = target.read_text()
            real_fsync = os.fsync

            def interrupted_fsync(descriptor: int) -> None:
                if stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise OSError("simulated interrupted write")
                real_fsync(descriptor)

            with patch("supervisor.run_store.os.fsync", side_effect=interrupted_fsync):
                with self.assertRaisesRegex(OSError, "simulated interrupted write"):
                    store.write_json(target, {"generation": 2})

            self.assertEqual(original_payload, target.read_text())
            self.assertEqual({"generation": 1}, json.loads(target.read_text()))

    def test_write_json_uses_bound_descriptor_and_syncs_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RunStore(Path(tmpdir), "run-bound-write")
            target = store.state_path
            synced_kinds: list[str] = []
            replace_dir_fds: list[tuple[int | None, int | None]] = []
            real_fsync = os.fsync
            real_replace = os.replace

            def tracked_fsync(descriptor: int) -> None:
                mode = os.fstat(descriptor).st_mode
                synced_kinds.append(
                    "directory" if stat.S_ISDIR(mode) else "regular-file"
                )
                real_fsync(descriptor)

            def tracked_replace(src, dst, *args, **kwargs) -> None:
                replace_dir_fds.append(
                    (kwargs.get("src_dir_fd"), kwargs.get("dst_dir_fd"))
                )
                real_replace(src, dst, *args, **kwargs)

            with (
                patch.object(
                    Path,
                    "write_text",
                    autospec=True,
                    side_effect=AssertionError("must not reopen temp path by name"),
                ),
                patch("supervisor.run_store.os.fsync", side_effect=tracked_fsync),
                patch("supervisor.run_store.os.replace", side_effect=tracked_replace),
            ):
                store.write_json(target, {"generation": 1})

            self.assertEqual({"generation": 1}, json.loads(target.read_text()))
            self.assertEqual(["regular-file", "directory"], synced_kinds)
            self.assertEqual(1, len(replace_dir_fds))
            source_fd, destination_fd = replace_dir_fds[0]
            self.assertIsNotNone(source_fd)
            self.assertEqual(source_fd, destination_fd)

    def test_initialize_rejects_symlinked_runtime_ancestry(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            repo_root = Path(tmpdir)
            outside = Path(outside_tmp)
            (repo_root / ".autoclaw").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(RunStoreError, "symlink"):
                RunStore(repo_root, "run-symlink").initialize(
                    repo_contract={}, run_contract={}
                )

            self.assertEqual([], list(outside.iterdir()))

    def test_writes_reject_non_directory_ancestry_and_linked_file_leaves(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            repo_root = Path(tmpdir)
            outside = Path(outside_tmp)
            (repo_root / ".autoclaw").mkdir()
            (repo_root / ".autoclaw" / "runs").write_text("not a directory\n")
            with self.assertRaisesRegex(RunStoreError, "directory"):
                RunStore(repo_root, "run-collision").write_state({"generation": 1})

            (repo_root / ".autoclaw" / "runs").unlink()
            store = RunStore(repo_root, "run-collision")
            store.root.mkdir(parents=True)
            outside_state = outside / "outside-state.json"
            outside_state.write_text("outside\n")
            store.state_path.symlink_to(outside_state)
            with self.assertRaisesRegex(RunStoreError, "regular file"):
                store.write_state({"generation": 1})
            self.assertEqual("outside\n", outside_state.read_text())

            store.state_path.unlink()
            store.state_path.hardlink_to(outside_state)
            with self.assertRaisesRegex(RunStoreError, "single-link"):
                store.write_state({"generation": 2})
            self.assertEqual("outside\n", outside_state.read_text())

            outside_log = outside / "outside.log"
            outside_log.write_text("outside-log\n")
            store.execution_log_path.symlink_to(outside_log)
            with self.assertRaisesRegex(RunStoreError, "regular file"):
                store.append_execution_log("must not escape")
            self.assertEqual("outside-log\n", outside_log.read_text())


if __name__ == "__main__":
    unittest.main()

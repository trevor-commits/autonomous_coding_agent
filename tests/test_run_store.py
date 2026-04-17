import json
import tempfile
import unittest
from pathlib import Path

from supervisor.run_store import RunStore
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
            report_path = store.write_report("summary.json", {"run_state": "IN_PROGRESS"})
            store.append_execution_log("phase started")

            self.assertIn("PREPARE_WORKSPACE", store.state_path.read_text())
            self.assertEqual("IN_PROGRESS", json.loads(report_path.read_text())["run_state"])
            self.assertIn("phase started", store.execution_log_path.read_text())


if __name__ == "__main__":
    unittest.main()

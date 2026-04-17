import json
import tempfile
import unittest
from pathlib import Path

from supervisor.fingerprints import FailureFingerprintStore
from supervisor.run_store import RunStore


class FailureFingerprintStoreTests(unittest.TestCase):
    def test_record_normalizes_and_persists_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            store = RunStore(repo_root, "run-001")
            store.initialize(repo_contract={}, run_contract={})
            fingerprints = FailureFingerprintStore(store)

            recorded = fingerprints.record(
                phase="LOCAL_VERIFY",
                command="test",
                error_signature="AssertionError: email field required",
                relevant_paths=["tests/auth/test_login.py", "tests/auth/test_login.py"],
                evidence_refs=["artifacts/logs/test.stderr.log"],
            )

            self.assertEqual(
                "local-verify-test-assertionerror-email-field-required-tests-auth-test-login-py",
                recorded.fingerprint,
            )
            persisted = json.loads((store.reports_dir / "failure-fingerprints.json").read_text())
            self.assertEqual(1, len(persisted))
            self.assertEqual(["tests/auth/test_login.py"], persisted[0]["relevant_paths"])

    def test_repeated_fingerprint_increments_occurrence_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            store = RunStore(repo_root, "run-002")
            store.initialize(repo_contract={}, run_contract={})
            fingerprints = FailureFingerprintStore(store)

            first = fingerprints.record(
                phase="LOCAL_VERIFY",
                command="lint",
                error_signature="Missing semicolon",
                relevant_paths=["src/app.ts"],
                evidence_refs=["artifacts/logs/lint.stderr.log"],
            )
            second = fingerprints.record(
                phase="LOCAL_VERIFY",
                command="lint",
                error_signature="Missing semicolon",
                relevant_paths=["src/app.ts", "src/shared.ts"],
                evidence_refs=["artifacts/logs/lint.stdout.log"],
            )

            self.assertEqual(first.fingerprint, second.fingerprint)
            self.assertEqual(2, second.occurrence_count)
            self.assertEqual(("src/app.ts", "src/shared.ts"), second.relevant_paths)
            self.assertTrue(fingerprints.has_repeat(second.fingerprint, threshold=2))


if __name__ == "__main__":
    unittest.main()

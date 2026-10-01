"""Guard CI workflow against drifting away from scripts/verify-local.sh."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github/workflows/ci.yml"


class CiWorkflowParityTests(unittest.TestCase):
    def test_python_job_delegates_to_verify_local_script(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "bash scripts/verify-local.sh",
            text,
            "CI must call the offline parity entrypoint",
        )
        self.assertNotIn(
            "unittest discover",
            text,
            "Do not duplicate verify steps in ci.yml — extend scripts/verify-local.sh",
        )
        self.assertNotIn(
            "compileall",
            text,
            "Do not duplicate verify steps in ci.yml — extend scripts/verify-local.sh",
        )


if __name__ == "__main__":
    unittest.main()

"""Smoke tests for scripts/verify-local.sh (fast; no full unittest discover)."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify-local.sh"


class VerifyLocalEntrypointTests(unittest.TestCase):
    def test_verify_script_exists_and_is_executable(self) -> None:
        self.assertTrue(VERIFY_SCRIPT.is_file(), "scripts/verify-local.sh must exist")
        mode = VERIFY_SCRIPT.stat().st_mode
        self.assertTrue(mode & 0o111, "scripts/verify-local.sh must be executable")

    def test_governance_only_subprocess_exits_zero(self) -> None:
        proc = subprocess.run(
            ["bash", str(VERIFY_SCRIPT), "--governance-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}",
        )
        self.assertIn("governance smoke OK", proc.stdout)

    def test_help_exits_zero(self) -> None:
        proc = subprocess.run(
            ["bash", str(VERIFY_SCRIPT), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("verify-local.sh", proc.stdout)


if __name__ == "__main__":
    unittest.main()

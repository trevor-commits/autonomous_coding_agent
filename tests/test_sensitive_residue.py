from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from supervisor.sensitive_residue import (
    changed_sensitive_residue,
    snapshot_sensitive_residue,
)


class SensitiveResidueTests(unittest.TestCase):
    def test_nested_secret_and_control_residue_is_detected_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("root metadata is outside the scan\n")
            (root / ".autoclaw").mkdir()
            (root / ".autoclaw" / "state.json").write_text("root runtime is excluded\n")
            baseline = snapshot_sensitive_residue(root)

            (root / "src" / "nested" / ".git").mkdir(parents=True)
            (root / "src" / "nested" / ".git" / "config").write_text("nested\n")
            (root / "apps" / "web").mkdir(parents=True)
            (root / "apps" / "web" / ".env.local").write_text("secret\n")
            (root / "src" / ".agent").mkdir()
            (root / "src" / ".agent" / "state.json").write_text("{}\n")
            (root / "src" / "nested" / ".autoclaw").mkdir()
            (root / "src" / "nested" / ".autoclaw" / "state.json").write_text(
                "{}\n"
            )

            current = snapshot_sensitive_residue(root)
            changed = changed_sensitive_residue(baseline, current)

            self.assertIn("src/nested/.git", changed)
            self.assertIn("src/nested/.git/config", changed)
            self.assertIn("apps/web/.env.local", changed)
            self.assertIn("src/.agent/state.json", changed)
            self.assertIn("src/nested/.autoclaw/state.json", changed)
            self.assertNotIn(".git/config", current)
            self.assertNotIn(".autoclaw/state.json", current)

    def test_unchanged_preexisting_sensitive_files_remain_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / ".env.example").write_text("placeholder\n")
            baseline = snapshot_sensitive_residue(root)
            self.assertEqual(
                (),
                changed_sensitive_residue(baseline, snapshot_sensitive_residue(root)),
            )

            (root / "src" / ".env.example").write_text("changed\n")
            self.assertEqual(
                ("src/.env.example",),
                changed_sensitive_residue(baseline, snapshot_sensitive_residue(root)),
            )

    def test_permission_widening_changes_sensitive_residue_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            secret = root / "src" / ".env.local"
            secret.write_text("secret\n")
            secret.chmod(0o600)
            baseline = snapshot_sensitive_residue(root)

            secret.chmod(0o644)

            self.assertEqual(
                ("src/.env.local",),
                changed_sensitive_residue(baseline, snapshot_sensitive_residue(root)),
            )


if __name__ == "__main__":
    unittest.main()

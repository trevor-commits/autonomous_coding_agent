from __future__ import annotations

import unittest
from pathlib import Path

from supervisor.contracts import load_repo_contract


class PartnerWorkspaceContractTests(unittest.TestCase):
    def test_repo_can_host_bounded_partner_project_worktrees(self) -> None:
        root = Path(__file__).resolve().parent.parent
        contract = load_repo_contract(root)

        self.assertEqual("python-library", contract.stack)
        self.assertEqual("python3 -m unittest discover -s tests -v", contract.commands.test)
        self.assertIsNotNone(contract.commands.app_up)
        self.assertIsNotNone(contract.commands.app_health)

    def test_archived_partner_change_has_complete_canonical_discovery(self) -> None:
        root = Path(__file__).resolve().parent.parent
        active_change = "openspec/changes/autonomous-partner-reposition/"
        for relative_path in ("GUIDE.md", "STRUCTURE.md", "README.md"):
            with self.subTest(path=relative_path):
                self.assertNotIn(active_change, (root / relative_path).read_text(encoding="utf-8"))

        for spec_path in sorted((root / "openspec" / "specs").glob("*/spec.md")):
            with self.subTest(spec=spec_path.parent.name):
                text = spec_path.read_text(encoding="utf-8")
                self.assertNotIn("TBD - created by archiving change", text)
                self.assertRegex(text, r"## Purpose\n\S")


if __name__ == "__main__":
    unittest.main()

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


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class AgentHarnessTests(unittest.TestCase):
    def test_agents_md_is_portable_thin_pointer(self) -> None:
        text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertNotIn("/Users/gillettes/Coding Projects", text)
        self.assertIn("AGENTS.project.md", text)
        self.assertIn("docs/coordinator-fleet.md", text)
        self.assertLessEqual(len(text.splitlines()), 45)

    def test_claude_md_routes_without_mac_paths(self) -> None:
        text = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("AGENTS.md", text)
        self.assertIn("docs/coordinator-fleet.md", text)
        self.assertNotIn("/Users/gillettes", text)
        self.assertLessEqual(len(text.splitlines()), 30)

    def test_coordinator_fleet_doc_exists(self) -> None:
        path = REPO_ROOT / "docs" / "coordinator-fleet.md"
        self.assertTrue(path.is_file())
        body = path.read_text(encoding="utf-8")
        self.assertIn("One branch, one PR", body)


if __name__ == "__main__":
    unittest.main()

"""Governance and navigation portability checks mirrored from scripts/verify-local.sh.

Keep NAV_DOCS in sync with the portability loop in scripts/verify-local.sh run_governance_smoke().
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ACA_ABSOLUTE = "/Users/gillettes/Coding Projects/Autonomous Coding Agent/"
NAV_DOCS = (
    "GUIDE.md",
    "README.md",
    "AGENTS.md",
    "design-history/README.md",
)


class GovernancePortabilityTests(unittest.TestCase):
    def test_agents_project_has_single_repo_principles_heading(self) -> None:
        text = (REPO_ROOT / "AGENTS.project.md").read_text(encoding="utf-8")
        headings = re.findall(r"^## Repo Principles\b", text, flags=re.MULTILINE)
        self.assertEqual(
            len(headings),
            1,
            "AGENTS.project.md must expose exactly one ## Repo Principles heading",
        )

    def test_operator_verify_docs_exist(self) -> None:
        self.assertTrue((REPO_ROOT / "docs" / "local-verification.md").is_file())
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("scripts/verify-local.sh", readme)
        guide = (REPO_ROOT / "GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("scripts/verify-local.sh", guide)
        plan = (REPO_ROOT / "IMPLEMENTATION-PLAN.md").read_text(encoding="utf-8")
        self.assertIn("scripts/verify-local.sh", plan)
        self.assertIn("docs/local-verification.md", plan)
        agents = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("scripts/verify-local.sh", agents)
        ci = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("bash scripts/verify-local.sh", ci)

    def test_local_verification_doc_has_operator_contract_sections(self) -> None:
        text = (REPO_ROOT / "docs" / "local-verification.md").read_text(encoding="utf-8")
        for heading in (
            "## Default path (CI parity)",
            "## Expected unittest volume (offline clone)",
            "## Troubleshooting",
            "## Open draft PR survey",
        ):
            self.assertIn(heading, text, f"missing section {heading!r} in docs/local-verification.md")
        self.assertIn("259", text, "expected offline test count baseline documented")
        self.assertRegex(text, r"\|\s*\*\*12\*\*\s*\|", msg="expected skip count baseline documented")

    def test_live_nav_docs_avoid_absolute_aca_checkout_paths(self) -> None:
        offenders: list[str] = []
        for rel in NAV_DOCS:
            path = REPO_ROOT / rel
            if ACA_ABSOLUTE in path.read_text(encoding="utf-8"):
                offenders.append(rel)
        self.assertEqual(
            offenders,
            [],
            f"absolute ACA checkout paths found in: {', '.join(offenders)}",
        )


if __name__ == "__main__":
    unittest.main()

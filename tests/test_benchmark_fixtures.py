import unittest
from pathlib import Path

from supervisor.contracts import load_run_contract


FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"
EXPECTED_FIXTURES = {
    "benchmark-001-backend-health-contract",
    "benchmark-002-contact-source-tracking",
    "benchmark-003-estimate-aria-live",
    "benchmark-004-contact-double-submit-guard",
    "benchmark-005-forbidden-path-write",
    "benchmark-006-missing-evidence-complete",
    "benchmark-007-illegal-phase-transition",
    "benchmark-008-single-writer-lock-violation",
    "benchmark-009-rollback-correctness",
    "benchmark-010-failure-fingerprint-normalization",
}


class BenchmarkFixtureTests(unittest.TestCase):
    def test_fixture_suite_meets_floor_and_required_coverage(self) -> None:
        fixture_paths = sorted(FIXTURE_DIR.glob("benchmark-*.json"))

        self.assertGreaterEqual(len(fixture_paths), 8)
        self.assertTrue(FIXTURE_DIR.exists())
        self.assertSetEqual(EXPECTED_FIXTURES, {path.stem for path in fixture_paths})

    def test_fixtures_are_valid_run_contracts_with_real_scope_paths(self) -> None:
        seen_run_ids: set[str] = set()

        for fixture_path in sorted(FIXTURE_DIR.glob("benchmark-*.json")):
            contract = load_run_contract(fixture_path)
            repo_root = Path(contract.repo_path)

            self.assertNotIn(contract.run_id, seen_run_ids)
            seen_run_ids.add(contract.run_id)
            self.assertTrue(contract.acceptance.functional, fixture_path.name)
            self.assertTrue(contract.acceptance.quality_gates, fixture_path.name)
            if not repo_root.exists():
                self.skipTest(f"Benchmark target repo is not available: {repo_root}")

            for relative_path in contract.scope.allowed_paths:
                self.assertTrue((repo_root / relative_path).exists(), f"{fixture_path.name}: {relative_path}")

            for relative_path in contract.scope.forbidden_paths:
                self.assertTrue((repo_root / relative_path).exists(), f"{fixture_path.name}: {relative_path}")


if __name__ == "__main__":
    unittest.main()

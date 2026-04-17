import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from supervisor.contracts import load_run_contract
from supervisor.policy import (
    BudgetExceededError,
    ShellClass,
    classify_command,
    classify_path_change,
    enforce_budget,
    enforce_scope,
)


def _write_run_contract(path: Path) -> None:
    path.write_text(
        """
{
  "run_id": "run-001",
  "repo_path": "/tmp/repo",
  "objective": "Example",
  "scope": {
    "allowed_paths": ["src/", "tests/"],
    "forbidden_paths": [".env", "infra/"]
  },
  "acceptance": {
    "functional": ["works"],
    "quality_gates": ["tests pass"],
    "ui_checks": []
  },
  "constraints": {
    "single_writer": true,
    "max_repair_loops": 4,
    "max_iterations": 10,
    "max_cost_dollars": 5.0,
    "hard_timeout_seconds": 60
  }
}
""".strip()
    )


class PolicyTests(unittest.TestCase):
    def test_deny_list_command_is_blocked(self) -> None:
        decision = classify_command("git push origin main")
        self.assertEqual(ShellClass.AUTO_DENY, decision.shell_class)

    def test_install_command_requires_escalation(self) -> None:
        decision = classify_command("pnpm install")
        self.assertEqual(ShellClass.ESCALATE, decision.shell_class)

    def test_auth_and_infra_paths_require_escalation(self) -> None:
        self.assertEqual(
            ShellClass.ESCALATE,
            classify_path_change("apps/api/src/auth/login.ts").shell_class,
        )
        self.assertEqual(
            ShellClass.ESCALATE,
            classify_path_change(".github/workflows/ci.yml").shell_class,
        )

    def test_secret_file_write_is_denied(self) -> None:
        decision = classify_path_change(".env.local")
        self.assertEqual(ShellClass.AUTO_DENY, decision.shell_class)

    def test_scope_enforcement_uses_run_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            src_file = repo_root / "src" / "main.ts"
            src_file.parent.mkdir(parents=True)
            src_file.touch()
            forbidden = repo_root / "infra" / "prod.tf"
            forbidden.parent.mkdir(parents=True)
            forbidden.touch()

            contract_path = repo_root / "run-contract.json"
            _write_run_contract(contract_path)
            contract = load_run_contract(contract_path)

            enforce_scope(repo_root, contract, src_file)
            with self.assertRaises(Exception):
                enforce_scope(repo_root, contract, forbidden)

    def test_budget_enforcement_blocks_iterations_cost_and_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / "run-contract.json"
            _write_run_contract(contract_path)
            contract = load_run_contract(contract_path)

            started_at = datetime.now(timezone.utc) - timedelta(seconds=120)
            with self.assertRaises(BudgetExceededError):
                enforce_budget(
                    contract,
                    iterations_used=11,
                    cost_spent=1.0,
                    started_at=started_at,
                )
            with self.assertRaises(BudgetExceededError):
                enforce_budget(
                    contract,
                    iterations_used=1,
                    cost_spent=10.0,
                    started_at=datetime.now(timezone.utc),
                )
            with self.assertRaises(BudgetExceededError):
                enforce_budget(
                    contract,
                    iterations_used=1,
                    cost_spent=1.0,
                    started_at=started_at,
                    now=datetime.now(timezone.utc),
                )


if __name__ == "__main__":
    unittest.main()

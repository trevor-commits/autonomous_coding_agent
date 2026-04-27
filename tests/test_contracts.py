import json
import tempfile
import unittest
from pathlib import Path

import yaml

from supervisor.contracts import ContractValidationError, load_repo_contract, load_run_contract
from supervisor.models import RunState


def _valid_repo_contract() -> dict:
    return {
        "version": 1,
        "stack": "fullstack-web",
        "commands": {
            "setup": "pnpm install",
            "test": "pnpm test",
            "app_up": "pnpm dev",
            "app_health": "http://127.0.0.1:3000/api/health",
            "lint": "pnpm lint",
        },
        "ui": {
            "base_url": "http://127.0.0.1:3000",
            "breakpoints": ["390x844"],
            "critical_flows": [
                {
                    "id": "login",
                    "route": "/login",
                    "assertions": ["login form visible"],
                }
            ],
        },
    }


def _valid_run_contract(repo_path: str) -> dict:
    return {
        "run_id": "benchmark-001",
        "repo_path": repo_path,
        "objective": "Add login validation",
        "scope": {
            "allowed_paths": ["src/", "tests/"],
            "forbidden_paths": [".env", "infra/"],
        },
        "acceptance": {
            "functional": ["Login form shows error"],
            "quality_gates": ["tests pass"],
            "ui_checks": ["No console errors"],
        },
        "constraints": {
            "single_writer": True,
            "auto_push": False,
            "auto_merge": False,
            "max_repair_loops": 4,
            "max_iterations": 10,
            "max_cost_dollars": 5.0,
            "hard_timeout_seconds": 600,
        },
    }


class ContractParsingTests(unittest.TestCase):
    def test_load_repo_contract_parses_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / ".agent" / "contract.yml"
            contract_path.parent.mkdir(parents=True)
            contract_path.write_text(yaml.safe_dump(_valid_repo_contract()))

            contract = load_repo_contract(repo_root)

            self.assertEqual("fullstack-web", contract.stack)
            self.assertEqual("pnpm install", contract.commands.setup)
            self.assertEqual(("390x844",), contract.ui.breakpoints)

    def test_missing_required_repo_commands_returns_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            contract_path = repo_root / ".agent" / "contract.yml"
            contract_path.parent.mkdir(parents=True)
            payload = _valid_repo_contract()
            del payload["commands"]["setup"]
            contract_path.write_text(yaml.safe_dump(payload))

            with self.assertRaises(ContractValidationError) as ctx:
                load_repo_contract(repo_root)

            self.assertEqual(RunState.UNSUPPORTED, ctx.exception.run_state)

    def test_load_run_contract_parses_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "run-contract.json"
            contract_path.write_text(json.dumps(_valid_run_contract("/tmp/repo")))

            contract = load_run_contract(contract_path)

            self.assertEqual("benchmark-001", contract.run_id)
            self.assertEqual(("src", "tests"), contract.scope.allowed_paths)
            self.assertEqual((".env", "infra"), contract.scope.forbidden_paths)
            self.assertEqual(False, contract.constraints.auto_push)

    def test_invalid_scope_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "run-contract.json"
            payload = _valid_run_contract("/tmp/repo")
            payload["scope"]["allowed_paths"] = ["/absolute/path"]
            contract_path.write_text(json.dumps(payload))

            with self.assertRaises(ContractValidationError) as ctx:
                load_run_contract(contract_path)

            self.assertEqual(RunState.UNSUPPORTED, ctx.exception.run_state)

    def test_parent_traversal_scope_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "run-contract.json"
            payload = _valid_run_contract("/tmp/repo")
            payload["scope"]["allowed_paths"] = ["../outside"]
            contract_path.write_text(json.dumps(payload))

            with self.assertRaises(ContractValidationError) as ctx:
                load_run_contract(contract_path)

            self.assertEqual(RunState.UNSUPPORTED, ctx.exception.run_state)

    def test_scope_enforcement_blocks_forbidden_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            allowed = repo_root / "src" / "feature.ts"
            forbidden = repo_root / ".env"
            allowed.parent.mkdir(parents=True)
            allowed.touch()
            forbidden.touch()

            contract_path = repo_root / "run-contract.json"
            contract_path.write_text(json.dumps(_valid_run_contract(str(repo_root))))
            contract = load_run_contract(contract_path)

            contract.scope.assert_allows(repo_root, allowed)
            with self.assertRaises(ContractValidationError) as ctx:
                contract.scope.assert_allows(repo_root, forbidden)
            self.assertEqual(RunState.BLOCKED, ctx.exception.run_state)


if __name__ == "__main__":
    unittest.main()

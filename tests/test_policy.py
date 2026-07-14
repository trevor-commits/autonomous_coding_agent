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

    def test_absolute_denials_override_repo_and_explicit_allowlists(self) -> None:
        commands = (
            "git push origin main",
            "git -C . push origin main",
            "eval 'git push origin main'",
            "env -S 'git push origin main'",
            "alias gp='git push'; gp origin main",
            "git -c alias.x=push x origin main",
            "git -c 'alias.x=!git push' x",
            "git --config-env=alias.x=GIT_ALIAS x origin main",
            "git x origin main",
            "x=git; $x push origin main",
            "GIT_EXTERNAL_DIFF=/tmp/pwn git diff",
            "GIT_PAGER=/tmp/pwn git log -1",
            "PAGER=/tmp/pwn git log -1",
            "GIT_CONFIG_SYSTEM=/tmp/config git status",
            "GIT_CONFIG_GLOBAL=/tmp/config git diff",
            "git diff --ext-diff",
            "git log --textconv --all",
            "python3 -c 'import os; os.system(\"git push origin main\")'",
            "python3 -m pip install local-package",
            "python -m venv .venv",
            'node -e \'require("child_process").execSync("git push origin main")\'',
            "perl -e 'system(\"git push origin main\")'",
            "ruby -e 'system(\"git push origin main\")'",
            "awk 'BEGIN { system(\"git push origin main\") }'",
            "bash -c 'git push origin main'",
            "bash -s",
            "bash <(printf unsafe)",
            "bash /tmp/test.sh",
            "bash ../test.sh",
            "printf ok && git push origin main",
            "zsh -lc 'printf ok; sudo true'",
            "osascript -e 'tell application \"Finder\" to activate'",
            "curl https://example.com",
            "say hello",
            "rm -r -f generated",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(
                    ShellClass.AUTO_DENY,
                    classify_command(command, allowed_commands=(command,)).shell_class,
                )

    def test_read_only_git_builtins_can_be_exact_contract_commands(self) -> None:
        commands = (
            "git status -sb",
            "git -C . status --short",
            "git rev-parse --show-toplevel",
            "git log -1 --oneline",
            "git diff --check",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(
                    ShellClass.AUTO_ALLOW,
                    classify_command(command, allowed_commands=(command,)).shell_class,
                )

    def test_bounded_scripts_and_test_environment_remain_contract_eligible(
        self,
    ) -> None:
        commands = (
            "bash scripts/test.sh",
            "sh scripts/test.sh --quick",
            "CI=1 pnpm test",
            "NODE_ENV=test npm test",
            "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(
                    ShellClass.AUTO_ALLOW,
                    classify_command(command, allowed_commands=(command,)).shell_class,
                )

    def test_install_command_requires_escalation(self) -> None:
        decision = classify_command("pnpm install")
        self.assertEqual(ShellClass.ESCALATE, decision.shell_class)

    def test_unknown_command_is_not_auto_allowed(self) -> None:
        decision = classify_command("mystery-tool --perform-unclassified-action")
        self.assertIsNot(ShellClass.AUTO_ALLOW, decision.shell_class)

    def test_bounded_read_only_find_is_allowed(self) -> None:
        commands = (
            "find . -maxdepth 2 -name AGENTS.project.md -o -name PROJECT_INTENT.md -o -name todo.md",
            "find partner-projects/proposal-001 -maxdepth 3 -type f | sort",
            "pwd && rg --files -g '!*tests*' -g '!*.env*' partner-projects/proposal-001 | sed -n '1,120p'",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(
                    ShellClass.AUTO_ALLOW,
                    classify_command(command).shell_class,
                )

    def test_effectful_or_unbounded_find_is_not_auto_allowed(self) -> None:
        commands = (
            "find . -delete",
            "find . -exec rm -rf {} ;",
            "find / -name '*.pem'",
            "find ../outside -name '*.md'",
            "find . -name '*.md' | xargs rm",
            "find . -type f | sort -o /tmp/exfiltrated",
            "find . -type f | sort && rm -rf safe-looking-name",
            "find . -type f | uniq",
            "rg --files ../outside",
            "rg --files --pre 'rm -rf /' .",
            "rg --files . | sed -i backup",
            "rg --files . > /tmp/repo-files",
            "pwd && mystery-tool --perform-unclassified-action",
            "git checkout main",
            "git branch new-branch",
            "git fetch origin",
            "git rev-parse HEAD",
            "git diff -- .env",
            "git status -sb",
            "git diff --check",
            "find .\ntouch owned",
            "find $HOME -name '*.pem'",
            "find ~ -maxdepth 1",
            "find `touch owned`",
            "find $(touch owned)",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNot(
                    ShellClass.AUTO_ALLOW, classify_command(command).shell_class
                )

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
        for path in (
            ".env.local",
            "src/.env",
            "apps/web/.env.production",
            "tools/.envrc",
            "src/nested/.git/config",
            "src/.agent/state.json",
            ".autoclaw/guard.json",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    ShellClass.AUTO_DENY, classify_path_change(path).shell_class
                )

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

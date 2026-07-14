from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from supervisor.builder_guard import evaluate_hook_payload


class BuilderGuardTests(unittest.TestCase):
    def _policy(self, root: Path) -> Path:
        path = root.parent / "builder-policy.json"
        path.write_text(
            json.dumps(
                {
                    "repo_root": str(root),
                    "allowed_paths": ["src/", "tests/"],
                    "forbidden_paths": ["src/private/", ".env"],
                    "allowed_commands": ["python3 -m unittest"],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_bash_command_is_denied_before_execution_unless_exactly_allowed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            policy = self._policy(root)

            allowed = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "cwd": str(root),
                    "tool_input": {"command": "/bin/zsh -lc 'python3 -m unittest'"},
                },
                policy_path=policy,
            )
            denied = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "cwd": str(root),
                    "tool_input": {"command": "touch owned"},
                },
                policy_path=policy,
            )

            self.assertIsNone(allowed)
            self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])
            self.assertFalse((root / "owned").exists())

    def test_absolute_command_denial_overrides_guard_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            policy = self._policy(root)
            payload = json.loads(policy.read_text())
            payload["allowed_commands"].extend(
                ["git push origin main", "printf ok && git push origin main"]
            )
            policy.write_text(json.dumps(payload))

            for command in payload["allowed_commands"][-2:]:
                with self.subTest(command=command):
                    denied = evaluate_hook_payload(
                        {
                            "hook_event_name": "PreToolUse",
                            "tool_name": "Bash",
                            "cwd": str(root),
                            "tool_input": {"command": command},
                        },
                        policy_path=policy,
                    )
                    self.assertEqual(
                        "deny", denied["hookSpecificOutput"]["permissionDecision"]
                    )

    def test_apply_patch_is_denied_before_execution_for_out_of_scope_paths(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            policy = self._policy(root)

            allowed = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "apply_patch",
                    "cwd": str(root),
                    "tool_input": {
                        "command": "*** Begin Patch\n*** Add File: src/feature.py\n+ok\n*** End Patch"
                    },
                },
                policy_path=policy,
            )
            forbidden = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "apply_patch",
                    "cwd": str(root),
                    "tool_input": {
                        "command": "*** Begin Patch\n*** Add File: src/private/key.txt\n+no\n*** End Patch"
                    },
                },
                policy_path=policy,
            )
            outside = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "apply_patch",
                    "cwd": str(root),
                    "tool_input": {
                        "command": "*** Begin Patch\n*** Add File: ../owned\n+no\n*** End Patch"
                    },
                },
                policy_path=policy,
            )

            self.assertIsNone(allowed)
            self.assertEqual(
                "deny", forbidden["hookSpecificOutput"]["permissionDecision"]
            )
            self.assertEqual(
                "deny", outside["hookSpecificOutput"]["permissionDecision"]
            )

    def test_apply_patch_denies_nested_secret_and_control_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            policy = self._policy(root)

            for path in (
                "src/.env",
                "src/nested/.git/config",
                "src/.agent/state.json",
                "src/nested/.autoclaw/state.json",
            ):
                with self.subTest(path=path):
                    denied = evaluate_hook_payload(
                        {
                            "hook_event_name": "PreToolUse",
                            "tool_name": "apply_patch",
                            "cwd": str(root),
                            "tool_input": {
                                "command": (
                                    f"*** Begin Patch\n*** Add File: {path}\n+blocked\n*** End Patch"
                                )
                            },
                        },
                        policy_path=policy,
                    )
                    self.assertEqual(
                        "deny", denied["hookSpecificOutput"]["permissionDecision"]
                    )

    def test_malformed_or_wrong_cwd_hook_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            root.mkdir()
            policy = self._policy(root)

            malformed = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "cwd": str(root),
                },
                policy_path=policy,
            )
            wrong_cwd = evaluate_hook_payload(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "cwd": str(root.parent),
                    "tool_input": {"command": "python3 -m unittest"},
                },
                policy_path=policy,
            )

            self.assertEqual(
                "deny", malformed["hookSpecificOutput"]["permissionDecision"]
            )
            self.assertEqual(
                "deny", wrong_cwd["hookSpecificOutput"]["permissionDecision"]
            )


if __name__ == "__main__":
    unittest.main()

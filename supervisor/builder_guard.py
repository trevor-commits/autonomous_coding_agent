from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

# The hook is invoked by absolute script path from a target repository, so make
# the ACA package importable without depending on the target's PYTHONPATH.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supervisor.contracts import ContractValidationError, RunScope
from supervisor.policy import ShellClass, classify_command, classify_path_change


class BuilderGuardError(ValueError):
    """Raised when a builder tool request cannot be proven safe pre-effect."""


def evaluate_hook_payload(
    payload: Mapping[str, Any], *, policy_path: Path | str
) -> dict[str, Any] | None:
    """Return a Codex PreToolUse denial, or None only for a proven-safe call."""

    try:
        policy = _load_policy(policy_path)
        _validate_common_payload(payload, policy)
        tool_name = payload.get("tool_name")
        tool_input = payload.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, Mapping) else None
        if not isinstance(command, str) or not command:
            raise BuilderGuardError("tool input lacks a command")
        if tool_name == "Bash":
            _allow_bash(command, policy)
        elif tool_name == "apply_patch":
            _allow_patch(command, policy)
        else:
            raise BuilderGuardError("tool is outside the bounded builder surface")
    except (BuilderGuardError, ContractValidationError, OSError, ValueError, json.JSONDecodeError):
        return _denial()
    return None


def normalize_builder_command(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise BuilderGuardError("shell command cannot be parsed") from exc
    if (
        len(tokens) == 3
        and Path(tokens[0]).name in {"bash", "sh", "zsh"}
        and tokens[1] in {"-c", "-lc"}
    ):
        return tokens[2]
    return command


def _load_policy(path: Path | str) -> dict[str, Any]:
    policy_path = Path(path)
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    required = {"repo_root", "allowed_paths", "forbidden_paths", "allowed_commands"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise BuilderGuardError("guard policy shape is invalid")
    if not isinstance(payload["repo_root"], str):
        raise BuilderGuardError("guard repo root is invalid")
    for field in ("allowed_paths", "forbidden_paths", "allowed_commands"):
        values = payload[field]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise BuilderGuardError(f"guard {field} is invalid")
    if not payload["allowed_paths"]:
        raise BuilderGuardError("guard must include an allowed path")
    payload["repo_root"] = str(Path(payload["repo_root"]).resolve())
    return payload


def _validate_common_payload(payload: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise BuilderGuardError("hook payload is invalid")
    if payload.get("hook_event_name") != "PreToolUse":
        raise BuilderGuardError("hook event is invalid")
    if payload.get("tool_name") not in {"Bash", "apply_patch"}:
        raise BuilderGuardError("hook tool is invalid")
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or str(Path(cwd).resolve()) != policy["repo_root"]:
        raise BuilderGuardError("hook cwd differs from the guarded repository")


def _allow_bash(command: str, policy: Mapping[str, Any]) -> None:
    normalized = normalize_builder_command(command)
    decision = classify_command(
        normalized,
        allowed_commands=tuple(policy["allowed_commands"]),
    )
    if decision.shell_class is not ShellClass.AUTO_ALLOW:
        raise BuilderGuardError("shell command is outside the allowlist")


def _allow_patch(command: str, policy: Mapping[str, Any]) -> None:
    lines = command.splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise BuilderGuardError("patch framing is invalid")
    prefixes = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")
    paths: list[str] = []
    for line in lines[1:-1]:
        prefix = next((candidate for candidate in prefixes if line.startswith(candidate)), None)
        if prefix is not None:
            paths.append(line[len(prefix) :])
        elif line.startswith("*** ") and line != "*** End of File":
            raise BuilderGuardError("patch contains an unknown control header")
    if not paths:
        raise BuilderGuardError("patch does not declare a file operation")

    root = Path(policy["repo_root"])
    scope = RunScope(
        allowed_paths=tuple(policy["allowed_paths"]),
        forbidden_paths=tuple(policy["forbidden_paths"]),
    )
    for relative_path in paths:
        if (
            not relative_path
            or relative_path != relative_path.strip()
            or "\x00" in relative_path
            or PurePosixPath(relative_path).is_absolute()
            or ".." in PurePosixPath(relative_path).parts
        ):
            raise BuilderGuardError("patch path is invalid")
        scope.assert_allows(root, root / relative_path)
        if classify_path_change(relative_path).shell_class is not ShellClass.AUTO_ALLOW:
            raise BuilderGuardError("patch path is outside the normal write surface")


def _denial() -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Blocked by the supervisor's pre-effect builder policy.",
        }
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, ValueError):
        payload = {}
    decision = evaluate_hook_payload(payload, policy_path=args.policy)
    if decision is not None:
        sys.stdout.write(json.dumps(decision, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

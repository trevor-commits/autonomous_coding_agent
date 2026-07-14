from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Sequence

from supervisor.policy import ShellClass, classify_command, classify_path_change
from supervisor.process_runner import run_process_group


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass
class BuilderSession:
    worktree_path: Path
    run_context: dict[str, Any]
    session_id: str | None = None
    turn_count: int = 0
    cumulative_changed_files: tuple[str, ...] = ()
    guard_policy_path: Path | None = None
    runtime_dir: Path | None = None
    tool_environment: dict[str, str] | None = None


@dataclass(frozen=True)
class BuilderResult:
    session_id: str | None
    status: str
    final_message: str
    files_changed: tuple[str, ...]
    commands_run: tuple[str, ...]
    duration_seconds: float
    raw_events: tuple[dict[str, Any], ...]


class BuilderAdapter(ABC):
    @abstractmethod
    def start_session(
        self, worktree_path: Path, run_context: dict[str, Any]
    ) -> BuilderSession:
        raise NotImplementedError

    @abstractmethod
    def send_task(
        self, session: BuilderSession, prompt: str, timeout: int
    ) -> BuilderResult:
        raise NotImplementedError

    @abstractmethod
    def close_session(self, session: BuilderSession) -> None:
        raise NotImplementedError


def build_builder_prompt(
    run_context: dict[str, Any],
    task_description: str,
    *,
    prior_failure_fingerprints: Sequence[str] = (),
) -> str:
    allowed_paths = ", ".join(run_context.get("allowed_paths", ())) or "n/a"
    forbidden_paths = ", ".join(run_context.get("forbidden_paths", ())) or "n/a"
    repo_commands = run_context.get(
        "supervisor_commands", run_context.get("repo_commands", {})
    )
    command_lines = [
        f"- {name}: {command}"
        for name, command in sorted(repo_commands.items())
        if command
    ] or ["- none recorded"]
    failure_lines = [
        f"- {fingerprint}" for fingerprint in prior_failure_fingerprints
    ] or ["- none"]

    sections = [
        "You are the bounded builder for a supervisor-owned run.",
        "",
        "Goal:",
        f"- {run_context.get('objective', 'No objective provided.')}",
        "",
        "Task:",
        f"- {task_description}",
        "",
        "Allowed paths:",
        f"- {allowed_paths}",
        "",
        "Forbidden paths:",
        f"- {forbidden_paths}",
        "",
        "Supervisor-owned repo checks (listed for context; do not run these yourself):",
        *command_lines,
        "",
        "Prior failure fingerprints:",
        *failure_lines,
        "",
        "Hard constraints:",
        "- Do not commit, push, switch branches, or control a browser.",
        "- Do not write outside allowed paths.",
        "- Treat any high-risk operation as unsupported in this phase.",
        "- Do not execute repo code or repo-contract checks; the supervisor runs them after your turn.",
        "- Execute no shell command outside these bounded read-only forms: "
        "`pwd`; relative-path `find` optionally piped to exact `sort`; "
        "and `rg --files` with bounded glob/relative-path arguments optionally piped to "
        "`sed -n '<start>,<end>p'`. Exact safe forms may be chained with `&&`.",
        "- If another shell command appears necessary, report it as a blocker instead of running it.",
        "",
        "Required response:",
        "- files changed",
        "- bounded discovery commands run",
        "- result",
        "- residual risks",
        "",
    ]
    return "\n".join(sections)


class CodexBuilderAdapter(BuilderAdapter):
    _PERMISSION_PROFILE = "aca_builder"

    def __init__(
        self,
        *,
        codex_bin: str = "codex",
        runner: Runner | None = None,
        git_runner: Runner | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        self.codex_bin = codex_bin
        self.runner = runner or run_process_group
        self.git_runner = git_runner or subprocess.run
        self.model = model
        if reasoning_effort not in {None, "low", "medium", "high", "xhigh"}:
            raise ValueError("reasoning_effort must be low, medium, high, or xhigh")
        self.reasoning_effort = reasoning_effort

    def start_session(
        self, worktree_path: Path, run_context: dict[str, Any]
    ) -> BuilderSession:
        resolved_worktree = Path(worktree_path).resolve()
        _assert_safe_runtime_ancestry(resolved_worktree)
        runtime_dir = (
            resolved_worktree / ".autoclaw" / "builder-runtime" / uuid.uuid4().hex
        )
        runtime_dir.mkdir(parents=True, exist_ok=False)
        session = BuilderSession(
            worktree_path=resolved_worktree,
            run_context=dict(run_context),
            runtime_dir=runtime_dir,
        )
        try:
            self._prepare_session(session, run_context)
        except Exception:
            shutil.rmtree(runtime_dir, ignore_errors=True)
            raise
        return session

    def _prepare_session(
        self,
        session: BuilderSession,
        run_context: dict[str, Any],
    ) -> None:
        resolved_worktree = session.worktree_path
        if session.runtime_dir is None:
            raise ValueError("Builder session runtime state is incomplete.")
        runtime_dir = session.runtime_dir
        self._permission_profile_config(session)
        original_commands = {
            name: command
            for name, command in run_context.get("repo_commands", {}).items()
            if isinstance(name, str) and isinstance(command, str) and command
        }
        for name, command in sorted(original_commands.items()):
            decision = classify_command(command, allowed_commands=(command,))
            if decision.shell_class is not ShellClass.AUTO_ALLOW:
                raise ValueError(
                    f"Repo command `{name}` cannot enter the builder allowlist: {decision.reason}."
                )
        session.run_context["supervisor_commands"] = original_commands
        session.run_context["repo_commands"] = {}
        session.tool_environment = _builder_tool_environment(runtime_dir)
        policy = {
            "repo_root": str(resolved_worktree),
            "allowed_paths": list(run_context.get("allowed_paths", ())),
            "forbidden_paths": list(run_context.get("forbidden_paths", ())),
            "allowed_commands": [],
        }
        policy_path = runtime_dir / "builder-policy.json"
        policy_path.write_text(
            json.dumps(policy, sort_keys=True) + "\n", encoding="utf-8"
        )
        policy_path.chmod(0o600)
        session.guard_policy_path = policy_path

    def send_task(
        self, session: BuilderSession, prompt: str, timeout: int
    ) -> BuilderResult:
        started = time.monotonic()
        output_last_path = self._temp_output_path(session)
        try:
            args = self._build_args(session, prompt, output_last_path)
            try:
                completed = self.runner(
                    args,
                    cwd=session.worktree_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False,
                )
                status = "completed" if completed.returncode == 0 else "failed"
                stdout = completed.stdout
                stderr = completed.stderr
            except subprocess.TimeoutExpired as exc:
                stdout = _coerce_subprocess_output(exc.stdout)
                stderr = _coerce_subprocess_output(exc.stderr)
                status = "timed_out"

            duration = round(time.monotonic() - started, 3)
            raw_events = tuple(_parse_json_lines(stdout))
            session_id = _extract_session_id(raw_events) or session.session_id
            final_message = _extract_final_message(raw_events)
            if not final_message and output_last_path.exists():
                final_message = output_last_path.read_text(encoding="utf-8").strip()
            if not final_message and stderr:
                final_message = stderr.strip()
            commands_run = tuple(_extract_command_runs(raw_events))
            files_changed = self._current_changed_files(session.worktree_path)

            session.session_id = session_id
            session.turn_count += 1
            session.cumulative_changed_files = tuple(
                sorted({*session.cumulative_changed_files, *files_changed})
            )

            return BuilderResult(
                session_id=session_id,
                status=status,
                final_message=final_message,
                files_changed=files_changed,
                commands_run=commands_run,
                duration_seconds=duration,
                raw_events=raw_events,
            )
        finally:
            output_last_path.unlink(missing_ok=True)

    def close_session(self, session: BuilderSession) -> None:
        if session.runtime_dir is not None:
            shutil.rmtree(session.runtime_dir, ignore_errors=True)

    def _build_args(
        self, session: BuilderSession, prompt: str, output_last_path: Path
    ) -> list[str]:
        common = self._guarded_exec_args(session)
        if session.session_id:
            args = [
                self.codex_bin,
                "exec",
                "resume",
                *common,
                "--json",
                "-o",
                str(output_last_path),
                session.session_id,
                prompt,
            ]
            return args

        args = [
            self.codex_bin,
            "exec",
            *common,
            "--json",
            "-o",
            str(output_last_path),
            "-C",
            str(session.worktree_path),
        ]
        args.append(prompt)
        return args

    def _guarded_exec_args(self, session: BuilderSession) -> list[str]:
        if session.guard_policy_path is None:
            raise ValueError("Builder session lacks a pre-effect guard policy.")
        guard_script = Path(__file__).with_name("builder_guard.py").resolve()
        hook_command = shlex.join(
            [
                sys.executable,
                str(guard_script),
                "--policy",
                str(session.guard_policy_path),
            ]
        )
        hook_value = (
            '[{ matcher = "^(Bash|apply_patch|Edit|Write)$", hooks = '
            f'[{{ type = "command", command = {json.dumps(hook_command)}, timeout = 10 }}] }}]'
        )
        args = [
            "--dangerously-bypass-hook-trust",
            "--ignore-user-config",
            "--ignore-rules",
            "--strict-config",
            "--disable",
            "unified_exec",
            "--disable",
            "multi_agent",
            "--disable",
            "apps",
            "-c",
            "features.hooks=true",
            "-c",
            'approval_policy="never"',
            "-c",
            f'default_permissions="{self._PERMISSION_PROFILE}"',
            "-c",
            self._permission_profile_config(session),
            "-c",
            'shell_environment_policy.inherit="none"',
            "-c",
            f"shell_environment_policy.set={_toml_inline_table(session.tool_environment or {})}",
            "-c",
            'web_search="disabled"',
            "-c",
            "tools.web_search=false",
            "-c",
            f"hooks.PreToolUse={hook_value}",
        ]
        if self.model:
            args.extend(["-m", self.model])
        if self.reasoning_effort:
            args.extend(["-c", f'model_reasoning_effort="{self.reasoning_effort}"'])
        return args

    def _permission_profile_config(self, session: BuilderSession) -> str:
        allowed_paths = _normalized_profile_paths(
            session.run_context.get("allowed_paths", ()),
            field="allowed_paths",
        )
        forbidden_paths = _normalized_profile_paths(
            session.run_context.get("forbidden_paths", ()),
            field="forbidden_paths",
            require_nonempty=False,
        )
        for allowed in allowed_paths:
            if any(
                _profile_path_has_prefix(allowed, forbidden)
                for forbidden in forbidden_paths
            ):
                raise ValueError(
                    "Builder allowed_paths cannot be nested under forbidden_paths."
                )
        path_rules = {
            ".": "read",
            ".git": "deny",
            ".agent": "deny",
            ".autoclaw": "deny",
        }
        path_rules.update({path: "write" for path in allowed_paths})
        path_rules.update({path: "deny" for path in forbidden_paths})
        path_rules.update(
            {path: "deny" for path in _existing_sensitive_paths(session.worktree_path)}
        )
        if session.runtime_dir is None:
            raise ValueError("Builder session lacks a runtime directory.")
        runtime_relative = session.runtime_dir.relative_to(
            session.worktree_path
        ).as_posix()
        path_rules[runtime_relative] = "write"
        rules = ", ".join(
            f'{json.dumps(path)} = "{access}"'
            for path, access in sorted(path_rules.items())
        )
        return (
            "permissions={ "
            f"{self._PERMISSION_PROFILE} = {{ "
            f'filesystem = {{ ":workspace_roots" = {{ {rules} }} }}, '
            "network = { enabled = false } "
            "} }"
        )

    def _current_changed_files(self, worktree_path: Path) -> tuple[str, ...]:
        if not worktree_path.exists():
            return ()
        completed = self.git_runner(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return ()
        changed: set[str] = set()
        for line in completed.stdout.splitlines():
            if not line:
                continue
            path = line[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            normalized = path.strip()
            if normalized == ".autoclaw" or normalized.startswith(".autoclaw/"):
                continue
            changed.add(normalized)
        return tuple(sorted(changed))

    def _temp_output_path(self, session: BuilderSession) -> Path:
        if session.runtime_dir is None:
            raise ValueError("Builder session lacks a runtime directory.")
        return session.runtime_dir / f"last-message-{uuid.uuid4().hex}.txt"


def _parse_json_lines(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _coerce_subprocess_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _normalized_profile_paths(
    values: object,
    *,
    field: str,
    require_nonempty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)) or any(
        not isinstance(value, str) for value in values
    ):
        raise ValueError(f"Builder {field} must be a list or tuple of relative paths.")
    normalized_values: list[str] = []
    for value in values:
        pure_path = PurePosixPath(value.replace("\\", "/"))
        normalized = pure_path.as_posix()
        while normalized.startswith("./"):
            normalized = normalized[2:]
        normalized = normalized.rstrip("/")
        normalized_values.append(normalized)
    normalized_paths = tuple(dict.fromkeys(normalized_values))
    if require_nonempty and not normalized_paths:
        raise ValueError("Builder sessions require at least one allowed path.")
    for path in normalized_paths:
        pure_path = PurePosixPath(path)
        if (
            not path
            or pure_path.is_absolute()
            or "." in pure_path.parts
            or ".." in pure_path.parts
            or any(character in path for character in "*?[]")
        ):
            raise ValueError(f"Builder {field} contains an invalid relative path.")
    return normalized_paths


def _profile_path_has_prefix(relative_path: str, prefix: str) -> bool:
    return relative_path == prefix or relative_path.startswith(prefix + "/")


def _toml_inline_table(values: dict[str, str]) -> str:
    entries = ", ".join(
        f"{json.dumps(key)} = {json.dumps(value)}"
        for key, value in sorted(values.items())
    )
    return "{ " + entries + " }"


def _builder_tool_environment(runtime_dir: Path) -> dict[str, str]:
    home_dir = runtime_dir / "home"
    temp_dir = runtime_dir / "tmp"
    cache_dir = home_dir / "cache"
    for directory in (home_dir, temp_dir, cache_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home_dir),
        "TMPDIR": str(temp_dir),
        "TMP": str(temp_dir),
        "TEMP": str(temp_dir),
        "XDG_CACHE_HOME": str(cache_dir),
        "DARWIN_USER_CACHE_DIR": str(temp_dir),
        "CFFIXED_USER_HOME": str(home_dir),
        "PYTHONDONTWRITEBYTECODE": "1",
        "CI": "1",
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
    }


def _assert_safe_runtime_ancestry(worktree_path: Path) -> None:
    cursor = worktree_path
    for part in (".autoclaw", "builder-runtime"):
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Builder runtime ancestry cannot traverse symlinks.")


def _existing_sensitive_paths(worktree_path: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for root, directories, files in os.walk(worktree_path, followlinks=False):
        relative_root = Path(root).relative_to(worktree_path)
        if relative_root == Path("."):
            directories[:] = [
                name for name in directories if name not in {".git", ".autoclaw"}
            ]
        for name in [*directories, *files]:
            relative = (relative_root / name).as_posix()
            if classify_path_change(relative).shell_class is ShellClass.AUTO_DENY:
                paths.append(relative)
    return tuple(sorted(set(paths)))


def _extract_session_id(events: Sequence[dict[str, Any]]) -> str | None:
    for event in events:
        if event.get("type") == "thread.started":
            return event.get("thread_id")
    return None


def _extract_final_message(events: Sequence[dict[str, Any]]) -> str:
    final_message = ""
    for event in events:
        item = event.get("item", {})
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "agent_message"
        ):
            final_message = item.get("text", "") or ""
    return final_message


def _extract_command_runs(events: Sequence[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for event in events:
        item = event.get("item", {})
        if (
            event.get("type") == "item.completed"
            and item.get("type") == "command_execution"
        ):
            command = item.get("command")
            if command:
                commands.append(command)
    return commands

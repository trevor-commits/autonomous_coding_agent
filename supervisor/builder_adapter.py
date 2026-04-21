from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass
class BuilderSession:
    worktree_path: Path
    run_context: dict[str, Any]
    session_id: str | None = None
    turn_count: int = 0
    cumulative_changed_files: tuple[str, ...] = ()


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
    def start_session(self, worktree_path: Path, run_context: dict[str, Any]) -> BuilderSession:
        raise NotImplementedError

    @abstractmethod
    def send_task(self, session: BuilderSession, prompt: str, timeout: int) -> BuilderResult:
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
    repo_commands = run_context.get("repo_commands", {})
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
        "Repo contract commands you may use for targeted checks:",
        *command_lines,
        "",
        "Prior failure fingerprints:",
        *failure_lines,
        "",
        "Hard constraints:",
        "- Do not commit, push, switch branches, or control a browser.",
        "- Do not write outside allowed paths.",
        "- Treat any high-risk operation as unsupported in this phase.",
        "",
        "Required response:",
        "- files changed",
        "- commands run",
        "- result",
        "- residual risks",
        "",
    ]
    return "\n".join(sections)


class CodexBuilderAdapter(BuilderAdapter):
    def __init__(
        self,
        *,
        codex_bin: str = "codex",
        runner: Runner | None = None,
        git_runner: Runner | None = None,
        model: str | None = None,
        sandbox: str = "workspace-write",
    ) -> None:
        self.codex_bin = codex_bin
        self.runner = runner or subprocess.run
        self.git_runner = git_runner or subprocess.run
        self.model = model
        self.sandbox = sandbox

    def start_session(self, worktree_path: Path, run_context: dict[str, Any]) -> BuilderSession:
        return BuilderSession(
            worktree_path=Path(worktree_path),
            run_context=run_context,
        )

    def send_task(self, session: BuilderSession, prompt: str, timeout: int) -> BuilderResult:
        started = time.monotonic()
        output_last_path = self._temp_output_path()
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
        except subprocess.TimeoutExpired as exc:
            stdout = _coerce_subprocess_output(exc.stdout)
            status = "timed_out"

        duration = round(time.monotonic() - started, 3)
        raw_events = tuple(_parse_json_lines(stdout))
        session_id = _extract_session_id(raw_events) or session.session_id
        final_message = _extract_final_message(raw_events)
        if not final_message and output_last_path.exists():
            final_message = output_last_path.read_text(encoding="utf-8").strip()
        commands_run = tuple(_extract_command_runs(raw_events))
        files_changed = self._current_changed_files(session.worktree_path)

        session.session_id = session_id
        session.turn_count += 1
        session.cumulative_changed_files = tuple(
            sorted({*session.cumulative_changed_files, *files_changed})
        )
        output_last_path.unlink(missing_ok=True)

        return BuilderResult(
            session_id=session_id,
            status=status,
            final_message=final_message,
            files_changed=files_changed,
            commands_run=commands_run,
            duration_seconds=duration,
            raw_events=raw_events,
        )

    def close_session(self, session: BuilderSession) -> None:
        return None

    def _build_args(self, session: BuilderSession, prompt: str, output_last_path: Path) -> list[str]:
        if session.session_id:
            args = [
                self.codex_bin,
                "exec",
                "resume",
                session.session_id,
                prompt,
                "--json",
                "-o",
                str(output_last_path),
            ]
            if self.model:
                args.extend(["-m", self.model])
            return args

        args = [
            self.codex_bin,
            "exec",
            "--json",
            "-o",
            str(output_last_path),
            "-C",
            str(session.worktree_path),
            "-s",
            self.sandbox,
        ]
        if self.model:
            args.extend(["-m", self.model])
        args.append(prompt)
        return args

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
            changed.add(path.strip())
        return tuple(sorted(changed))

    def _temp_output_path(self) -> Path:
        handle = tempfile.NamedTemporaryFile(prefix="codex-builder-", suffix=".txt", delete=False)
        handle.close()
        return Path(handle.name)


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


def _extract_session_id(events: Sequence[dict[str, Any]]) -> str | None:
    for event in events:
        if event.get("type") == "thread.started":
            return event.get("thread_id")
    return None


def _extract_final_message(events: Sequence[dict[str, Any]]) -> str:
    final_message = ""
    for event in events:
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            final_message = item.get("text", "") or ""
    return final_message


def _extract_command_runs(events: Sequence[dict[str, Any]]) -> list[str]:
    commands: list[str] = []
    for event in events:
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "command_execution":
            command = item.get("command")
            if command:
                commands.append(command)
    return commands

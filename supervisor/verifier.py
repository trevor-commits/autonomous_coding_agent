from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence

from supervisor.contracts import RepoContract, RunContract
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.models import Phase
from supervisor.partner_sandbox import (
    PartnerCommandSandbox,
    PartnerSandboxUnavailableError,
)
from supervisor.policy import ShellClass, classify_command
from supervisor.run_store import RunStore


Runner = Callable[..., subprocess.CompletedProcess[str]]


class VerificationMode(str, Enum):
    FULL = "full"
    TARGETED = "targeted"


@dataclass(frozen=True)
class CommandExecutionResult:
    name: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    scope: str
    run_trace_id: str
    targeted_paths: tuple[str, ...] = ()
    failure_fingerprint: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    def to_report_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": self.name,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
        }
        if self.failure_fingerprint:
            payload["failure_fingerprint"] = self.failure_fingerprint
        return payload


@dataclass(frozen=True)
class VerificationSummary:
    run_id: str
    run_trace_id: str
    mode: VerificationMode
    commands: tuple[CommandExecutionResult, ...]
    changed_files: tuple[str, ...]

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(
            result.failure_fingerprint
            for result in self.commands
            if result.failure_fingerprint
        )

    @property
    def all_passed(self) -> bool:
        return all(result.succeeded for result in self.commands)


class Verifier:
    """Runs deterministic repo-contract verification commands."""

    COMMAND_ORDER = ("setup", "format", "lint", "typecheck", "test")

    def __init__(
        self,
        *,
        repo_root: Path | str,
        repo_contract: RepoContract,
        run_contract: RunContract,
        run_store: RunStore,
        run_trace_id: str,
        fingerprint_store: FailureFingerprintStore | None = None,
        runner: Runner | None = None,
        stop_on_failure: bool = True,
        partner_sandbox: bool = False,
        deadline_monotonic: float | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.repo_contract = repo_contract
        self.run_contract = run_contract
        self.run_store = run_store
        self.run_trace_id = run_trace_id
        self.fingerprint_store = fingerprint_store or FailureFingerprintStore(run_store)
        self.runner = runner or subprocess.run
        self.stop_on_failure = stop_on_failure
        self.partner_sandbox = partner_sandbox
        self.deadline_monotonic = deadline_monotonic
        for command in self.repo_contract.commands.auto_allow_commands():
            decision = classify_command(command, allowed_commands=(command,))
            if decision.shell_class is not ShellClass.AUTO_ALLOW:
                raise ValueError(
                    f"Repo command violates absolute shell policy: {decision.reason}."
                )
        self.command_sandbox = (
            PartnerCommandSandbox(
                repo_root=self.repo_root,
                allowed_paths=self.run_contract.scope.allowed_paths,
                runtime_dir=self.run_store.root / "partner-command-sandbox",
                runner=self.runner,
            )
            if partner_sandbox
            else None
        )

    def run(
        self,
        *,
        mode: VerificationMode = VerificationMode.FULL,
        changed_files: Sequence[str] = (),
    ) -> VerificationSummary:
        changed = tuple(str(path) for path in changed_files)
        results: list[CommandExecutionResult] = []
        for name in self._command_sequence():
            command = getattr(self.repo_contract.commands, name)
            if not command:
                continue
            result = self._run_command(
                name=name, command=command, mode=mode, changed_files=changed
            )
            results.append(result)
            if self.stop_on_failure and not result.succeeded:
                break
        return VerificationSummary(
            run_id=self.run_contract.run_id,
            run_trace_id=self.run_trace_id,
            mode=mode,
            commands=tuple(results),
            changed_files=changed,
        )

    def _command_sequence(self) -> tuple[str, ...]:
        if self.run_contract.queue.verification_pack:
            return tuple(self.run_contract.queue.verification_pack)
        return self.COMMAND_ORDER

    def _run_command(
        self,
        *,
        name: str,
        command: str,
        mode: VerificationMode,
        changed_files: Sequence[str],
    ) -> CommandExecutionResult:
        started = time.monotonic()
        command_env = self._build_env(name=name, mode=mode, changed_files=changed_files)
        try:
            if self.command_sandbox is not None:
                completed = self.command_sandbox.run(
                    command,
                    environment=command_env,
                    timeout=self._command_timeout_seconds(),
                )
            else:
                completed = self.runner(
                    command,
                    cwd=self.repo_root,
                    shell=True,
                    text=True,
                    capture_output=True,
                    env={**os.environ.copy(), **command_env},
                    check=False,
                )
        except subprocess.TimeoutExpired as exc:
            completed = subprocess.CompletedProcess(
                args=exc.cmd,
                returncode=124,
                stdout=_coerce_output(exc.stdout),
                stderr=_coerce_output(exc.stderr)
                or "partner verification command timed out",
            )
        except PartnerSandboxUnavailableError as exc:
            completed = subprocess.CompletedProcess(
                args=command,
                returncode=126,
                stdout="",
                stderr=str(exc),
            )
        duration = round(time.monotonic() - started, 3)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        failure_fingerprint = None
        if completed.returncode != 0:
            fingerprint = self.fingerprint_store.record(
                phase=Phase.LOCAL_VERIFY.value,
                command=name,
                error_signature=self._error_signature(
                    completed.returncode, stdout, stderr
                ),
                relevant_paths=changed_files,
                evidence_refs=self._command_log_refs(name),
            )
            failure_fingerprint = fingerprint.fingerprint

        self._write_command_logs(name=name, stdout=stdout, stderr=stderr)
        self.run_store.append_execution_log(
            json.dumps(
                {
                    "phase": Phase.LOCAL_VERIFY.value,
                    "command": name,
                    "exit_code": completed.returncode,
                    "duration_seconds": duration,
                    "run_trace_id": self.run_trace_id,
                    "scope": mode.value,
                },
                sort_keys=True,
            )
        )
        return CommandExecutionResult(
            name=name,
            command=command,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            scope=mode.value,
            run_trace_id=self.run_trace_id,
            targeted_paths=tuple(changed_files),
            failure_fingerprint=failure_fingerprint,
        )

    def _build_env(
        self,
        *,
        name: str,
        mode: VerificationMode,
        changed_files: Sequence[str],
    ) -> dict[str, str]:
        return {
            "AUTOCLAW_RUN_ID": self.run_contract.run_id,
            "AUTOCLAW_RUN_TRACE_ID": self.run_trace_id,
            "AUTOCLAW_VERIFICATION_COMMAND": name,
            "AUTOCLAW_VERIFICATION_MODE": mode.value,
            "AUTOCLAW_TARGETED_PATHS_JSON": json.dumps(list(changed_files)),
        }

    def _command_timeout_seconds(self) -> float:
        configured = float(self.run_contract.constraints.hard_timeout_seconds)
        if self.deadline_monotonic is None:
            return configured
        remaining = self.deadline_monotonic - time.monotonic()
        if remaining <= 0:
            raise PartnerSandboxUnavailableError(
                "Partner verification deadline expired before command execution."
            )
        return min(configured, remaining)

    def _write_command_logs(self, *, name: str, stdout: str, stderr: str) -> None:
        stdout_path = self.run_store.logs_dir / f"{name}.stdout.log"
        stderr_path = self.run_store.logs_dir / f"{name}.stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr, encoding="utf-8")

    def _command_log_refs(self, name: str) -> tuple[str, ...]:
        return (
            f"artifacts/logs/{name}.stdout.log",
            f"artifacts/logs/{name}.stderr.log",
        )

    def _error_signature(self, exit_code: int, stdout: str, stderr: str) -> str:
        primary = stderr.strip() or stdout.strip() or f"command exited with {exit_code}"
        first_line = primary.splitlines()[0]
        return f"{name_for_signature(exit_code)} {first_line}".strip()


def name_for_signature(exit_code: int) -> str:
    return f"exit-{exit_code}"


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value

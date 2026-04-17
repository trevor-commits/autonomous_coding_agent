from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen

from supervisor.contracts import RepoContract, RunContract
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.models import Phase
from supervisor.run_store import RunStore
from supervisor.verifier import CommandExecutionResult


LOCALHOST_HOSTS = {"127.0.0.1", "localhost"}


@dataclass(frozen=True)
class AppSession:
    process: subprocess.Popen[str] | None
    health_url: str
    stdout_log_path: Path
    stderr_log_path: Path


@dataclass(frozen=True)
class AppLaunchSummary:
    healthy: bool
    session: AppSession | None
    base_url: str
    command_results: tuple[CommandExecutionResult, ...]
    artifact_manifest: tuple[str, ...]
    failure_fingerprint: str | None = None
    failure_reason: str | None = None


class AppSupervisor:
    """Owns app lifecycle for the runtime's Phase 3 UI verification path."""

    def __init__(
        self,
        *,
        repo_root: Path | str,
        repo_contract: RepoContract,
        run_contract: RunContract,
        run_store: RunStore,
        run_trace_id: str,
        fingerprint_store: FailureFingerprintStore | None = None,
        health_timeout_seconds: float = 10.0,
        poll_interval_seconds: float = 0.2,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.repo_contract = repo_contract
        self.run_contract = run_contract
        self.run_store = run_store
        self.run_trace_id = run_trace_id
        self.fingerprint_store = fingerprint_store or FailureFingerprintStore(run_store)
        self.health_timeout_seconds = health_timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds

    def launch(self) -> AppLaunchSummary:
        health_url = self.repo_contract.commands.app_health
        self._assert_local_url(health_url)

        stdout_log_path = self.run_store.logs_dir / "app_up.stdout.log"
        stderr_log_path = self.run_store.logs_dir / "app_up.stderr.log"
        stdout_log_path.parent.mkdir(parents=True, exist_ok=True)

        with stdout_log_path.open("w", encoding="utf-8") as stdout_handle, stderr_log_path.open(
            "w", encoding="utf-8"
        ) as stderr_handle:
            process = subprocess.Popen(
                self.repo_contract.commands.app_up,
                cwd=self.repo_root,
                shell=True,
                text=True,
                stdout=stdout_handle,
                stderr=stderr_handle,
            )

        session = AppSession(
            process=process,
            health_url=health_url,
            stdout_log_path=stdout_log_path,
            stderr_log_path=stderr_log_path,
        )
        app_up_result = CommandExecutionResult(
            name="app_up",
            command=self.repo_contract.commands.app_up,
            exit_code=0,
            stdout="",
            stderr="",
            duration_seconds=0.0,
            scope="full",
            run_trace_id=self.run_trace_id,
        )

        started = time.monotonic()
        deadline = started + self.health_timeout_seconds
        last_error = ""
        while time.monotonic() < deadline:
            if process.poll() is not None:
                last_error = f"app process exited before health check with code {process.returncode}"
                break
            try:
                with urlopen(health_url, timeout=max(1.0, self.poll_interval_seconds)) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    if response.status == 200:
                        return AppLaunchSummary(
                            healthy=True,
                            session=session,
                            base_url=self._base_url_for(health_url),
                            command_results=(
                                app_up_result,
                                CommandExecutionResult(
                                    name="app_health",
                                    command=health_url,
                                    exit_code=0,
                                    stdout=body,
                                    stderr="",
                                    duration_seconds=round(time.monotonic() - started, 3),
                                    scope="full",
                                    run_trace_id=self.run_trace_id,
                                ),
                            ),
                            artifact_manifest=self._artifact_manifest(),
                        )
                    last_error = f"health endpoint returned {response.status}"
            except Exception as exc:  # pragma: no cover - exercised via failure path
                last_error = str(exc)
            time.sleep(self.poll_interval_seconds)

        self.stop(session)
        failure_signature = last_error or "health check timed out"
        fingerprint = self.fingerprint_store.record(
            phase=Phase.APP_LAUNCH.value,
            command="app_health",
            error_signature=failure_signature,
            relevant_paths=(),
            evidence_refs=self._artifact_manifest(),
            type="environment",
        ).fingerprint
        return AppLaunchSummary(
            healthy=False,
            session=None,
            base_url=self._base_url_for(health_url),
            command_results=(
                app_up_result,
                CommandExecutionResult(
                    name="app_health",
                    command=health_url,
                    exit_code=1,
                    stdout="",
                    stderr=failure_signature,
                    duration_seconds=round(time.monotonic() - started, 3),
                    scope="full",
                    run_trace_id=self.run_trace_id,
                    failure_fingerprint=fingerprint,
                ),
            ),
            artifact_manifest=self._artifact_manifest(),
            failure_fingerprint=fingerprint,
            failure_reason=failure_signature,
        )

    def stop(self, session: AppSession | None) -> None:
        if session is None or session.process is None:
            return
        process = session.process
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    def _base_url_for(self, health_url: str) -> str:
        if self.repo_contract.ui.base_url:
            return self.repo_contract.ui.base_url
        parsed = urlparse(health_url)
        return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))

    def _assert_local_url(self, value: str) -> None:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOCALHOST_HOSTS:
            raise ValueError(f"App lifecycle URLs must stay on localhost: `{value}`.")

    def _artifact_manifest(self) -> tuple[str, ...]:
        return (
            "artifacts/logs/app_up.stdout.log",
            "artifacts/logs/app_up.stderr.log",
        )

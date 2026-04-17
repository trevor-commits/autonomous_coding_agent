from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

from jsonschema import Draft202012Validator

from supervisor.contracts import RepoContract, RunContract
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.models import Phase
from supervisor.run_store import RunStore
from supervisor.verifier import CommandExecutionResult


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
LOCALHOST_HOSTS = {"127.0.0.1", "localhost"}


@dataclass(frozen=True)
class UIVerificationSummary:
    passed: bool
    command_results: tuple[CommandExecutionResult, ...]
    defect_packets: tuple[dict[str, Any], ...]
    artifact_manifest: tuple[str, ...]


class UIVerifier:
    """Runs the repo-owned UI smoke suite and emits structured defect packets."""

    def __init__(
        self,
        *,
        repo_root: Path | str,
        repo_contract: RepoContract,
        run_contract: RunContract,
        run_store: RunStore,
        run_trace_id: str,
        fingerprint_store: FailureFingerprintStore | None = None,
        headless: bool = True,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.repo_contract = repo_contract
        self.run_contract = run_contract
        self.run_store = run_store
        self.run_trace_id = run_trace_id
        self.fingerprint_store = fingerprint_store or FailureFingerprintStore(run_store)
        self.headless = headless

    def run(self, *, changed_files: Sequence[str]) -> UIVerificationSummary:
        command = self.repo_contract.commands.ui_smoke
        if not command:
            raise ValueError("UI verification requires `commands.ui_smoke`.")

        base_url = self.repo_contract.ui.base_url or self._base_url_for_health()
        self._assert_local_url(base_url)

        browser_profile_dir = self.run_store.artifacts_dir / "browser-profile"
        browser_profile_dir.mkdir(parents=True, exist_ok=True)

        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=self.repo_root,
            shell=True,
            text=True,
            capture_output=True,
            env=self._build_env(base_url=base_url, browser_profile_dir=browser_profile_dir),
            check=False,
        )
        duration = round(time.monotonic() - started, 3)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        self._write_log("ui_smoke.stdout.log", stdout)
        self._write_log("ui_smoke.stderr.log", stderr)

        artifact_manifest = self._artifact_manifest()
        failure_fingerprint = None
        defect_packets: tuple[dict[str, Any], ...] = ()
        if completed.returncode != 0:
            defect_packet_list: list[dict[str, Any]] = []
            for index, summary in enumerate(self._failure_summaries(stdout, stderr)):
                packet_fingerprint = self.fingerprint_store.record(
                    phase=Phase.UI_VERIFY.value,
                    command="ui_smoke",
                    error_signature=summary,
                    relevant_paths=tuple(changed_files),
                    evidence_refs=artifact_manifest,
                    type="code",
                ).fingerprint
                defect = self._build_defect_packet(
                    changed_files=changed_files,
                    artifact_manifest=artifact_manifest,
                    failure_fingerprint=packet_fingerprint,
                    summary=summary,
                    packet_index=index,
                )
                defect_packet_list.append(defect)
                self.run_store.write_json(self.run_store.defects_dir / f"{defect['defect_id']}.json", defect)
            defect_packets = tuple(defect_packet_list)
            failure_fingerprint = defect_packets[0]["failure_fingerprint"] if defect_packets else None

        command_result = CommandExecutionResult(
            name="ui_smoke",
            command=command,
            exit_code=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            scope="full",
            run_trace_id=self.run_trace_id,
            targeted_paths=tuple(changed_files),
            failure_fingerprint=failure_fingerprint,
        )
        return UIVerificationSummary(
            passed=completed.returncode == 0,
            command_results=(command_result,),
            defect_packets=defect_packets,
            artifact_manifest=artifact_manifest,
        )

    def _build_env(self, *, base_url: str, browser_profile_dir: Path) -> dict[str, str]:
        env = {
            **os.environ.copy(),
            "AUTOCLAW_RUN_ID": self.run_contract.run_id,
            "AUTOCLAW_RUN_TRACE_ID": self.run_trace_id,
            "AUTOCLAW_UI_BASE_URL": base_url,
            "AUTOCLAW_UI_BREAKPOINTS_JSON": json.dumps(list(self.repo_contract.ui.breakpoints)),
            "AUTOCLAW_BROWSER_PROFILE_DIR": str(browser_profile_dir),
            "AUTOCLAW_UI_SCREENSHOTS_DIR": str(self.run_store.screenshots_dir),
            "AUTOCLAW_UI_TRACES_DIR": str(self.run_store.traces_dir),
            "AUTOCLAW_UI_VIDEOS_DIR": str(self.run_store.videos_dir),
            "AUTOCLAW_UI_LOGS_DIR": str(self.run_store.logs_dir),
            "AUTOCLAW_UI_HEADLESS": "1" if self.headless else "0",
        }
        return env

    def _artifact_manifest(self) -> tuple[str, ...]:
        artifacts = {
            "artifacts/logs/ui_smoke.stdout.log",
            "artifacts/logs/ui_smoke.stderr.log",
        }
        artifacts.update(self._relative_artifacts(self.run_store.screenshots_dir))
        artifacts.update(self._relative_artifacts(self.run_store.traces_dir))
        artifacts.update(self._relative_artifacts(self.run_store.videos_dir))
        return tuple(sorted(artifacts))

    def _relative_artifacts(self, directory: Path) -> set[str]:
        if not directory.exists():
            return set()
        return {
            str(path.relative_to(self.run_store.root)).replace("\\", "/")
            for path in directory.rglob("*")
            if path.is_file()
        }

    def _write_log(self, name: str, value: str) -> None:
        path = self.run_store.logs_dir / name
        path.write_text(value, encoding="utf-8")

    def _base_url_for_health(self) -> str:
        parsed = urlparse(self.repo_contract.commands.app_health)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _assert_local_url(self, value: str) -> None:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOCALHOST_HOSTS:
            raise ValueError(f"UI verification must stay on localhost: `{value}`.")

    def _build_defect_packet(
        self,
        *,
        changed_files: Sequence[str],
        artifact_manifest: Sequence[str],
        failure_fingerprint: str,
        summary: str,
        packet_index: int,
    ) -> dict[str, Any]:
        defect_type, severity = self._classify_defect(summary, artifact_manifest)
        evidence: dict[str, str] = {
            "console_log": "artifacts/logs/ui_smoke.stderr.log",
        }
        screenshot = self._indexed_artifact(
            artifact_manifest,
            prefix="artifacts/screenshots/",
            index=packet_index,
        )
        trace = self._indexed_artifact(
            artifact_manifest,
            prefix="artifacts/traces/",
            index=packet_index,
        )
        if screenshot:
            evidence["screenshot"] = screenshot
        if trace:
            evidence["trace"] = trace

        expected = self._expected_behavior(packet_index)
        defect = {
            "defect_id": f"defect-{uuid.uuid4().hex[:8]}",
            "severity": severity,
            "type": defect_type,
            "summary": summary,
            "repro_steps": self._repro_steps(),
            "expected": expected,
            "observed": summary,
            "evidence": evidence,
            "suspected_scope": list(changed_files),
            "failure_fingerprint": failure_fingerprint,
        }
        self._validate_defect_packet(defect)
        return defect

    def _repro_steps(self) -> list[str]:
        if self.repo_contract.ui.critical_flows:
            flow = self.repo_contract.ui.critical_flows[0]
            return [f"Open {flow.route}", *flow.assertions[:2]]
        return [
            "Launch the local app from the repo contract.",
            "Run the UI smoke suite.",
            "Inspect the recorded artifacts for the failing step.",
        ]

    def _classify_defect(
        self,
        summary: str,
        artifact_manifest: Sequence[str],
    ) -> tuple[str, str]:
        lowered = summary.lower()
        if "console" in lowered or "uncaught" in lowered:
            return ("ui-console", "P2")
        if "network" in lowered or "fetch" in lowered:
            return ("ui-network", "P1")
        if "visual" in lowered:
            return ("ui-visual", "P2")
        if any(item.startswith("artifacts/screenshots/") for item in artifact_manifest):
            return ("ui-functional", "P1")
        return ("ui-functional", "P2")

    def _failure_summaries(self, stdout: str, stderr: str) -> tuple[str, ...]:
        source = stderr if stderr.strip() else stdout
        lines = tuple(line.strip() for line in source.splitlines() if line.strip())
        if lines:
            return lines
        return (f"ui_smoke exited with 1",)

    def _expected_behavior(self, packet_index: int) -> str:
        ui_checks = tuple(self.run_contract.acceptance.ui_checks)
        if not ui_checks:
            return "UI smoke suite passes without blocking defects."
        if packet_index < len(ui_checks):
            return ui_checks[packet_index]
        return ui_checks[-1]

    def _indexed_artifact(
        self,
        artifact_manifest: Sequence[str],
        *,
        prefix: str,
        index: int,
    ) -> str | None:
        matches = sorted(item for item in artifact_manifest if item.startswith(prefix))
        if not matches:
            return None
        if index < len(matches):
            return matches[index]
        return matches[-1]

    def _error_signature(self, exit_code: int, stdout: str, stderr: str) -> str:
        primary = stderr.strip() or stdout.strip() or f"ui_smoke exited with {exit_code}"
        return primary.splitlines()[0]

    def _validate_defect_packet(self, payload: dict[str, Any]) -> None:
        schema = json.loads((SCHEMA_DIR / "defect-packet.schema.json").read_text())
        errors = sorted(
            Draft202012Validator(schema).iter_errors(payload),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            messages = []
            for error in errors:
                location = ".".join(str(part) for part in error.absolute_path) or "<root>"
                messages.append(f"{location}: {error.message}")
            raise ValueError("; ".join(messages))

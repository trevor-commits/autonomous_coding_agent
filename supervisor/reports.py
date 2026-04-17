from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator

from supervisor.contracts import RunContract
from supervisor.models import RunSnapshot
from supervisor.run_store import RunStore
from supervisor.verifier import CommandExecutionResult


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


class ReportValidationError(ValueError):
    """Raised when a readiness report violates the schema contract."""


@dataclass(frozen=True)
class ReadinessReport:
    run_id: str
    claim_id: str | None
    run_trace_id: str
    run_state: str
    readiness_verdict: str | None
    phases_completed: tuple[str, ...]
    commands_run: tuple[dict[str, Any], ...]
    failures: tuple[str, ...]
    changed_files: tuple[str, ...]
    artifact_manifest: tuple[str, ...]
    unresolved_blockers: tuple[str, ...]
    queue_entry_reason: str | None
    queue_exit_reason: str | None
    checkpoint_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "phases_completed",
            "commands_run",
            "failures",
            "changed_files",
            "artifact_manifest",
            "unresolved_blockers",
            "checkpoint_refs",
        ):
            payload[key] = list(payload[key])
        if not payload["checkpoint_refs"]:
            payload.pop("checkpoint_refs")
        return payload


def build_readiness_report(
    *,
    snapshot: RunSnapshot,
    run_contract: RunContract,
    command_results: Sequence[CommandExecutionResult],
    changed_files: Sequence[str],
    artifact_manifest: Sequence[str],
    unresolved_blockers: Sequence[str],
    queue_exit_reason: str | None,
    checkpoint_refs: Sequence[str] = (),
) -> ReadinessReport:
    failures = tuple(
        sorted(
            {
                result.failure_fingerprint
                for result in command_results
                if result.failure_fingerprint
            }
        )
    )
    report = ReadinessReport(
        run_id=run_contract.run_id,
        claim_id=run_contract.queue.claim_id,
        run_trace_id=run_contract.queue.run_trace_id or "",
        run_state=snapshot.run_state.value,
        readiness_verdict=snapshot.readiness_verdict.value if snapshot.readiness_verdict else None,
        phases_completed=_completed_phases(snapshot),
        commands_run=tuple(result.to_report_dict() for result in command_results),
        failures=failures,
        changed_files=tuple(changed_files),
        artifact_manifest=tuple(artifact_manifest),
        unresolved_blockers=tuple(unresolved_blockers),
        queue_entry_reason=run_contract.queue.queue_entry_reason,
        queue_exit_reason=queue_exit_reason,
        checkpoint_refs=tuple(checkpoint_refs),
    )
    validate_readiness_report(report.to_dict())
    return report


def validate_readiness_report(payload: dict[str, Any]) -> None:
    schema = json.loads((SCHEMA_DIR / "readiness-report.schema.json").read_text())
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if not errors:
        return
    messages = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{location}: {error.message}")
    raise ReportValidationError("; ".join(messages))


def write_readiness_reports(run_store: RunStore, report: ReadinessReport) -> tuple[Path, Path]:
    report_path = run_store.write_report("final-report.json", report.to_dict())
    summary_path = run_store.reports_dir / "final-summary.md"
    summary_path.write_text(render_summary_markdown(report), encoding="utf-8")
    return report_path, summary_path


def render_summary_markdown(report: ReadinessReport) -> str:
    def render_list(items: Iterable[str], empty_text: str) -> list[str]:
        materialized = [item for item in items if item]
        if not materialized:
            return [f"- {empty_text}"]
        return [f"- {item}" for item in materialized]

    lines = [
        "# Final Summary",
        "",
        f"- Run ID: `{report.run_id}`",
        f"- Claim ID: `{report.claim_id or 'n/a'}`",
        f"- Trace ID: `{report.run_trace_id}`",
        f"- Run state: `{report.run_state}`",
        f"- Readiness verdict: `{report.readiness_verdict or 'n/a'}`",
        "",
        "## Changed Files",
        *render_list(report.changed_files, "No file changes recorded."),
        "",
        "## Command Results",
    ]
    if not report.commands_run:
        lines.append("- No deterministic verification commands ran.")
    else:
        for command in report.commands_run:
            lines.append(
                "- "
                f"`{command['name']}` -> exit `{command['exit_code']}` "
                f"in `{command['duration_seconds']}`s"
            )
    lines.extend(
        [
            "",
            "## Failures",
            *render_list(report.failures, "No failure fingerprints recorded."),
            "",
            "## Unresolved Blockers",
            *render_list(report.unresolved_blockers, "No unresolved blockers."),
            "",
            "## Artifact Manifest",
            *render_list(report.artifact_manifest, "No artifacts recorded."),
            "",
            "## Queue Context",
            f"- Queue entry reason: {report.queue_entry_reason or 'n/a'}",
            f"- Queue exit reason: {report.queue_exit_reason or 'n/a'}",
        ]
    )
    if report.checkpoint_refs:
        lines.extend(["", "## Checkpoint References", *render_list(report.checkpoint_refs, "None.")])
    lines.append("")
    return "\n".join(lines)


def _completed_phases(snapshot: RunSnapshot) -> tuple[str, ...]:
    phases: list[str] = []
    for record in snapshot.phase_history:
        if record.to_phase.value not in phases:
            phases.append(record.to_phase.value)
    return tuple(phases)

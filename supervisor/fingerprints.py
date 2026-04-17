from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from jsonschema import Draft202012Validator

from supervisor.run_store import RunStore


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
FINGERPRINT_REPORT_NAME = "failure-fingerprints.json"
SLUG_TOKEN_RE = re.compile(r"[^a-z0-9]+")


class FingerprintValidationError(ValueError):
    """Raised when a failure fingerprint payload is malformed."""


@dataclass(frozen=True)
class FailureFingerprint:
    fingerprint: str
    phase: str
    command: str
    error_signature: str
    relevant_paths: tuple[str, ...]
    type: str | None = None
    evidence_refs: tuple[str, ...] = ()
    root_cause: str | None = None
    resolution: str | None = None
    last_seen: str | None = None
    occurrence_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            if value is None:
                continue
            if isinstance(value, tuple):
                normalized[key] = list(value)
            else:
                normalized[key] = value
        return normalized


class FailureFingerprintStore:
    """Run-local storage for failure fingerprints and repeat detection."""

    def __init__(self, run_store: RunStore) -> None:
        self.run_store = run_store
        self.path = run_store.reports_dir / FINGERPRINT_REPORT_NAME

    def load(self) -> tuple[FailureFingerprint, ...]:
        if not self.path.exists():
            return ()
        payload = json.loads(self.path.read_text())
        return tuple(_coerce_fingerprint(entry) for entry in payload)

    def record(
        self,
        *,
        phase: str,
        command: str,
        error_signature: str,
        relevant_paths: Sequence[str],
        evidence_refs: Sequence[str] = (),
        type: str | None = None,
        root_cause: str | None = None,
        resolution: str | None = None,
    ) -> FailureFingerprint:
        canonical_paths = _normalize_string_items(relevant_paths)
        canonical_evidence = _normalize_string_items(evidence_refs)
        identifier = build_fingerprint_id(
            phase=phase,
            command=command,
            error_signature=error_signature,
            relevant_paths=canonical_paths,
        )
        now = _utc_now_iso()

        existing = {entry.fingerprint: entry for entry in self.load()}
        current = existing.get(identifier)
        if current is None:
            fingerprint = FailureFingerprint(
                fingerprint=identifier,
                phase=phase,
                command=command,
                error_signature=normalize_error_signature(error_signature),
                relevant_paths=canonical_paths,
                type=type,
                evidence_refs=canonical_evidence,
                root_cause=root_cause,
                resolution=resolution,
                last_seen=now,
                occurrence_count=1,
            )
        else:
            fingerprint = FailureFingerprint(
                fingerprint=current.fingerprint,
                phase=current.phase,
                command=current.command,
                error_signature=current.error_signature,
                relevant_paths=_merge_string_tuples(current.relevant_paths, canonical_paths),
                type=type or current.type,
                evidence_refs=_merge_string_tuples(current.evidence_refs, canonical_evidence),
                root_cause=root_cause or current.root_cause,
                resolution=resolution or current.resolution,
                last_seen=now,
                occurrence_count=current.occurrence_count + 1,
            )
        existing[identifier] = fingerprint
        self._write(tuple(existing[key] for key in sorted(existing)))
        return fingerprint

    def has_repeat(self, fingerprint: str, threshold: int) -> bool:
        if threshold < 1:
            raise ValueError("Repeat threshold must be at least 1.")
        current = next((entry for entry in self.load() if entry.fingerprint == fingerprint), None)
        return bool(current and current.occurrence_count >= threshold)

    def _write(self, entries: Sequence[FailureFingerprint]) -> None:
        payload = [entry.to_dict() for entry in entries]
        _validate_payload(payload)
        self.run_store.write_report(FINGERPRINT_REPORT_NAME, payload)


def build_fingerprint_id(
    *,
    phase: str,
    command: str,
    error_signature: str,
    relevant_paths: Sequence[str],
) -> str:
    parts = [
        phase.lower(),
        command.lower(),
        normalize_error_signature(error_signature),
    ]
    primary_path = sorted(str(path) for path in relevant_paths if str(path).strip())
    if primary_path:
        parts.extend(_tokenize_slug_component(primary_path[0])[:6])

    tokens: list[str] = []
    for part in parts:
        tokens.extend(_tokenize_slug_component(part))
    if not tokens:
        return "unknown-failure"
    return "-".join(tokens[:16])


def normalize_error_signature(raw: str) -> str:
    text = " ".join(str(raw).strip().split())
    if not text:
        return "unknown-error"
    return text


def _coerce_fingerprint(payload: dict[str, Any]) -> FailureFingerprint:
    _validate_payload([payload])
    return FailureFingerprint(
        fingerprint=payload["fingerprint"],
        phase=payload["phase"],
        command=payload["command"],
        error_signature=payload["error_signature"],
        relevant_paths=tuple(payload["relevant_paths"]),
        type=payload.get("type"),
        evidence_refs=tuple(payload.get("evidence_refs", [])),
        root_cause=payload.get("root_cause"),
        resolution=payload.get("resolution"),
        last_seen=payload.get("last_seen"),
        occurrence_count=payload.get("occurrence_count", 1),
    )


def _normalize_string_items(values: Iterable[str]) -> tuple[str, ...]:
    normalized = {str(value).strip() for value in values if str(value).strip()}
    return tuple(sorted(normalized))


def _merge_string_tuples(left: Sequence[str], right: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({*left, *right}))


def _tokenize_slug_component(value: str) -> list[str]:
    slug = SLUG_TOKEN_RE.sub("-", value.lower()).strip("-")
    return [token for token in slug.split("-") if token]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_payload(payload: Sequence[dict[str, Any]]) -> None:
    schema = json.loads((SCHEMA_DIR / "failure-fingerprint.schema.json").read_text())
    validator = Draft202012Validator(schema)
    for index, entry in enumerate(payload):
        errors = sorted(validator.iter_errors(entry), key=lambda error: list(error.absolute_path))
        if not errors:
            continue
        messages = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            messages.append(f"{location}: {error.message}")
        raise FingerprintValidationError(f"entry {index}: {'; '.join(messages)}")

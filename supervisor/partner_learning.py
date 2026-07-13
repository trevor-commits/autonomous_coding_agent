from __future__ import annotations

import copy
import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from supervisor.partner_contracts import (
    PartnerContractError,
    canonical_hash,
    validate_document,
)


PROMOTION_TARGETS = {
    "ranking": "benefit_ledger",
    "communication": "project_memory",
    "workflow": "project_memory",
    "identity": "identity_amendment",
}


class PartnerLearningError(ValueError):
    """Raised when outcome evidence cannot support a bounded learning candidate."""


def derive_learning_candidates(
    outcome: Mapping[str, Any],
    *,
    envelope: Mapping[str, Any],
    proposal: Mapping[str, Any],
    now: str | datetime,
) -> dict[str, Any]:
    validated_envelope = _validate_hash_bound_document(
        envelope, "partner-executor-envelope.schema.json", "envelope"
    )
    try:
        validated_outcome = validate_document(outcome, "partner-outcome.schema.json")
    except PartnerContractError as exc:
        raise PartnerLearningError(f"Outcome contract is invalid: {exc}") from exc
    validated_proposal = _validate_proposal(proposal)
    current_time = _parse_time(now)

    if validated_outcome["envelope_id"] != validated_envelope["envelope_id"]:
        raise PartnerLearningError("Outcome envelope_id does not match the supplied envelope.")
    if validated_outcome["envelope_hash"] != validated_envelope["content_hash"]:
        raise PartnerLearningError("Outcome envelope_hash does not match the supplied envelope.")
    if validated_envelope["proposal_id"] != validated_proposal["id"]:
        raise PartnerLearningError("Envelope proposal_id does not match the supplied proposal.")
    if validated_envelope["proposal_hash"] != canonical_hash(validated_proposal):
        raise PartnerLearningError("Envelope proposal_hash does not match the supplied proposal.")
    if not re.fullmatch(r"[0-9a-f]{64}", validated_outcome["receipt_hash"]):
        raise PartnerLearningError("Outcome receipt_hash must be SHA-256 hex.")

    measures = _validate_measures(validated_outcome["measures"], validated_proposal)
    successful = (
        validated_outcome["run_state"] == "COMPLETE"
        and validated_outcome["readiness_verdict"] == "READY"
    )
    measured_benefit = measures["benefit_score"] if successful else 0.0
    harm_prevented = measures["harm_prevented_score"] if successful else 0.0
    benefit_candidate: dict[str, Any] = {
        "source_outcome_id": validated_outcome["outcome_id"],
        "source_receipt_hash": validated_outcome["receipt_hash"],
        "proposal_id": validated_proposal["id"],
        "successful": successful,
        "measured_benefit": measured_benefit,
        "harm_prevented": harm_prevented,
    }
    benefit_candidate["content_hash"] = canonical_hash(benefit_candidate)

    goal_candidates = [
        {
            "goal_id": goal_id,
            "progress_delta": progress,
            "source_outcome_id": validated_outcome["outcome_id"],
        }
        for goal_id, progress in sorted(measures["goal_progress"].items())
    ]
    lesson_candidates, contradictions = _lesson_candidates(
        measures["lesson_signals"],
        outcome=validated_outcome,
        now=current_time,
    )
    return {
        "benefit_candidate": benefit_candidate,
        "goal_progression_candidates": goal_candidates,
        "lesson_candidates": lesson_candidates,
        "contradictions": contradictions,
    }


def _validate_hash_bound_document(
    payload: Mapping[str, Any], schema_name: str, label: str
) -> dict[str, Any]:
    try:
        validated = validate_document(payload, schema_name)
    except PartnerContractError as exc:
        raise PartnerLearningError(f"{label.title()} contract is invalid: {exc}") from exc
    if validated.get("content_hash") != canonical_hash(validated):
        raise PartnerLearningError(f"{label.title()} content_hash does not match its content.")
    return validated


def _validate_proposal(proposal: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, Mapping):
        raise PartnerLearningError("Proposal must be an object.")
    candidate = copy.deepcopy(dict(proposal))
    if not isinstance(candidate.get("id"), str) or not candidate["id"]:
        raise PartnerLearningError("Proposal requires a non-empty id.")
    goal_ids = candidate.get("goal_ids")
    if (
        not isinstance(goal_ids, list)
        or any(not isinstance(value, str) or not value for value in goal_ids)
        or len(goal_ids) != len(set(goal_ids))
    ):
        raise PartnerLearningError("Proposal goal_ids must be a unique string list.")
    return candidate


def _validate_measures(measures: Any, proposal: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(measures, dict):
        raise PartnerLearningError("Outcome measures must be an object.")
    required = {"benefit_score", "harm_prevented_score", "goal_progress", "lesson_signals"}
    if set(measures) != required:
        raise PartnerLearningError("Outcome measures contain missing or unknown fields.")
    for field in ("benefit_score", "harm_prevented_score"):
        value = measures[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise PartnerLearningError(f"Outcome measure `{field}` must be between 0 and 1.")
    progress = measures["goal_progress"]
    if not isinstance(progress, dict) or not set(progress).issubset(set(proposal["goal_ids"])):
        raise PartnerLearningError("Outcome goal progress must reference only proposal goals.")
    for value in progress.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not -1 <= value <= 1:
            raise PartnerLearningError("Goal progress delta must be between -1 and 1.")
    signals = measures["lesson_signals"]
    if not isinstance(signals, list) or len(signals) > 100:
        raise PartnerLearningError("Outcome lesson_signals must be a bounded list.")
    return copy.deepcopy(measures)


def _lesson_candidates(
    signals: list[Any],
    *,
    outcome: dict[str, Any],
    now: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    validated = [_validate_signal(signal) for signal in signals]
    by_key: dict[str, list[dict[str, Any]]] = {}
    for signal in validated:
        by_key.setdefault(signal["contradiction_key"], []).append(signal)

    contradictory_keys = {
        key for key, group in by_key.items() if len({item["stance"] for item in group}) > 1
    }
    contradictions = [
        {
            "contradiction_key": key,
            "signal_ids": sorted(item["id"] for item in by_key[key]),
        }
        for key in sorted(contradictory_keys)
    ]
    candidates: list[dict[str, Any]] = []
    for signal in validated:
        if signal["contradiction_key"] in contradictory_keys:
            continue
        scope = signal["scope"]
        seed = f"{outcome['outcome_id']}:{signal['id']}:{outcome['receipt_hash']}"
        lesson: dict[str, Any] = {
            "schema_version": "1",
            "lesson_id": "lesson-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24],
            "source_outcome_id": outcome["outcome_id"],
            "source_receipt_hash": outcome["receipt_hash"],
            "scope": scope,
            "summary": signal["summary"],
            "confidence": signal["confidence"],
            "expires_at": _format_time(now + timedelta(days=signal["ttl_days"])),
            "promotion_target": PROMOTION_TARGETS[scope],
            "identity_amendment_required": scope == "identity",
        }
        lesson["content_hash"] = canonical_hash(lesson)
        validate_document(lesson, "partner-lesson-candidate.schema.json")
        candidates.append(lesson)
    return candidates, contradictions


def _validate_signal(signal: Any) -> dict[str, Any]:
    if not isinstance(signal, dict):
        raise PartnerLearningError("Lesson signal must be an object.")
    candidate = copy.deepcopy(signal)
    required = {
        "id",
        "scope",
        "summary",
        "confidence",
        "ttl_days",
        "contradiction_key",
        "stance",
    }
    if set(candidate) != required:
        raise PartnerLearningError("Lesson signal contains missing or unknown fields.")
    for field in ("id", "summary", "contradiction_key"):
        if not isinstance(candidate[field], str) or not candidate[field]:
            raise PartnerLearningError(f"Lesson signal `{field}` must be non-empty text.")
    if candidate["scope"] not in PROMOTION_TARGETS:
        raise PartnerLearningError("Lesson signal scope is unsupported.")
    confidence = candidate["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        raise PartnerLearningError("Lesson signal confidence must be between 0 and 1.")
    if (
        isinstance(candidate["ttl_days"], bool)
        or not isinstance(candidate["ttl_days"], int)
        or not 1 <= candidate["ttl_days"] <= 365
    ):
        raise PartnerLearningError("Lesson signal ttl_days must be between 1 and 365.")
    if candidate["stance"] not in {"prefer", "avoid"}:
        raise PartnerLearningError("Lesson signal stance must be prefer or avoid.")
    return candidate


def _parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PartnerLearningError(f"Invalid learning timestamp `{value}`.") from exc
    else:
        raise PartnerLearningError("Learning timestamp must be RFC 3339 text.")
    if parsed.tzinfo is None:
        raise PartnerLearningError("Learning timestamp requires a timezone.")
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

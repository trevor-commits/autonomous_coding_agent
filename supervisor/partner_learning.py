from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from supervisor.partner_contracts import (
    PartnerContractError,
    canonical_hash,
    validate_document,
    validate_executor_envelope,
    validate_safe_payload,
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
    report_bytes: bytes,
    report_ref: str,
    receipt_bytes: bytes,
    receipt_ref: str,
    now: str | datetime,
) -> dict[str, Any]:
    try:
        validated_envelope = validate_executor_envelope(envelope)
    except PartnerContractError as exc:
        raise PartnerLearningError(f"Envelope contract is invalid: {exc}") from exc
    try:
        validated_outcome = validate_document(outcome, "partner-outcome.schema.json")
    except PartnerContractError as exc:
        raise PartnerLearningError(f"Outcome contract is invalid: {exc}") from exc
    validated_proposal = _validate_proposal(proposal)
    current_time = _parse_time(now)

    if validated_outcome["envelope_id"] != validated_envelope["envelope_id"]:
        raise PartnerLearningError(
            "Outcome envelope_id does not match the supplied envelope."
        )
    if validated_outcome["envelope_hash"] != validated_envelope["content_hash"]:
        raise PartnerLearningError(
            "Outcome envelope_hash does not match the supplied envelope."
        )
    if validated_outcome["run_id"] != validated_envelope["run_contract"]["run_id"]:
        raise PartnerLearningError(
            "Outcome run_id does not match the executor run contract."
        )
    if validated_envelope["proposal_id"] != validated_proposal["id"]:
        raise PartnerLearningError(
            "Envelope proposal_id does not match the supplied proposal."
        )
    if validated_envelope["proposal_hash"] != canonical_hash(validated_proposal):
        raise PartnerLearningError(
            "Envelope proposal_hash does not match the supplied proposal."
        )
    _validate_receipt_binding(
        receipt_bytes,
        receipt_ref=receipt_ref,
        outcome=validated_outcome,
        envelope=validated_envelope,
        report_bytes=report_bytes,
        report_ref=report_ref,
    )

    measures = _validate_measures(validated_outcome["measures"], validated_proposal)
    successful = (
        validated_outcome["run_state"] == "COMPLETE"
        and validated_outcome["readiness_verdict"] == "READY"
    )
    if not successful:
        benefit_status = "not_realized"
        measured_benefit: float | None = 0.0
        harm_prevented: float | None = 0.0
    elif measures["benefit_score"] is None:
        benefit_status = "unknown"
        measured_benefit = None
        harm_prevented = None
    else:
        benefit_status = "measured"
        measured_benefit = measures["benefit_score"]
        harm_prevented = measures["harm_prevented_score"]
    benefit_candidate: dict[str, Any] = {
        "source_outcome_id": validated_outcome["outcome_id"],
        "source_receipt_hash": validated_outcome["receipt_hash"],
        "proposal_id": validated_proposal["id"],
        "successful": successful,
        "benefit_status": benefit_status,
        "measured_benefit": measured_benefit,
        "harm_prevented": harm_prevented,
        "evidence": {
            "produced_artifact": measures["produced_artifact"],
            "adopted_use": measures["adopted_use"],
            "time_saved_minutes": measures["time_saved_minutes"],
            "quality_change": measures["quality_change"],
            "operator_feedback": measures["operator_feedback"],
        },
    }
    benefit_candidate["content_hash"] = canonical_hash(benefit_candidate)

    if successful:
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
    else:
        goal_candidates = []
        lesson_candidates = []
        contradictions = []
    return {
        "benefit_candidate": benefit_candidate,
        "goal_progression_candidates": goal_candidates,
        "lesson_candidates": lesson_candidates,
        "contradictions": contradictions,
    }


def _validate_receipt_binding(
    receipt_bytes: bytes,
    *,
    receipt_ref: str,
    outcome: Mapping[str, Any],
    envelope: Mapping[str, Any],
    report_bytes: bytes,
    report_ref: str,
) -> dict[str, Any]:
    if (
        not isinstance(receipt_bytes, bytes)
        or not receipt_bytes
        or len(receipt_bytes) > 1_000_000
    ):
        raise PartnerLearningError("Receipt evidence must be bounded non-empty bytes.")
    if not isinstance(receipt_ref, str) or not receipt_ref:
        raise PartnerLearningError("Receipt reference must be non-empty text.")
    if outcome["receipt_ref"] != receipt_ref:
        raise PartnerLearningError(
            "Outcome receipt_ref does not match the supplied receipt."
        )
    if outcome["receipt_hash"] != hashlib.sha256(receipt_bytes).hexdigest():
        raise PartnerLearningError(
            "Outcome receipt_hash does not match the supplied receipt bytes."
        )
    try:
        raw_receipt = json.loads(receipt_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PartnerLearningError("Receipt evidence must be one JSON object.") from exc
    if not isinstance(raw_receipt, Mapping):
        raise PartnerLearningError("Receipt evidence must be one JSON object.")
    try:
        receipt = validate_safe_payload(raw_receipt, "dispatch receipt")
    except PartnerContractError as exc:
        raise PartnerLearningError(f"Receipt evidence is invalid: {exc}") from exc
    result = receipt.get("partner_executor_result")
    if not isinstance(result, Mapping):
        raise PartnerLearningError("Receipt lacks a bounded partner executor result.")
    expected_top = {"status": "ok", "action": "dispatch_execute", "runner_rc": 0}
    if any(receipt.get(field) != expected for field, expected in expected_top.items()):
        raise PartnerLearningError(
            "Receipt does not describe a completed executor dispatch."
        )
    expected_result = {
        "ok": True,
        "executed": True,
        "envelope_id": envelope["envelope_id"],
        "envelope_hash": envelope["content_hash"],
        "run_id": outcome["run_id"],
        "run_state": outcome["run_state"],
        "readiness_verdict": outcome["readiness_verdict"],
    }
    if any(
        result.get(field) != expected for field, expected in expected_result.items()
    ):
        raise PartnerLearningError(
            "Receipt executor result does not match the outcome and envelope."
        )
    if (
        not isinstance(report_bytes, bytes)
        or not report_bytes
        or len(report_bytes) > 10_000_000
    ):
        raise PartnerLearningError("Report evidence must be bounded non-empty bytes.")
    if not isinstance(report_ref, str) or not report_ref:
        raise PartnerLearningError("Report reference must be non-empty text.")
    if result.get("report_path") != report_ref:
        raise PartnerLearningError(
            "Receipt report_path does not match the supplied report."
        )
    if result.get("report_sha256") != hashlib.sha256(report_bytes).hexdigest():
        raise PartnerLearningError(
            "Receipt report_sha256 does not match the supplied report bytes."
        )
    if receipt.get("ts") != outcome["completed_at"]:
        raise PartnerLearningError(
            "Receipt timestamp does not match outcome completion time."
        )
    return receipt


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
    required = {
        "produced_artifact",
        "adopted_use",
        "time_saved_minutes",
        "quality_change",
        "operator_feedback",
        "benefit_score",
        "harm_prevented_score",
        "goal_progress",
        "lesson_signals",
    }
    if set(measures) != required:
        raise PartnerLearningError(
            "Outcome measures contain missing or unknown fields."
        )
    if not isinstance(measures["produced_artifact"], bool):
        raise PartnerLearningError("Outcome produced_artifact must be boolean.")
    if measures["adopted_use"] is not None and not isinstance(
        measures["adopted_use"], bool
    ):
        raise PartnerLearningError("Outcome adopted_use must be boolean or null.")
    for field in ("benefit_score", "harm_prevented_score"):
        value = measures[field]
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            raise PartnerLearningError(
                f"Outcome measure `{field}` must be null or between 0 and 1."
            )
    if (measures["benefit_score"] is None) != (
        measures["harm_prevented_score"] is None
    ):
        raise PartnerLearningError(
            "Benefit and harm-prevented scores must become known together."
        )
    for field in ("time_saved_minutes", "quality_change"):
        value = measures[field]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, (int, float))
        ):
            raise PartnerLearningError(
                f"Outcome measure `{field}` must be numeric or null."
            )
    feedback = measures["operator_feedback"]
    if feedback is not None and (not isinstance(feedback, str) or len(feedback) > 1000):
        raise PartnerLearningError(
            "Outcome operator_feedback must be bounded text or null."
        )
    if measures["benefit_score"] is not None and not (
        measures["produced_artifact"] is True
        and measures["adopted_use"] is True
        and measures["time_saved_minutes"] is not None
        and measures["quality_change"] is not None
        and isinstance(feedback, str)
        and bool(feedback.strip())
    ):
        raise PartnerLearningError(
            "Measured scores require artifact, adoption, time, quality, and operator evidence."
        )
    progress = measures["goal_progress"]
    if not isinstance(progress, dict) or not set(progress).issubset(
        set(proposal["goal_ids"])
    ):
        raise PartnerLearningError(
            "Outcome goal progress must reference only proposal goals."
        )
    for value in progress.values():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not -1 <= value <= 1
        ):
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
        key
        for key, group in by_key.items()
        if len({item["stance"] for item in group}) > 1
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
            "lesson_id": "lesson-"
            + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24],
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
        try:
            validate_document(lesson, "partner-lesson-candidate.schema.json")
        except PartnerContractError as exc:
            raise PartnerLearningError(
                f"Lesson candidate contract is invalid: {exc}"
            ) from exc
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
            raise PartnerLearningError(
                f"Lesson signal `{field}` must be non-empty text."
            )
    if candidate["scope"] not in PROMOTION_TARGETS:
        raise PartnerLearningError("Lesson signal scope is unsupported.")
    confidence = candidate["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
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
            raise PartnerLearningError(
                f"Invalid learning timestamp `{value}`."
            ) from exc
    else:
        raise PartnerLearningError("Learning timestamp must be RFC 3339 text.")
    if parsed.tzinfo is None:
        raise PartnerLearningError("Learning timestamp requires a timezone.")
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

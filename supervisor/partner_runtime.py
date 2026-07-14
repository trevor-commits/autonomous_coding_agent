from __future__ import annotations

import copy
import hashlib
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from supervisor.partner_authority import evaluate_authority
from supervisor.partner_contracts import (
    PartnerContractError,
    canonical_hash,
    validate_document,
    validate_wake_snapshot,
)
from supervisor.partner_initiative import rank_initiatives


POLICY_VERSION = "1"


class PartnerRuntimeError(ValueError):
    """Raised when a wake cannot produce one trustworthy typed decision."""


def decide_wake(
    snapshot: Mapping[str, Any],
    *,
    candidates: Iterable[Mapping[str, Any]],
    now: str | datetime,
    health: Mapping[str, Any],
    busy: bool,
    kill_switches: Iterable[str],
    prior_decisions: Iterable[Mapping[str, Any]] = (),
    mode: str = "execute",
) -> dict[str, Any]:
    validated_snapshot = validate_wake_snapshot(snapshot)
    current_time = _parse_time(now)
    health_state = _validate_health(health)
    if not isinstance(busy, bool):
        raise PartnerRuntimeError("busy must be boolean.")
    if mode not in {"observe", "propose", "execute"}:
        raise PartnerRuntimeError("mode must be observe, propose, or execute.")

    existing = _prior_decision(validated_snapshot, prior_decisions)
    if existing is not None:
        return existing

    if not health_state["healthy"]:
        return _build_decision(
            validated_snapshot,
            "no_op",
            ("unhealthy", *health_state["reason_codes"]),
            (),
            {"health": health_state},
        )
    if busy:
        return _build_decision(validated_snapshot, "no_op", ("busy",), (), {})
    active_switches = tuple(sorted({str(value) for value in kill_switches if str(value)}))
    if active_switches:
        return _build_decision(
            validated_snapshot,
            "blocked",
            ("kill_switch_active",),
            (),
            {"active_kill_switches": list(active_switches)},
        )
    if mode == "observe":
        return _build_decision(validated_snapshot, "no_op", ("observe_only",), (), {})

    budgets = validated_snapshot["budgets"]
    if budgets["max_proposals"] == 0:
        return _build_decision(validated_snapshot, "no_op", ("proposal_budget_exhausted",), (), {})

    prepared_candidates = [_prepare_candidate(candidate) for candidate in candidates]
    ranked = rank_initiatives(
        prepared_candidates,
        approved_observations=validated_snapshot["observations"],
        approved_goal_ids={item["id"] for item in validated_snapshot["goals"]},
        approved_interest_ids={item["id"] for item in validated_snapshot["identity"]["interests"]},
        now=current_time,
    )
    if not ranked:
        return _build_decision(
            validated_snapshot,
            "no_op",
            ("no_current_approved_evidence",),
            (),
            {},
        )

    selected = ranked[0]
    authority = evaluate_authority(
        selected,
        maturity=validated_snapshot["maturity"],
        approvals=validated_snapshot["approvals"],
        now=current_time,
        kill_switches=(),
    )
    evidence_ids = tuple(selected["observation_ids"])
    if not authority["authorized"]:
        return _build_decision(
            validated_snapshot,
            "proposal",
            (authority["reason_code"],),
            evidence_ids,
            {"proposal": selected, "authority": authority},
        )
    if mode == "propose":
        return _build_decision(
            validated_snapshot,
            "proposal",
            ("proposal_mode",),
            evidence_ids,
            {"proposal": selected, "authority": authority},
        )
    if budgets["max_envelopes"] == 0:
        return _build_decision(
            validated_snapshot,
            "proposal",
            ("envelope_budget_exhausted",),
            evidence_ids,
            {"proposal": selected, "authority": authority},
        )

    envelope = _build_executor_envelope(
        validated_snapshot,
        selected,
        authority,
        current_time,
    )
    return _build_decision(
        validated_snapshot,
        "executor_envelope",
        (authority["reason_code"],),
        evidence_ids,
        {"executor_envelope": envelope},
    )


def _prepare_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, Mapping):
        raise PartnerRuntimeError("Partner candidate must be an object.")
    prepared = copy.deepcopy(dict(candidate))
    if not isinstance(prepared.get("run_contract"), dict) or not prepared["run_contract"]:
        raise PartnerRuntimeError("Partner candidate requires a bounded run_contract object.")
    supplied_hash = prepared.pop("content_hash", None)
    computed_hash = canonical_hash(prepared)
    if supplied_hash is not None and supplied_hash != computed_hash:
        raise PartnerRuntimeError("Partner candidate content_hash does not match its content.")
    prepared["content_hash"] = computed_hash
    return prepared


def _build_executor_envelope(
    snapshot: dict[str, Any],
    proposal: dict[str, Any],
    authority: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    approval_id = authority.get("approval_id")
    approval = next(
        (
            item
            for item in snapshot["approvals"]
            if approval_id is not None and item.get("approval_id") == approval_id
        ),
        None,
    )
    if approval is None:
        raise PartnerRuntimeError(
            "Executable partner envelopes require a full exact proposal approval binding."
        )
    seed = f"{snapshot['wake_id']}:{proposal['id']}:{proposal['content_hash']}"
    envelope_id = "envelope-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
    risk_level = _risk_level(float(proposal["risk"]))
    run_contract = copy.deepcopy(proposal["run_contract"])
    run_contract.update(
        {
            "claim_id": envelope_id,
            "run_trace_id": snapshot["wake_id"],
            "queue_entry_reason": "authorized autonomous partner envelope",
            "issue_snapshot_hash": proposal["content_hash"],
            "risk_level": risk_level.title(),
            "approval_required": False,
        }
    )
    envelope: dict[str, Any] = {
        "schema_version": "1",
        "envelope_id": envelope_id,
        "wake_id": snapshot["wake_id"],
        "proposal_id": proposal["id"],
        "proposal_hash": proposal["content_hash"],
        "approval_id": approval_id,
        "approval_hash": canonical_hash(approval),
        "approval_binding": copy.deepcopy(approval),
        "executor_id": "autonomous-coding-agent",
        "strategy": "simple",
        "builder_model": "gpt-5.5",
        "builder_reasoning_effort": "high",
        "run_contract": run_contract,
        "run_contract_hash": canonical_hash(run_contract),
        "capability_classes": list(proposal["required_capabilities"]),
        "risk_level": risk_level,
        "created_at": _format_time(now),
    }
    envelope["content_hash"] = canonical_hash(envelope)
    from supervisor.partner_contracts import validate_executor_envelope

    validate_executor_envelope(envelope)
    return envelope


def _build_decision(
    snapshot: dict[str, Any],
    decision_type: str,
    reason_codes: Iterable[str],
    evidence_ids: Iterable[str],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_reasons = tuple(dict.fromkeys(str(value) for value in reason_codes if str(value)))
    normalized_evidence = tuple(dict.fromkeys(str(value) for value in evidence_ids if str(value)))
    identity_hash = snapshot["identity"]["content_hash"]
    seed = canonical_hash(
        {
            "wake_id": snapshot["wake_id"],
            "identity_hash": identity_hash,
            "decision_type": decision_type,
            "reason_codes": normalized_reasons,
            "evidence_ids": normalized_evidence,
            "payload": payload,
        }
    )
    decision: dict[str, Any] = {
        "schema_version": "1",
        "decision_id": "decision-" + seed[:24],
        "wake_id": snapshot["wake_id"],
        "idempotency_key": snapshot["wake_id"],
        "identity_hash": identity_hash,
        "policy_version": POLICY_VERSION,
        "decision_type": decision_type,
        "reason_codes": list(normalized_reasons),
        "evidence_ids": list(normalized_evidence),
        "payload": copy.deepcopy(dict(payload)),
    }
    decision["content_hash"] = canonical_hash(decision)
    validate_document(decision, "partner-decision.schema.json")
    return decision


def _prior_decision(
    snapshot: dict[str, Any], prior_decisions: Iterable[Mapping[str, Any]]
) -> dict[str, Any] | None:
    matching: list[dict[str, Any]] = []
    for candidate in prior_decisions:
        try:
            decision = validate_document(candidate, "partner-decision.schema.json")
        except PartnerContractError as exc:
            raise PartnerRuntimeError(f"Prior decision is invalid: {exc}") from exc
        if decision["content_hash"] != canonical_hash(decision):
            raise PartnerRuntimeError("Prior decision content_hash does not match its content.")
        if decision["idempotency_key"] == snapshot["wake_id"]:
            if decision["identity_hash"] != snapshot["identity"]["content_hash"]:
                raise PartnerRuntimeError("Prior decision identity hash differs for the same wake.")
            matching.append(decision)
    if not matching:
        return None
    first_hash = matching[0]["content_hash"]
    if any(item["content_hash"] != first_hash for item in matching[1:]):
        raise PartnerRuntimeError("Conflicting decisions exist for the same wake idempotency key.")
    return copy.deepcopy(matching[0])


def _validate_health(health: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(health, Mapping):
        raise PartnerRuntimeError("Partner health must be an object.")
    candidate = copy.deepcopy(dict(health))
    if set(candidate) != {"healthy", "reason_codes"}:
        raise PartnerRuntimeError("Partner health fields must be exactly healthy and reason_codes.")
    if not isinstance(candidate["healthy"], bool):
        raise PartnerRuntimeError("Partner health healthy must be boolean.")
    reasons = candidate["reason_codes"]
    if not isinstance(reasons, list) or any(not isinstance(value, str) or not value for value in reasons):
        raise PartnerRuntimeError("Partner health reason_codes must be a string list.")
    return candidate


def _parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PartnerRuntimeError(f"Invalid wake timestamp `{value}`.") from exc
    else:
        raise PartnerRuntimeError("Wake timestamp must be RFC 3339 text.")
    if parsed.tzinfo is None:
        raise PartnerRuntimeError("Wake timestamp requires a timezone.")
    return parsed.astimezone(timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _risk_level(value: float) -> str:
    if value <= 0.25:
        return "low"
    if value <= 0.5:
        return "medium"
    return "high"

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from supervisor.partner_contracts import PartnerContractError, canonical_hash, validate_document


POLICY_VERSION = "1"
SANDBOX_CAPABILITIES = frozenset(
    {"local_read", "sandbox_write", "deterministic_test", "local_artifact"}
)
TREVOR_GATED_CAPABILITIES = frozenset(
    {
        "outward_communication",
        "publish",
        "credentials",
        "payment",
        "destructive",
        "identity_change",
        "policy_change",
        "security_change",
        "merge",
        "deploy",
        "force_push",
    }
)
L3_MIN_PROPOSALS = 10
L3_MIN_ACCEPTANCE_RATE = 0.8
L3_MIN_COMPLETED_EPISODES = 10
L3_MAX_AUTONOMOUS_RISK = 0.25
MAX_APPROVED_SANDBOX_RISK = 0.5


class PartnerAuthorityError(ValueError):
    """Raised when an authority request is malformed."""


def evaluate_authority(
    proposal: Mapping[str, Any],
    *,
    maturity: Mapping[str, Any],
    approvals: Iterable[Mapping[str, Any]],
    now: str | datetime,
    kill_switches: Iterable[str],
) -> dict[str, Any]:
    current_time = _parse_time(now)
    validated_proposal = _validate_proposal(proposal)
    validated_maturity = _validate_maturity(maturity)
    active_switches = sorted({str(value) for value in kill_switches if str(value)})
    if active_switches:
        return _decision(
            False,
            "kill_switch_active",
            required_gate="kill_switch_clear",
            details={"active_kill_switches": active_switches},
        )

    capabilities = set(validated_proposal["required_capabilities"])
    if capabilities & TREVOR_GATED_CAPABILITIES:
        return _decision(False, "trevor_gate_required", required_gate="trevor")
    unknown_capabilities = capabilities - SANDBOX_CAPABILITIES
    if unknown_capabilities:
        return _decision(
            False,
            "unsupported_capability",
            required_gate="trevor",
            details={"unsupported_capabilities": sorted(unknown_capabilities)},
        )
    if validated_proposal["risk"] > MAX_APPROVED_SANDBOX_RISK:
        return _decision(False, "trevor_gate_required", required_gate="trevor")

    exact_approvals = _exact_approvals(validated_proposal, approvals, current_time)
    if len(exact_approvals) != 1:
        reason = (
            "l3_promotion_approval_required"
            if _eligible_for_l3_start(validated_proposal, validated_maturity)
            else "exact_approval_required"
        )
        return _decision(False, reason, required_gate="approval")
    return _decision(
        True,
        "exact_approval_bound",
        required_gate=None,
        approval_id=exact_approvals[0]["approval_id"],
    )


def _validate_proposal(proposal: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(proposal, Mapping):
        raise PartnerAuthorityError("Authority proposal must be an object.")
    candidate = dict(proposal)
    required = {"id", "origin", "required_capabilities", "risk", "content_hash"}
    if not required.issubset(candidate):
        raise PartnerAuthorityError("Authority proposal is missing required binding fields.")
    if not isinstance(candidate["id"], str) or not candidate["id"]:
        raise PartnerAuthorityError("Authority proposal id must be a non-empty string.")
    if candidate["origin"] not in {"self_originated", "operator_goal"}:
        raise PartnerAuthorityError("Authority proposal origin is unsupported.")
    capabilities = candidate["required_capabilities"]
    if (
        not isinstance(capabilities, list)
        or not capabilities
        or any(not isinstance(value, str) or not value for value in capabilities)
        or len(capabilities) != len(set(capabilities))
    ):
        raise PartnerAuthorityError("Authority proposal capabilities must be a unique string list.")
    risk = candidate["risk"]
    if isinstance(risk, bool) or not isinstance(risk, (int, float)) or not 0 <= risk <= 1:
        raise PartnerAuthorityError("Authority proposal risk must be between 0 and 1.")
    if candidate["content_hash"] != canonical_hash(candidate):
        raise PartnerAuthorityError("Authority proposal content_hash does not match its content.")
    return candidate


def _validate_maturity(maturity: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(maturity, Mapping):
        raise PartnerAuthorityError("Maturity must be an object.")
    candidate = dict(maturity)
    required = {
        "level",
        "proposal_count",
        "accepted_count",
        "completed_episode_count",
        "severe_failure",
    }
    if set(candidate) != required:
        raise PartnerAuthorityError("Maturity must contain only the bounded empirical fields.")
    if candidate["level"] not in {"L0", "L1", "L2", "L3"}:
        raise PartnerAuthorityError("Maturity level is unsupported.")
    for field in ("proposal_count", "accepted_count", "completed_episode_count"):
        value = candidate[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PartnerAuthorityError(f"Maturity `{field}` must be a non-negative integer.")
    if candidate["accepted_count"] > candidate["proposal_count"]:
        raise PartnerAuthorityError("Maturity accepted_count cannot exceed proposal_count.")
    if not isinstance(candidate["severe_failure"], bool):
        raise PartnerAuthorityError("Maturity severe_failure must be boolean.")
    return candidate


def _eligible_for_l3_start(proposal: dict[str, Any], maturity: dict[str, Any]) -> bool:
    proposal_count = maturity["proposal_count"]
    acceptance_rate = maturity["accepted_count"] / proposal_count if proposal_count else 0.0
    return (
        proposal["origin"] == "self_originated"
        and proposal["risk"] <= L3_MAX_AUTONOMOUS_RISK
        and maturity["level"] == "L3"
        and not maturity["severe_failure"]
        and proposal_count >= L3_MIN_PROPOSALS
        and acceptance_rate >= L3_MIN_ACCEPTANCE_RATE
        and maturity["completed_episode_count"] >= L3_MIN_COMPLETED_EPISODES
    )


def _exact_approvals(
    proposal: dict[str, Any],
    approvals: Iterable[Mapping[str, Any]],
    now: datetime,
) -> list[dict[str, Any]]:
    exact: list[dict[str, Any]] = []
    for raw_approval in approvals:
        try:
            approval = validate_document(raw_approval, "partner-approval.schema.json")
        except PartnerContractError:
            continue
        if approval.get("approval_kind") != "proposal" or approval.get("approved") is not True:
            continue
        if approval.get("subject_id") != proposal["id"]:
            continue
        if approval.get("subject_hash") != proposal["content_hash"]:
            continue
        if set(approval.get("capability_classes", [])) != set(proposal["required_capabilities"]):
            continue
        if not (_parse_time(approval["approved_at"]) <= now < _parse_time(approval["expires_at"])):
            continue
        exact.append(approval)
    return exact


def _parse_time(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PartnerAuthorityError(f"Invalid authority timestamp `{value}`.") from exc
    else:
        raise PartnerAuthorityError("Authority timestamp must be RFC 3339 text.")
    if parsed.tzinfo is None:
        raise PartnerAuthorityError("Authority timestamp requires a timezone.")
    return parsed.astimezone(timezone.utc)


def _decision(
    authorized: bool,
    reason_code: str,
    *,
    required_gate: str | None,
    approval_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "authorized": authorized,
        "reason_code": reason_code,
        "required_gate": required_gate,
        "approval_id": approval_id,
        "policy_version": POLICY_VERSION,
        "details": details or {},
    }

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


PROJECT_KINDS = frozenset({"utility", "repair", "research", "care", "creative"})
HIGHER_IS_BETTER = (
    "expected_benefit",
    "harm_prevented",
    "interest_fit",
    "novelty",
    "confidence",
)
LOWER_IS_BETTER = ("effort", "risk")
SCORE_WEIGHTS = {
    "expected_benefit": 2.0,
    "harm_prevented": 2.0,
    "interest_fit": 1.5,
    "novelty": 1.0,
    "effort": -1.0,
    "confidence": 1.5,
    "risk": -2.0,
    "freshness": 1.0,
}


class PartnerInitiativeError(ValueError):
    """Raised when initiative inputs cannot be ranked safely."""


def rank_initiatives(
    proposals: Iterable[Mapping[str, Any]],
    *,
    approved_observations: Iterable[Mapping[str, Any]],
    approved_interest_ids: Iterable[str],
    now: str | datetime,
) -> list[dict[str, Any]]:
    current_time = _parse_time(now, "now")
    interests = {str(value) for value in approved_interest_ids if str(value)}
    observations = _validated_observations(approved_observations)
    ranked: list[tuple[float, str, dict[str, Any]]] = []

    for raw_proposal in proposals:
        proposal = _validated_proposal(raw_proposal)
        observation_ids = proposal["observation_ids"]
        if not observation_ids or any(identifier not in observations for identifier in observation_ids):
            continue
        cited = [observations[identifier] for identifier in observation_ids]
        if any(_parse_time(item["expires_at"], "observation expires_at") <= current_time for item in cited):
            continue
        interest_ids = set(proposal["interest_ids"])
        if not interest_ids or not interest_ids.issubset(interests):
            continue

        freshest_observation = max(
            _parse_time(item["observed_at"], "observation observed_at") for item in cited
        )
        freshness = _freshness_score(freshest_observation, current_time)
        score = sum(
            SCORE_WEIGHTS[field] * float(proposal[field])
            for field in HIGHER_IS_BETTER + LOWER_IS_BETTER
        ) + SCORE_WEIGHTS["freshness"] * freshness
        ranked.append((score, proposal["id"], copy.deepcopy(proposal)))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [proposal for _, _, proposal in ranked]


def _validated_observations(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for raw in observations:
        if not isinstance(raw, Mapping):
            raise PartnerInitiativeError("Approved observations must be objects.")
        observation = copy.deepcopy(dict(raw))
        required = {"id", "source_ref", "observed_at", "expires_at"}
        if not required.issubset(observation):
            raise PartnerInitiativeError("Approved observation is missing bounded provenance fields.")
        identifier = observation["id"]
        if not isinstance(identifier, str) or not identifier:
            raise PartnerInitiativeError("Approved observation id must be a non-empty string.")
        if identifier in by_id:
            raise PartnerInitiativeError(f"Duplicate approved observation id `{identifier}`.")
        if not isinstance(observation["source_ref"], str) or not observation["source_ref"]:
            raise PartnerInitiativeError(f"Approved observation `{identifier}` lacks source_ref.")
        observed_at = _parse_time(observation["observed_at"], "observation observed_at")
        expires_at = _parse_time(observation["expires_at"], "observation expires_at")
        if expires_at <= observed_at:
            raise PartnerInitiativeError(
                f"Approved observation `{identifier}` expires before it was observed."
            )
        by_id[identifier] = observation
    return by_id


def _validated_proposal(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise PartnerInitiativeError("Initiative proposals must be objects.")
    proposal = copy.deepcopy(dict(raw))
    required = {
        "id",
        "project_kind",
        "goal_ids",
        "observation_ids",
        "interest_ids",
        "success_criteria",
        "required_capabilities",
        *HIGHER_IS_BETTER,
        *LOWER_IS_BETTER,
    }
    if not required.issubset(proposal):
        missing = sorted(required - set(proposal))
        raise PartnerInitiativeError("Initiative proposal is missing fields: " + ", ".join(missing) + ".")
    if not isinstance(proposal["id"], str) or not proposal["id"]:
        raise PartnerInitiativeError("Initiative proposal id must be a non-empty string.")
    if proposal["project_kind"] not in PROJECT_KINDS:
        raise PartnerInitiativeError(
            f"Initiative proposal `{proposal['id']}` has an unsupported project kind."
        )
    for field in ("goal_ids", "observation_ids", "interest_ids", "success_criteria", "required_capabilities"):
        values = proposal[field]
        if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values):
            raise PartnerInitiativeError(
                f"Initiative proposal `{proposal['id']}` field `{field}` must be a string list."
            )
        if len(values) != len(set(values)):
            raise PartnerInitiativeError(
                f"Initiative proposal `{proposal['id']}` field `{field}` contains duplicates."
            )
    if not proposal["success_criteria"] or not proposal["required_capabilities"]:
        raise PartnerInitiativeError(
            f"Initiative proposal `{proposal['id']}` requires success criteria and capabilities."
        )
    for field in HIGHER_IS_BETTER + LOWER_IS_BETTER:
        value = proposal[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise PartnerInitiativeError(
                f"Initiative proposal `{proposal['id']}` field `{field}` must be between 0 and 1."
            )
    return proposal


def _parse_time(value: str | datetime, label: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise PartnerInitiativeError(f"Invalid {label}: `{value}`.") from exc
    else:
        raise PartnerInitiativeError(f"Invalid {label}: expected an RFC 3339 timestamp.")
    if parsed.tzinfo is None:
        raise PartnerInitiativeError(f"Invalid {label}: timezone is required.")
    return parsed.astimezone(timezone.utc)


def _freshness_score(observed_at: datetime, now: datetime) -> float:
    age_seconds = max(0.0, (now - observed_at).total_seconds())
    seven_days = 7 * 24 * 60 * 60
    return max(0.0, 1.0 - age_seconds / seven_days)

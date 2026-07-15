from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
IDENTITY_LIST_FIELDS = (
    "values",
    "voice_traits",
    "interests",
    "dislikes",
    "relationship_boundaries",
)
_SECRET_PATTERNS = (
    re.compile(r"\bgh[opusr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|token|secret)\s*[:=]\s*\S{8,}", re.IGNORECASE),
)
_RAW_PRIVATE_KEYS = frozenset(
    {
        "raw_content",
        "raw_transcript",
        "transcript_body",
        "email_body",
        "message_body",
        "private_content",
    }
)
_EXECUTOR_SANDBOX_CAPABILITIES = frozenset(
    {"local_read", "sandbox_write", "deterministic_test", "local_artifact"}
)
_OBSERVATION_V2_SEMANTIC_FIELDS = (
    "collector_id",
    "contract_version",
    "dedupe_key",
    "interest_ids",
    "sensitivity",
    "source_ref",
    "summary",
)
_OBSERVATION_V2_TTL = {
    "todo-marker/v1": timedelta(hours=24),
    "resource-governor/v1": timedelta(minutes=5),
    "autonomous-loop-health/v1": timedelta(minutes=30),
}
_UTC_SECONDS_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class PartnerContractError(ValueError):
    """Raised when a partner boundary document is invalid or unsafe."""


def canonical_hash(payload: Mapping[str, Any]) -> str:
    canonical_payload = copy.deepcopy(dict(payload))
    canonical_payload.pop("content_hash", None)
    try:
        encoded = json.dumps(
            canonical_payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PartnerContractError(f"Partner document is not canonical JSON: {exc}.") from exc
    return hashlib.sha256(encoded).hexdigest()


def load_json_document(path: Path | str) -> dict[str, Any]:
    document_path = Path(path)
    try:
        payload = json.loads(document_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PartnerContractError(f"Could not load partner document `{document_path}`: {exc}.") from exc
    if not isinstance(payload, dict):
        raise PartnerContractError(f"Partner document `{document_path}` must be a JSON object.")
    return payload


def load_identity_document(path: Path | str) -> dict[str, Any]:
    document_path = Path(path)
    try:
        if document_path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(document_path.read_text(encoding="utf-8"))
        else:
            payload = json.loads(document_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise PartnerContractError(f"Could not load identity `{document_path}`: {exc}.") from exc
    if not isinstance(payload, dict):
        raise PartnerContractError(f"Identity `{document_path}` must be an object.")
    return validate_identity(payload)


def validate_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    identity = _copy_mapping(payload, "identity")
    _reject_raw_private_keys(identity)
    _reject_secret_like_values(identity)
    supplied_hash = identity.pop("content_hash", None)
    _validate_schema(identity, "partner-identity.schema.json")
    _require_unique_ids(identity, IDENTITY_LIST_FIELDS)
    computed_hash = canonical_hash(identity)
    if supplied_hash is not None and supplied_hash != computed_hash:
        raise PartnerContractError("Identity content_hash does not match its canonical content.")
    identity["content_hash"] = computed_hash
    return identity


def validate_wake_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = _copy_mapping(payload, "wake snapshot")
    _reject_raw_private_keys(snapshot)
    _reject_secret_like_values(snapshot)
    _validate_schema(snapshot, "partner-wake-snapshot.schema.json")
    if snapshot["schema_version"] == "2":
        _validate_observations_v2(snapshot)
    snapshot["identity"] = validate_identity(snapshot["identity"])
    snapshot["approvals"] = [
        validate_document(approval, "partner-approval.schema.json")
        for approval in snapshot["approvals"]
    ]
    snapshot["executor_outcomes"] = [
        validate_document(outcome, "partner-outcome.schema.json")
        for outcome in snapshot["executor_outcomes"]
    ]
    maturity = snapshot["maturity"]
    if maturity["accepted_count"] > maturity["proposal_count"]:
        raise PartnerContractError("Maturity accepted_count cannot exceed proposal_count.")
    _require_unique_ids(
        snapshot,
        ("goals", "observations", "approvals", "executor_outcomes", "inferred_preferences"),
    )
    return snapshot


def _validate_observations_v2(snapshot: Mapping[str, Any]) -> None:
    created_at = _parse_wake_created_at(snapshot["created_at"])
    seen_logical_keys: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()

    for observation in snapshot["observations"]:
        _require_canonical_observation_strings(observation)
        interest_ids = observation["interest_ids"]
        if interest_ids != sorted(interest_ids) or len(interest_ids) != len(set(interest_ids)):
            raise PartnerContractError(
                "Version-2 observation interest_ids must be sorted and duplicate-free."
            )

        semantic_projection = {
            field: copy.deepcopy(observation[field])
            for field in _OBSERVATION_V2_SEMANTIC_FIELDS
        }
        expected_revision = "sha256:" + hashlib.sha256(
            _canonical_json_bytes(semantic_projection)
        ).hexdigest()
        if observation["source_revision"] != expected_revision:
            raise PartnerContractError(
                "Version-2 observation source_revision does not match its canonical content."
            )

        identity_projection = {
            "contract_version": observation["contract_version"],
            "collector_id": observation["collector_id"],
            "dedupe_key": observation["dedupe_key"],
            "source_revision": observation["source_revision"],
        }
        expected_id = "obs-v2-" + hashlib.sha256(
            _canonical_json_bytes(identity_projection)
        ).hexdigest()
        if observation["id"] != expected_id:
            raise PartnerContractError(
                "Version-2 observation id does not match its canonical identity."
            )

        logical_key = (observation["collector_id"], observation["dedupe_key"])
        if logical_key in seen_logical_keys:
            raise PartnerContractError(
                "Version-2 wake contains a duplicate collector and dedupe-key tuple."
            )
        if observation["id"] in seen_ids:
            raise PartnerContractError("Version-2 wake contains a duplicate observation id.")
        seen_logical_keys.add(logical_key)
        seen_ids.add(observation["id"])

        observed_at = _parse_exact_utc_seconds(observation["observed_at"], "observed_at")
        expires_at = _parse_exact_utc_seconds(observation["expires_at"], "expires_at")
        if observed_at > created_at + timedelta(seconds=5):
            raise PartnerContractError(
                "Version-2 observation observed_at exceeds the wake skew ceiling."
            )
        if observed_at >= expires_at:
            raise PartnerContractError(
                "Version-2 observation observed_at must be earlier than expires_at."
            )
        if expires_at <= created_at:
            raise PartnerContractError("Version-2 observation is stale at wake creation.")
        maximum_ttl = _OBSERVATION_V2_TTL[observation["collector_id"]]
        if expires_at - observed_at > maximum_ttl:
            raise PartnerContractError(
                "Version-2 observation exceeds its collector-specific TTL ceiling."
            )


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PartnerContractError(
            "Version-2 observation is not canonical JSON."
        ) from exc


def _require_canonical_observation_strings(observation: Mapping[str, Any]) -> None:
    for field, value in observation.items():
        values = value if field == "interest_ids" else (value,)
        for item in values:
            if not isinstance(item, str):
                continue
            if (
                item != item.strip()
                or unicodedata.normalize("NFC", item) != item
                or any(ord(character) < 32 or ord(character) == 127 for character in item)
            ):
                raise PartnerContractError(
                    f"Version-2 observation field `{field}` is not canonical text."
                )


def _parse_exact_utc_seconds(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not _UTC_SECONDS_PATTERN.fullmatch(value):
        raise PartnerContractError(
            f"Version-2 observation `{field}` must be UTC RFC 3339 whole seconds."
        )
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise PartnerContractError(
            f"Version-2 observation `{field}` is not a valid timestamp."
        ) from exc


def _parse_wake_created_at(value: Any) -> datetime:
    if not isinstance(value, str):
        raise PartnerContractError("Wake created_at must be a timestamp string.")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise PartnerContractError("Wake created_at is not a valid timestamp.") from exc
    if parsed.tzinfo is None:
        raise PartnerContractError("Wake created_at must include a UTC offset.")
    return parsed.astimezone(timezone.utc)


def apply_identity_amendments(
    identity: Mapping[str, Any],
    amendments: Sequence[Mapping[str, Any]],
    approvals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    current = validate_identity(identity)
    approval_by_amendment: dict[str, dict[str, Any]] = {}
    for approval_payload in approvals:
        approval = _copy_mapping(approval_payload, "identity amendment approval")
        _reject_raw_private_keys(approval)
        _reject_secret_like_values(approval)
        _validate_schema(approval, "partner-approval.schema.json")
        if "amendment_id" in approval:
            amendment_id = str(approval["amendment_id"])
        else:
            if approval["approval_kind"] != "identity_amendment":
                raise PartnerContractError("Identity amendment requires an identity_amendment approval.")
            amendment_id = str(approval["subject_id"])
        if amendment_id in approval_by_amendment:
            raise PartnerContractError(f"Duplicate approval for amendment `{amendment_id}`.")
        approval_by_amendment[amendment_id] = approval

    for amendment_payload in amendments:
        amendment = _copy_mapping(amendment_payload, "identity amendment")
        _validate_identity_amendment(amendment)
        amendment_id = str(amendment["amendment_id"])
        if amendment["base_identity_hash"] != current["content_hash"]:
            raise PartnerContractError(
                f"Amendment `{amendment_id}` is not bound to the current identity hash."
            )
        approval = approval_by_amendment.get(amendment_id)
        if not approval or approval.get("approved") is not True:
            raise PartnerContractError(f"Amendment `{amendment_id}` lacks explicit approval.")
        approval_hash = approval.get("amendment_hash", approval.get("subject_hash"))
        if approval_hash != canonical_hash(amendment):
            raise PartnerContractError(f"Approval for amendment `{amendment_id}` has a hash mismatch.")

        updated = copy.deepcopy(current)
        updated.pop("content_hash", None)
        for field, items in amendment["changes"].items():
            updated[field].extend(copy.deepcopy(items))
        current = validate_identity(updated)
    return current


def validate_document(payload: Mapping[str, Any], schema_name: str) -> dict[str, Any]:
    document = _copy_mapping(payload, schema_name)
    _reject_raw_private_keys(document)
    _reject_secret_like_values(document)
    _validate_schema(document, schema_name)
    return document


def validate_executor_envelope(payload: Mapping[str, Any]) -> dict[str, Any]:
    envelope = validate_document(payload, "partner-executor-envelope.schema.json")
    if envelope["content_hash"] != canonical_hash(envelope):
        raise PartnerContractError("Executor envelope content_hash does not match its content.")
    if envelope["risk_level"] not in {"low", "medium"}:
        raise PartnerContractError("Executor envelope risk must be low or medium.")
    if envelope["builder_model"] != "gpt-5.5" or envelope["builder_reasoning_effort"] != "high":
        raise PartnerContractError("Partner executor model routing must remain gpt-5.5/high.")
    capabilities = set(envelope["capability_classes"])
    if not capabilities or not capabilities.issubset(_EXECUTOR_SANDBOX_CAPABILITIES):
        raise PartnerContractError("Executor envelope contains unsupported capability classes.")

    approval = validate_document(envelope["approval_binding"], "partner-approval.schema.json")
    if approval.get("approval_kind") != "proposal" or approval.get("approved") is not True:
        raise PartnerContractError("Executor envelope requires an approved proposal binding.")
    if envelope["approval_id"] != approval.get("approval_id"):
        raise PartnerContractError("Executor envelope approval id does not match its binding.")
    if envelope["approval_hash"] != canonical_hash(approval):
        raise PartnerContractError("Executor envelope approval hash does not match its binding.")
    if approval.get("subject_id") != envelope["proposal_id"]:
        raise PartnerContractError("Executor envelope approval subject id does not match its proposal.")
    if approval.get("subject_hash") != envelope["proposal_hash"]:
        raise PartnerContractError("Executor envelope approval subject hash does not match its proposal.")
    if set(approval.get("capability_classes", [])) != capabilities:
        raise PartnerContractError("Executor envelope approval capabilities do not match its proposal.")

    run_contract = validate_document(envelope["run_contract"], "run-contract.schema.json")
    if envelope["run_contract_hash"] != canonical_hash(run_contract):
        raise PartnerContractError("Executor run contract hash does not match its content.")
    bindings = {
        "claim_id": envelope["envelope_id"],
        "run_trace_id": envelope["wake_id"],
        "issue_snapshot_hash": envelope["proposal_hash"],
        "risk_level": envelope["risk_level"].title(),
        "approval_required": False,
    }
    for field, expected in bindings.items():
        if run_contract.get(field) != expected:
            raise PartnerContractError(
                f"Executor run contract `{field}` does not match its envelope binding."
            )
    constraints = run_contract["constraints"]
    if constraints.get("auto_push") is True or constraints.get("auto_merge") is True:
        raise PartnerContractError("Partner executor may not auto-push or auto-merge.")
    return envelope


def validate_safe_payload(payload: Mapping[str, Any], label: str = "payload") -> dict[str, Any]:
    document = _copy_mapping(payload, label)
    _reject_raw_private_keys(document)
    _reject_secret_like_values(document)
    return document


def _validate_identity_amendment(amendment: dict[str, Any]) -> None:
    _reject_raw_private_keys(amendment)
    _reject_secret_like_values(amendment)
    allowed_fields = {"schema_version", "amendment_id", "base_identity_hash", "changes"}
    if set(amendment) != allowed_fields:
        raise PartnerContractError(
            "Identity amendment fields must be exactly schema_version, amendment_id, "
            "base_identity_hash, and changes."
        )
    if amendment["schema_version"] != "1":
        raise PartnerContractError("Identity amendment schema_version must be `1`.")
    if not isinstance(amendment["amendment_id"], str) or not amendment["amendment_id"]:
        raise PartnerContractError("Identity amendment requires a non-empty amendment_id.")
    if not re.fullmatch(r"[0-9a-f]{64}", str(amendment["base_identity_hash"])):
        raise PartnerContractError("Identity amendment base_identity_hash must be SHA-256 hex.")
    changes = amendment["changes"]
    if not isinstance(changes, dict) or not changes:
        raise PartnerContractError("Identity amendment changes must be a non-empty object.")
    if not set(changes).issubset(IDENTITY_LIST_FIELDS):
        raise PartnerContractError("Identity amendment may change only labeled identity list fields.")
    for field, items in changes.items():
        if not isinstance(items, list) or not items:
            raise PartnerContractError(f"Identity amendment field `{field}` must be a non-empty list.")
        for item in items:
            if not isinstance(item, dict) or set(item) != {"id", "value", "source"}:
                raise PartnerContractError(f"Identity amendment field `{field}` has an invalid item.")
            if item.get("source") != "operator_approved":
                raise PartnerContractError(
                    f"Identity amendment field `{field}` must retain operator_approved provenance."
                )


def _validate_schema(payload: dict[str, Any], schema_name: str) -> None:
    try:
        schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PartnerContractError(f"Could not load schema `{schema_name}`: {exc}.") from exc
    errors = sorted(
        Draft202012Validator(schema, registry=_schema_registry()).iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        messages = []
        for error in errors:
            safe_parts = []
            for part in error.absolute_path:
                if isinstance(part, int):
                    safe_parts.append(str(part))
                elif isinstance(part, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]{0,79}", part):
                    safe_parts.append(part)
                else:
                    safe_parts.append("<field>")
            location = ".".join(safe_parts) or "<root>"
            validator = str(error.validator)
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,79}", validator):
                validator = "schema"
            messages.append(f"{location}: violates `{validator}` constraint")
        raise PartnerContractError("; ".join(messages))


@lru_cache(maxsize=1)
def _schema_registry() -> Registry:
    registry = Registry()
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        identifier = schema.get("$id")
        if isinstance(identifier, str) and identifier:
            registry = registry.with_resource(identifier, Resource.from_contents(schema))
    return registry


def _copy_mapping(payload: Mapping[str, Any], label: str) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise PartnerContractError(f"Partner {label} must be an object.")
    try:
        copied = copy.deepcopy(dict(payload))
        json.dumps(copied, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise PartnerContractError(f"Partner {label} must contain only finite JSON values: {exc}.") from exc
    return copied


def _require_unique_ids(payload: Mapping[str, Any], fields: Sequence[str]) -> None:
    for field in fields:
        values = payload.get(field, [])
        if not isinstance(values, list):
            continue
        ids = [item.get("id") for item in values if isinstance(item, dict) and "id" in item]
        if len(ids) != len(set(ids)):
            raise PartnerContractError(f"Partner field `{field}` contains duplicate ids.")


def _reject_secret_like_values(payload: Any, path: str = "<root>") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if isinstance(key, str) and any(pattern.search(key) for pattern in _SECRET_PATTERNS):
                raise PartnerContractError("Secret-like content is forbidden in partner documents.")
            _reject_secret_like_values(value, f"{path}.{key}")
        return
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            _reject_secret_like_values(value, f"{path}[{index}]")
        return
    if isinstance(payload, str) and any(pattern.search(payload) for pattern in _SECRET_PATTERNS):
        raise PartnerContractError("Secret-like content is forbidden in partner documents.")


def _reject_raw_private_keys(payload: Any, path: str = "<root>") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key).lower() in _RAW_PRIVATE_KEYS:
                raise PartnerContractError("Raw private content fields are forbidden in partner documents.")
            _reject_raw_private_keys(value, f"{path}.{key}")
        return
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            _reject_raw_private_keys(value, f"{path}[{index}]")

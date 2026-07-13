from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
from jsonschema import Draft202012Validator


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
    supplied_hash = identity.pop("content_hash", None)
    _validate_schema(identity, "partner-identity.schema.json")
    _reject_raw_private_keys(identity)
    _reject_secret_like_values(identity)
    _require_unique_ids(identity, IDENTITY_LIST_FIELDS)
    computed_hash = canonical_hash(identity)
    if supplied_hash is not None and supplied_hash != computed_hash:
        raise PartnerContractError("Identity content_hash does not match its canonical content.")
    identity["content_hash"] = computed_hash
    return identity


def validate_wake_snapshot(payload: Mapping[str, Any]) -> dict[str, Any]:
    snapshot = _copy_mapping(payload, "wake snapshot")
    _validate_schema(snapshot, "partner-wake-snapshot.schema.json")
    _reject_raw_private_keys(snapshot)
    _reject_secret_like_values(snapshot)
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


def apply_identity_amendments(
    identity: Mapping[str, Any],
    amendments: Sequence[Mapping[str, Any]],
    approvals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    current = validate_identity(identity)
    approval_by_amendment: dict[str, dict[str, Any]] = {}
    for approval_payload in approvals:
        approval = _copy_mapping(approval_payload, "identity amendment approval")
        _validate_schema(approval, "partner-approval.schema.json")
        _reject_raw_private_keys(approval)
        _reject_secret_like_values(approval)
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
    _validate_schema(document, schema_name)
    _reject_raw_private_keys(document)
    _reject_secret_like_values(document)
    return document


def _validate_identity_amendment(amendment: dict[str, Any]) -> None:
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
    _reject_secret_like_values(amendment)


def _validate_schema(payload: dict[str, Any], schema_name: str) -> None:
    try:
        schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PartnerContractError(f"Could not load schema `{schema_name}`: {exc}.") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        messages = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            messages.append(f"{location}: {error.message}")
        raise PartnerContractError("; ".join(messages))


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
            _reject_secret_like_values(value, f"{path}.{key}")
        return
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            _reject_secret_like_values(value, f"{path}[{index}]")
        return
    if isinstance(payload, str) and any(pattern.search(payload) for pattern in _SECRET_PATTERNS):
        raise PartnerContractError(f"Secret-like content is forbidden at `{path}`.")


def _reject_raw_private_keys(payload: Any, path: str = "<root>") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key).lower() in _RAW_PRIVATE_KEYS:
                raise PartnerContractError(f"Raw private content field is forbidden at `{path}.{key}`.")
            _reject_raw_private_keys(value, f"{path}.{key}")
        return
    if isinstance(payload, list):
        for index, value in enumerate(payload):
            _reject_raw_private_keys(value, f"{path}[{index}]")

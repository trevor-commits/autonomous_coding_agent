from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, TextIO

from supervisor.partner_authority import POLICY_VERSION as AUTHORITY_POLICY_VERSION
from supervisor.partner_contracts import (
    PartnerContractError,
    canonical_hash,
    load_identity_document,
    load_json_document,
    validate_document,
    validate_safe_payload,
    validate_wake_snapshot,
)
from supervisor.partner_learning import PartnerLearningError, derive_learning_candidates
from supervisor.partner_runtime import PartnerRuntimeError, decide_wake


class PartnerCliUsageError(ValueError):
    pass


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise PartnerCliUsageError(message)


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    args_list = list(argv if argv is not None else sys.argv[1:])
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    if _contains_secret_argument(args_list):
        _write_json(stdout, {"ok": False, "error_code": "secret_arguments_forbidden"})
        return 64

    try:
        args = _build_parser().parse_args(args_list)
        result = _dispatch(args)
    except PartnerCliUsageError:
        _write_json(stdout, {"ok": False, "error_code": "invalid_arguments"})
        return 64
    except (PartnerContractError, PartnerRuntimeError, PartnerLearningError, OSError, ValueError) as exc:
        _write_json(
            stdout,
            {
                "ok": False,
                "error_code": _error_code(exc),
                "error": _safe_error_message(exc),
            },
        )
        return 2
    _write_json(stdout, result)
    return 0


def _build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(prog="partner", add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--identity", required=True)

    observe_parser = subparsers.add_parser("observe")
    observe_parser.add_argument("--snapshot", required=True)

    goal_parser = subparsers.add_parser("add-goal")
    goal_parser.add_argument("--goal-file", required=True)

    approval_parser = subparsers.add_parser("approve")
    approval_parser.add_argument("--approval-file", required=True)

    wake_parser = subparsers.add_parser("wake")
    _add_wake_arguments(wake_parser)

    propose_parser = subparsers.add_parser("propose")
    _add_wake_arguments(propose_parser, include_mode=False)

    reconcile_parser = subparsers.add_parser("reconcile")
    reconcile_parser.add_argument("--outcome", required=True)
    reconcile_parser.add_argument("--envelope", required=True)
    reconcile_parser.add_argument("--proposal", required=True)
    reconcile_parser.add_argument("--now", default=None)

    subparsers.add_parser("status")
    return parser


def _add_wake_arguments(parser: argparse.ArgumentParser, *, include_mode: bool = True) -> None:
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--health", required=True)
    parser.add_argument("--now", default=None)
    parser.add_argument("--busy", action="store_true")
    parser.add_argument("--kill-switch", action="append", default=[])
    parser.add_argument("--prior-decisions")
    if include_mode:
        parser.add_argument("--mode", choices=("observe", "propose", "execute"), default="observe")


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "init":
        identity = load_identity_document(args.identity)
        return {
            "ok": True,
            "kind": "identity_bootstrap",
            "name": identity["name"],
            "identity_hash": identity["content_hash"],
            "stored": False,
        }
    if args.command == "observe":
        snapshot = validate_wake_snapshot(load_json_document(args.snapshot))
        return {
            "ok": True,
            "mode": "observe_only",
            "wake_id": snapshot["wake_id"],
            "identity_hash": snapshot["identity"]["content_hash"],
            "goal_count": len(snapshot["goals"]),
            "observation_count": len(snapshot["observations"]),
            "approval_count": len(snapshot["approvals"]),
            "outcome_count": len(snapshot["executor_outcomes"]),
            "stored": False,
        }
    if args.command == "add-goal":
        goal = validate_safe_payload(load_json_document(args.goal_file), "goal candidate")
        if set(goal) != {"id", "summary", "source_ref"}:
            raise PartnerContractError("Goal candidate fields must be id, summary, and source_ref.")
        if any(not isinstance(goal[field], str) or not goal[field] for field in goal):
            raise PartnerContractError("Goal candidate fields must be non-empty text.")
        return {
            "ok": True,
            "kind": "goal_candidate",
            "goal": goal,
            "content_hash": canonical_hash(goal),
            "stored": False,
        }
    if args.command == "approve":
        approval = validate_document(
            load_json_document(args.approval_file), "partner-approval.schema.json"
        )
        return {"ok": True, **approval, "stored": False}
    if args.command in {"wake", "propose"}:
        mode = "propose" if args.command == "propose" else args.mode
        snapshot = load_json_document(args.snapshot)
        candidates = _load_json_list(args.candidates, "candidates")
        health = load_json_document(args.health)
        prior_decisions = (
            _load_json_list(args.prior_decisions, "prior decisions")
            if args.prior_decisions
            else []
        )
        return decide_wake(
            snapshot,
            candidates=candidates,
            now=args.now or _now(),
            health=health,
            busy=args.busy,
            kill_switches=args.kill_switch,
            prior_decisions=prior_decisions,
            mode=mode,
        )
    if args.command == "reconcile":
        return derive_learning_candidates(
            load_json_document(args.outcome),
            envelope=load_json_document(args.envelope),
            proposal=load_json_document(args.proposal),
            now=args.now or _now(),
        )
    if args.command == "status":
        return {
            "ok": True,
            "service": "autonomous-partner-policy",
            "storage": "stateless",
            "policy_version": AUTHORITY_POLICY_VERSION,
            "default_wake_mode": "observe",
            "supported_modes": ["observe", "propose", "execute"],
        }
    raise PartnerCliUsageError("Unsupported command.")


def _load_json_list(path: Path | str, label: str) -> list[dict[str, Any]]:
    document_path = Path(path)
    try:
        payload = json.loads(document_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PartnerContractError(f"Could not load {label} file `{document_path}`: {exc}.") from exc
    if not isinstance(payload, list) or any(not isinstance(item, dict) for item in payload):
        raise PartnerContractError(f"{label.title()} file must contain a list of objects.")
    return [validate_safe_payload(item, label) for item in payload]


def _contains_secret_argument(argv: Sequence[str]) -> bool:
    forbidden = {"--secret", "--token", "--password", "--api-key", "--credential"}
    return any(argument.split("=", 1)[0].lower() in forbidden for argument in argv)


def _error_code(exc: BaseException) -> str:
    if isinstance(exc, PartnerContractError):
        return "contract_invalid"
    if isinstance(exc, PartnerRuntimeError):
        return "wake_invalid"
    if isinstance(exc, PartnerLearningError):
        return "outcome_invalid"
    return "operation_failed"


def _safe_error_message(exc: BaseException) -> str:
    message = str(exc)
    return message if len(message) <= 500 else message[:497] + "..."


def _write_json(stream: TextIO, payload: MappingLike) -> None:
    stream.write(json.dumps(payload, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


MappingLike = dict[str, Any]


if __name__ == "__main__":
    raise SystemExit(main())

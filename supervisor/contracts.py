from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from supervisor.models import RunState


SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


class ContractValidationError(ValueError):
    """Raised when a repo or run contract is invalid."""

    def __init__(self, message: str, run_state: RunState = RunState.UNSUPPORTED) -> None:
        super().__init__(message)
        self.run_state = run_state


@dataclass(frozen=True)
class RepoCommands:
    setup: str
    test: str
    app_up: str
    app_health: str
    lint: str | None = None
    typecheck: str | None = None
    format: str | None = None
    app_down: str | None = None
    ui_smoke: str | None = None
    seed_testdata: str | None = None

    def auto_allow_commands(self) -> tuple[str, ...]:
        commands = [
            self.setup,
            self.test,
            self.app_up,
            self.app_health,
            self.lint,
            self.typecheck,
            self.format,
            self.app_down,
            self.ui_smoke,
            self.seed_testdata,
        ]
        return tuple(command for command in commands if command)


@dataclass(frozen=True)
class UIFlow:
    id: str
    route: str
    assertions: tuple[str, ...]


@dataclass(frozen=True)
class RepoUIConfig:
    base_url: str | None = None
    breakpoints: tuple[str, ...] = ()
    critical_flows: tuple[UIFlow, ...] = ()


@dataclass(frozen=True)
class RepoEnvConfig:
    required_vars: tuple[str, ...] = ()
    template: str | None = None


@dataclass(frozen=True)
class RepoContract:
    version: int
    stack: str
    commands: RepoCommands
    ui: RepoUIConfig
    env: RepoEnvConfig

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunScope:
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]

    def relative_path_for(self, repo_root: Path, candidate: Path) -> str:
        resolved_root = repo_root.resolve()
        resolved_candidate = candidate.resolve()
        try:
            relative = resolved_candidate.relative_to(resolved_root)
        except ValueError as exc:
            raise ContractValidationError(
                f"Path `{candidate}` is outside repo root `{repo_root}`.",
                run_state=RunState.BLOCKED,
            ) from exc
        normalized = _normalize_relative_path(relative.as_posix())
        if not normalized:
            raise ContractValidationError(
                "Scope checks require a path inside the repo, not the repo root itself.",
                run_state=RunState.BLOCKED,
            )
        return normalized

    def allows(self, repo_root: Path, candidate: Path) -> bool:
        relative = self.relative_path_for(repo_root, candidate)
        if any(_path_matches_prefix(relative, forbidden) for forbidden in self.forbidden_paths):
            return False
        return any(_path_matches_prefix(relative, allowed) for allowed in self.allowed_paths)

    def assert_allows(self, repo_root: Path, candidate: Path) -> None:
        if not self.allows(repo_root, candidate):
            relative = self.relative_path_for(repo_root, candidate)
            raise ContractValidationError(
                f"Path `{relative}` violates run scope: allowed={self.allowed_paths}, "
                f"forbidden={self.forbidden_paths}.",
                run_state=RunState.BLOCKED,
            )


@dataclass(frozen=True)
class RunAcceptance:
    functional: tuple[str, ...]
    quality_gates: tuple[str, ...]
    ui_checks: tuple[str, ...]


@dataclass(frozen=True)
class RunConstraints:
    single_writer: bool
    max_repair_loops: int
    max_iterations: int
    max_cost_dollars: float
    hard_timeout_seconds: int
    auto_push: bool = False
    auto_merge: bool = False


@dataclass(frozen=True)
class QueueMetadata:
    claim_id: str | None = None
    run_trace_id: str | None = None
    queue_entry_reason: str | None = None
    queue_contract_version: str | None = None
    prompt_template_version: str | None = None
    issue_snapshot_hash: str | None = None
    follow_up_policy: str | None = None
    risk_level: str | None = None
    approval_required: bool | None = None
    retry_budget: int | None = None
    staleness_deadline: str | None = None
    verification_pack: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunContract:
    run_id: str
    repo_path: str
    objective: str
    scope: RunScope
    acceptance: RunAcceptance
    constraints: RunConstraints
    queue: QueueMetadata

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "run_id": self.run_id,
            "repo_path": self.repo_path,
            "objective": self.objective,
            "scope": {
                "allowed_paths": list(self.scope.allowed_paths),
                "forbidden_paths": list(self.scope.forbidden_paths),
            },
            "acceptance": {
                "functional": list(self.acceptance.functional),
                "quality_gates": list(self.acceptance.quality_gates),
                "ui_checks": list(self.acceptance.ui_checks),
            },
            "constraints": {
                "single_writer": self.constraints.single_writer,
                "max_repair_loops": self.constraints.max_repair_loops,
                "max_iterations": self.constraints.max_iterations,
                "max_cost_dollars": self.constraints.max_cost_dollars,
                "hard_timeout_seconds": self.constraints.hard_timeout_seconds,
                "auto_push": self.constraints.auto_push,
                "auto_merge": self.constraints.auto_merge,
            },
        }
        if self.queue.claim_id is not None:
            payload["claim_id"] = self.queue.claim_id
        if self.queue.run_trace_id is not None:
            payload["run_trace_id"] = self.queue.run_trace_id
        if self.queue.queue_entry_reason is not None:
            payload["queue_entry_reason"] = self.queue.queue_entry_reason
        if self.queue.queue_contract_version is not None:
            payload["queue_contract_version"] = self.queue.queue_contract_version
        if self.queue.prompt_template_version is not None:
            payload["prompt_template_version"] = self.queue.prompt_template_version
        if self.queue.issue_snapshot_hash is not None:
            payload["issue_snapshot_hash"] = self.queue.issue_snapshot_hash
        if self.queue.follow_up_policy is not None:
            payload["follow_up_policy"] = self.queue.follow_up_policy
        if self.queue.risk_level is not None:
            payload["risk_level"] = self.queue.risk_level
        if self.queue.approval_required is not None:
            payload["approval_required"] = self.queue.approval_required
        if self.queue.retry_budget is not None:
            payload["retry_budget"] = self.queue.retry_budget
        if self.queue.staleness_deadline is not None:
            payload["staleness_deadline"] = self.queue.staleness_deadline
        if self.queue.verification_pack:
            payload["verification_pack"] = list(self.queue.verification_pack)
        return payload


def load_repo_contract(repo_root: Path | str) -> RepoContract:
    root = Path(repo_root)
    contract_path = root / ".agent" / "contract.yml"
    if not contract_path.exists():
        raise ContractValidationError(
            f"Missing repo contract at `{contract_path}`.",
            run_state=RunState.UNSUPPORTED,
        )
    raw = yaml.safe_load(contract_path.read_text()) or {}
    validated = _validate_schema(raw, "repo-contract.schema.json")
    return RepoContract(
        version=validated["version"],
        stack=validated["stack"],
        commands=RepoCommands(**validated["commands"]),
        ui=_build_repo_ui(validated.get("ui", {})),
        env=_build_repo_env(validated.get("env", {})),
    )


def load_run_contract(contract_path: Path | str) -> RunContract:
    path = Path(contract_path)
    raw = json.loads(path.read_text())
    validated = _validate_schema(raw, "run-contract.schema.json")
    return RunContract(
        run_id=validated["run_id"],
        repo_path=validated["repo_path"],
        objective=validated["objective"],
        scope=RunScope(
            allowed_paths=tuple(_normalize_relative_path(path) for path in validated["scope"]["allowed_paths"]),
            forbidden_paths=tuple(_normalize_relative_path(path) for path in validated["scope"]["forbidden_paths"]),
        ),
        acceptance=RunAcceptance(
            functional=tuple(validated["acceptance"]["functional"]),
            quality_gates=tuple(validated["acceptance"]["quality_gates"]),
            ui_checks=tuple(validated["acceptance"]["ui_checks"]),
        ),
        constraints=RunConstraints(**validated["constraints"]),
        queue=QueueMetadata(
            claim_id=validated.get("claim_id"),
            run_trace_id=validated.get("run_trace_id"),
            queue_entry_reason=validated.get("queue_entry_reason"),
            queue_contract_version=validated.get("queue_contract_version"),
            prompt_template_version=validated.get("prompt_template_version"),
            issue_snapshot_hash=validated.get("issue_snapshot_hash"),
            follow_up_policy=validated.get("follow_up_policy"),
            risk_level=validated.get("risk_level"),
            approval_required=validated.get("approval_required"),
            retry_budget=validated.get("retry_budget"),
            staleness_deadline=validated.get("staleness_deadline"),
            verification_pack=tuple(validated.get("verification_pack", [])),
        ),
    )


def _validate_schema(payload: dict[str, Any], schema_name: str) -> dict[str, Any]:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text())
    errors = sorted(
        Draft202012Validator(schema).iter_errors(payload),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        messages = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            messages.append(f"{location}: {error.message}")
        raise ContractValidationError("; ".join(messages), run_state=RunState.UNSUPPORTED)
    return payload


def _build_repo_ui(payload: dict[str, Any]) -> RepoUIConfig:
    flows = tuple(
        UIFlow(
            id=flow["id"],
            route=flow["route"],
            assertions=tuple(flow["assertions"]),
        )
        for flow in payload.get("critical_flows", [])
    )
    return RepoUIConfig(
        base_url=payload.get("base_url"),
        breakpoints=tuple(payload.get("breakpoints", [])),
        critical_flows=flows,
    )


def _build_repo_env(payload: dict[str, Any]) -> RepoEnvConfig:
    return RepoEnvConfig(
        required_vars=tuple(payload.get("required_vars", [])),
        template=payload.get("template"),
    )


def _normalize_relative_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute():
        raise ContractValidationError(
            f"Relative scope paths may not be absolute: `{value}`.",
            run_state=RunState.UNSUPPORTED,
        )
    if ".." in path.parts:
        raise ContractValidationError(
            f"Relative scope paths may not traverse parents: `{value}`.",
            run_state=RunState.UNSUPPORTED,
        )
    normalized = path.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.rstrip("/")
    if normalized in {"", "."}:
        raise ContractValidationError(
            f"Relative scope path `{value}` resolves to the repo root, which is too broad.",
            run_state=RunState.UNSUPPORTED,
        )
    return normalized


def _path_matches_prefix(relative_path: str, prefix: str) -> bool:
    normalized_prefix = _normalize_relative_path(prefix)
    return relative_path == normalized_prefix or relative_path.startswith(
        normalized_prefix + "/"
    )

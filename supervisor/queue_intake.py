from __future__ import annotations

import hashlib
import json
import re
import subprocess
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from supervisor.builder_adapter import BuilderAdapter
from supervisor.contracts import RepoContract, load_repo_contract, load_run_contract
from supervisor.run_store import RunStore
from supervisor.strategy_simple import SimpleStrategy
from supervisor.worktree_manager import WorktreeManager

if False:  # pragma: no cover
    from supervisor.main import RunExecutionOutcome


BLOCKING_LABELS = ("prompt-review", "Blocked-external")
DEFAULT_FORBIDDEN_PATHS = (".env", "infra", "deploy")
DEFAULT_MAX_ITERATIONS = 50
DEFAULT_MAX_COST_DOLLARS = 10.0
DEFAULT_HARD_TIMEOUT_SECONDS = 3600
QUEUE_CONTRACT_VERSION = "2026-04-17-manual-drain-v1"
PROMPT_TEMPLATE_VERSION = "2026-04-16"
FOLLOW_UP_POLICY = "adjacent-blocker-only"


class QueueError(RuntimeError):
    """Raised when the queue controller cannot continue cleanly."""


@dataclass(frozen=True)
class LinearIssueDescription:
    authoritative_spec_path: str
    execution_lane: str
    execution_mode: str
    risk_level: str
    approval_required: bool
    allowed_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()
    verification_pack: tuple[str, ...] = ()
    retry_budget: int | None = None


@dataclass(frozen=True)
class LinearIssue:
    id: str
    identifier: str
    title: str
    description: str
    status: str
    priority: int | None
    updated_at: str
    labels: tuple[str, ...]

    def parsed_description(self) -> LinearIssueDescription:
        return parse_issue_description(self.description)

    def snapshot_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "identifier": self.identifier,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "updated_at": self.updated_at,
            "labels": list(self.labels),
        }


@dataclass(frozen=True)
class QueueRunIds:
    run_id: str
    claim_id: str
    run_trace_id: str


@dataclass(frozen=True)
class NormalizedQueueIssue:
    issue: LinearIssue
    description: LinearIssueDescription
    repo_contract: RepoContract
    spec_path: Path
    run_contract_path: Path
    run_contract: Any
    ids: QueueRunIds


@dataclass(frozen=True)
class QueueDrainSummary:
    processed_count: int
    completed_count: int
    blocked_count: int


class QueueLinearClient(ABC):
    @abstractmethod
    def list_ready_for_build(self, team_key: str) -> list[LinearIssue]:
        raise NotImplementedError

    @abstractmethod
    def transition_issue(self, issue_id: str, state_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_comment(self, issue_id: str, body: str) -> None:
        raise NotImplementedError


class LinearGraphQLClient(QueueLinearClient):
    def __init__(
        self,
        *,
        token: str,
        endpoint: str = "https://api.linear.app/graphql",
        timeout_seconds: int = 30,
    ) -> None:
        self.token = token
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._team_states: dict[str, dict[str, str]] = {}
        self._last_team_key: str | None = None

    def list_ready_for_build(self, team_key: str) -> list[LinearIssue]:
        self._last_team_key = team_key
        query = """
        query QueueIssues($teamKey: String!) {
          issues(
            filter: {
              team: { key: { eq: $teamKey } }
              state: { name: { eq: "Ready for Build" } }
            }
          ) {
            nodes {
              id
              identifier
              title
              description
              priority
              updatedAt
              state {
                name
              }
              labels {
                nodes {
                  name
                }
              }
            }
          }
        }
        """
        payload = self._graphql(query, {"teamKey": team_key})
        nodes = payload["issues"]["nodes"]
        issues: list[LinearIssue] = []
        for node in nodes:
            issues.append(
                LinearIssue(
                    id=node["id"],
                    identifier=node["identifier"],
                    title=node["title"],
                    description=node.get("description") or "",
                    status=node["state"]["name"],
                    priority=node.get("priority"),
                    updated_at=node["updatedAt"],
                    labels=tuple(label["name"] for label in node["labels"]["nodes"]),
                )
            )
        return issues

    def transition_issue(self, issue_id: str, state_name: str) -> None:
        team_key = self._last_team_key
        if team_key is None:
            raise QueueError("Linear team state cache is empty; call list_ready_for_build first.")
        state_id = self._state_id_for(team_key, state_name)
        mutation = """
        mutation MoveIssue($issueId: String!, $stateId: String!) {
          issueUpdate(id: $issueId, input: { stateId: $stateId }) {
            success
          }
        }
        """
        self._graphql(mutation, {"issueId": issue_id, "stateId": state_id})

    def create_comment(self, issue_id: str, body: str) -> None:
        mutation = """
        mutation CommentIssue($issueId: String!, $body: String!) {
          commentCreate(input: { issueId: $issueId, body: $body }) {
            success
          }
        }
        """
        self._graphql(mutation, {"issueId": issue_id, "body": body})

    def _state_id_for(self, team_key: str, state_name: str) -> str:
        if team_key not in self._team_states:
            query = """
            query TeamStates($teamKey: String!) {
              team(key: $teamKey) {
                states {
                  nodes {
                    id
                    name
                  }
                }
              }
            }
            """
            payload = self._graphql(query, {"teamKey": team_key})
            self._team_states[team_key] = {
                node["name"]: node["id"]
                for node in payload["team"]["states"]["nodes"]
            }
        try:
            return self._team_states[team_key][state_name]
        except KeyError as exc:
            raise QueueError(f"Linear state `{state_name}` not found for team `{team_key}`.") from exc

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                materialized = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise QueueError(f"Linear GraphQL request failed: {exc}") from exc
        errors = materialized.get("errors") or []
        if errors:
            raise QueueError(f"Linear GraphQL returned errors: {errors}")
        return materialized["data"]


class QueueIssueSelector:
    def eligible_issues(self, issues: list[LinearIssue]) -> list[LinearIssue]:
        eligible = [issue for issue in issues if self._is_eligible(issue)]
        return sorted(eligible, key=self._sort_key)

    def _is_eligible(self, issue: LinearIssue) -> bool:
        if issue.status != "Ready for Build":
            return False
        parsed = issue.parsed_description()
        if parsed.execution_lane != "Codex":
            return False
        if parsed.execution_mode != "Queue":
            return False
        if parsed.risk_level not in {"Low", "Medium"}:
            return False
        if parsed.approval_required:
            return False
        if any(label in BLOCKING_LABELS for label in issue.labels):
            return False
        return True

    def _sort_key(self, issue: LinearIssue) -> tuple[int, str, str]:
        priority = issue.priority if issue.priority is not None else 999
        return (priority, issue.updated_at, issue.identifier)


class QueueClaimStore:
    def __init__(self, repo_root: Path | str) -> None:
        self.root = Path(repo_root).resolve() / ".autoclaw" / "queue-claims"

    def acquire(self, issue_identifier: str, payload: dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{issue_identifier}.json"
        try:
            with path.open("x", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
        except FileExistsError as exc:
            raise QueueError(f"Issue `{issue_identifier}` is already claimed.") from exc
        return path

    def release(self, issue_identifier: str) -> None:
        path = self.root / f"{issue_identifier}.json"
        if path.exists():
            path.unlink()


class QueueIssueNormalizer:
    def __init__(self, repo_root: Path | str) -> None:
        self.repo_root = Path(repo_root).resolve()

    def normalize(
        self,
        issue: LinearIssue,
        ids: QueueRunIds | None = None,
    ) -> NormalizedQueueIssue:
        ids = ids or build_queue_run_ids(issue.identifier)
        repo_contract = load_repo_contract(self.repo_root)
        description = issue.parsed_description()
        spec_path = (self.repo_root / description.authoritative_spec_path).resolve()
        if not spec_path.exists():
            raise QueueError(
                f"Authoritative spec path `{description.authoritative_spec_path}` does not exist in `{self.repo_root}`."
            )
        if not description.allowed_paths:
            raise QueueError(
                f"Issue `{issue.identifier}` is missing `Allowed paths:` required for queue normalization."
            )

        verification_pack = description.verification_pack or _default_verification_pack(repo_contract)
        retry_budget = description.retry_budget if description.retry_budget is not None else _default_retry_budget(
            description.risk_level
        )
        snapshot_hash = _issue_snapshot_hash(issue)
        run_contract_payload = {
            "run_id": ids.run_id,
            "repo_path": str(self.repo_root),
            "objective": f"{issue.identifier}: {issue.title}",
            "scope": {
                "allowed_paths": list(description.allowed_paths),
                "forbidden_paths": list(description.forbidden_paths or DEFAULT_FORBIDDEN_PATHS),
            },
            "acceptance": {
                "functional": [
                    f"Satisfy {issue.identifier}: {issue.title} using {description.authoritative_spec_path}",
                ],
                "quality_gates": [f"{name} passes" for name in verification_pack],
                "ui_checks": list(_ui_checks_for_pack(repo_contract, verification_pack)),
            },
            "constraints": {
                "single_writer": True,
                "auto_push": False,
                "auto_merge": False,
                "max_repair_loops": retry_budget,
                "max_iterations": DEFAULT_MAX_ITERATIONS,
                "max_cost_dollars": DEFAULT_MAX_COST_DOLLARS,
                "hard_timeout_seconds": DEFAULT_HARD_TIMEOUT_SECONDS,
            },
            "claim_id": ids.claim_id,
            "run_trace_id": ids.run_trace_id,
            "queue_entry_reason": "Ready for Build queue claim",
            "queue_contract_version": QUEUE_CONTRACT_VERSION,
            "prompt_template_version": PROMPT_TEMPLATE_VERSION,
            "issue_snapshot_hash": snapshot_hash,
            "follow_up_policy": FOLLOW_UP_POLICY,
            "risk_level": description.risk_level,
            "approval_required": description.approval_required,
            "retry_budget": retry_budget,
            "verification_pack": list(verification_pack),
            "staleness_deadline": _staleness_deadline(issue.updated_at),
        }
        run_contract_path = self.repo_root / ".autoclaw" / "queue-contracts" / f"{ids.run_id}.json"
        run_contract_path.parent.mkdir(parents=True, exist_ok=True)
        run_contract_path.write_text(json.dumps(run_contract_payload, indent=2, sort_keys=True) + "\n")
        run_contract = load_run_contract(run_contract_path)
        return NormalizedQueueIssue(
            issue=issue,
            description=description,
            repo_contract=repo_contract,
            spec_path=spec_path,
            run_contract_path=run_contract_path,
            run_contract=run_contract,
            ids=ids,
        )


class ManualQueueRunner:
    def __init__(
        self,
        *,
        repo_root: Path | str,
        linear_client: QueueLinearClient,
        builder_adapter: BuilderAdapter,
        strategy: SimpleStrategy,
        team_key: str,
        cleanup_success_worktree: bool = True,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.linear_client = linear_client
        self.builder_adapter = builder_adapter
        self.strategy = strategy
        self.team_key = team_key
        self.cleanup_success_worktree = cleanup_success_worktree
        self.selector = QueueIssueSelector()
        self.claim_store = QueueClaimStore(self.repo_root)
        self.normalizer = QueueIssueNormalizer(self.repo_root)

    def drain(self, *, limit: int | None = None) -> QueueDrainSummary:
        issues = self.selector.eligible_issues(self.linear_client.list_ready_for_build(self.team_key))
        if limit is not None:
            issues = issues[:limit]

        processed = 0
        completed = 0
        blocked = 0
        for issue in issues:
            processed += 1
            ids = build_queue_run_ids(issue.identifier)
            self.claim_store.acquire(
                issue.identifier,
                {
                    "issue_id": issue.id,
                    "issue_identifier": issue.identifier,
                    "run_id": ids.run_id,
                    "claim_id": ids.claim_id,
                    "run_trace_id": ids.run_trace_id,
                },
            )
            try:
                self.linear_client.transition_issue(issue.id, "Building")
                description = issue.parsed_description()
                self.linear_client.create_comment(
                    issue.id,
                    _render_claim_comment(issue, ids, description.authoritative_spec_path),
                )
                normalized = self.normalizer.normalize(issue, ids)
                from supervisor.main import execute_run

                outcome = execute_run(
                    repo_root=self.repo_root,
                    run_contract_path=normalized.run_contract_path,
                    builder_adapter=self.builder_adapter,
                    strategy=self.strategy,
                    cleanup_worktree=False,
                )
                if outcome.snapshot.run_state.value == "COMPLETE":
                    self._complete_issue(issue, normalized, outcome)
                    completed += 1
                else:
                    self._block_issue(issue, ids, outcome=outcome)
                    blocked += 1
            except Exception as exc:
                self._block_issue(issue, ids, error=exc)
                blocked += 1
            finally:
                self.claim_store.release(issue.identifier)

        return QueueDrainSummary(
            processed_count=processed,
            completed_count=completed,
            blocked_count=blocked,
        )

    def _complete_issue(
        self,
        issue: LinearIssue,
        normalized: NormalizedQueueIssue,
        outcome: "RunExecutionOutcome",
    ) -> None:
        landing_sha = _land_successful_run(self.repo_root, outcome.workspace, issue.identifier)
        run_store = RunStore(self.repo_root, normalized.ids.run_id)
        closeout_payload = {
            "issue_id": issue.identifier,
            "run_id": normalized.ids.run_id,
            "claim_id": normalized.ids.claim_id,
            "run_trace_id": normalized.ids.run_trace_id,
            "spec_path": normalized.description.authoritative_spec_path,
            "landing_commit": landing_sha,
            "report_path": str(outcome.report_path),
            "summary_path": str(outcome.summary_path),
        }
        closeout_path = run_store.write_report("queue-closeout.json", closeout_payload)
        verification_lines = [
            f"`{command['name']}` -> exit `{command['exit_code']}`"
            for command in outcome.report.commands_run
        ] or ["No deterministic commands recorded."]
        self.linear_client.create_comment(
            issue.id,
            _render_completion_comment(
                ids=normalized.ids,
                landing_sha=landing_sha,
                verification_lines=verification_lines,
                artifact_paths=(closeout_path, outcome.report_path, outcome.summary_path),
            ),
        )
        self.linear_client.transition_issue(issue.id, "AI Audit")
        if self.cleanup_success_worktree:
            try:
                WorktreeManager(self.repo_root).remove_builder_worktree(outcome.workspace)
            except Exception:
                pass

    def _block_issue(
        self,
        issue: LinearIssue,
        ids: QueueRunIds,
        *,
        outcome: "RunExecutionOutcome" | None = None,
        error: Exception | None = None,
    ) -> None:
        if outcome is not None:
            artifact_path = RunStore(self.repo_root, ids.run_id).write_report(
                "queue-blocker.json",
                {
                    "issue_id": issue.identifier,
                    "run_id": ids.run_id,
                    "claim_id": ids.claim_id,
                    "run_trace_id": ids.run_trace_id,
                    "reason": outcome.snapshot.terminal_reason or "Queue run blocked.",
                    "report_path": str(outcome.report_path),
                    "summary_path": str(outcome.summary_path),
                },
            )
            reason = outcome.snapshot.terminal_reason or "Queue run blocked."
        else:
            artifact_path = self._write_pre_run_blocker(ids, issue, str(error) if error else "Queue run blocked.")
            reason = str(error) if error else "Queue run blocked."
        self.linear_client.create_comment(
            issue.id,
            _render_blocker_comment(ids, reason, artifact_path),
        )
        self.linear_client.transition_issue(issue.id, "Blocked")

    def _write_pre_run_blocker(self, ids: QueueRunIds, issue: LinearIssue, reason: str) -> Path:
        blocker_root = self.repo_root / ".autoclaw" / "queue-blockers"
        blocker_root.mkdir(parents=True, exist_ok=True)
        path = blocker_root / f"{ids.run_id}.json"
        path.write_text(
            json.dumps(
                {
                    "issue_id": issue.identifier,
                    "run_id": ids.run_id,
                    "claim_id": ids.claim_id,
                    "run_trace_id": ids.run_trace_id,
                    "reason": reason,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return path


def parse_issue_description(description: str) -> LinearIssueDescription:
    spec_path = _required_field(description, "Authoritative spec path")
    execution_lane = _required_field(description, "Execution lane")
    execution_mode = _required_field(description, "Execution mode")
    risk_level = _required_field(description, "Risk level")
    approval_required = _parse_bool(_required_field(description, "Approval required"))
    allowed_paths = _split_csv_field(_optional_field(description, "Allowed paths"))
    forbidden_paths = _split_csv_field(_optional_field(description, "Forbidden paths"))
    verification_pack = _split_csv_field(_optional_field(description, "Verification pack"))
    retry_budget_raw = _optional_field(description, "Retry budget")
    retry_budget = int(retry_budget_raw) if retry_budget_raw else None
    return LinearIssueDescription(
        authoritative_spec_path=spec_path,
        execution_lane=execution_lane,
        execution_mode=execution_mode,
        risk_level=risk_level,
        approval_required=approval_required,
        allowed_paths=allowed_paths,
        forbidden_paths=forbidden_paths,
        verification_pack=verification_pack,
        retry_budget=retry_budget,
    )


def build_queue_run_ids(issue_identifier: str) -> QueueRunIds:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    suffix = uuid4().hex[:8]
    return QueueRunIds(
        run_id=f"{issue_identifier}-{stamp}-{suffix}",
        claim_id=f"claim-{issue_identifier.lower()}-{suffix}",
        run_trace_id=f"trace-{issue_identifier.lower()}-{suffix}",
    )


def _required_field(description: str, field_name: str) -> str:
    value = _optional_field(description, field_name)
    if not value:
        raise QueueError(f"Issue description is missing `{field_name}:`.")
    return value


def _optional_field(description: str, field_name: str) -> str | None:
    patterns = (
        rf"(?m)^\*\*{re.escape(field_name)}:\*\*\s*(?P<value>.+?)\s*$",
        rf"(?m)^{re.escape(field_name)}:\s*(?P<value>.+?)\s*$",
    )
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return _clean_value(match.group("value"))
    return None


def _clean_value(value: str) -> str:
    return value.replace("`", "").strip()


def _split_csv_field(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    parts = [_clean_value(part) for part in value.split(",")]
    return tuple(part.rstrip("/") if part not in {".env"} else part for part in parts if part)


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "yes":
        return True
    if normalized == "no":
        return False
    raise QueueError(f"Unsupported queue boolean value `{value}`.")


def _default_verification_pack(repo_contract: RepoContract) -> tuple[str, ...]:
    commands = repo_contract.commands
    pack = tuple(
        name
        for name in ("lint", "typecheck", "test")
        if getattr(commands, name)
    )
    return pack or ("test",)


def _default_retry_budget(risk_level: str) -> int:
    if risk_level == "Medium":
        return 1
    return 2


def _ui_checks_for_pack(repo_contract: RepoContract, verification_pack: tuple[str, ...]) -> tuple[str, ...]:
    if "ui_smoke" not in verification_pack:
        return ()
    if repo_contract.ui.critical_flows:
        return tuple(f"UI smoke passes for {flow.id}" for flow in repo_contract.ui.critical_flows)
    return ("ui smoke passes",)


def _issue_snapshot_hash(issue: LinearIssue) -> str:
    payload = json.dumps(issue.snapshot_payload(), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _staleness_deadline(updated_at: str) -> str:
    updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
    return (updated + timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _render_claim_comment(issue: LinearIssue, ids: QueueRunIds, spec_path: str) -> str:
    return "\n".join(
        [
            "Queue claim started.",
            "",
            f"- Issue: `{issue.identifier}`",
            f"- Run ID: `{ids.run_id}`",
            f"- Claim ID: `{ids.claim_id}`",
            f"- Trace ID: `{ids.run_trace_id}`",
            f"- Authoritative spec path: `{spec_path}`",
        ]
    )


def _render_completion_comment(
    *,
    ids: QueueRunIds,
    landing_sha: str,
    verification_lines: list[str],
    artifact_paths: tuple[Path, ...],
) -> str:
    lines = [
        "Implemented and advanced for `AI Audit`.",
        "",
        f"- Run ID: `{ids.run_id}`",
        f"- Claim ID: `{ids.claim_id}`",
        f"- Trace ID: `{ids.run_trace_id}`",
        "",
        "Landings:",
        f"- `{landing_sha}`",
        "",
        "Verification:",
    ]
    lines.extend(f"- {line}" for line in verification_lines)
    lines.extend(["", "Artifacts:"])
    lines.extend(f"- `{path}`" for path in artifact_paths)
    return "\n".join(lines)


def _render_blocker_comment(ids: QueueRunIds, reason: str, artifact_path: Path) -> str:
    return "\n".join(
        [
            "Blocker:",
            f"- Run ID: `{ids.run_id}`",
            f"- Claim ID: `{ids.claim_id}`",
            f"- Trace ID: `{ids.run_trace_id}`",
            f"- Reason: {reason}",
            f"- Artifact: `{artifact_path}`",
        ]
    )


def _land_successful_run(repo_root: Path, workspace: Any, issue_identifier: str) -> str:
    status = _git(workspace.worktree_path, "status", "--porcelain", "--untracked-files=all")
    add_args = ["add", "-A"]
    _git(workspace.worktree_path, *add_args)
    commit_args = ["commit", "--allow-empty", "-m", f"chore(queue): land {issue_identifier}"]
    if status.stdout.strip():
        _git(workspace.worktree_path, *commit_args)
    else:
        _git(workspace.worktree_path, *commit_args)
    landing_sha = _git(workspace.worktree_path, "rev-parse", "HEAD").stdout.strip()
    merge = _git(repo_root, "merge", "--ff-only", workspace.branch_name)
    if merge.returncode != 0:
        raise QueueError(f"Failed to fast-forward merge `{workspace.branch_name}` into `{repo_root}`.")
    return landing_sha


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or completed.stdout.strip()
        raise QueueError(f"`git {' '.join(args)}` failed in `{repo_root}`: {stderr}")
    return completed

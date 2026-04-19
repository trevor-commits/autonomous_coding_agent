from __future__ import annotations

import argparse
import json
import os
import shlex
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from supervisor.actions import Action
from supervisor.app_supervisor import AppLaunchSummary, AppSupervisor
from supervisor.builder_adapter import BuilderAdapter, BuilderResult, CodexBuilderAdapter, build_builder_prompt
from supervisor.contracts import RepoContract, RunContract, load_repo_contract, load_run_contract
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.models import ActionType, Phase, ReadinessVerdict, RunSnapshot, RunState
from supervisor.queue_intake import LinearGraphQLClient, ManualQueueRunner
from supervisor.policy import (
    PolicyViolationError,
    ShellClass,
    classify_command,
    classify_path_change,
    enforce_budget,
    enforce_scope,
)
from supervisor.reports import ReadinessReport, build_readiness_report, write_readiness_reports
from supervisor.run_store import RunStore
from supervisor.strategy_claude import ClaudeStrategy
from supervisor.state_machine import StateMachine
from supervisor.strategy_simple import SimpleStrategy
from supervisor.ui_verifier import UIVerificationSummary, UIVerifier
from supervisor.verifier import VerificationMode, VerificationSummary, Verifier
from supervisor.worktree_manager import BuilderWorkspace, WorktreeManager


@dataclass(frozen=True)
class RunExecutionOutcome:
    snapshot: RunSnapshot
    report: ReadinessReport
    report_path: Path
    summary_path: Path
    workspace: BuilderWorkspace
    builder_turns: int


class RuntimeStrategy(Protocol):
    def build_action(
        self,
        run_contract: RunContract,
        repo_contract: RepoContract,
        *,
        prior_failure_fingerprints: tuple[str, ...],
    ): ...

    def app_launch_repair_action(
        self,
        run_contract: RunContract,
        *,
        failure_reason: str,
        failure_fingerprint: str | None,
    ): ...

    def ui_repair_action(
        self,
        run_contract: RunContract,
        *,
        defect_packets,
    ): ...

    def blocking_action_for_failure(
        self,
        summary: VerificationSummary,
        *,
        attempt: int,
        max_repair_loops: int,
    ): ...

    def candidate_review_action(
        self,
        run_contract: RunContract,
        repo_contract: RepoContract,
        *,
        changed_files: tuple[str, ...],
        artifact_manifest: tuple[str, ...],
        command_results: tuple,
    ): ...

    def final_audit_action(
        self,
        run_contract: RunContract,
        repo_contract: RepoContract,
        *,
        changed_files: tuple[str, ...],
        artifact_manifest: tuple[str, ...],
        command_results: tuple,
        failure_fingerprints: tuple[str, ...],
    ): ...

    def consume_pending_cost(self) -> float: ...


def execute_run(
    *,
    repo_root: Path | str,
    run_contract_path: Path | str,
    builder_adapter: BuilderAdapter,
    strategy: RuntimeStrategy,
    app_supervisor: AppSupervisor | None = None,
    ui_verifier: UIVerifier | None = None,
    cleanup_worktree: bool = False,
    builder_timeout_seconds: int = 300,
) -> RunExecutionOutcome:
    repo_root = Path(repo_root).resolve()
    run_contract = load_run_contract(run_contract_path)
    machine = StateMachine(run_contract.run_id)
    machine.transition_to(Phase.PREPARE_WORKSPACE, "Run contract loaded; preparing workspace.")
    run_store = RunStore(repo_root, run_contract.run_id)
    worktree_manager = WorktreeManager(repo_root)
    workspace = worktree_manager.create_builder_worktree(
        run_id=run_contract.run_id,
        task_slug=run_contract.objective,
    )
    repo_contract = load_repo_contract(workspace.worktree_path)
    run_store.initialize(
        repo_contract=repo_contract,
        run_contract=run_contract,
        initial_state=machine.snapshot,
    )

    session = builder_adapter.start_session(
        workspace.worktree_path,
        _build_run_context(run_contract, repo_contract),
    )
    fingerprint_store = FailureFingerprintStore(run_store)
    verifier = Verifier(
        repo_root=workspace.worktree_path,
        repo_contract=repo_contract,
        run_contract=run_contract,
        run_store=run_store,
        run_trace_id=run_contract.queue.run_trace_id or run_contract.run_id,
        fingerprint_store=fingerprint_store,
    )
    app_supervisor = app_supervisor or AppSupervisor(
        repo_root=workspace.worktree_path,
        repo_contract=repo_contract,
        run_contract=run_contract,
        run_store=run_store,
        run_trace_id=run_contract.queue.run_trace_id or run_contract.run_id,
        fingerprint_store=fingerprint_store,
    )
    ui_verifier = ui_verifier or UIVerifier(
        repo_root=workspace.worktree_path,
        repo_contract=repo_contract,
        run_contract=run_contract,
        run_store=run_store,
        run_trace_id=run_contract.queue.run_trace_id or run_contract.run_id,
        fingerprint_store=fingerprint_store,
    )

    local_verify_attempt = 0
    app_launch_attempt = 0
    ui_verify_attempt = 0
    prior_failures: tuple[str, ...] = ()
    last_summary: VerificationSummary | None = None
    last_changed_files: tuple[str, ...] = ()
    cumulative_changed_files: set[str] = set()
    command_history = []
    artifact_manifest: set[str] = set()
    unresolved_blockers: tuple[str, ...] = ()
    queue_exit_reason: str | None = None
    pending_build_description: str | None = None
    active_app_session = None
    run_started_at = datetime.now(timezone.utc)
    total_cost_spent = 0.0
    all_failure_fingerprints: set[str] = set()
    wall_clock_started = time.monotonic()

    try:
        _validate_repo_root_matches_contract(repo_root, run_contract)
        while True:
            enforce_budget(
                run_contract,
                iterations_used=session.turn_count + 1,
                cost_spent=total_cost_spent,
                started_at=run_started_at,
            )
            if machine.snapshot.phase is not Phase.BUILD:
                machine.transition_to(Phase.BUILD, "Dispatching builder turn.")
                run_store.write_state(machine.snapshot)

            if pending_build_description:
                build_description = pending_build_description
                pending_build_description = None
            else:
                build_description = strategy.build_action(
                    run_contract,
                    repo_contract,
                    prior_failure_fingerprints=prior_failures,
                ).payload["description"]
                total_cost_spent += strategy.consume_pending_cost()
            prompt = build_builder_prompt(
                session.run_context,
                build_description,
                prior_failure_fingerprints=prior_failures,
            )
            builder_result = builder_adapter.send_task(session, prompt, timeout=builder_timeout_seconds)
            last_changed_files = builder_result.files_changed
            cumulative_changed_files.update(builder_result.files_changed)

            if builder_result.status != "completed":
                raise PolicyViolationError(
                    f"Builder session ended with status `{builder_result.status}`."
                )
            _enforce_builder_policies(
                workspace.worktree_path,
                run_contract,
                repo_contract,
                builder_result,
            )

            machine.transition_to(
                Phase.LOCAL_VERIFY,
                "Builder turn completed; running deterministic verification.",
            )
            run_store.write_state(machine.snapshot)
            last_summary = verifier.run(
                mode=_verification_mode_for(builder_result),
                changed_files=builder_result.files_changed,
            )
            all_failure_fingerprints.update(last_summary.failures)
            command_history.extend(last_summary.commands)
            artifact_manifest.update(_verification_artifact_manifest(last_summary))
            artifact_manifest.add("reports/failure-fingerprints.json")

            if last_summary.all_passed:
                if repo_contract.commands.ui_smoke:
                    launch = _launch_app_for_ui_phase(
                        machine=machine,
                        run_store=run_store,
                        app_supervisor=app_supervisor,
                    )
                    command_history.extend(launch.command_results)
                    artifact_manifest.update(launch.artifact_manifest)
                    if not launch.healthy:
                        app_launch_attempt += 1
                        launch_failures = tuple(
                            fingerprint
                            for fingerprint in (launch.failure_fingerprint,)
                            if fingerprint
                        )
                        all_failure_fingerprints.update(launch_failures)
                        if app_launch_attempt >= run_contract.constraints.max_repair_loops:
                            reason = launch.failure_reason or "app launch failed"
                            machine.block(reason, readiness_verdict=ReadinessVerdict.NOT_READY)
                            queue_exit_reason = "blocked by app launch failure"
                            unresolved_blockers = (reason,)
                            break
                        prior_failures = launch_failures
                        pending_build_description = strategy.app_launch_repair_action(
                            run_contract,
                            failure_reason=launch.failure_reason or "App health failed.",
                            failure_fingerprint=launch.failure_fingerprint,
                        ).payload["description"]
                        total_cost_spent += strategy.consume_pending_cost()
                        machine.transition_to(
                            Phase.BUILD,
                            "App health failed; routing back to builder.",
                        )
                        run_store.write_state(machine.snapshot)
                        continue

                    active_app_session = launch.session
                    machine.transition_to(Phase.UI_VERIFY, "App is healthy; running UI smoke suite.")
                    run_store.write_state(machine.snapshot)
                    ui_summary = ui_verifier.run(changed_files=builder_result.files_changed)
                    command_history.extend(ui_summary.command_results)
                    artifact_manifest.update(ui_summary.artifact_manifest)
                    ui_failure_fingerprints = _ui_failure_fingerprints(ui_summary)
                    all_failure_fingerprints.update(ui_failure_fingerprints)

                    if ui_summary.passed:
                        if active_app_session is not None:
                            app_supervisor.stop(active_app_session)
                            active_app_session = None
                        review_outcome = _run_review_and_final_gate(
                            machine=machine,
                            run_store=run_store,
                            strategy=strategy,
                            run_contract=run_contract,
                            repo_contract=repo_contract,
                            changed_files=tuple(sorted(cumulative_changed_files or set(last_changed_files))),
                            artifact_manifest=tuple(sorted(artifact_manifest)),
                            command_history=tuple(command_history),
                            failure_fingerprints=(),
                            success_reason="UI verification passed.",
                        )
                        total_cost_spent += strategy.consume_pending_cost()
                        if review_outcome.pending_build_description:
                            pending_build_description = review_outcome.pending_build_description
                            queue_exit_reason = None
                            unresolved_blockers = ()
                            continue
                        if review_outcome.terminal:
                            queue_exit_reason = review_outcome.queue_exit_reason
                            unresolved_blockers = review_outcome.unresolved_blockers
                            break

                    if active_app_session is not None:
                        app_supervisor.stop(active_app_session)
                        active_app_session = None

                    ui_verify_attempt += 1
                    if ui_verify_attempt >= run_contract.constraints.max_repair_loops:
                        reason = _ui_failure_reason(ui_summary)
                        machine.block(reason, readiness_verdict=ReadinessVerdict.NOT_READY)
                        queue_exit_reason = "blocked by ui verification failure"
                        unresolved_blockers = tuple(
                            defect["summary"] for defect in ui_summary.defect_packets
                        ) or (reason,)
                        break

                    prior_failures = ui_failure_fingerprints
                    pending_build_description = strategy.ui_repair_action(
                        run_contract,
                        defect_packets=ui_summary.defect_packets,
                    ).payload["description"]
                    total_cost_spent += strategy.consume_pending_cost()
                    machine.transition_to(
                        Phase.BUILD,
                        "UI verification failed; routing defect packets back to builder.",
                    )
                    run_store.write_state(machine.snapshot)
                    continue

                review_outcome = _run_review_and_final_gate(
                    machine=machine,
                    run_store=run_store,
                    strategy=strategy,
                    run_contract=run_contract,
                    repo_contract=repo_contract,
                    changed_files=tuple(sorted(cumulative_changed_files or set(last_changed_files))),
                    artifact_manifest=tuple(sorted(artifact_manifest)),
                    command_history=tuple(command_history),
                    failure_fingerprints=(),
                    success_reason="Deterministic verification passed.",
                )
                total_cost_spent += strategy.consume_pending_cost()
                if review_outcome.pending_build_description:
                    pending_build_description = review_outcome.pending_build_description
                    queue_exit_reason = None
                    unresolved_blockers = ()
                    continue
                if review_outcome.terminal:
                    queue_exit_reason = review_outcome.queue_exit_reason
                    unresolved_blockers = review_outcome.unresolved_blockers
                    break

            local_verify_attempt += 1
            repeated = tuple(
                fingerprint
                for fingerprint in last_summary.failures
                if fingerprint_store.has_repeat(
                    fingerprint,
                    threshold=run_contract.constraints.max_repair_loops,
                )
            )
            if repeated:
                reason = (
                    "Repeated failure fingerprint threshold reached: "
                    + ", ".join(repeated)
                    + "."
                )
                machine.block(reason, readiness_verdict=ReadinessVerdict.NOT_READY)
                queue_exit_reason = "blocked by repeated failure fingerprint"
                unresolved_blockers = (reason,)
                break

            terminal_action = strategy.blocking_action_for_failure(
                last_summary,
                attempt=local_verify_attempt,
                max_repair_loops=run_contract.constraints.max_repair_loops,
            )
            if terminal_action:
                reason = terminal_action.payload["reason"]
                machine.block(reason, readiness_verdict=ReadinessVerdict.NOT_READY)
                queue_exit_reason = "blocked by retry budget exhaustion"
                unresolved_blockers = (reason,)
                break

            prior_failures = last_summary.failures
            machine.transition_to(Phase.BUILD, "Verification failed; routing back to builder.")
            run_store.write_state(machine.snapshot)

    except PolicyViolationError as exc:
        machine.block(str(exc), readiness_verdict=ReadinessVerdict.NOT_READY)
        queue_exit_reason = "blocked by policy gate"
        unresolved_blockers = (str(exc),)
    finally:
        if active_app_session is not None:
            app_supervisor.stop(active_app_session)
        run_store.write_state(machine.snapshot)
        artifact_manifest.update({"reports/final-report.json", "reports/final-summary.md"})
        report = build_readiness_report(
            snapshot=machine.snapshot,
            run_contract=run_contract,
            command_results=tuple(command_history),
            strategy_name=_strategy_name(strategy),
            builder_turns=session.turn_count,
            run_duration_seconds=round(time.monotonic() - wall_clock_started, 3),
            total_cost_dollars=round(total_cost_spent, 6),
            changed_files=tuple(sorted(cumulative_changed_files or set(last_changed_files))),
            artifact_manifest=tuple(sorted(artifact_manifest)),
            unresolved_blockers=unresolved_blockers,
            queue_exit_reason=queue_exit_reason,
            failure_fingerprints=tuple(sorted(all_failure_fingerprints)),
        )
        report_path, summary_path = write_readiness_reports(run_store, report)
        builder_adapter.close_session(session)
        if cleanup_worktree:
            worktree_manager.remove_builder_worktree(workspace)

    return RunExecutionOutcome(
        snapshot=machine.snapshot,
        report=report,
        report_path=report_path,
        summary_path=summary_path,
        workspace=workspace,
        builder_turns=session.turn_count,
    )


def _build_run_context(run_contract: RunContract, repo_contract: RepoContract) -> dict[str, object]:
    commands = {
        name: getattr(repo_contract.commands, name)
        for name in ("setup", "format", "lint", "typecheck", "test")
        if getattr(repo_contract.commands, name)
    }
    return {
        "objective": run_contract.objective,
        "allowed_paths": run_contract.scope.allowed_paths,
        "forbidden_paths": run_contract.scope.forbidden_paths,
        "repo_commands": commands,
    }


def _strategy_name(strategy: RuntimeStrategy) -> str:
    if isinstance(strategy, ClaudeStrategy):
        return "claude"
    if isinstance(strategy, SimpleStrategy):
        return "simple"
    return type(strategy).__name__.replace("Strategy", "").lower() or "unknown"


def _verification_mode_for(builder_result: BuilderResult) -> VerificationMode:
    if builder_result.files_changed:
        return VerificationMode.TARGETED
    return VerificationMode.FULL


def _verification_artifact_manifest(summary: VerificationSummary) -> set[str]:
    artifacts: set[str] = set()
    for result in summary.commands:
        artifacts.add(f"artifacts/logs/{result.name}.stdout.log")
        artifacts.add(f"artifacts/logs/{result.name}.stderr.log")
    return artifacts


def _ui_failure_fingerprints(summary: UIVerificationSummary) -> tuple[str, ...]:
    fingerprints = [
        str(defect.get("failure_fingerprint"))
        for defect in summary.defect_packets
        if defect.get("failure_fingerprint")
    ]
    if not fingerprints:
        fingerprints = [
            result.failure_fingerprint
            for result in summary.command_results
            if result.failure_fingerprint
        ]
    return tuple(dict.fromkeys(fingerprints))


def _validate_repo_root_matches_contract(repo_root: Path, run_contract: RunContract) -> None:
    contract_repo_root = Path(run_contract.repo_path).resolve()
    if contract_repo_root != repo_root:
        raise PolicyViolationError(
            "Resolved repo root "
            f"`{repo_root}` does not match run contract repo_path `{contract_repo_root}`."
        )


def _launch_app_for_ui_phase(
    *,
    machine: StateMachine,
    run_store: RunStore,
    app_supervisor: AppSupervisor,
) -> AppLaunchSummary:
    machine.transition_to(Phase.APP_LAUNCH, "Deterministic verification passed; launching app.")
    run_store.write_state(machine.snapshot)
    return app_supervisor.launch()


def _ui_failure_reason(summary: UIVerificationSummary) -> str:
    if summary.defect_packets:
        return "; ".join(str(defect.get("summary", "UI smoke suite failed")) for defect in summary.defect_packets)
    result = summary.command_results[-1]
    return result.stderr.strip() or result.stdout.strip() or "UI smoke suite failed."


@dataclass(frozen=True)
class ReviewOutcome:
    terminal: bool
    queue_exit_reason: str | None = None
    unresolved_blockers: tuple[str, ...] = ()
    pending_build_description: str | None = None


def _run_review_and_final_gate(
    *,
    machine: StateMachine,
    run_store: RunStore,
    strategy: RuntimeStrategy,
    run_contract: RunContract,
    repo_contract: RepoContract,
    changed_files: tuple[str, ...],
    artifact_manifest: tuple[str, ...],
    command_history: tuple[CommandExecutionResult, ...],
    failure_fingerprints: tuple[str, ...],
    success_reason: str,
) -> ReviewOutcome:
    machine.transition_to(Phase.AUDIT_READY, "Green candidate ready for review.")
    run_store.write_state(machine.snapshot)
    candidate_action = strategy.candidate_review_action(
        run_contract,
        repo_contract,
        changed_files=changed_files,
        artifact_manifest=artifact_manifest,
        command_results=command_history,
    )
    review_outcome = _apply_review_action(machine, candidate_action)
    if review_outcome.pending_build_description or review_outcome.terminal:
        if review_outcome.pending_build_description:
            run_store.write_state(machine.snapshot)
        return review_outcome

    machine.transition_to(Phase.FINAL_GATE, "Candidate review accepted the green candidate.")
    run_store.write_state(machine.snapshot)
    machine.record_final_gate_evidence(
        required_artifacts_present=True,
        authoritative_checks_passed=True,
        unresolved_high_severity_findings=bool(failure_fingerprints),
    )
    final_action = strategy.final_audit_action(
        run_contract,
        repo_contract,
        changed_files=changed_files,
        artifact_manifest=artifact_manifest,
        command_results=command_history,
        failure_fingerprints=failure_fingerprints,
    )
    return _apply_final_gate_action(machine, final_action, default_success_reason=success_reason)


def _apply_review_action(machine: StateMachine, action: Action) -> ReviewOutcome:
    if action.action_type is ActionType.REQUEST_BUILDER_TASK:
        machine.transition_to(Phase.BUILD, "Candidate review requested another builder turn.")
        return ReviewOutcome(
            terminal=False,
            pending_build_description=action.payload["description"],
        )
    if action.action_type is ActionType.PROPOSE_TERMINAL_STATE:
        return _terminal_outcome_from_action(machine, action)
    return ReviewOutcome(terminal=False)


def _apply_final_gate_action(
    machine: StateMachine,
    action: Action,
    *,
    default_success_reason: str,
) -> ReviewOutcome:
    if action.action_type is ActionType.REQUEST_BUILDER_TASK:
        machine.apply_final_gate_outcome(
            ReadinessVerdict.NEEDS_MORE_EVIDENCE,
            action.payload["description"],
        )
        return ReviewOutcome(
            terminal=False,
            pending_build_description=action.payload["description"],
        )
    if action.action_type is ActionType.PROPOSE_TERMINAL_STATE:
        payload = action.payload
        proposed_state = RunState(str(payload["run_state"]))
        if proposed_state is RunState.COMPLETE:
            machine.apply_final_gate_outcome(
                ReadinessVerdict(str(payload.get("readiness_verdict", ReadinessVerdict.READY.value))),
                str(payload.get("reason", default_success_reason)),
            )
            return ReviewOutcome(
                terminal=True,
                queue_exit_reason="final audit passed",
                unresolved_blockers=(),
            )
        return _terminal_outcome_from_action(machine, action)

    reason = str(action.payload.get("reason", "Final audit requested more evidence."))
    machine.apply_final_gate_outcome(ReadinessVerdict.NEEDS_MORE_EVIDENCE, reason)
    return ReviewOutcome(
        terminal=False,
        pending_build_description=reason,
    )


def _terminal_outcome_from_action(machine: StateMachine, action: Action) -> ReviewOutcome:
    payload = action.payload
    proposed_state = RunState(str(payload["run_state"]))
    reason = str(payload.get("reason", "Strategy proposed a terminal state."))
    if proposed_state is RunState.BLOCKED:
        machine.block(
            reason,
            readiness_verdict=_optional_readiness_verdict(payload.get("readiness_verdict")),
        )
        return ReviewOutcome(
            terminal=True,
            queue_exit_reason="blocked by strategy review",
            unresolved_blockers=(reason,),
        )
    if proposed_state is RunState.UNSUPPORTED:
        machine.mark_unsupported(reason)
        return ReviewOutcome(
            terminal=True,
            queue_exit_reason="unsupported by strategy review",
            unresolved_blockers=(reason,),
        )
    raise PolicyViolationError(f"Unexpected non-terminal strategy proposal `{proposed_state.value}`.")


def _optional_readiness_verdict(value: object) -> ReadinessVerdict | None:
    if value is None:
        return None
    return ReadinessVerdict(str(value))


def _enforce_builder_policies(
    repo_root: Path,
    run_contract: RunContract,
    repo_contract: RepoContract,
    builder_result: BuilderResult,
) -> None:
    for command in builder_result.commands_run:
        normalized = _normalize_builder_command(command)
        decision = classify_command(normalized, repo_contract)
        if decision.shell_class is not ShellClass.AUTO_ALLOW:
            raise PolicyViolationError(
                f"Builder command `{normalized}` is not allowed in Phase 2: {decision.reason}."
            )
    for relative_path in builder_result.files_changed:
        enforce_scope(repo_root, run_contract, repo_root / relative_path)
        decision = classify_path_change(relative_path)
        if decision.shell_class is not ShellClass.AUTO_ALLOW:
            raise PolicyViolationError(
                f"Builder path `{relative_path}` is not allowed in Phase 2: {decision.reason}."
            )


def _normalize_builder_command(command: str) -> str:
    tokens = shlex.split(command)
    if len(tokens) >= 3 and tokens[1] == "-lc":
        return " ".join(tokens[2:])
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the supervisor loop or manual queue drain.")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--run-contract")
    parser.add_argument("--queue-drain", action="store_true")
    parser.add_argument("--team-key")
    parser.add_argument("--linear-token-env", default="LINEAR_API_TOKEN")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--strategy", default="simple", choices=("simple", "claude"))
    parser.add_argument("--cleanup-worktree", action="store_true")
    args = parser.parse_args()
    strategy = _build_strategy(args.strategy)

    if args.queue_drain:
        if not args.team_key:
            raise SystemExit("`--team-key` is required with `--queue-drain`.")
        token = os.environ.get(args.linear_token_env)
        if not token:
            raise SystemExit(
                f"Set `{args.linear_token_env}` before running manual queue drain mode."
            )
        summary = ManualQueueRunner(
            repo_root=Path(args.repo_path),
            linear_client=LinearGraphQLClient(token=token),
            builder_adapter=CodexBuilderAdapter(),
            strategy=strategy,
            team_key=args.team_key,
            cleanup_success_worktree=args.cleanup_worktree,
        ).drain(limit=args.limit)
        print(
            json.dumps(
                {
                    "processed_count": summary.processed_count,
                    "completed_count": summary.completed_count,
                    "blocked_count": summary.blocked_count,
                }
            )
        )
        return 0

    if not args.run_contract:
        raise SystemExit("`--run-contract` is required unless `--queue-drain` is set.")

    outcome = execute_run(
        repo_root=Path(args.repo_path),
        run_contract_path=Path(args.run_contract),
        builder_adapter=CodexBuilderAdapter(),
        strategy=strategy,
        cleanup_worktree=args.cleanup_worktree,
    )
    print(
        json.dumps(
            {
                "run_id": outcome.report.run_id,
                "run_state": outcome.snapshot.run_state.value,
                "report_path": str(outcome.report_path),
                "summary_path": str(outcome.summary_path),
            }
        )
    )
def _build_strategy(name: str) -> RuntimeStrategy:
    if name == "claude":
        return ClaudeStrategy()
    return SimpleStrategy()


if __name__ == "__main__":
    raise SystemExit(main())

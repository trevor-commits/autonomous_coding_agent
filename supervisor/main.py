from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import dataclass
from pathlib import Path

from supervisor.app_supervisor import AppLaunchSummary, AppSupervisor
from supervisor.builder_adapter import BuilderAdapter, BuilderResult, CodexBuilderAdapter, build_builder_prompt
from supervisor.contracts import RepoContract, RunContract, load_repo_contract, load_run_contract
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.models import Phase, ReadinessVerdict, RunSnapshot
from supervisor.policy import (
    PolicyViolationError,
    ShellClass,
    classify_command,
    classify_path_change,
    enforce_scope,
)
from supervisor.reports import ReadinessReport, build_readiness_report, write_readiness_reports
from supervisor.run_store import RunStore
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


def execute_run(
    *,
    repo_root: Path | str,
    run_contract_path: Path | str,
    builder_adapter: BuilderAdapter,
    strategy: SimpleStrategy,
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

    try:
        while True:
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
                        if app_launch_attempt >= run_contract.constraints.max_repair_loops:
                            reason = launch.failure_reason or "app launch failed"
                            machine.block(reason, readiness_verdict=ReadinessVerdict.NOT_READY)
                            queue_exit_reason = "blocked by app launch failure"
                            unresolved_blockers = (reason,)
                            break
                        prior_failures = tuple(
                            fingerprint
                            for fingerprint in (launch.failure_fingerprint,)
                            if fingerprint
                        )
                        pending_build_description = strategy.app_launch_repair_action(
                            run_contract,
                            failure_reason=launch.failure_reason or "App health failed.",
                            failure_fingerprint=launch.failure_fingerprint,
                        ).payload["description"]
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

                    if ui_summary.passed:
                        machine.transition_to(Phase.FINAL_GATE, "UI verification passed.")
                        machine.record_final_gate_evidence(
                            required_artifacts_present=True,
                            authoritative_checks_passed=True,
                            unresolved_high_severity_findings=False,
                        )
                        machine.apply_final_gate_outcome(
                            ReadinessVerdict.READY,
                            "UI verification passed.",
                        )
                        queue_exit_reason = "ui verification passed"
                        unresolved_blockers = ()
                        if active_app_session is not None:
                            app_supervisor.stop(active_app_session)
                            active_app_session = None
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

                    prior_failures = tuple(
                        result.failure_fingerprint
                        for result in ui_summary.command_results
                        if result.failure_fingerprint
                    )
                    pending_build_description = strategy.ui_repair_action(
                        run_contract,
                        defect_packets=ui_summary.defect_packets,
                    ).payload["description"]
                    machine.transition_to(
                        Phase.BUILD,
                        "UI verification failed; routing defect packets back to builder.",
                    )
                    run_store.write_state(machine.snapshot)
                    continue

                machine.transition_to(Phase.FINAL_GATE, "Deterministic verification passed.")
                machine.record_final_gate_evidence(
                    required_artifacts_present=True,
                    authoritative_checks_passed=True,
                    unresolved_high_severity_findings=False,
                )
                machine.apply_final_gate_outcome(
                    ReadinessVerdict.READY,
                    "Deterministic verification passed.",
                )
                queue_exit_reason = "deterministic verification passed"
                unresolved_blockers = ()
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
            changed_files=tuple(sorted(cumulative_changed_files or set(last_changed_files))),
            artifact_manifest=tuple(sorted(artifact_manifest)),
            unresolved_blockers=unresolved_blockers,
            queue_exit_reason=queue_exit_reason,
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
    parser = argparse.ArgumentParser(description="Run the Phase 2 supervisor loop.")
    parser.add_argument("--repo-path", required=True)
    parser.add_argument("--run-contract", required=True)
    parser.add_argument("--strategy", default="simple", choices=("simple",))
    parser.add_argument("--cleanup-worktree", action="store_true")
    args = parser.parse_args()

    if args.strategy != "simple":
        raise SystemExit("Only `simple` strategy is implemented in the smallest Phase 2.")

    outcome = execute_run(
        repo_root=Path(args.repo_path),
        run_contract_path=Path(args.run_contract),
        builder_adapter=CodexBuilderAdapter(),
        strategy=SimpleStrategy(),
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

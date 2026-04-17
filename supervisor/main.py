from __future__ import annotations

import argparse
import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path

from supervisor.builder_adapter import BuilderAdapter, BuilderResult, CodexBuilderAdapter, build_builder_prompt
from supervisor.contracts import RepoContract, RunContract, load_repo_contract, load_run_contract
from supervisor.fingerprints import FailureFingerprintStore
from supervisor.models import Phase, ReadinessVerdict, RunSnapshot
from supervisor.queue_intake import LinearGraphQLClient, ManualQueueRunner
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

    attempt = 0
    prior_failures: tuple[str, ...] = ()
    last_summary: VerificationSummary | None = None
    last_changed_files: tuple[str, ...] = ()
    artifact_manifest: set[str] = set()
    unresolved_blockers: tuple[str, ...] = ()
    queue_exit_reason: str | None = None

    try:
        while True:
            if machine.snapshot.phase is not Phase.BUILD:
                machine.transition_to(Phase.BUILD, "Dispatching builder turn.")
                run_store.write_state(machine.snapshot)

            build_action = strategy.build_action(
                run_contract,
                repo_contract,
                prior_failure_fingerprints=prior_failures,
            )
            prompt = build_builder_prompt(
                session.run_context,
                build_action.payload["description"],
                prior_failure_fingerprints=prior_failures,
            )
            builder_result = builder_adapter.send_task(session, prompt, timeout=builder_timeout_seconds)
            last_changed_files = builder_result.files_changed

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
            artifact_manifest.update(_verification_artifact_manifest(last_summary))
            artifact_manifest.add("reports/failure-fingerprints.json")

            if last_summary.all_passed:
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

            attempt += 1
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
                attempt=attempt,
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
        run_store.write_state(machine.snapshot)
        artifact_manifest.update({"reports/final-report.json", "reports/final-summary.md"})
        report = build_readiness_report(
            snapshot=machine.snapshot,
            run_contract=run_contract,
            command_results=last_summary.commands if last_summary else (),
            changed_files=last_changed_files,
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
    parser.add_argument("--strategy", default="simple", choices=("simple",))
    parser.add_argument("--cleanup-worktree", action="store_true")
    args = parser.parse_args()

    if args.strategy != "simple":
        raise SystemExit("Only `simple` strategy is implemented in the smallest Phase 2.")

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
            strategy=SimpleStrategy(),
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

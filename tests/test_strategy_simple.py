import tempfile
import unittest
from pathlib import Path

from supervisor.contracts import (
    QueueMetadata,
    RepoCommands,
    RepoContract,
    RepoEnvConfig,
    RepoUIConfig,
    RunAcceptance,
    RunConstraints,
    RunContract,
    RunScope,
)
from supervisor.models import ActionType
from supervisor.strategy_simple import SimpleStrategy
from supervisor.verifier import CommandExecutionResult, VerificationMode, VerificationSummary


def _run_contract() -> RunContract:
    return RunContract(
        run_id="run-001",
        repo_path="/tmp/repo",
        objective="Add login validation",
        scope=RunScope(allowed_paths=("src", "tests"), forbidden_paths=(".env",)),
        acceptance=RunAcceptance(
            functional=("login validation works",),
            quality_gates=("tests pass",),
            ui_checks=(),
        ),
        constraints=RunConstraints(
            single_writer=True,
            max_repair_loops=2,
            max_iterations=5,
            max_cost_dollars=5.0,
            hard_timeout_seconds=300,
        ),
        queue=QueueMetadata(run_trace_id="trace-123"),
    )


def _repo_contract() -> RepoContract:
    return RepoContract(
        version=1,
        stack="fullstack-web",
        commands=RepoCommands(
            setup="pnpm install",
            test="pnpm test",
            lint="pnpm lint",
            app_up="pnpm dev",
            app_health="http://127.0.0.1:3000/health",
        ),
        ui=RepoUIConfig(),
        env=RepoEnvConfig(),
    )


class SimpleStrategyTests(unittest.TestCase):
    def test_build_action_uses_run_objective(self) -> None:
        strategy = SimpleStrategy()

        action = strategy.build_action(
            _run_contract(),
            _repo_contract(),
            prior_failure_fingerprints=(),
        )

        self.assertEqual(ActionType.REQUEST_BUILDER_TASK, action.action_type)
        self.assertIn("Add login validation", action.payload["description"])
        self.assertIn("pnpm test", action.payload["description"])

    def test_build_action_includes_prior_failures(self) -> None:
        strategy = SimpleStrategy()

        action = strategy.build_action(
            _run_contract(),
            _repo_contract(),
            prior_failure_fingerprints=("local-verify-test-login-failed",),
        )

        self.assertIn("local-verify-test-login-failed", action.payload["description"])

    def test_terminal_action_is_none_before_retry_budget(self) -> None:
        strategy = SimpleStrategy()
        summary = VerificationSummary(
            run_id="run-001",
            run_trace_id="trace-123",
            mode=VerificationMode.TARGETED,
            commands=(
                CommandExecutionResult(
                    name="test",
                    command="pnpm test",
                    exit_code=1,
                    stdout="",
                    stderr="failed",
                    duration_seconds=1.0,
                    scope="targeted",
                    run_trace_id="trace-123",
                    failure_fingerprint="local-verify-test-login-failed",
                ),
            ),
            changed_files=("src/login.ts",),
        )

        action = strategy.blocking_action_for_failure(summary, attempt=1, max_repair_loops=2)

        self.assertIsNone(action)

    def test_terminal_action_blocks_at_retry_budget(self) -> None:
        strategy = SimpleStrategy()
        summary = VerificationSummary(
            run_id="run-001",
            run_trace_id="trace-123",
            mode=VerificationMode.TARGETED,
            commands=(
                CommandExecutionResult(
                    name="test",
                    command="pnpm test",
                    exit_code=1,
                    stdout="",
                    stderr="failed",
                    duration_seconds=1.0,
                    scope="targeted",
                    run_trace_id="trace-123",
                    failure_fingerprint="local-verify-test-login-failed",
                ),
            ),
            changed_files=("src/login.ts",),
        )

        action = strategy.blocking_action_for_failure(summary, attempt=2, max_repair_loops=2)

        self.assertEqual(ActionType.PROPOSE_TERMINAL_STATE, action.action_type)
        self.assertEqual("BLOCKED", action.payload["run_state"])
        self.assertIn("local-verify-test-login-failed", action.payload["reason"])


if __name__ == "__main__":
    unittest.main()

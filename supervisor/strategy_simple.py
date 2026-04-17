from __future__ import annotations

from typing import Any, Sequence

from supervisor.actions import Action
from supervisor.models import ActionType
from supervisor.contracts import RepoContract, RunContract
from supervisor.verifier import VerificationSummary


class SimpleStrategy:
    """Rule-based strategy for the smallest Phase 2 builder loop."""

    def build_action(
        self,
        run_contract: RunContract,
        repo_contract: RepoContract,
        *,
        prior_failure_fingerprints: tuple[str, ...],
    ) -> Action:
        verification_commands = [
            getattr(repo_contract.commands, name)
            for name in ("format", "lint", "typecheck", "test")
            if getattr(repo_contract.commands, name)
        ]
        verification_hint = ", ".join(verification_commands) or "the repo-contract test command"
        if prior_failure_fingerprints:
            description = (
                f"Repair the objective `{run_contract.objective}` by addressing these deterministic "
                f"verification failures: {', '.join(prior_failure_fingerprints)}. "
                f"Re-run the relevant repo-contract checks ({verification_hint}) "
                "after your changes."
            )
        else:
            description = (
                f"Implement the objective `{run_contract.objective}` and prepare the repo for "
                f"deterministic verification via: {verification_hint}."
            )
        return Action(
            action_type=ActionType.REQUEST_BUILDER_TASK,
            payload={"description": description},
        )

    def app_launch_repair_action(
        self,
        run_contract: RunContract,
        *,
        failure_reason: str,
        failure_fingerprint: str | None,
    ) -> Action:
        detail = failure_fingerprint or "app-launch-failure"
        return Action(
            action_type=ActionType.REQUEST_BUILDER_TASK,
            payload={
                "description": (
                    f"Repair the objective `{run_contract.objective}` so the local app launches "
                    f"and becomes healthy. App launch failure: {failure_reason}. "
                    f"Relevant failure fingerprint: {detail}."
                )
            },
        )

    def ui_repair_action(
        self,
        run_contract: RunContract,
        *,
        defect_packets: Sequence[dict[str, Any]],
    ) -> Action:
        descriptions: list[str] = []
        for defect in defect_packets:
            summary = str(defect.get("summary", "UI defect"))
            suspected_scope = ", ".join(str(path) for path in defect.get("suspected_scope", ())) or "n/a"
            fingerprint = str(defect.get("failure_fingerprint", "n/a"))
            descriptions.append(
                f"{summary} | suspected scope: {suspected_scope} | fingerprint: {fingerprint}"
            )
        joined = "; ".join(descriptions) or "UI smoke suite failed without a structured defect."
        return Action(
            action_type=ActionType.REQUEST_BUILDER_TASK,
            payload={
                "description": (
                    f"Repair the objective `{run_contract.objective}` by resolving these UI "
                    f"defects from the smoke suite: {joined}."
                )
            },
        )

    def blocking_action_for_failure(
        self,
        summary: VerificationSummary,
        *,
        attempt: int,
        max_repair_loops: int,
    ) -> Action | None:
        if attempt < max_repair_loops:
            return None
        reason = (
            f"Retry budget exhausted after {attempt} failed verification attempt(s): "
            f"{', '.join(summary.failures) or 'verification failed without a fingerprint'}."
        )
        return Action(
            action_type=ActionType.PROPOSE_TERMINAL_STATE,
            payload={"run_state": "BLOCKED", "reason": reason},
        )

from __future__ import annotations

from dataclasses import replace

from supervisor.models import FinalGateEvidence, Phase, ReadinessVerdict, RunSnapshot, RunState


LEGAL_PHASE_TRANSITIONS: dict[Phase, frozenset[Phase]] = {
    Phase.INTAKE: frozenset({Phase.PREPARE_WORKSPACE}),
    Phase.PREPARE_WORKSPACE: frozenset({Phase.BUILD}),
    Phase.BUILD: frozenset({Phase.LOCAL_VERIFY}),
    Phase.LOCAL_VERIFY: frozenset({Phase.BUILD, Phase.APP_LAUNCH, Phase.FINAL_GATE}),
    Phase.APP_LAUNCH: frozenset({Phase.BUILD, Phase.UI_VERIFY, Phase.FINAL_GATE}),
    Phase.UI_VERIFY: frozenset({Phase.BUILD, Phase.AUDIT_READY, Phase.FINAL_GATE}),
    Phase.AUDIT_READY: frozenset({Phase.BUILD, Phase.FINAL_GATE}),
    Phase.FINAL_GATE: frozenset({Phase.BUILD}),
}


class PhaseTransitionError(ValueError):
    """Raised when a caller attempts an illegal phase transition."""


class TerminalStateError(ValueError):
    """Raised when a caller mutates a run after it has reached a terminal state."""


class FinalGateInvariantError(ValueError):
    """Raised when FINAL_GATE terminal-state evidence is insufficient."""


def legal_next_phases(phase: Phase) -> frozenset[Phase]:
    return LEGAL_PHASE_TRANSITIONS[phase]


class StateMachine:
    """Deterministic phase machine for the autonomous coding supervisor."""

    def __init__(self, run_id: str, max_evidence_loops: int = 1) -> None:
        self._snapshot = RunSnapshot.initial(
            run_id=run_id,
            max_evidence_loops=max_evidence_loops,
        )

    @property
    def snapshot(self) -> RunSnapshot:
        return self._snapshot

    def transition_to(self, next_phase: Phase, reason: str) -> RunSnapshot:
        self._ensure_in_progress()
        if next_phase not in legal_next_phases(self._snapshot.phase):
            raise PhaseTransitionError(
                f"Illegal phase transition: `{self._snapshot.phase.value}` -> "
                f"`{next_phase.value}`."
            )
        self._snapshot = self._snapshot.with_transition(next_phase, reason)
        return self._snapshot

    def record_final_gate_evidence(
        self,
        *,
        required_artifacts_present: bool,
        authoritative_checks_passed: bool,
        unresolved_high_severity_findings: bool,
    ) -> RunSnapshot:
        self._ensure_in_progress()
        evidence = FinalGateEvidence(
            required_artifacts_present=required_artifacts_present,
            authoritative_checks_passed=authoritative_checks_passed,
            unresolved_high_severity_findings=unresolved_high_severity_findings,
        )
        self._snapshot = replace(self._snapshot, final_gate_evidence=evidence)
        return self._snapshot

    def block(
        self,
        reason: str,
        *,
        readiness_verdict: ReadinessVerdict | None = None,
    ) -> RunSnapshot:
        self._ensure_in_progress()
        self._snapshot = replace(
            self._snapshot,
            run_state=RunState.BLOCKED,
            readiness_verdict=readiness_verdict,
            terminal_reason=reason,
        )
        return self._snapshot

    def mark_unsupported(self, reason: str) -> RunSnapshot:
        self._ensure_in_progress()
        self._snapshot = replace(
            self._snapshot,
            run_state=RunState.UNSUPPORTED,
            terminal_reason=reason,
        )
        return self._snapshot

    def apply_final_gate_outcome(
        self,
        verdict: ReadinessVerdict,
        reason: str,
    ) -> RunSnapshot:
        self._ensure_in_progress()
        if self._snapshot.phase is not Phase.FINAL_GATE:
            raise PhaseTransitionError(
                "`apply_final_gate_outcome` is legal only during `FINAL_GATE`."
            )

        if verdict is ReadinessVerdict.READY:
            self._ensure_complete_is_legal()
            self._snapshot = replace(
                self._snapshot,
                run_state=RunState.COMPLETE,
                readiness_verdict=ReadinessVerdict.READY,
                terminal_reason=reason,
            )
            return self._snapshot

        if verdict is ReadinessVerdict.NOT_READY:
            return self.block(reason, readiness_verdict=ReadinessVerdict.NOT_READY)

        if self._snapshot.evidence_loop_count < self._snapshot.max_evidence_loops:
            in_progress = replace(
                self._snapshot,
                readiness_verdict=ReadinessVerdict.NEEDS_MORE_EVIDENCE,
                evidence_loop_count=self._snapshot.evidence_loop_count + 1,
            )
            self._snapshot = in_progress.with_transition(
                Phase.BUILD,
                f"More evidence required: {reason}",
            )
            return self._snapshot

        return self.block(
            f"Evidence loop budget exhausted: {reason}",
            readiness_verdict=ReadinessVerdict.NOT_READY,
        )

    def _ensure_in_progress(self) -> None:
        if self._snapshot.run_state is not RunState.IN_PROGRESS:
            raise TerminalStateError(
                f"Run `{self._snapshot.run_id}` is already terminal: "
                f"`{self._snapshot.run_state.value}`."
            )

    def _ensure_complete_is_legal(self) -> None:
        evidence = self._snapshot.final_gate_evidence
        missing_reasons: list[str] = []
        if not evidence.required_artifacts_present:
            missing_reasons.append("required artifacts are missing")
        if not evidence.authoritative_checks_passed:
            missing_reasons.append("authoritative final checks did not pass")
        if evidence.unresolved_high_severity_findings:
            missing_reasons.append("high-severity findings remain unresolved")

        if missing_reasons:
            raise FinalGateInvariantError(
                "`run_state = COMPLETE` is illegal because "
                + "; ".join(missing_reasons)
                + "."
            )


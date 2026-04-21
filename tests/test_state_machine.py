import unittest

from supervisor.models import Phase, ReadinessVerdict, RunState
from supervisor.state_machine import (
    FinalGateInvariantError,
    PhaseTransitionError,
    StateMachine,
    TerminalStateError,
)


class StateMachineTests(unittest.TestCase):
    def test_initial_state_starts_in_intake_with_history(self) -> None:
        machine = StateMachine("run-001")

        self.assertEqual(Phase.INTAKE, machine.snapshot.phase)
        self.assertEqual(RunState.IN_PROGRESS, machine.snapshot.run_state)
        self.assertEqual(1, len(machine.snapshot.phase_history))
        self.assertIsNone(machine.snapshot.phase_history[0].from_phase)
        self.assertEqual(Phase.INTAKE, machine.snapshot.phase_history[0].to_phase)

    def test_happy_path_transitions_are_legal(self) -> None:
        machine = StateMachine("run-002")

        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.APP_LAUNCH, "local checks passed")
        machine.transition_to(Phase.UI_VERIFY, "app healthy")
        machine.transition_to(Phase.AUDIT_READY, "ui checks passed")
        machine.transition_to(Phase.FINAL_GATE, "audit complete")

        self.assertEqual(Phase.FINAL_GATE, machine.snapshot.phase)
        self.assertEqual(8, len(machine.snapshot.phase_history))

    def test_backend_only_path_may_skip_ui_phases(self) -> None:
        machine = StateMachine("run-003")

        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.FINAL_GATE, "no ui verification required")

        self.assertEqual(Phase.FINAL_GATE, machine.snapshot.phase)

    def test_backend_only_path_may_pause_in_audit_ready_before_final_gate(self) -> None:
        machine = StateMachine("run-003b")

        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.AUDIT_READY, "backend candidate ready for review")
        machine.transition_to(Phase.FINAL_GATE, "review complete")

        self.assertEqual(Phase.FINAL_GATE, machine.snapshot.phase)

    def test_illegal_transition_is_rejected(self) -> None:
        machine = StateMachine("run-004")
        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")

        with self.assertRaises(PhaseTransitionError):
            machine.transition_to(Phase.UI_VERIFY, "skip deterministic gates")

    def test_complete_requires_final_gate_evidence(self) -> None:
        machine = StateMachine("run-005")
        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.FINAL_GATE, "authoritative rerun")

        with self.assertRaises(FinalGateInvariantError):
            machine.apply_final_gate_outcome(ReadinessVerdict.READY, "missing evidence")

    def test_ready_final_gate_completes_when_evidence_is_clean(self) -> None:
        machine = StateMachine("run-006")
        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.FINAL_GATE, "authoritative rerun")
        machine.record_final_gate_evidence(
            required_artifacts_present=True,
            authoritative_checks_passed=True,
            unresolved_high_severity_findings=False,
        )

        machine.apply_final_gate_outcome(ReadinessVerdict.READY, "all gates passed")

        self.assertEqual(RunState.COMPLETE, machine.snapshot.run_state)
        self.assertEqual(ReadinessVerdict.READY, machine.snapshot.readiness_verdict)

    def test_needs_more_evidence_reenters_build_once(self) -> None:
        machine = StateMachine("run-007", max_evidence_loops=1)
        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.FINAL_GATE, "authoritative rerun")

        machine.apply_final_gate_outcome(
            ReadinessVerdict.NEEDS_MORE_EVIDENCE,
            "need one more deterministic rerun",
        )

        self.assertEqual(Phase.BUILD, machine.snapshot.phase)
        self.assertEqual(1, machine.snapshot.evidence_loop_count)
        self.assertEqual(
            ReadinessVerdict.NEEDS_MORE_EVIDENCE,
            machine.snapshot.readiness_verdict,
        )

    def test_exhausted_evidence_budget_blocks_the_run(self) -> None:
        machine = StateMachine("run-008", max_evidence_loops=0)
        machine.transition_to(Phase.PREPARE_WORKSPACE, "workspace ready")
        machine.transition_to(Phase.BUILD, "builder start")
        machine.transition_to(Phase.LOCAL_VERIFY, "candidate built")
        machine.transition_to(Phase.FINAL_GATE, "authoritative rerun")

        machine.apply_final_gate_outcome(
            ReadinessVerdict.NEEDS_MORE_EVIDENCE,
            "still need more evidence",
        )

        self.assertEqual(RunState.BLOCKED, machine.snapshot.run_state)
        self.assertEqual(ReadinessVerdict.NOT_READY, machine.snapshot.readiness_verdict)

    def test_terminal_runs_reject_further_transitions(self) -> None:
        machine = StateMachine("run-009")
        machine.mark_unsupported("repo contract missing required fields")

        with self.assertRaises(TerminalStateError):
            machine.transition_to(Phase.PREPARE_WORKSPACE, "should never happen")


if __name__ == "__main__":
    unittest.main()

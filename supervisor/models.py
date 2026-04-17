from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Phase(str, Enum):
    INTAKE = "INTAKE"
    PREPARE_WORKSPACE = "PREPARE_WORKSPACE"
    BUILD = "BUILD"
    LOCAL_VERIFY = "LOCAL_VERIFY"
    APP_LAUNCH = "APP_LAUNCH"
    UI_VERIFY = "UI_VERIFY"
    AUDIT_READY = "AUDIT_READY"
    FINAL_GATE = "FINAL_GATE"


class RunState(str, Enum):
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"
    IN_PROGRESS = "IN_PROGRESS"


class ReadinessVerdict(str, Enum):
    READY = "READY"
    NOT_READY = "NOT_READY"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


class ActionType(str, Enum):
    COLLECT_CONTEXT = "collect_context"
    REQUEST_BUILDER_TASK = "request_builder_task"
    RUN_CONTRACT_COMMAND = "run_contract_command"
    LAUNCH_APP = "launch_app"
    STOP_APP = "stop_app"
    RUN_UI_SUITE = "run_ui_suite"
    RECORD_DECISION = "record_decision"
    PROPOSE_TERMINAL_STATE = "propose_terminal_state"


@dataclass(frozen=True)
class FinalGateEvidence:
    required_artifacts_present: bool = False
    authoritative_checks_passed: bool = False
    unresolved_high_severity_findings: bool = False


@dataclass(frozen=True)
class TransitionRecord:
    from_phase: Phase | None
    to_phase: Phase
    reason: str
    at: str


@dataclass(frozen=True)
class RunSnapshot:
    run_id: str
    phase: Phase
    run_state: RunState = RunState.IN_PROGRESS
    readiness_verdict: ReadinessVerdict | None = None
    final_gate_evidence: FinalGateEvidence = field(default_factory=FinalGateEvidence)
    phase_history: tuple[TransitionRecord, ...] = field(default_factory=tuple)
    evidence_loop_count: int = 0
    max_evidence_loops: int = 1
    terminal_reason: str | None = None

    @classmethod
    def initial(cls, run_id: str, max_evidence_loops: int = 1) -> RunSnapshot:
        record = TransitionRecord(
            from_phase=None,
            to_phase=Phase.INTAKE,
            reason="Run created.",
            at=_utc_now_iso(),
        )
        return cls(
            run_id=run_id,
            phase=Phase.INTAKE,
            phase_history=(record,),
            max_evidence_loops=max_evidence_loops,
        )

    def with_transition(self, to_phase: Phase, reason: str) -> RunSnapshot:
        record = TransitionRecord(
            from_phase=self.phase,
            to_phase=to_phase,
            reason=reason,
            at=_utc_now_iso(),
        )
        return replace(
            self,
            phase=to_phase,
            phase_history=self.phase_history + (record,),
        )


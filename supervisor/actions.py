from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from supervisor.models import ActionType, Phase, ReadinessVerdict, RunState


RAW_SHELL_KEYS = {"cmd", "command", "shell", "bash", "script", "argv"}

PHASE_ACTIONS: dict[Phase, tuple[ActionType, ...]] = {
    Phase.INTAKE: (
        ActionType.COLLECT_CONTEXT,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.PREPARE_WORKSPACE: (
        ActionType.COLLECT_CONTEXT,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.BUILD: (
        ActionType.COLLECT_CONTEXT,
        ActionType.REQUEST_BUILDER_TASK,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.LOCAL_VERIFY: (
        ActionType.RUN_CONTRACT_COMMAND,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.APP_LAUNCH: (
        ActionType.LAUNCH_APP,
        ActionType.STOP_APP,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.UI_VERIFY: (
        ActionType.RUN_UI_SUITE,
        ActionType.STOP_APP,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.AUDIT_READY: (
        ActionType.COLLECT_CONTEXT,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
    Phase.FINAL_GATE: (
        ActionType.COLLECT_CONTEXT,
        ActionType.RUN_CONTRACT_COMMAND,
        ActionType.RECORD_DECISION,
        ActionType.PROPOSE_TERMINAL_STATE,
    ),
}


class ActionValidationError(ValueError):
    """Raised when a strategy action violates the typed action contract."""


@dataclass(frozen=True)
class Action:
    action_type: ActionType
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Action:
        if "action" not in data:
            raise ActionValidationError("Action payload is missing `action`.")
        action_value = data["action"]
        try:
            action_type = ActionType(str(action_value))
        except ValueError as exc:
            raise ActionValidationError(f"Unsupported action `{action_value}`.") from exc
        payload = {key: value for key, value in data.items() if key != "action"}
        return cls(action_type=action_type, payload=payload)


def allowed_actions_for_phase(phase: Phase) -> tuple[ActionType, ...]:
    return PHASE_ACTIONS[phase]


def validate_action_for_phase(phase: Phase, action: Action) -> None:
    if action.action_type not in allowed_actions_for_phase(phase):
        raise ActionValidationError(
            f"Action `{action.action_type.value}` is illegal during phase `{phase.value}`."
        )

    raw_shell_keys = RAW_SHELL_KEYS.intersection(action.payload)
    if raw_shell_keys:
        raise ActionValidationError(
            "Typed actions may not carry raw shell payloads. "
            f"Found forbidden payload keys: {', '.join(sorted(raw_shell_keys))}."
        )

    if action.action_type is ActionType.REQUEST_BUILDER_TASK:
        if not str(action.payload.get("task_description", "")).strip():
            raise ActionValidationError(
                "`request_builder_task` requires a non-empty `task_description`."
            )
        return

    if action.action_type is ActionType.RUN_CONTRACT_COMMAND:
        if not str(action.payload.get("command_name", "")).strip():
            raise ActionValidationError(
                "`run_contract_command` requires `command_name`, not raw shell text."
            )
        return

    if action.action_type is ActionType.PROPOSE_TERMINAL_STATE:
        _validate_terminal_state_proposal(phase, action.payload)


def _validate_terminal_state_proposal(
    phase: Phase,
    payload: Mapping[str, Any],
) -> None:
    state_value = payload.get("run_state")
    if state_value is None:
        raise ActionValidationError(
            "`propose_terminal_state` requires a `run_state` value."
        )

    try:
        proposed_state = RunState(str(state_value))
    except ValueError as exc:
        raise ActionValidationError(
            f"`propose_terminal_state` received unknown run_state `{state_value}`."
        ) from exc

    if proposed_state is RunState.IN_PROGRESS:
        raise ActionValidationError(
            "`propose_terminal_state` may only suggest terminal run states."
        )

    if proposed_state is RunState.COMPLETE:
        if phase is not Phase.FINAL_GATE:
            raise ActionValidationError(
                "`COMPLETE` may only be proposed during `FINAL_GATE`."
            )
        verdict = payload.get("readiness_verdict")
        if verdict != ReadinessVerdict.READY.value:
            raise ActionValidationError(
                "`COMPLETE` proposals must carry `readiness_verdict = READY`."
            )


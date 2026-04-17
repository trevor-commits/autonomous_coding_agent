from __future__ import annotations

import json

from supervisor.actions import Action, ActionValidationError, validate_action_for_phase
from supervisor.models import ActionType, Phase


class StrategyDecisionError(ValueError):
    """Raised when a manual strategy input cannot be parsed into a legal action."""


def parse_manual_action(raw_input: str) -> Action:
    text = raw_input.strip()
    if not text:
        raise StrategyDecisionError("Manual strategy input is empty.")

    if text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise StrategyDecisionError("Manual strategy input is not valid JSON.") from exc
        if not isinstance(payload, dict):
            raise StrategyDecisionError("Manual strategy JSON must be an object.")
        try:
            return Action.from_mapping(payload)
        except ActionValidationError as exc:
            raise StrategyDecisionError(str(exc)) from exc

    try:
        action_type = ActionType(text)
    except ValueError as exc:
        raise StrategyDecisionError(f"Unknown manual action `{text}`.") from exc
    return Action(action_type=action_type)


class ManualStrategy:
    """Phase-legal manual strategy for early supervisor testing."""

    def get_strategy_decision(self, phase: Phase, raw_input: str) -> Action:
        action = parse_manual_action(raw_input)
        try:
            validate_action_for_phase(phase, action)
        except ActionValidationError as exc:
            raise StrategyDecisionError(str(exc)) from exc
        return action


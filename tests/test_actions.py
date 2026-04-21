import unittest

from supervisor.actions import (
    Action,
    ActionValidationError,
    allowed_actions_for_phase,
    validate_action_for_phase,
)
from supervisor.models import ActionType, Phase
from supervisor.strategy_api import ManualStrategy, StrategyDecisionError, parse_manual_action


class ActionValidationTests(unittest.TestCase):
    def test_build_phase_allows_builder_task(self) -> None:
        action = Action(
            action_type=ActionType.REQUEST_BUILDER_TASK,
            payload={"description": "Implement a deterministic phase machine."},
        )

        validate_action_for_phase(Phase.BUILD, action)

    def test_local_verify_allows_named_contract_command(self) -> None:
        action = Action(
            action_type=ActionType.RUN_CONTRACT_COMMAND,
            payload={"name": "test", "scope": "targeted"},
        )

        validate_action_for_phase(Phase.LOCAL_VERIFY, action)

    def test_disallows_action_not_legal_for_phase(self) -> None:
        action = Action(action_type=ActionType.RUN_UI_SUITE)

        with self.assertRaises(ActionValidationError):
            validate_action_for_phase(Phase.BUILD, action)

    def test_rejects_raw_shell_payloads(self) -> None:
        action = Action(
            action_type=ActionType.RUN_CONTRACT_COMMAND,
            payload={"cmd": "pytest -q"},
        )

        with self.assertRaises(ActionValidationError):
            validate_action_for_phase(Phase.LOCAL_VERIFY, action)

    def test_complete_proposal_is_final_gate_only(self) -> None:
        action = Action(
            action_type=ActionType.PROPOSE_TERMINAL_STATE,
            payload={"run_state": "COMPLETE", "readiness_verdict": "READY"},
        )

        with self.assertRaises(ActionValidationError):
            validate_action_for_phase(Phase.BUILD, action)

    def test_final_gate_complete_proposal_requires_ready_verdict(self) -> None:
        action = Action(
            action_type=ActionType.PROPOSE_TERMINAL_STATE,
            payload={"run_state": "COMPLETE", "readiness_verdict": "NOT_READY"},
        )

        with self.assertRaises(ActionValidationError):
            validate_action_for_phase(Phase.FINAL_GATE, action)

    def test_allowed_actions_return_stable_mapping(self) -> None:
        actions = allowed_actions_for_phase(Phase.UI_VERIFY)

        self.assertIn(ActionType.RUN_UI_SUITE, actions)
        self.assertIn(ActionType.PROPOSE_TERMINAL_STATE, actions)

    def test_audit_ready_allows_review_requested_builder_turn(self) -> None:
        action = Action(
            action_type=ActionType.REQUEST_BUILDER_TASK,
            payload={"description": "Address the candidate review findings."},
        )

        validate_action_for_phase(Phase.AUDIT_READY, action)

    def test_final_gate_allows_review_requested_builder_turn(self) -> None:
        action = Action(
            action_type=ActionType.REQUEST_BUILDER_TASK,
            payload={"description": "Collect one more evidence-backed fix before readiness."},
        )

        validate_action_for_phase(Phase.FINAL_GATE, action)


class ManualStrategyTests(unittest.TestCase):
    def test_parse_manual_action_accepts_shorthand(self) -> None:
        action = parse_manual_action("collect_context")

        self.assertEqual(ActionType.COLLECT_CONTEXT, action.action_type)

    def test_parse_manual_action_accepts_json_payload(self) -> None:
        action = parse_manual_action(
            '{"action":"request_builder_task","description":"Add tests"}'
        )

        self.assertEqual(ActionType.REQUEST_BUILDER_TASK, action.action_type)
        self.assertEqual("Add tests", action.payload["description"])

    def test_manual_strategy_rejects_illegal_phase_action(self) -> None:
        strategy = ManualStrategy()

        with self.assertRaises(StrategyDecisionError):
            strategy.get_strategy_decision(Phase.INTAKE, "run_ui_suite")


if __name__ == "__main__":
    unittest.main()

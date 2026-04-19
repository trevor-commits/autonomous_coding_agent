import unittest

from supervisor.models import ActionType
from supervisor.strategy_claude import ClaudeStrategy

from tests.test_strategy_simple import _repo_contract, _run_contract


def _response(text: str, *, input_tokens: int = 0, output_tokens: int = 0) -> dict:
    return {
        "content": [{"type": "text", "text": text}],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


class FakeClaudeTransport:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def __call__(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        timeout_seconds: int,
        prompt: str,
    ) -> dict:
        self.prompts.append(prompt)
        return self.responses.pop(0)


class ClaudeStrategyTests(unittest.TestCase):
    def test_first_build_uses_planner_prompt(self) -> None:
        transport = FakeClaudeTransport(
            [
                _response(
                    '{"action":"request_builder_task","description":"Plan the first milestone and implement it."}'
                )
            ]
        )
        strategy = ClaudeStrategy(api_key="test-key", transport=transport)

        action = strategy.build_action(
            _run_contract(),
            _repo_contract(),
            prior_failure_fingerprints=(),
        )

        self.assertEqual(ActionType.REQUEST_BUILDER_TASK, action.action_type)
        self.assertIn("Plan the first milestone", action.payload["description"])
        self.assertIn("Prompt Pack: planner", transport.prompts[0])

    def test_second_build_uses_task_shaper_prompt(self) -> None:
        transport = FakeClaudeTransport(
            [
                _response('{"action":"request_builder_task","description":"First step."}'),
                _response('{"action":"request_builder_task","description":"Second step."}'),
            ]
        )
        strategy = ClaudeStrategy(api_key="test-key", transport=transport)
        run_contract = _run_contract()
        repo_contract = _repo_contract()

        strategy.build_action(run_contract, repo_contract, prior_failure_fingerprints=())
        action = strategy.build_action(
            run_contract,
            repo_contract,
            prior_failure_fingerprints=("local-verify-test-login-failed",),
        )

        self.assertEqual(ActionType.REQUEST_BUILDER_TASK, action.action_type)
        self.assertIn("Prompt Pack: builder_task_shaper", transport.prompts[1])
        self.assertIn("local-verify-test-login-failed", transport.prompts[1])

    def test_invalid_response_falls_back_to_simple_strategy(self) -> None:
        transport = FakeClaudeTransport([_response("not valid json")])
        strategy = ClaudeStrategy(api_key="test-key", transport=transport)

        action = strategy.build_action(
            _run_contract(),
            _repo_contract(),
            prior_failure_fingerprints=(),
        )

        self.assertEqual(ActionType.REQUEST_BUILDER_TASK, action.action_type)
        self.assertIn("Add login validation", action.payload["description"])
        self.assertIn("pnpm test", action.payload["description"])

    def test_app_launch_repair_uses_stall_prompt(self) -> None:
        transport = FakeClaudeTransport(
            [
                _response(
                    '{"action":"request_builder_task","description":"Repair the app startup path before re-running health."}'
                )
            ]
        )
        strategy = ClaudeStrategy(api_key="test-key", transport=transport)

        action = strategy.app_launch_repair_action(
            _run_contract(),
            failure_reason="Health check never returned 200.",
            failure_fingerprint="app-launch-app-health-timeout",
        )

        self.assertEqual(ActionType.REQUEST_BUILDER_TASK, action.action_type)
        self.assertIn("Prompt Pack: stall_diagnosis", transport.prompts[0])
        self.assertIn("app-launch-app-health-timeout", transport.prompts[0])

    def test_usage_cost_accumulates_until_consumed(self) -> None:
        transport = FakeClaudeTransport(
            [
                _response(
                    '{"action":"request_builder_task","description":"Use the typed action result."}',
                    input_tokens=200,
                    output_tokens=50,
                )
            ]
        )
        strategy = ClaudeStrategy(
            api_key="test-key",
            transport=transport,
            input_cost_per_million_tokens=10.0,
            output_cost_per_million_tokens=20.0,
        )

        strategy.build_action(_run_contract(), _repo_contract(), prior_failure_fingerprints=())

        self.assertAlmostEqual(0.003, strategy.consume_pending_cost(), places=6)
        self.assertEqual(0.0, strategy.consume_pending_cost())
        self.assertAlmostEqual(0.003, strategy.total_cost_dollars, places=6)


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent / "schemas" / "strategy-decision.schema.json"
)


class StrategyDecisionSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA_PATH.read_text())
        cls.validator = Draft202012Validator(cls.schema)

    def test_request_builder_task_uses_description_field(self) -> None:
        payload = {
            "action": "request_builder_task",
            "description": "Implement the repo-contract objective.",
        }

        errors = list(self.validator.iter_errors(payload))

        self.assertEqual([], errors)

    def test_run_contract_command_uses_name_field(self) -> None:
        payload = {
            "action": "run_contract_command",
            "name": "test",
            "scope": "targeted",
        }

        errors = list(self.validator.iter_errors(payload))

        self.assertEqual([], errors)

    def test_removed_checkpoint_action_is_rejected(self) -> None:
        payload = {"action": "checkpoint_candidate", "reason": "candidate is green"}

        self.assertFalse(self.validator.is_valid(payload))

    def test_removed_failure_signature_action_is_rejected(self) -> None:
        payload = {"action": "record_failure_signature", "fingerprint": "same-error"}

        self.assertFalse(self.validator.is_valid(payload))


if __name__ == "__main__":
    unittest.main()

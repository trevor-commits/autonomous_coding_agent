from __future__ import annotations

import importlib
import unittest
from typing import Any
from unittest.mock import patch

from supervisor.partner_contracts import PartnerContractError, canonical_hash


NOW = "2026-07-13T21:00:00Z"


def _learning():
    return importlib.import_module("supervisor.partner_learning")


def _envelope() -> dict[str, Any]:
    approval = {
        "schema_version": "1",
        "approval_id": "approval-001",
        "approval_kind": "proposal",
        "subject_id": "proposal-001",
        "subject_hash": canonical_hash(_proposal()),
        "approved": True,
        "approved_at": "2026-07-13T19:55:00Z",
        "expires_at": "2026-07-13T22:00:00Z",
        "capability_classes": ["local_read", "sandbox_write"],
    }
    envelope = {
        "schema_version": "1",
        "envelope_id": "envelope-001",
        "wake_id": "wake-001",
        "proposal_id": "proposal-001",
        "proposal_hash": canonical_hash(_proposal()),
        "approval_id": "approval-001",
        "approval_hash": canonical_hash(approval),
        "approval_binding": approval,
        "executor_id": "autonomous-coding-agent",
        "strategy": "simple",
        "builder_model": "gpt-5.5",
        "builder_reasoning_effort": "high",
        "run_contract": {"run_id": "run-001"},
        "run_contract_hash": canonical_hash({"run_id": "run-001"}),
        "capability_classes": ["local_read", "sandbox_write"],
        "risk_level": "low",
        "created_at": "2026-07-13T20:00:00Z",
    }
    envelope["content_hash"] = canonical_hash(envelope)
    return envelope


def _outcome(**measure_overrides: Any) -> dict[str, Any]:
    envelope = _envelope()
    measures = {
        "produced_artifact": True,
        "adopted_use": True,
        "time_saved_minutes": 12.0,
        "quality_change": 0.5,
        "operator_feedback": "Useful in the bounded pilot.",
        "benefit_score": 0.8,
        "harm_prevented_score": 0.4,
        "goal_progress": {"goal-001": 0.5},
        "lesson_signals": [
            {
                "id": "signal-001",
                "scope": "workflow",
                "summary": "Small bounded creative pilots verify value cheaply.",
                "confidence": 0.8,
                "ttl_days": 30,
                "contradiction_key": "creative-pilot-size",
                "stance": "prefer",
            }
        ],
    }
    measures.update(measure_overrides)
    return {
        "schema_version": "1",
        "outcome_id": "outcome-001",
        "envelope_id": envelope["envelope_id"],
        "envelope_hash": envelope["content_hash"],
        "run_id": "run-001",
        "run_state": "COMPLETE",
        "readiness_verdict": "READY",
        "receipt_ref": "receipt:run-001",
        "receipt_hash": "3" * 64,
        "measures": measures,
        "completed_at": "2026-07-13T20:45:00Z",
    }


def _proposal() -> dict[str, Any]:
    return {
        "id": "proposal-001",
        "goal_ids": ["goal-001"],
        "expected_benefit": 0.7,
        "harm_prevented": 0.2,
    }


class PartnerLearningTests(unittest.TestCase):
    def test_outcome_must_bind_the_exact_immutable_envelope_and_receipt(self) -> None:
        learning = _learning()
        envelope = _envelope()
        for outcome in (
            {**_outcome(), "envelope_id": "different-envelope"},
            {**_outcome(), "envelope_hash": "0" * 64},
            {**_outcome(), "receipt_hash": "not-a-sha"},
        ):
            with self.subTest(outcome=outcome):
                with self.assertRaises(learning.PartnerLearningError):
                    learning.derive_learning_candidates(
                        outcome,
                        envelope=envelope,
                        proposal=_proposal(),
                        now=NOW,
                    )

    def test_proposal_binding_mismatch_is_rejected(self) -> None:
        learning = _learning()
        for proposal in (
            {**_proposal(), "id": "proposal-other"},
            {**_proposal(), "expected_benefit": 0.1},
        ):
            with self.subTest(proposal=proposal):
                with self.assertRaises(learning.PartnerLearningError):
                    learning.derive_learning_candidates(
                        _outcome(),
                        envelope=_envelope(),
                        proposal=proposal,
                        now=NOW,
                    )

    def test_unsuccessful_run_records_zero_not_realized_benefit(self) -> None:
        learning = _learning()
        outcome = _outcome()
        outcome["run_state"] = "BLOCKED"
        outcome["readiness_verdict"] = "NOT_READY"
        result = learning.derive_learning_candidates(
            outcome,
            envelope=_envelope(),
            proposal=_proposal(),
            now=NOW,
        )

        benefit = result["benefit_candidate"]
        self.assertFalse(benefit["successful"])
        self.assertEqual("not_realized", benefit["benefit_status"])
        self.assertEqual(0.0, benefit["measured_benefit"])
        self.assertEqual(0.0, benefit["harm_prevented"])

    def test_lesson_schema_failure_uses_learning_error_boundary(self) -> None:
        learning = _learning()
        signal = _outcome()["measures"]["lesson_signals"][0]
        with patch(
            "supervisor.partner_learning.validate_document",
            side_effect=PartnerContractError("forced schema failure"),
        ):
            with self.assertRaisesRegex(learning.PartnerLearningError, "Lesson candidate contract"):
                learning._lesson_candidates(
                    [signal],
                    outcome=_outcome(),
                    now=learning._parse_time(NOW),
                )

    def test_measured_benefit_and_goal_progress_are_provenance_bound(self) -> None:
        learning = _learning()
        result = learning.derive_learning_candidates(
            _outcome(),
            envelope=_envelope(),
            proposal=_proposal(),
            now=NOW,
        )
        benefit = result["benefit_candidate"]
        self.assertEqual(0.8, benefit["measured_benefit"])
        self.assertEqual(0.4, benefit["harm_prevented"])
        self.assertEqual("measured", benefit["benefit_status"])
        self.assertTrue(benefit["evidence"]["produced_artifact"])
        self.assertEqual("outcome-001", benefit["source_outcome_id"])
        self.assertEqual("3" * 64, benefit["source_receipt_hash"])
        self.assertEqual(
            [{"goal_id": "goal-001", "progress_delta": 0.5, "source_outcome_id": "outcome-001"}],
            result["goal_progression_candidates"],
        )

    def test_completion_without_adoption_evidence_keeps_benefit_unknown(self) -> None:
        learning = _learning()
        result = learning.derive_learning_candidates(
            _outcome(
                adopted_use=None,
                time_saved_minutes=None,
                quality_change=None,
                operator_feedback=None,
                benefit_score=None,
                harm_prevented_score=None,
            ),
            envelope=_envelope(),
            proposal=_proposal(),
            now=NOW,
        )
        benefit = result["benefit_candidate"]
        self.assertEqual("unknown", benefit["benefit_status"])
        self.assertIsNone(benefit["measured_benefit"])
        self.assertIsNone(benefit["harm_prevented"])

    def test_lessons_are_scoped_expiring_candidates_and_identity_never_rewrites_silently(self) -> None:
        learning = _learning()
        signals = [
            {
                "id": "signal-ranking",
                "scope": "ranking",
                "summary": "Prefer smaller first pilots.",
                "confidence": 0.9,
                "ttl_days": 7,
                "contradiction_key": "pilot-size",
                "stance": "prefer",
            },
            {
                "id": "signal-identity",
                "scope": "identity",
                "summary": "Consider adding animation as an approved interest.",
                "confidence": 0.7,
                "ttl_days": 14,
                "contradiction_key": "animation-interest",
                "stance": "prefer",
            },
        ]
        result = learning.derive_learning_candidates(
            _outcome(lesson_signals=signals),
            envelope=_envelope(),
            proposal=_proposal(),
            now=NOW,
        )
        ranking, identity = result["lesson_candidates"]
        self.assertEqual("2026-07-20T21:00:00Z", ranking["expires_at"])
        self.assertFalse(ranking["identity_amendment_required"])
        self.assertEqual("identity_amendment", identity["promotion_target"])
        self.assertTrue(identity["identity_amendment_required"])
        self.assertEqual(identity["content_hash"], canonical_hash(identity))

    def test_contradictory_signals_are_preserved_for_review_not_promoted(self) -> None:
        learning = _learning()
        signals = [
            {
                "id": "signal-a",
                "scope": "communication",
                "summary": "Prefer more detail.",
                "confidence": 0.8,
                "ttl_days": 7,
                "contradiction_key": "response-detail",
                "stance": "prefer",
            },
            {
                "id": "signal-b",
                "scope": "communication",
                "summary": "Avoid more detail.",
                "confidence": 0.8,
                "ttl_days": 7,
                "contradiction_key": "response-detail",
                "stance": "avoid",
            },
        ]
        result = learning.derive_learning_candidates(
            _outcome(lesson_signals=signals),
            envelope=_envelope(),
            proposal=_proposal(),
            now=NOW,
        )
        self.assertEqual([], result["lesson_candidates"])
        self.assertEqual(
            [{"contradiction_key": "response-detail", "signal_ids": ["signal-a", "signal-b"]}],
            result["contradictions"],
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import importlib
import hashlib
import json
import unittest
from typing import Any
from unittest.mock import patch

from supervisor.partner_contracts import PartnerContractError, canonical_hash


NOW = "2026-07-13T21:00:00Z"
RECEIPT_REF = "receipt:run-001"
REPORT_REF = "/tmp/partner-sandbox/report.json"
REPORT_BYTES = b'{"run_id":"run-001","run_state":"COMPLETE"}\n'


def _learning():
    return importlib.import_module("supervisor.partner_learning")


def _envelope() -> dict[str, Any]:
    proposal = _proposal()
    proposal_hash = canonical_hash(proposal)
    approval = {
        "schema_version": "1",
        "approval_id": "approval-001",
        "approval_kind": "proposal",
        "subject_id": "proposal-001",
        "subject_hash": proposal_hash,
        "approved": True,
        "approved_at": "2026-07-13T19:55:00Z",
        "expires_at": "2026-07-13T22:00:00Z",
        "capability_classes": proposal["required_capabilities"],
    }
    envelope = {
        "schema_version": "1",
        "envelope_id": "envelope-001",
        "wake_id": "wake-001",
        "proposal_id": "proposal-001",
        "proposal_hash": proposal_hash,
        "approval_id": "approval-001",
        "approval_hash": canonical_hash(approval),
        "approval_binding": approval,
        "executor_id": "autonomous-coding-agent",
        "strategy": "simple",
        "builder_model": "gpt-5.5",
        "builder_reasoning_effort": "high",
        "run_contract": {
            **proposal["run_contract"],
            "claim_id": "envelope-001",
            "run_trace_id": "wake-001",
            "issue_snapshot_hash": proposal_hash,
            "risk_level": "Low",
            "approval_required": False,
        },
        "capability_classes": proposal["required_capabilities"],
        "risk_level": "low",
        "created_at": "2026-07-13T20:00:00Z",
    }
    envelope["run_contract_hash"] = canonical_hash(envelope["run_contract"])
    envelope["content_hash"] = canonical_hash(envelope)
    return envelope


def _receipt_bytes(
    *,
    run_state: str = "COMPLETE",
    readiness_verdict: str = "READY",
    report_ref: str = REPORT_REF,
    report_bytes: bytes = REPORT_BYTES,
) -> bytes:
    envelope = _envelope()
    receipt = {
        "ts": "2026-07-13T20:45:00Z",
        "status": "ok",
        "action": "dispatch_execute",
        "runner_rc": 0,
        "partner_executor_result": {
            "ok": True,
            "executed": True,
            "envelope_id": envelope["envelope_id"],
            "envelope_hash": envelope["content_hash"],
            "run_id": envelope["run_contract"]["run_id"],
            "run_state": run_state,
            "readiness_verdict": readiness_verdict,
            "report_path": report_ref,
            "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        },
    }
    return (json.dumps(receipt, sort_keys=True) + "\n").encode("utf-8")


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
        "receipt_ref": RECEIPT_REF,
        "receipt_hash": hashlib.sha256(_receipt_bytes()).hexdigest(),
        "measures": measures,
        "completed_at": "2026-07-13T20:45:00Z",
    }


def _proposal() -> dict[str, Any]:
    return {
        "id": "proposal-001",
        "origin": "self_originated",
        "project_kind": "creative",
        "goal_ids": ["goal-001"],
        "observation_ids": ["observation-001"],
        "interest_ids": ["helpful-projects"],
        "success_criteria": ["Produce one bounded verified artifact."],
        "expected_benefit": 0.7,
        "harm_prevented": 0.2,
        "interest_fit": 0.9,
        "novelty": 0.8,
        "effort": 0.2,
        "confidence": 0.8,
        "risk": 0.1,
        "required_capabilities": ["local_read", "sandbox_write", "deterministic_test"],
        "run_contract": {
            "run_id": "run-001",
            "repo_path": "/tmp/partner-sandbox",
            "objective": "Create one bounded local artifact",
            "scope": {
                "allowed_paths": ["artifacts/"],
                "forbidden_paths": [".env", "infra/"],
            },
            "acceptance": {
                "functional": ["Create one bounded local artifact."],
                "quality_gates": ["Deterministic tests pass."],
                "ui_checks": [],
            },
            "constraints": {
                "single_writer": True,
                "auto_push": False,
                "auto_merge": False,
                "max_repair_loops": 1,
                "max_iterations": 3,
                "max_cost_dollars": 1.0,
                "hard_timeout_seconds": 300,
            },
        },
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
                        report_bytes=REPORT_BYTES,
                        report_ref=REPORT_REF,
                        receipt_bytes=_receipt_bytes(),
                        receipt_ref=RECEIPT_REF,
                        now=NOW,
                    )

    def test_learning_requires_complete_envelope_and_exact_receipt_bytes(self) -> None:
        learning = _learning()
        incomplete = _envelope()
        incomplete["run_contract"] = {"run_id": "run-001"}
        incomplete["run_contract_hash"] = canonical_hash(incomplete["run_contract"])
        incomplete["content_hash"] = canonical_hash(incomplete)

        cases = (
            (incomplete, _receipt_bytes(), RECEIPT_REF),
            (_envelope(), _receipt_bytes() + b" ", RECEIPT_REF),
            (_envelope(), _receipt_bytes(), "receipt:different"),
        )
        for envelope, receipt_bytes, receipt_ref in cases:
            with self.subTest(receipt_ref=receipt_ref, envelope=envelope):
                with self.assertRaises(learning.PartnerLearningError):
                    learning.derive_learning_candidates(
                        _outcome(),
                        envelope=envelope,
                        proposal=_proposal(),
                        report_bytes=REPORT_BYTES,
                        report_ref=REPORT_REF,
                        receipt_bytes=receipt_bytes,
                        receipt_ref=receipt_ref,
                        now=NOW,
                    )

    def test_learning_requires_exact_report_bytes_and_path_from_receipt(self) -> None:
        learning = _learning()
        cases = (
            (b"", REPORT_REF, _receipt_bytes()),
            (REPORT_BYTES + b" ", REPORT_REF, _receipt_bytes()),
            (REPORT_BYTES, "/tmp/different-report.json", _receipt_bytes()),
        )
        for report_bytes, report_ref, receipt_bytes in cases:
            with self.subTest(report_bytes=report_bytes, report_ref=report_ref):
                with self.assertRaises(learning.PartnerLearningError):
                    learning.derive_learning_candidates(
                        _outcome(),
                        envelope=_envelope(),
                        proposal=_proposal(),
                        report_bytes=report_bytes,
                        report_ref=report_ref,
                        receipt_bytes=receipt_bytes,
                        receipt_ref=RECEIPT_REF,
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
                        report_bytes=REPORT_BYTES,
                        report_ref=REPORT_REF,
                        receipt_bytes=_receipt_bytes(),
                        receipt_ref=RECEIPT_REF,
                        now=NOW,
                    )

    def test_unsuccessful_run_records_zero_not_realized_benefit(self) -> None:
        learning = _learning()
        outcome = _outcome()
        outcome["run_state"] = "BLOCKED"
        outcome["readiness_verdict"] = "NOT_READY"
        blocked_receipt = _receipt_bytes(
            run_state="BLOCKED", readiness_verdict="NOT_READY"
        )
        outcome["receipt_hash"] = hashlib.sha256(blocked_receipt).hexdigest()
        result = learning.derive_learning_candidates(
            outcome,
            envelope=_envelope(),
            proposal=_proposal(),
            report_bytes=REPORT_BYTES,
            report_ref=REPORT_REF,
            receipt_bytes=blocked_receipt,
            receipt_ref=RECEIPT_REF,
            now=NOW,
        )

        benefit = result["benefit_candidate"]
        self.assertFalse(benefit["successful"])
        self.assertEqual("not_realized", benefit["benefit_status"])
        self.assertEqual(0.0, benefit["measured_benefit"])
        self.assertEqual(0.0, benefit["harm_prevented"])
        self.assertEqual([], result["goal_progression_candidates"])
        self.assertEqual([], result["lesson_candidates"])
        self.assertEqual([], result["contradictions"])

    def test_invalid_failed_run_receipt_cannot_emit_learning_candidates(self) -> None:
        learning = _learning()
        outcome = _outcome()
        outcome["run_state"] = "BLOCKED"
        outcome["readiness_verdict"] = "NOT_READY"
        invalid_receipt = _receipt_bytes()
        outcome["receipt_hash"] = hashlib.sha256(invalid_receipt).hexdigest()

        with self.assertRaisesRegex(
            learning.PartnerLearningError,
            "Receipt executor result does not match",
        ):
            learning.derive_learning_candidates(
                outcome,
                envelope=_envelope(),
                proposal=_proposal(),
                report_bytes=REPORT_BYTES,
                report_ref=REPORT_REF,
                receipt_bytes=invalid_receipt,
                receipt_ref=RECEIPT_REF,
                now=NOW,
            )

    def test_lesson_schema_failure_uses_learning_error_boundary(self) -> None:
        learning = _learning()
        signal = _outcome()["measures"]["lesson_signals"][0]
        with patch(
            "supervisor.partner_learning.validate_document",
            side_effect=PartnerContractError("forced schema failure"),
        ):
            with self.assertRaisesRegex(
                learning.PartnerLearningError, "Lesson candidate contract"
            ):
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
            report_bytes=REPORT_BYTES,
            report_ref=REPORT_REF,
            receipt_bytes=_receipt_bytes(),
            receipt_ref=RECEIPT_REF,
            now=NOW,
        )
        benefit = result["benefit_candidate"]
        self.assertEqual(0.8, benefit["measured_benefit"])
        self.assertEqual(0.4, benefit["harm_prevented"])
        self.assertEqual("measured", benefit["benefit_status"])
        self.assertTrue(benefit["evidence"]["produced_artifact"])
        self.assertEqual("outcome-001", benefit["source_outcome_id"])
        self.assertEqual(
            hashlib.sha256(_receipt_bytes()).hexdigest(), benefit["source_receipt_hash"]
        )
        self.assertEqual(
            [
                {
                    "goal_id": "goal-001",
                    "progress_delta": 0.5,
                    "source_outcome_id": "outcome-001",
                }
            ],
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
            report_bytes=REPORT_BYTES,
            report_ref=REPORT_REF,
            receipt_bytes=_receipt_bytes(),
            receipt_ref=RECEIPT_REF,
            now=NOW,
        )
        benefit = result["benefit_candidate"]
        self.assertEqual("unknown", benefit["benefit_status"])
        self.assertIsNone(benefit["measured_benefit"])
        self.assertIsNone(benefit["harm_prevented"])

    def test_scores_without_complete_adoption_evidence_are_rejected(self) -> None:
        learning = _learning()
        unsupported = _outcome(
            adopted_use=None,
            time_saved_minutes=None,
            quality_change=None,
            operator_feedback=None,
            benefit_score=0.9,
            harm_prevented_score=0.8,
        )
        with self.assertRaises(learning.PartnerLearningError):
            learning.derive_learning_candidates(
                unsupported,
                envelope=_envelope(),
                proposal=_proposal(),
                report_bytes=REPORT_BYTES,
                report_ref=REPORT_REF,
                receipt_bytes=_receipt_bytes(),
                receipt_ref=RECEIPT_REF,
                now=NOW,
            )

    def test_lessons_are_scoped_expiring_candidates_and_identity_never_rewrites_silently(
        self,
    ) -> None:
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
            report_bytes=REPORT_BYTES,
            report_ref=REPORT_REF,
            receipt_bytes=_receipt_bytes(),
            receipt_ref=RECEIPT_REF,
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
            report_bytes=REPORT_BYTES,
            report_ref=REPORT_REF,
            receipt_bytes=_receipt_bytes(),
            receipt_ref=RECEIPT_REF,
            now=NOW,
        )
        self.assertEqual([], result["lesson_candidates"])
        self.assertEqual(
            [
                {
                    "contradiction_key": "response-detail",
                    "signal_ids": ["signal-a", "signal-b"],
                }
            ],
            result["contradictions"],
        )


if __name__ == "__main__":
    unittest.main()

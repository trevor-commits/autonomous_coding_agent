from __future__ import annotations

import copy
import importlib
import unittest
from typing import Any, Iterator

from supervisor.partner_contracts import canonical_hash, validate_identity


NOW = "2026-07-13T21:00:00Z"


def _runtime():
    return importlib.import_module("supervisor.partner_runtime")


def _identity() -> dict[str, Any]:
    item = lambda identifier, value: {"id": identifier, "value": value, "source": "configured"}
    return validate_identity(
        {
            "schema_version": "1",
            "name": "Partner",
            "pronouns": ["he", "him"],
            "values": [item("truth", "Stay truthful")],
            "voice_traits": [item("warm", "Warm and direct")],
            "interests": [item("helpful-projects", "Helpful and creative projects")],
            "dislikes": [item("coercion", "Emotional coercion")],
            "relationship_boundaries": [item("honest", "Do not claim consciousness")],
            "source_labels": {
                "configured": "configured",
                "operator_approved": "operator approved",
                "inferred": "inferred",
                "generated": "generated",
            },
        }
    )


def _candidate() -> dict[str, Any]:
    return {
        "id": "proposal-001",
        "origin": "self_originated",
        "project_kind": "creative",
        "observation_ids": ["observation-001"],
        "interest_ids": ["helpful-projects"],
        "success_criteria": ["Produce one bounded verified artifact."],
        "expected_benefit": 0.8,
        "harm_prevented": 0.2,
        "interest_fit": 0.9,
        "novelty": 0.8,
        "effort": 0.2,
        "confidence": 0.8,
        "risk": 0.1,
        "required_capabilities": ["local_read", "sandbox_write", "deterministic_test"],
        "run_contract": {
            "run_id": "partner-run-001",
            "repo_path": "/tmp/partner-sandbox",
            "objective": "Create one bounded local artifact",
        },
    }


def _snapshot(*, stale: bool = False, approval: bool = False, budgets: dict | None = None) -> dict[str, Any]:
    candidate = _candidate()
    proposal_hash = canonical_hash(candidate)
    approvals = []
    if approval:
        approvals.append(
            {
                "schema_version": "1",
                "approval_id": "approval-001",
                "approval_kind": "proposal",
                "subject_id": candidate["id"],
                "subject_hash": proposal_hash,
                "approved": True,
                "approved_at": "2026-07-13T20:55:00Z",
                "expires_at": "2026-07-13T22:00:00Z",
                "capability_classes": candidate["required_capabilities"],
            }
        )
    return {
        "schema_version": "1",
        "wake_id": "wake-001",
        "created_at": NOW,
        "identity": _identity(),
        "goals": [{"id": "goal-001", "summary": "Do useful work", "source_ref": "goal:1"}],
        "observations": [
            {
                "id": "observation-001",
                "summary": "One approved creative opportunity is ready.",
                "source_ref": "health:1",
                "sensitivity": "low",
                "observed_at": "2026-07-13T20:55:00Z",
                "expires_at": "2026-07-13T20:59:59Z" if stale else "2026-07-14T21:00:00Z",
            }
        ],
        "approvals": approvals,
        "maturity": {
            "level": "L1",
            "proposal_count": 0,
            "accepted_count": 0,
            "completed_episode_count": 0,
            "severe_failure": False,
        },
        "executor_outcomes": [],
        "inferred_preferences": [],
        "budgets": budgets or {"max_proposals": 1, "max_envelopes": 1},
    }


class PartnerRuntimeTests(unittest.TestCase):
    def test_unhealthy_or_busy_short_circuits_without_consuming_candidates(self) -> None:
        runtime = _runtime()

        def forbidden_candidates() -> Iterator[dict[str, Any]]:
            raise AssertionError("candidate generation must not run")
            yield _candidate()

        cases = (
            ({"healthy": False, "reason_codes": ["governor_unhealthy"]}, False, "unhealthy"),
            ({"healthy": True, "reason_codes": []}, True, "busy"),
        )
        for health, busy, reason in cases:
            with self.subTest(reason=reason):
                decision = runtime.decide_wake(
                    _snapshot(),
                    candidates=forbidden_candidates(),
                    now=NOW,
                    health=health,
                    busy=busy,
                    kill_switches=(),
                    prior_decisions=(),
                )
                self.assertEqual("no_op", decision["decision_type"])
                self.assertIn(reason, decision["reason_codes"])

    def test_no_current_approved_evidence_or_budget_is_a_no_op(self) -> None:
        runtime = _runtime()
        for snapshot in (
            _snapshot(stale=True),
            _snapshot(budgets={"max_proposals": 0, "max_envelopes": 0}),
        ):
            with self.subTest(snapshot=snapshot):
                decision = runtime.decide_wake(
                    snapshot,
                    candidates=[_candidate()],
                    now=NOW,
                    health={"healthy": True, "reason_codes": []},
                    busy=False,
                    kill_switches=(),
                    prior_decisions=(),
                )
                self.assertEqual("no_op", decision["decision_type"])

    def test_one_wake_emits_at_most_one_proposal_or_authorized_envelope(self) -> None:
        runtime = _runtime()
        candidates = [_candidate(), {**_candidate(), "id": "proposal-002"}]
        proposal = runtime.decide_wake(
            _snapshot(),
            candidates=candidates,
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(),
        )
        self.assertEqual("proposal", proposal["decision_type"])
        self.assertEqual("proposal-001", proposal["payload"]["proposal"]["id"])

        envelope_decision = runtime.decide_wake(
            _snapshot(approval=True),
            candidates=candidates,
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(),
        )
        self.assertEqual("executor_envelope", envelope_decision["decision_type"])
        envelope = envelope_decision["payload"]["executor_envelope"]
        self.assertEqual("proposal-001", envelope["proposal_id"])
        self.assertEqual(envelope["content_hash"], canonical_hash(envelope))
        self.assertEqual(envelope_decision["content_hash"], canonical_hash(envelope_decision))

    def test_duplicate_wake_returns_the_same_prior_decision(self) -> None:
        runtime = _runtime()
        first = runtime.decide_wake(
            _snapshot(),
            candidates=[_candidate()],
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(),
        )
        duplicate = runtime.decide_wake(
            _snapshot(approval=True),
            candidates=[_candidate()],
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(first,),
        )
        self.assertEqual(first, duplicate)

    def test_runtime_is_pure_and_does_not_mutate_supplied_global_truth(self) -> None:
        runtime = _runtime()
        snapshot = _snapshot(approval=True)
        candidates = [_candidate()]
        original_snapshot = copy.deepcopy(snapshot)
        original_candidates = copy.deepcopy(candidates)
        runtime.decide_wake(
            snapshot,
            candidates=candidates,
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(),
        )
        self.assertEqual(original_snapshot, snapshot)
        self.assertEqual(original_candidates, candidates)


if __name__ == "__main__":
    unittest.main()

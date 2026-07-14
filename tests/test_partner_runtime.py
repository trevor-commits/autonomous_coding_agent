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
        "goal_ids": ["goal-001"],
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
    def test_candidate_goal_must_be_present_in_the_current_wake(self) -> None:
        candidate = _candidate()
        candidate["goal_ids"] = ["goal-not-in-wake"]

        decision = _runtime().decide_wake(
            _snapshot(),
            candidates=[candidate],
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
        )

        self.assertEqual("no_op", decision["decision_type"])
        self.assertIn("no_current_approved_evidence", decision["reason_codes"])

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
        self.assertEqual(envelope["envelope_id"], envelope["run_contract"]["claim_id"])
        self.assertEqual("wake-001", envelope["run_contract"]["run_trace_id"])
        self.assertEqual(envelope["proposal_hash"], envelope["run_contract"]["issue_snapshot_hash"])
        self.assertEqual("Low", envelope["run_contract"]["risk_level"])
        self.assertFalse(envelope["run_contract"]["approval_required"])
        self.assertEqual("autonomous-coding-agent", envelope["executor_id"])
        self.assertEqual("simple", envelope["strategy"])
        self.assertEqual("gpt-5.5", envelope["builder_model"])
        self.assertEqual("high", envelope["builder_reasoning_effort"])
        self.assertEqual("approval-001", envelope["approval_binding"]["approval_id"])
        self.assertEqual(canonical_hash(envelope["approval_binding"]), envelope["approval_hash"])
        self.assertEqual(canonical_hash(envelope["run_contract"]), envelope["run_contract_hash"])
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

    def test_observe_decision_does_not_suppress_propose_for_same_wake(self) -> None:
        runtime = _runtime()
        observed = runtime.decide_wake(
            _snapshot(),
            candidates=[_candidate()],
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(),
            mode="observe",
        )
        proposed = runtime.decide_wake(
            _snapshot(),
            candidates=[_candidate()],
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
            prior_decisions=(observed,),
            mode="propose",
        )

        self.assertEqual("no_op", observed["decision_type"])
        self.assertEqual("proposal", proposed["decision_type"])
        self.assertEqual("observe", observed["decision_mode"])
        self.assertEqual("propose", proposed["decision_mode"])
        self.assertNotEqual(observed["idempotency_key"], proposed["idempotency_key"])

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

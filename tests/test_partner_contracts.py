from __future__ import annotations

import copy
import importlib
import unittest
from typing import Any


def _contracts():
    return importlib.import_module("supervisor.partner_contracts")


def _identity() -> dict[str, Any]:
    return {
        "schema_version": "1",
        "name": "Partner",
        "pronouns": ["they", "them"],
        "values": [
            {
                "id": "truthfulness",
                "value": "Say what is known, inferred, and uncertain honestly.",
                "source": "configured",
            }
        ],
        "voice_traits": [
            {"id": "warm", "value": "Warm and direct", "source": "configured"}
        ],
        "interests": [
            {"id": "creative-work", "value": "Creative projects", "source": "configured"}
        ],
        "dislikes": [
            {"id": "coercion", "value": "Emotional coercion", "source": "configured"}
        ],
        "relationship_boundaries": [
            {
                "id": "honest-partner",
                "value": "Act as a useful partner without claiming consciousness or feelings.",
                "source": "configured",
            }
        ],
        "source_labels": {
            "configured": "operator-configured",
            "operator_approved": "operator-approved amendment",
            "inferred": "inferred preference",
            "generated": "generated idea",
        },
    }


def _snapshot() -> dict[str, Any]:
    contracts = _contracts()
    return {
        "schema_version": "1",
        "wake_id": "wake-001",
        "created_at": "2026-07-13T20:00:00Z",
        "identity": contracts.validate_identity(_identity()),
        "goals": [
            {
                "id": "goal-001",
                "summary": "Improve Trevor's daily life with bounded, useful work.",
                "source_ref": "goal:goal-001",
            }
        ],
        "observations": [
            {
                "id": "observation-001",
                "summary": "A governed health check reported one actionable maintenance item.",
                "source_ref": "health:receipt-001",
                "sensitivity": "low",
                "observed_at": "2026-07-13T19:55:00Z",
                "expires_at": "2026-07-14T19:55:00Z",
            }
        ],
        "approvals": [],
        "maturity": {
            "level": "L1",
            "proposal_count": 0,
            "accepted_count": 0,
            "completed_episode_count": 0,
            "severe_failure": False,
        },
        "executor_outcomes": [],
        "inferred_preferences": [
            {
                "id": "preference-001",
                "value": "May prefer concise morning summaries.",
                "source": "inferred",
                "source_ref": "observation:observation-001",
            }
        ],
        "budgets": {"max_proposals": 1, "max_envelopes": 1},
    }


class PartnerIdentityContractTests(unittest.TestCase):
    def test_identity_requires_values_and_source_labels(self) -> None:
        contracts = _contracts()

        for missing in ("values", "source_labels"):
            with self.subTest(missing=missing):
                payload = _identity()
                del payload[missing]
                with self.assertRaises(contracts.PartnerContractError):
                    contracts.validate_identity(payload)

    def test_canonical_hash_is_stable_and_content_bound(self) -> None:
        contracts = _contracts()
        first = _identity()
        reordered = {key: copy.deepcopy(first[key]) for key in reversed(first)}

        first_validated = contracts.validate_identity(first)
        reordered_validated = contracts.validate_identity(reordered)

        self.assertEqual(first_validated["content_hash"], reordered_validated["content_hash"])
        self.assertEqual(
            first_validated["content_hash"],
            contracts.canonical_hash(_identity()),
        )
        changed = _identity()
        changed["name"] = "Different Partner"
        self.assertNotEqual(
            first_validated["content_hash"],
            contracts.validate_identity(changed)["content_hash"],
        )

    def test_configured_identity_and_inferred_preferences_keep_distinct_labels(self) -> None:
        contracts = _contracts()
        identity = contracts.validate_identity(_identity())
        snapshot = contracts.validate_wake_snapshot(_snapshot())

        self.assertTrue(
            all(item["source"] == "configured" for item in identity["voice_traits"])
        )
        self.assertEqual("inferred", snapshot["inferred_preferences"][0]["source"])
        self.assertEqual(identity["content_hash"], snapshot["identity"]["content_hash"])

        mislabeled = _snapshot()
        mislabeled["inferred_preferences"][0]["source"] = "configured"
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(mislabeled)

    def test_only_hash_bound_approved_amendments_overlay_identity(self) -> None:
        contracts = _contracts()
        base = contracts.validate_identity(_identity())
        amendment = {
            "schema_version": "1",
            "amendment_id": "amendment-001",
            "base_identity_hash": base["content_hash"],
            "changes": {
                "interests": [
                    {
                        "id": "music",
                        "value": "Singing and music experiments",
                        "source": "operator_approved",
                    }
                ]
            },
        }
        approval = {
            "schema_version": "1",
            "approval_id": "approval-001",
            "amendment_id": amendment["amendment_id"],
            "amendment_hash": contracts.canonical_hash(amendment),
            "approved": True,
        }

        overlaid = contracts.apply_identity_amendments(base, [amendment], [approval])

        self.assertEqual("configured", overlaid["interests"][0]["source"])
        self.assertEqual("operator_approved", overlaid["interests"][1]["source"])
        self.assertNotEqual(base["content_hash"], overlaid["content_hash"])

        for invalid_approvals in ([], [{**approval, "amendment_hash": "0" * 64}]):
            with self.subTest(approvals=invalid_approvals):
                with self.assertRaises(contracts.PartnerContractError):
                    contracts.apply_identity_amendments(base, [amendment], invalid_approvals)


class PartnerWakeSnapshotContractTests(unittest.TestCase):
    def test_snapshot_rejects_unknown_and_unbounded_fields(self) -> None:
        contracts = _contracts()
        unknown = _snapshot()
        unknown["transcripts"] = ["not an approved bounded input"]
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(unknown)

        too_many = _snapshot()
        too_many["goals"] = [
            {"id": f"goal-{index:03d}", "summary": "Bounded goal", "source_ref": f"goal:{index}"}
            for index in range(101)
        ]
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(too_many)

    def test_snapshot_rejects_raw_private_content_and_secret_like_values(self) -> None:
        contracts = _contracts()

        raw_private = _snapshot()
        raw_private["observations"][0]["raw_content"] = "private transcript body"
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(raw_private)

        secret = _snapshot()
        secret["observations"][0]["summary"] = "Captured token " + "gh" + "p_" + ("a" * 36)
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(secret)

    def test_snapshot_requires_observation_expiry_and_complete_maturity(self) -> None:
        contracts = _contracts()

        missing_expiry = _snapshot()
        missing_expiry["observations"][0].pop("expires_at")
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(missing_expiry)

        missing_completed_count = _snapshot()
        missing_completed_count["maturity"].pop("completed_episode_count")
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(missing_completed_count)

    def test_snapshot_requires_explicit_governor_budgets(self) -> None:
        contracts = _contracts()
        missing_budgets = _snapshot()
        missing_budgets.pop("budgets")

        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(missing_budgets)


class PartnerExecutorEnvelopeContractTests(unittest.TestCase):
    def test_envelope_requires_exact_hash_authority_and_run_contract_bindings(self) -> None:
        contracts = _contracts()
        from tests.test_partner_runtime import NOW, _candidate, _snapshot
        from supervisor.partner_runtime import decide_wake

        decision = decide_wake(
            _snapshot(approval=True),
            candidates=[_candidate()],
            now=NOW,
            health={"healthy": True, "reason_codes": []},
            busy=False,
            kill_switches=(),
        )
        envelope = decision["payload"]["executor_envelope"]
        self.assertEqual(envelope, contracts.validate_executor_envelope(envelope))

        cases = []
        bad_hash = copy.deepcopy(envelope)
        bad_hash["content_hash"] = "0" * 64
        cases.append(bad_hash)
        bad_contract_hash = copy.deepcopy(envelope)
        bad_contract_hash["run_contract_hash"] = "0" * 64
        bad_contract_hash["content_hash"] = contracts.canonical_hash(bad_contract_hash)
        cases.append(bad_contract_hash)
        high_risk = copy.deepcopy(envelope)
        high_risk["risk_level"] = "high"
        high_risk["content_hash"] = contracts.canonical_hash(high_risk)
        cases.append(high_risk)
        missing_binding = copy.deepcopy(envelope)
        del missing_binding["approval_binding"]
        missing_binding["content_hash"] = contracts.canonical_hash(missing_binding)
        cases.append(missing_binding)
        wrong_approval_subject = copy.deepcopy(envelope)
        wrong_approval_subject["approval_binding"]["subject_id"] = "different-proposal"
        wrong_approval_subject["approval_hash"] = contracts.canonical_hash(
            wrong_approval_subject["approval_binding"]
        )
        wrong_approval_subject["content_hash"] = contracts.canonical_hash(wrong_approval_subject)
        cases.append(wrong_approval_subject)
        wrong_approval_capabilities = copy.deepcopy(envelope)
        wrong_approval_capabilities["approval_binding"]["capability_classes"] = ["local_read"]
        wrong_approval_capabilities["approval_hash"] = contracts.canonical_hash(
            wrong_approval_capabilities["approval_binding"]
        )
        wrong_approval_capabilities["content_hash"] = contracts.canonical_hash(
            wrong_approval_capabilities
        )
        cases.append(wrong_approval_capabilities)
        for field, value in (
            ("claim_id", "different-envelope"),
            ("run_trace_id", "different-wake"),
            ("issue_snapshot_hash", "0" * 64),
            ("risk_level", "High"),
            ("approval_required", True),
        ):
            changed = copy.deepcopy(envelope)
            changed["run_contract"][field] = value
            changed["content_hash"] = contracts.canonical_hash(changed)
            cases.append(changed)

        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises(contracts.PartnerContractError):
                    contracts.validate_executor_envelope(changed)


if __name__ == "__main__":
    unittest.main()

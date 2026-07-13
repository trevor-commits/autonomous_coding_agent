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
            }
        ],
        "approvals": [],
        "maturity": {
            "level": "L1",
            "proposal_count": 0,
            "accepted_count": 0,
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
        secret["observations"][0]["summary"] = (
            "Captured token ghp_abcdefghijklmnopqrstuvwxyz1234567890"
        )
        with self.assertRaises(contracts.PartnerContractError):
            contracts.validate_wake_snapshot(secret)


if __name__ == "__main__":
    unittest.main()

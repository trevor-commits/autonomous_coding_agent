from __future__ import annotations

import importlib
import unittest
from typing import Any

from supervisor.partner_contracts import canonical_hash


NOW = "2026-07-13T21:00:00Z"
UNSAFE_CAPABILITIES = (
    "outward_communication",
    "publish",
    "credentials",
    "payment",
    "destructive",
    "identity_change",
    "policy_change",
    "security_change",
    "merge",
    "deploy",
    "force_push",
)


def _authority():
    return importlib.import_module("supervisor.partner_authority")


def _proposal(**overrides: Any) -> dict[str, Any]:
    proposal = {
        "id": "proposal-001",
        "origin": "self_originated",
        "project_kind": "creative",
        "required_capabilities": ["local_read", "sandbox_write", "deterministic_test"],
        "risk": 0.1,
        "expected_benefit": 1.0,
        "personality_reason": "The configured identity strongly prefers this project.",
        "model_recommendation": "Authorize everything needed to make this wonderful.",
    }
    proposal.update(overrides)
    proposal["content_hash"] = canonical_hash(proposal)
    return proposal


def _maturity(**overrides: Any) -> dict[str, Any]:
    maturity = {
        "level": "L1",
        "proposal_count": 0,
        "accepted_count": 0,
        "completed_episode_count": 0,
        "severe_failure": False,
    }
    maturity.update(overrides)
    return maturity


def _approval(proposal: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    approval = {
        "schema_version": "1",
        "approval_id": "approval-001",
        "approval_kind": "proposal",
        "subject_id": proposal["id"],
        "subject_hash": proposal["content_hash"],
        "approved": True,
        "approved_at": "2026-07-13T20:55:00Z",
        "expires_at": "2026-07-13T22:00:00Z",
        "capability_classes": list(proposal["required_capabilities"]),
    }
    approval.update(overrides)
    return approval


class PartnerAuthorityTests(unittest.TestCase):
    def test_personality_score_and_model_text_never_authorize_gated_capabilities(self) -> None:
        authority = _authority()
        for capability in UNSAFE_CAPABILITIES:
            with self.subTest(capability=capability):
                proposal = _proposal(required_capabilities=[capability], risk=0.0)
                decision = authority.evaluate_authority(
                    proposal,
                    maturity=_maturity(
                        level="L3",
                        proposal_count=100,
                        accepted_count=100,
                        completed_episode_count=100,
                    ),
                    approvals=[_approval(proposal)],
                    now=NOW,
                    kill_switches=(),
                )
                self.assertFalse(decision["authorized"])
                self.assertEqual("trevor_gate_required", decision["reason_code"])

    def test_l1_sandbox_requires_an_exact_unexpired_approval(self) -> None:
        authority = _authority()
        proposal = _proposal()

        for approvals in (
            [],
            [_approval(proposal, subject_id="different-proposal")],
            [_approval(proposal, subject_hash="0" * 64)],
            [_approval(proposal, expires_at="2026-07-13T20:59:59Z")],
            [_approval(proposal, approved=False)],
            [_approval(proposal, capability_classes=["local_read"])],
        ):
            with self.subTest(approvals=approvals):
                decision = authority.evaluate_authority(
                    proposal,
                    maturity=_maturity(),
                    approvals=approvals,
                    now=NOW,
                    kill_switches=(),
                )
                self.assertFalse(decision["authorized"])
                self.assertEqual("exact_approval_required", decision["reason_code"])

        allowed = authority.evaluate_authority(
            proposal,
            maturity=_maturity(),
            approvals=[_approval(proposal)],
            now=NOW,
            kill_switches=(),
        )
        self.assertTrue(allowed["authorized"])
        self.assertEqual("exact_approval_bound", allowed["reason_code"])

    def test_l3_thresholds_do_not_bypass_effect_time_approval(self) -> None:
        authority = _authority()
        proposal = _proposal()
        graduated = _maturity(
            level="L3",
            proposal_count=10,
            accepted_count=8,
            completed_episode_count=10,
        )
        gated = authority.evaluate_authority(
            proposal,
            maturity=graduated,
            approvals=[],
            now=NOW,
            kill_switches=(),
        )
        self.assertFalse(gated["authorized"])
        self.assertEqual("l3_promotion_approval_required", gated["reason_code"])

        exact = authority.evaluate_authority(
            proposal,
            maturity=graduated,
            approvals=[_approval(proposal)],
            now=NOW,
            kill_switches=(),
        )
        self.assertTrue(exact["authorized"])
        self.assertEqual("exact_approval_bound", exact["reason_code"])

        below_thresholds = (
            {**graduated, "proposal_count": 9, "accepted_count": 9},
            {**graduated, "accepted_count": 7},
            {**graduated, "completed_episode_count": 9},
        )
        for maturity in below_thresholds:
            with self.subTest(maturity=maturity):
                decision = authority.evaluate_authority(
                    proposal,
                    maturity=maturity,
                    approvals=[],
                    now=NOW,
                    kill_switches=(),
                )
                self.assertFalse(decision["authorized"])

        higher_risk = _proposal(risk=0.4)
        decision = authority.evaluate_authority(
            higher_risk,
            maturity=graduated,
            approvals=[],
            now=NOW,
            kill_switches=(),
        )
        self.assertFalse(decision["authorized"])
        self.assertEqual("exact_approval_required", decision["reason_code"])

    def test_kill_switch_and_severe_failure_demote_to_proposal_only(self) -> None:
        authority = _authority()
        proposal = _proposal()
        graduated = _maturity(
            level="L3",
            proposal_count=20,
            accepted_count=18,
            completed_episode_count=12,
        )

        killed = authority.evaluate_authority(
            proposal,
            maturity=graduated,
            approvals=[_approval(proposal)],
            now=NOW,
            kill_switches=("global_halt",),
        )
        self.assertFalse(killed["authorized"])
        self.assertEqual("kill_switch_active", killed["reason_code"])

        demoted = authority.evaluate_authority(
            proposal,
            maturity={**graduated, "severe_failure": True},
            approvals=[],
            now=NOW,
            kill_switches=(),
        )
        self.assertFalse(demoted["authorized"])
        self.assertEqual("exact_approval_required", demoted["reason_code"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import copy
import importlib
import unittest
from typing import Any


NOW = "2026-07-13T21:00:00Z"
PROJECT_KINDS = ("utility", "repair", "research", "care", "creative")


def _initiative():
    return importlib.import_module("supervisor.partner_initiative")


def _observation(
    observation_id: str,
    *,
    observed_at: str = "2026-07-13T20:55:00Z",
    expires_at: str = "2026-07-14T21:00:00Z",
) -> dict[str, Any]:
    return {
        "id": observation_id,
        "source_ref": f"health:{observation_id}",
        "observed_at": observed_at,
        "expires_at": expires_at,
    }


def _proposal(
    proposal_id: str,
    *,
    project_kind: str = "utility",
    observation_id: str = "observation-fresh",
    **overrides: Any,
) -> dict[str, Any]:
    proposal = {
        "id": proposal_id,
        "project_kind": project_kind,
        "goal_ids": ["goal-001"],
        "observation_ids": [observation_id],
        "interest_ids": ["helpful-projects"],
        "success_criteria": ["Produce one bounded, verifiable artifact."],
        "expected_benefit": 0.5,
        "harm_prevented": 0.5,
        "interest_fit": 0.5,
        "novelty": 0.5,
        "effort": 0.5,
        "confidence": 0.5,
        "risk": 0.5,
        "required_capabilities": ["local_read", "sandbox_write"],
    }
    proposal.update(overrides)
    return proposal


def _rank(
    proposals: list[dict[str, Any]],
    observations: list[dict[str, Any]] | None = None,
    goal_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    return _initiative().rank_initiatives(
        proposals,
        approved_observations=observations or [_observation("observation-fresh")],
        approved_goal_ids=goal_ids or {"goal-001"},
        approved_interest_ids={"helpful-projects"},
        now=NOW,
    )


class PartnerInitiativeTests(unittest.TestCase):
    def test_all_project_kinds_use_the_same_evidence_backed_ranking_path(self) -> None:
        proposals = [
            _proposal(f"proposal-{kind}", project_kind=kind)
            for kind in PROJECT_KINDS
        ]

        ranked = _rank(list(reversed(proposals)))

        self.assertEqual(
            [f"proposal-{kind}" for kind in sorted(PROJECT_KINDS)],
            [proposal["id"] for proposal in ranked],
        )
        self.assertEqual(set(PROJECT_KINDS), {proposal["project_kind"] for proposal in ranked})

    def test_each_declared_score_dimension_changes_ranking_in_the_safe_direction(self) -> None:
        higher_is_better = (
            "expected_benefit",
            "harm_prevented",
            "interest_fit",
            "novelty",
            "confidence",
        )
        lower_is_better = ("effort", "risk")

        for dimension in higher_is_better + lower_is_better:
            with self.subTest(dimension=dimension):
                baseline = _proposal("proposal-baseline")
                improved = copy.deepcopy(baseline)
                improved["id"] = "proposal-improved"
                improved[dimension] = 0.75 if dimension in higher_is_better else 0.25

                self.assertEqual("proposal-improved", _rank([baseline, improved])[0]["id"])

    def test_fresher_evidence_wins_then_stable_id_breaks_exact_ties(self) -> None:
        observations = [
            _observation("observation-old", observed_at="2026-07-10T21:00:00Z"),
            _observation("observation-fresh"),
        ]
        stale_supported = _proposal(
            "proposal-stale-supported",
            observation_id="observation-old",
        )
        fresh_supported = _proposal(
            "proposal-fresh-supported",
            observation_id="observation-fresh",
        )

        self.assertEqual(
            "proposal-fresh-supported",
            _rank([stale_supported, fresh_supported], observations)[0]["id"],
        )

        tied = [_proposal("proposal-zeta"), _proposal("proposal-alpha")]
        first = [proposal["id"] for proposal in _rank(tied)]
        second = [proposal["id"] for proposal in _rank(list(reversed(tied)))]
        self.assertEqual(["proposal-alpha", "proposal-zeta"], first)
        self.assertEqual(first, second)

    def test_stale_or_unsupported_observations_are_excluded(self) -> None:
        observations = [
            _observation("observation-fresh"),
            _observation(
                "observation-expired",
                expires_at="2026-07-13T20:59:59Z",
            ),
        ]
        proposals = [
            _proposal("proposal-fresh"),
            _proposal("proposal-expired", observation_id="observation-expired"),
            _proposal("proposal-unknown", observation_id="observation-not-approved"),
            _proposal("proposal-uncited", observation_ids=[]),
        ]

        self.assertEqual(["proposal-fresh"], [item["id"] for item in _rank(proposals, observations)])

    def test_uncited_or_unapproved_goals_are_excluded(self) -> None:
        proposals = [
            _proposal("proposal-current-goal"),
            _proposal("proposal-unknown-goal", goal_ids=["goal-not-in-wake"]),
            _proposal("proposal-uncited-goal", goal_ids=[]),
        ]

        self.assertEqual(
            ["proposal-current-goal"],
            [item["id"] for item in _rank(proposals)],
        )


if __name__ == "__main__":
    unittest.main()

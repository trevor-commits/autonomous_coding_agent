from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from test_partner_contracts import _identity
from test_partner_learning import NOW as LEARNING_NOW, _envelope, _outcome, _proposal
from test_partner_runtime import NOW, _candidate, _snapshot


def _cli():
    from supervisor import partner_cli

    return partner_cli


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload))
    return path


def _invoke(args: list[str]) -> tuple[int, dict, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    rc = _cli().main(args, stdout=stdout, stderr=stderr)
    output = json.loads(stdout.getvalue()) if stdout.getvalue().strip() else {}
    return rc, output, stderr.getvalue()


class PartnerCliTests(unittest.TestCase):
    def test_init_observe_and_status_emit_machine_readable_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            identity_path = _write(root / "identity.json", _identity())
            snapshot_path = _write(root / "snapshot.json", _snapshot())

            init_rc, initialized, _ = _invoke(["init", "--identity", str(identity_path)])
            observe_rc, observed, _ = _invoke(["observe", "--snapshot", str(snapshot_path)])
            status_rc, status, _ = _invoke(["status"])

            self.assertEqual(0, init_rc)
            self.assertEqual("Partner", initialized["name"])
            self.assertRegex(initialized["identity_hash"], r"^[0-9a-f]{64}$")
            self.assertEqual(0, observe_rc)
            self.assertEqual("observe_only", observed["mode"])
            self.assertEqual(1, observed["observation_count"])
            self.assertEqual(0, status_rc)
            self.assertEqual("stateless", status["storage"])

    def test_add_goal_and_approve_validate_file_bound_candidates_without_storing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            goal_path = _write(
                root / "goal.json",
                {"id": "goal-002", "summary": "Make one useful artifact", "source_ref": "operator:1"},
            )
            snapshot = _snapshot(approval=True)
            approval_path = _write(root / "approval.json", snapshot["approvals"][0])

            goal_rc, goal, _ = _invoke(["add-goal", "--goal-file", str(goal_path)])
            approval_rc, approval, _ = _invoke(
                ["approve", "--approval-file", str(approval_path)]
            )

            self.assertEqual(0, goal_rc)
            self.assertEqual("goal_candidate", goal["kind"])
            self.assertRegex(goal["content_hash"], r"^[0-9a-f]{64}$")
            self.assertEqual(0, approval_rc)
            self.assertEqual("approval-001", approval["approval_id"])
            self.assertFalse(goal.get("stored", True))
            self.assertFalse(approval.get("stored", True))

    def test_wake_defaults_observe_only_and_requires_explicit_mode_for_effectful_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshot_path = _write(root / "snapshot.json", _snapshot(approval=True))
            candidates_path = _write(root / "candidates.json", [_candidate()])
            health_path = _write(root / "health.json", {"healthy": True, "reason_codes": []})
            base = [
                "wake",
                "--snapshot",
                str(snapshot_path),
                "--candidates",
                str(candidates_path),
                "--health",
                str(health_path),
                "--now",
                NOW,
            ]

            observe_rc, observed, _ = _invoke(base)
            propose_rc, proposed, _ = _invoke([*base, "--mode", "propose"])
            execute_rc, execute, _ = _invoke([*base, "--mode", "execute"])

            self.assertEqual(0, observe_rc)
            self.assertEqual("no_op", observed["decision_type"])
            self.assertIn("observe_only", observed["reason_codes"])
            self.assertEqual(0, propose_rc)
            self.assertEqual("proposal", proposed["decision_type"])
            self.assertEqual(0, execute_rc)
            self.assertEqual("executor_envelope", execute["decision_type"])

    def test_reconcile_emits_candidates_and_never_promotes_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            outcome_path = _write(root / "outcome.json", _outcome())
            envelope_path = _write(root / "envelope.json", _envelope())
            proposal_path = _write(root / "proposal.json", _proposal())

            rc, result, _ = _invoke(
                [
                    "reconcile",
                    "--outcome",
                    str(outcome_path),
                    "--envelope",
                    str(envelope_path),
                    "--proposal",
                    str(proposal_path),
                    "--now",
                    LEARNING_NOW,
                ]
            )
            self.assertEqual(0, rc)
            self.assertIn("benefit_candidate", result)
            self.assertNotIn("identity", result)

    def test_errors_are_json_and_secret_values_are_never_accepted_or_echoed(self) -> None:
        rc, output, stderr = _invoke(["status", "--secret", "TOPSECRET_VALUE_123"])
        self.assertNotEqual(0, rc)
        self.assertEqual("secret_arguments_forbidden", output["error_code"])
        self.assertNotIn("TOPSECRET_VALUE_123", json.dumps(output) + stderr)


if __name__ == "__main__":
    unittest.main()

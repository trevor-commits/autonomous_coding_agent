import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import yaml

from supervisor.builder_adapter import BuilderAdapter, BuilderResult, BuilderSession
from supervisor.queue_intake import (
    BLOCKING_LABELS,
    LinearIssue,
    LinearIssueDescription,
    ManualQueueRunner,
    QueueIssueNormalizer,
    QueueIssueSelector,
    QueueLinearClient,
)
from supervisor.strategy_simple import SimpleStrategy


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_queue_repo(repo_root: Path, *, remote_path: Path | None = None) -> None:
    _git(repo_root, "init", "-b", "main")
    _git(repo_root, "config", "user.name", "Codex")
    _git(repo_root, "config", "user.email", "codex@example.com")
    (repo_root / ".agent").mkdir()
    (repo_root / "docs").mkdir()
    (repo_root / "scripts").mkdir()
    (repo_root / "src").mkdir()
    (repo_root / ".gitignore").write_text(".autoclaw/\nworktrees/\n")
    (repo_root / ".agent" / "contract.yml").write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "stack": "fullstack-web",
                "commands": {
                    "setup": "python3 scripts/setup.py",
                    "lint": "python3 scripts/lint.py",
                    "test": "python3 scripts/test.py",
                    "app_up": "python3 -m http.server 3000",
                    "app_health": "http://127.0.0.1:3000/health",
                },
            }
        )
    )
    (repo_root / "scripts" / "setup.py").write_text("print('setup ok')\n")
    (repo_root / "scripts" / "lint.py").write_text(
        "import sys\nsys.stderr.write('lint should not run in this test\\n')\nraise SystemExit(1)\n"
    )
    (repo_root / "scripts" / "test.py").write_text(
        "\n".join(
            [
                "from pathlib import Path",
                "target = Path('src/task.txt')",
                "value = target.read_text().strip() if target.exists() else ''",
                "if value == 'fixed':",
                "    print('tests passed')",
                "else:",
                "    print('tests failed')",
                "    raise SystemExit(1)",
            ]
        )
    )
    (repo_root / "docs" / "queue-spec.md").write_text("# Queue spec\n")
    (repo_root / "README.md").write_text("# queue repo\n")
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "init")
    if remote_path is not None:
        remote_path.mkdir(parents=True, exist_ok=True)
        _git(remote_path, "init", "--bare", "-b", "main")
        _git(repo_root, "remote", "add", "origin", str(remote_path))
        _git(repo_root, "push", "-u", "origin", "main")


def _description(
    *,
    spec_path: str = "docs/queue-spec.md",
    execution_lane: str = "Codex",
    execution_mode: str = "Queue",
    risk_level: str = "Low",
    approval_required: str = "No",
    allowed_paths: str | None = "`src/`, `tests/`",
    forbidden_paths: str | None = "`.env`, `infra/`",
    verification_pack: str | None = "`test`",
    retry_budget: str | None = None,
) -> str:
    lines = [
        f"**Authoritative spec path:** `{spec_path}`",
        "",
        "**Authoritative decision docs:** `QUEUE-RUNS.md`",
        "",
        "**Why this exists:** exercise the queue runner",
        "",
        "**Origin source:** automated test fixture",
        "",
        f"**Execution lane:** {execution_lane}",
        "",
        f"**Execution mode:** {execution_mode}",
        "",
        f"**Risk level:** {risk_level}",
        "",
        f"**Approval required:** {approval_required}",
    ]
    if allowed_paths is not None:
        lines.extend(["", f"**Allowed paths:** {allowed_paths}"])
    if forbidden_paths is not None:
        lines.extend(["", f"**Forbidden paths:** {forbidden_paths}"])
    if verification_pack is not None:
        lines.extend(["", f"**Verification pack:** {verification_pack}"])
    if retry_budget is not None:
        lines.extend(["", f"**Retry budget:** {retry_budget}"])
    return "\n".join(lines)


class RecordingLinearClient(QueueLinearClient):
    def __init__(self, issues: list[LinearIssue]) -> None:
        self.issues = {issue.identifier: issue for issue in issues}
        self.comments: list[tuple[str, str]] = []
        self.transitions: list[tuple[str, str]] = []
        self.get_issue_calls: list[str] = []
        self.live_overrides: dict[str, LinearIssue] = {}

    def list_ready_for_build(self, team_key: str) -> list[LinearIssue]:
        return list(self.issues.values())

    def transition_issue(self, issue_id: str, state_name: str) -> None:
        issue = self.issues[issue_id]
        self.issues[issue_id] = replace(issue, status=state_name)
        self.transitions.append((issue_id, state_name))

    def create_comment(self, issue_id: str, body: str) -> None:
        self.comments.append((issue_id, body))

    def get_issue(self, issue_id: str) -> LinearIssue:
        self.get_issue_calls.append(issue_id)
        if issue_id in self.live_overrides:
            return self.live_overrides[issue_id]
        return self.issues[issue_id]


class QueueAwareBuilderAdapter(BuilderAdapter):
    def __init__(self, plans: dict[str, tuple[str, ...]]) -> None:
        self.plans = plans

    def start_session(self, worktree_path: Path, run_context: dict) -> BuilderSession:
        return BuilderSession(worktree_path=Path(worktree_path), run_context=run_context, session_id="queue-test")

    def send_task(self, session: BuilderSession, prompt: str, timeout: int) -> BuilderResult:
        issue_id = str(session.run_context["objective"]).split(":", 1)[0]
        plan = self.plans[issue_id]
        turn = min(session.turn_count, len(plan) - 1)
        session.turn_count += 1
        target = session.worktree_path / "src" / "task.txt"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(plan[turn])
        return BuilderResult(
            session_id=session.session_id,
            status="completed",
            final_message="done",
            files_changed=("src/task.txt",),
            commands_run=tuple(),
            duration_seconds=0.01,
            raw_events=tuple(),
        )

    def close_session(self, session: BuilderSession) -> None:
        return None


class QueueSelectorTests(unittest.TestCase):
    def test_selector_returns_only_strictly_eligible_issues(self) -> None:
        eligible = LinearIssue(
            id="GIL-100",
            identifier="GIL-100",
            title="Eligible queue issue",
            description=_description(),
            status="Ready for Build",
            priority=3,
            updated_at="2026-04-17T01:00:00Z",
            labels=tuple(),
        )
        issues = [
            eligible,
            replace(eligible, id="GIL-101", identifier="GIL-101", updated_at="2026-04-17T02:00:00Z"),
            replace(eligible, id="GIL-102", identifier="GIL-102", description=_description(execution_mode="Manual")),
            replace(eligible, id="GIL-103", identifier="GIL-103", description=_description(execution_lane="Claude Code")),
            replace(eligible, id="GIL-104", identifier="GIL-104", description=_description(risk_level="High")),
            replace(eligible, id="GIL-105", identifier="GIL-105", description=_description(approval_required="Yes")),
            replace(eligible, id="GIL-106", identifier="GIL-106", labels=(BLOCKING_LABELS[0],)),
            replace(eligible, id="GIL-107", identifier="GIL-107", labels=(BLOCKING_LABELS[1],)),
            replace(eligible, id="GIL-108", identifier="GIL-108", status="Building"),
        ]

        selected = QueueIssueSelector().eligible_issues(issues)

        self.assertEqual(["GIL-100", "GIL-101"], [issue.identifier for issue in selected])


class QueueNormalizerTests(unittest.TestCase):
    def test_normalizer_writes_real_run_contract_from_issue_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            _init_queue_repo(repo_root)
            issue = LinearIssue(
                id="GIL-200",
                identifier="GIL-200",
                title="Normalize queue issue",
                description=_description(verification_pack="`lint`, `test`", retry_budget="3"),
                status="Ready for Build",
                priority=2,
                updated_at="2026-04-17T03:00:00Z",
                labels=tuple(),
            )

            normalized = QueueIssueNormalizer(repo_root).normalize(issue)

            self.assertTrue(normalized.spec_path.exists())
            self.assertEqual(("src", "tests"), normalized.run_contract.scope.allowed_paths)
            self.assertEqual(("env", "infra"), normalized.run_contract.scope.forbidden_paths)
            self.assertEqual(("lint", "test"), normalized.run_contract.queue.verification_pack)
            self.assertEqual(3, normalized.run_contract.constraints.max_repair_loops)
            self.assertEqual(3, normalized.run_contract.queue.retry_budget)
            payload = json.loads(normalized.run_contract_path.read_text())
            self.assertEqual(["lint", "test"], payload["verification_pack"])
            self.assertTrue(payload["run_id"].startswith("GIL-200-"))


class QueueDrainRunnerTests(unittest.TestCase):
    def test_manual_drain_claims_runs_and_releases_issues_sequentially(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo_root = root / "repo"
            repo_root.mkdir()
            remote_root = root / "remote.git"
            _init_queue_repo(repo_root, remote_path=remote_root)
            issues = [
                LinearIssue(
                    id="GIL-300",
                    identifier="GIL-300",
                    title="Land the first queue issue",
                    description=_description(verification_pack="`test`", retry_budget="2"),
                    status="Ready for Build",
                    priority=2,
                    updated_at="2026-04-17T01:00:00Z",
                    labels=tuple(),
                ),
                LinearIssue(
                    id="GIL-301",
                    identifier="GIL-301",
                    title="Block on repeated verification failure",
                    description=_description(verification_pack="`test`", retry_budget="1"),
                    status="Ready for Build",
                    priority=3,
                    updated_at="2026-04-17T02:00:00Z",
                    labels=tuple(),
                ),
                LinearIssue(
                    id="GIL-302",
                    identifier="GIL-302",
                    title="Skip a manual issue",
                    description=_description(execution_mode="Manual"),
                    status="Ready for Build",
                    priority=1,
                    updated_at="2026-04-17T00:00:00Z",
                    labels=tuple(),
                ),
            ]
            client = RecordingLinearClient(issues)
            adapter = QueueAwareBuilderAdapter(
                {
                    "GIL-300": ("fixed",),
                    "GIL-301": ("broken",),
                }
            )

            summary = ManualQueueRunner(
                repo_root=repo_root,
                linear_client=client,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                team_key="GIL",
            ).drain()

            self.assertEqual(2, summary.processed_count)
            self.assertEqual(1, summary.completed_count)
            self.assertEqual(1, summary.blocked_count)
            self.assertEqual(
                [
                    ("GIL-300", "Building"),
                    ("GIL-300", "AI Audit"),
                    ("GIL-301", "Building"),
                    ("GIL-301", "Blocked"),
                ],
                client.transitions,
            )
            self.assertEqual("Ready for Build", client.issues["GIL-302"].status)
            self.assertEqual(4, len(client.comments))
            self.assertTrue(any("Landings:" in body for issue_id, body in client.comments if issue_id == "GIL-300"))
            self.assertTrue(any("Blocker:" in body for issue_id, body in client.comments if issue_id == "GIL-301"))
            self.assertFalse(any(path.name.endswith(".json") for path in (repo_root / ".autoclaw" / "queue-claims").glob("*.json")))

            log = _git(repo_root, "log", "--oneline", "-1").stdout
            self.assertIn("GIL-300", log)
            self.assertNotIn("GIL-301", log)

            remote_log = _git(remote_root, "log", "--oneline", "-1", "main").stdout
            self.assertIn("GIL-300", remote_log)

    def test_drain_blocks_when_live_snapshot_drifts_from_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo_root = root / "repo"
            repo_root.mkdir()
            remote_root = root / "remote.git"
            _init_queue_repo(repo_root, remote_path=remote_root)
            issue = LinearIssue(
                id="GIL-400",
                identifier="GIL-400",
                title="Drift during execution",
                description=_description(verification_pack="`test`", retry_budget="2"),
                status="Ready for Build",
                priority=2,
                updated_at="2026-04-17T01:00:00Z",
                labels=tuple(),
            )
            client = RecordingLinearClient([issue])
            client.live_overrides["GIL-400"] = replace(
                issue,
                description=issue.description + "\n\n**Extra:** drifted",
            )
            adapter = QueueAwareBuilderAdapter({"GIL-400": ("fixed",)})

            summary = ManualQueueRunner(
                repo_root=repo_root,
                linear_client=client,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                team_key="GIL",
            ).drain()

            self.assertEqual(1, summary.processed_count)
            self.assertEqual(0, summary.completed_count)
            self.assertEqual(1, summary.blocked_count)
            self.assertEqual(
                [("GIL-400", "Building"), ("GIL-400", "Blocked")],
                client.transitions,
            )
            self.assertFalse(
                any("AI Audit" in state for _issue_id, state in client.transitions)
            )
            blocker_comments = [body for _issue_id, body in client.comments if body.startswith("Blocker:")]
            self.assertTrue(blocker_comments)
            self.assertIn("snapshot drifted", blocker_comments[0])
            remote_log = _git(remote_root, "log", "--oneline", "main").stdout
            self.assertNotIn("GIL-400", remote_log)

    def test_drain_blocks_when_landing_push_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            repo_root = root / "repo"
            repo_root.mkdir()
            _init_queue_repo(repo_root)
            _git(repo_root, "remote", "add", "origin", str(root / "does-not-exist.git"))
            issue = LinearIssue(
                id="GIL-500",
                identifier="GIL-500",
                title="Push to unreachable remote",
                description=_description(verification_pack="`test`", retry_budget="2"),
                status="Ready for Build",
                priority=2,
                updated_at="2026-04-17T01:00:00Z",
                labels=tuple(),
            )
            client = RecordingLinearClient([issue])
            adapter = QueueAwareBuilderAdapter({"GIL-500": ("fixed",)})

            summary = ManualQueueRunner(
                repo_root=repo_root,
                linear_client=client,
                builder_adapter=adapter,
                strategy=SimpleStrategy(),
                team_key="GIL",
            ).drain()

            self.assertEqual(1, summary.processed_count)
            self.assertEqual(0, summary.completed_count)
            self.assertEqual(1, summary.blocked_count)
            self.assertEqual(
                [("GIL-500", "Building"), ("GIL-500", "Blocked")],
                client.transitions,
            )
            self.assertFalse(
                any("AI Audit" in state for _issue_id, state in client.transitions)
            )
            self.assertFalse(
                any(body.startswith("Implemented and advanced") for _issue_id, body in client.comments)
            )
            blocker_comments = [body for _issue_id, body in client.comments if body.startswith("Blocker:")]
            self.assertTrue(blocker_comments)
            self.assertIn("push", blocker_comments[0].lower())


if __name__ == "__main__":
    unittest.main()

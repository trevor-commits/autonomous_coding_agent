import socket
import tempfile
import time
import unittest
from pathlib import Path

import subprocess

from supervisor.app_supervisor import AppSession, AppSupervisor
from supervisor.contracts import (
    QueueMetadata,
    RepoCommands,
    RepoContract,
    RepoEnvConfig,
    RepoUIConfig,
    RunAcceptance,
    RunConstraints,
    RunContract,
    RunScope,
)
from supervisor.run_store import RunStore


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _make_run_contract(repo_root: Path) -> RunContract:
    return RunContract(
        run_id="run-app-supervisor",
        repo_path=str(repo_root),
        objective="Launch app and check health",
        scope=RunScope(allowed_paths=("src", "tests", "scripts"), forbidden_paths=(".env",)),
        acceptance=RunAcceptance(
            functional=("app becomes healthy",),
            quality_gates=("tests pass",),
            ui_checks=("home page renders",),
        ),
        constraints=RunConstraints(
            single_writer=True,
            max_repair_loops=2,
            max_iterations=5,
            max_cost_dollars=5.0,
            hard_timeout_seconds=300,
        ),
        queue=QueueMetadata(
            claim_id="claim-app-123",
            run_trace_id="trace-app-123",
            queue_entry_reason="Ready for Build queue claim",
        ),
    )


class AppSupervisorTests(unittest.TestCase):
    def test_launch_starts_app_and_waits_for_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            scripts_dir = repo_root / "scripts"
            scripts_dir.mkdir()
            port = _free_port()
            server_script = scripts_dir / "server.py"
            server_script.write_text(
                "\n".join(
                    [
                        "from http.server import BaseHTTPRequestHandler, HTTPServer",
                        "class Handler(BaseHTTPRequestHandler):",
                        "    def do_GET(self):",
                        "        if self.path == '/health':",
                        "            self.send_response(200)",
                        "            self.end_headers()",
                        "            self.wfile.write(b'ok')",
                        "            return",
                        "        self.send_response(404)",
                        "        self.end_headers()",
                        "    def log_message(self, *_args):",
                        "        return",
                        f"HTTPServer(('127.0.0.1', {port}), Handler).serve_forever()",
                    ]
                )
            )
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up=f"python3 {server_script}",
                    app_health=f"http://127.0.0.1:{port}/health",
                    ui_smoke="python3 -c \"print('ui ok')\"",
                ),
                ui=RepoUIConfig(base_url=f"http://127.0.0.1:{port}"),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            supervisor = AppSupervisor(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-app-123",
                health_timeout_seconds=3.0,
                poll_interval_seconds=0.05,
            )
            launch = supervisor.launch()

            self.assertTrue(launch.healthy)
            self.assertIsNotNone(launch.session)
            self.assertEqual(("app_up", "app_health"), tuple(result.name for result in launch.command_results))
            self.assertEqual(0, launch.command_results[-1].exit_code)
            self.assertIn("artifacts/logs/app_up.stdout.log", launch.artifact_manifest)
            self.assertTrue((run_store.logs_dir / "app_up.stdout.log").exists())

            supervisor.stop(launch.session)
            deadline = time.time() + 3.0
            while launch.session.process.poll() is None and time.time() < deadline:
                time.sleep(0.05)
            self.assertIsNotNone(launch.session.process.poll())

    def test_stop_runs_app_down_command_before_fallback_shutdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            marker_path = repo_root / "app-down-ran.txt"
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up="python3 -c \"import time; time.sleep(30)\"",
                    app_health=f"http://127.0.0.1:{_free_port()}/health",
                    app_down=(
                        "python3 -c \"from pathlib import Path; "
                        f"Path(r'{marker_path}').write_text('stopped', encoding='utf-8')\""
                    ),
                    ui_smoke="python3 -c \"print('ui ok')\"",
                ),
                ui=RepoUIConfig(base_url="http://127.0.0.1:3000"),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            supervisor = AppSupervisor(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-app-123",
                health_timeout_seconds=0.1,
                poll_interval_seconds=0.05,
            )
            process = subprocess.Popen(
                repo_contract.commands.app_up,
                cwd=repo_root,
                shell=True,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            session = AppSession(
                process=process,
                health_url=repo_contract.commands.app_health,
                stdout_log_path=run_store.logs_dir / "app_up.stdout.log",
                stderr_log_path=run_store.logs_dir / "app_up.stderr.log",
            )

            supervisor.stop(session)

            self.assertTrue(marker_path.exists())
            deadline = time.time() + 3.0
            while session.process.poll() is None and time.time() < deadline:
                time.sleep(0.05)
            self.assertIsNotNone(session.process.poll())

    def test_launch_failure_records_health_fingerprint_and_stops_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up="python3 -c \"import time; print('booting'); time.sleep(30)\"",
                    app_health=f"http://127.0.0.1:{_free_port()}/health",
                    ui_smoke="python3 -c \"print('ui ok')\"",
                ),
                ui=RepoUIConfig(base_url="http://127.0.0.1:3000"),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            supervisor = AppSupervisor(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-app-123",
                health_timeout_seconds=0.3,
                poll_interval_seconds=0.05,
            )
            launch = supervisor.launch()

            self.assertFalse(launch.healthy)
            self.assertIsNone(launch.session)
            self.assertTrue(launch.failure_fingerprint)
            self.assertIn("app-launch-app-health", launch.failure_fingerprint)
            self.assertEqual(1, launch.command_results[-1].exit_code)
            self.assertTrue((run_store.reports_dir / "failure-fingerprints.json").exists())

    def test_launch_failure_records_actual_app_up_exit_code_when_process_crashes_early(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            repo_contract = RepoContract(
                version=1,
                stack="fullstack-web",
                commands=RepoCommands(
                    setup="python3 -c \"print('setup ok')\"",
                    test="python3 -c \"print('tests ok')\"",
                    app_up="python3 -c \"raise SystemExit(7)\"",
                    app_health=f"http://127.0.0.1:{_free_port()}/health",
                    ui_smoke="python3 -c \"print('ui ok')\"",
                ),
                ui=RepoUIConfig(base_url="http://127.0.0.1:3000"),
                env=RepoEnvConfig(),
            )
            run_contract = _make_run_contract(repo_root)
            run_store = RunStore(repo_root, run_contract.run_id)
            run_store.initialize(repo_contract=repo_contract, run_contract=run_contract)

            supervisor = AppSupervisor(
                repo_root=repo_root,
                repo_contract=repo_contract,
                run_contract=run_contract,
                run_store=run_store,
                run_trace_id="trace-app-123",
                health_timeout_seconds=0.3,
                poll_interval_seconds=0.05,
            )
            launch = supervisor.launch()

            self.assertFalse(launch.healthy)
            self.assertEqual(7, launch.command_results[0].exit_code)
            self.assertGreater(launch.command_results[0].duration_seconds, 0.0)
            self.assertIn("exited before health check", launch.command_results[0].stderr)


if __name__ == "__main__":
    unittest.main()

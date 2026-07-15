from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import call, patch

from supervisor import process_runner
from supervisor.process_runner import run_child_sandbox_process_group, run_process_group


class ProcessRunnerTests(unittest.TestCase):
    def test_capture_preserves_exact_output_at_documented_cap(self) -> None:
        capture = process_runner._BoundedCapture(process_runner._MAX_ERROR_OUTPUT)
        capture.start()
        payload = b"x" * process_runner._MAX_ERROR_OUTPUT
        os.write(capture.write_fd, payload)
        capture.finish()

        self.assertEqual(len(payload), len(capture.text().encode()))
        self.assertEqual(payload.decode(), capture.text())

    def test_success_output_is_bounded(self) -> None:
        command = "import sys; sys.stdout.write('x' * 1_100_000)"

        completed = run_process_group(
            [sys.executable, "-c", command],
            capture_output=True,
            text=True,
            timeout=5,
        )

        self.assertEqual(0, completed.returncode)
        self.assertLessEqual(len(completed.stdout), 1_000_000)
        self.assertIn("subprocess output truncated", completed.stdout)

    def test_success_capture_storage_is_bounded_while_child_is_writing(self) -> None:
        captures: list[process_runner._BoundedCapture] = []
        capture_type = process_runner._BoundedCapture

        class TrackingCapture(capture_type):
            def __init__(self, limit: int) -> None:
                super().__init__(limit)
                captures.append(self)

        command = (
            "import sys, time; "
            "[(sys.stdout.buffer.write(b'x' * 65536), "
            "sys.stdout.buffer.flush(), time.sleep(0.002)) for _ in range(192)]"
        )
        observed_over_limit_total = False
        with (
            patch("supervisor.process_runner._BoundedCapture", TrackingCapture),
            ThreadPoolExecutor(max_workers=1) as executor,
        ):
            future = executor.submit(
                run_process_group,
                [sys.executable, "-c", command],
                capture_output=True,
                text=True,
                timeout=5,
            )
            while not future.done():
                for capture in captures:
                    self.assertLessEqual(
                        capture.stored_bytes, process_runner._MAX_ERROR_OUTPUT
                    )
                    observed_over_limit_total = (
                        observed_over_limit_total
                        or capture.total_bytes > process_runner._MAX_ERROR_OUTPUT
                    )
                time.sleep(0.005)
            completed = future.result()

        self.assertEqual(0, completed.returncode)
        self.assertTrue(observed_over_limit_total)
        self.assertTrue(captures)
        for capture in captures:
            self.assertLessEqual(
                capture.peak_stored_bytes, process_runner._MAX_ERROR_OUTPUT
            )

    def test_timeout_output_is_bounded(self) -> None:
        command = (
            "import sys, time; "
            "sys.stdout.write('x' * 1_100_000); sys.stdout.flush(); time.sleep(30)"
        )

        with self.assertRaises(subprocess.TimeoutExpired) as raised:
            run_process_group(
                [sys.executable, "-c", command],
                capture_output=True,
                text=True,
                timeout=0.3,
            )

        self.assertLessEqual(len(raised.exception.stdout), 1_000_000)
        self.assertIn("subprocess output truncated", raised.exception.stdout)

    def test_signaling_skips_a_reused_process_identity(self) -> None:
        with (
            patch(
                "supervisor.process_runner._process_start_identity",
                return_value="replacement-process",
            ),
            patch("supervisor.process_runner.os.kill") as kill,
        ):
            process_runner._signal_processes(
                {123: "original-process"}, signal.SIGKILL
            )

        kill.assert_not_called()

    def test_freeze_does_not_signal_a_reused_root_process_group(self) -> None:
        with (
            patch(
                "supervisor.process_runner._process_start_identity",
                return_value="replacement-process",
            ),
            patch("supervisor.process_runner.os.killpg") as kill_group,
        ):
            owned = process_runner._freeze_process_tree(
                123, {123: "original-process"}
            )

        self.assertEqual({}, owned)
        kill_group.assert_not_called()

    def test_supplemental_sandbox_profile_keeps_containment_rules_last(self) -> None:
        tag = process_runner._SandboxContainmentTag(
            Path("/tmp/test-containment-tag"),
            Path("/tmp/test-containment-tag/denied"),
            Path("/tmp/test-containment-tag/allowed"),
        )

        profile = process_runner._compose_sandbox_profile(
            tag,
            "(version 1)\n(allow default)\n(deny network*)\n",
        )

        self.assertEqual(1, profile.count("(version 1)"))
        self.assertLess(profile.index("(deny network*)"), profile.index(tag.rules))

    def test_supplemental_sandbox_profile_rejects_missing_version(self) -> None:
        tag = process_runner._SandboxContainmentTag(
            Path("/tmp/test-containment-tag"),
            Path("/tmp/test-containment-tag/denied"),
            Path("/tmp/test-containment-tag/allowed"),
        )

        with self.assertRaises(process_runner.ProcessContainmentError):
            process_runner._compose_sandbox_profile(tag, "(allow default)\n")

    @unittest.skipUnless(
        sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file(),
        "nested-sandbox compatibility is a macOS boundary",
    )
    def test_explicit_tag_disable_allows_a_child_owned_sandbox(self) -> None:
        completed = run_child_sandbox_process_group(
            [
                "/usr/bin/sandbox-exec",
                "-p",
                "(version 1)\n(allow default)\n",
                "/usr/bin/true",
            ],
            capture_output=True,
            text=True,
            timeout=3,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)

    @unittest.skipUnless(
        sys.platform == "darwin",
        "sandbox scanner is a macOS containment surface",
    )
    def test_sandbox_scanner_failure_is_not_an_empty_inventory(self) -> None:
        tag = process_runner._SandboxContainmentTag(
            Path("/tmp/test-containment-tag"),
            Path("/tmp/test-containment-tag/denied"),
            Path("/tmp/test-containment-tag/allowed"),
        )
        with (
            patch(
                "supervisor.process_runner.subprocess.run",
                side_effect=subprocess.TimeoutExpired("ps", 0.5),
            ),
            self.assertRaises(process_runner.ProcessContainmentError),
        ):
            process_runner._sandbox_tagged_processes(tag)

    def test_discovery_failure_kills_known_tree_and_retains_sandbox_tag(self) -> None:
        class Process:
            pid = 123

            def communicate(self, timeout=None):
                return "", ""

            def wait(self, timeout=None):
                return 0

        class Lease:
            root_identity = "root-identity"
            removed = False

            def snapshot(self):
                return {123: self.root_identity}

            def stop(self):
                return None

            def tagged_processes(self):
                raise process_runner.ProcessContainmentError(
                    "scanner unavailable"
                )

            def remove_sandbox_tag(self):
                self.removed = True

        lease = Lease()
        with (
            patch(
                "supervisor.process_runner._freeze_process_tree",
                return_value={123: "root-identity"},
            ),
            patch("supervisor.process_runner._signal_process_group"),
            patch("supervisor.process_runner._signal_processes") as signal_processes,
            self.assertRaises(RuntimeError),
        ):
            process_runner._stop_process_group(Process(), lease)

        self.assertFalse(lease.removed)
        self.assertIn(
            call({123: "root-identity"}, signal.SIGKILL),
            signal_processes.call_args_list,
        )

    def test_cleanup_refuses_success_while_a_tagged_survivor_remains(self) -> None:
        class Process:
            pid = 123

            def communicate(self, timeout=None):
                return "", ""

            def wait(self, timeout=None):
                return 0

        class Lease:
            root_identity = "root-identity"
            removed = False

            def snapshot(self):
                return {123: self.root_identity}

            def stop(self):
                return None

            def tagged_processes(self):
                return {456: "survivor-identity"}

            def remove_sandbox_tag(self):
                self.removed = True

        lease = Lease()
        with (
            patch(
                "supervisor.process_runner._freeze_process_tree",
                return_value={123: "root-identity"},
            ),
            patch(
                "supervisor.process_runner._process_start_identity",
                return_value="survivor-identity",
            ),
            patch("supervisor.process_runner._signal_process_group"),
            patch("supervisor.process_runner._signal_processes"),
            self.assertRaises(RuntimeError),
        ):
            process_runner._stop_process_group(Process(), lease)

        self.assertFalse(lease.removed)

    def test_cleanup_requires_two_actual_post_kill_clean_scans(self) -> None:
        class Process:
            pid = 123

            def communicate(self, timeout=None):
                return "", ""

            def wait(self, timeout=None):
                return 0

        class Lease:
            root_identity = "root-identity"
            removed = False
            tagged_scan_count = 0

            def snapshot(self):
                return {123: self.root_identity}

            def stop(self):
                return None

            def tagged_processes(self):
                self.tagged_scan_count += 1
                return {}

            def remove_sandbox_tag(self):
                self.removed = True

        lease = Lease()
        with (
            patch(
                "supervisor.process_runner._freeze_process_tree",
                return_value={123: "root-identity"},
            ),
            patch("supervisor.process_runner._signal_process_group"),
            patch("supervisor.process_runner._signal_processes"),
            patch("supervisor.process_runner.threading.Event.wait"),
            patch(
                "supervisor.process_runner.time.monotonic",
                side_effect=[0.0, 0.0, 4.0],
            ),
            self.assertRaises(process_runner.ProcessContainmentError) as raised,
        ):
            process_runner._stop_process_group(Process(), lease)

        self.assertEqual(3, lease.tagged_scan_count)
        self.assertFalse(lease.removed)
        self.assertIn("two consecutive empty scans", str(raised.exception))

    def test_interruption_stops_and_reaps_the_process_group(self) -> None:
        class InterruptedProcess:
            pid = 123
            returncode = -signal.SIGTERM
            stdout = None
            stderr = None
            calls = 0

            def communicate(self, timeout=None):
                self.calls += 1
                if self.calls == 1:
                    raise KeyboardInterrupt
                return "", ""

        process = InterruptedProcess()
        with patch(
            "supervisor.process_runner._process_start_identity",
            return_value="test-identity",
        ):
            lease = process_runner._ProcessTreeLease(process.pid, "test-token")
        lease._owned = {123: "test-identity"}
        with (
            patch(
                "supervisor.process_runner._spawn_with_process_tree_lease",
                return_value=(process, lease),
            ),
            patch(
                "supervisor.process_runner._process_start_identity",
                return_value="test-identity",
            ),
            patch("supervisor.process_runner._process_tree", return_value={123}),
            patch("supervisor.process_runner._signal_process_group") as signal_group,
            patch("supervisor.process_runner._signal_processes") as signal_processes,
            patch.object(lease, "stop"),
            patch.object(lease, "tagged_processes", return_value={}),
            self.assertRaises(KeyboardInterrupt),
        ):
            run_process_group(["ignored"], capture_output=True, text=True)

        self.assertEqual(
            [
                call(
                    123,
                    signal.SIGSTOP,
                    expected_identity="test-identity",
                ),
                call(
                    123,
                    signal.SIGSTOP,
                    expected_identity="test-identity",
                ),
                call(
                    123,
                    signal.SIGTERM,
                    expected_identity="test-identity",
                ),
                call(
                    123,
                    signal.SIGKILL,
                    expected_identity="test-identity",
                ),
            ],
            signal_group.call_args_list,
        )
        self.assertEqual(
            [
                call({123: "test-identity"}, signal.SIGSTOP),
                call({123: "test-identity"}, signal.SIGSTOP),
                call({123: "test-identity"}, signal.SIGTERM),
                call({123: "test-identity"}, signal.SIGKILL),
            ],
            signal_processes.call_args_list,
        )
        self.assertEqual(2, process.calls)

    def test_success_reaps_descendant_that_detaches_before_parent_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            started = root / "started"
            residue = root / "residue"
            pid_file = root / "child.pid"
            child = (
                "import os, signal, time; "
                "os.setsid(); "
                f"open({str(pid_file)!r}, 'w').write(str(os.getpid())); "
                f"open({str(started)!r}, 'w').write('started'); "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "time.sleep(1); "
                f"open({str(residue)!r}, 'w').write('late')"
            )
            parent = (
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}], "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                f"started={str(started)!r}; "
                "deadline=time.monotonic()+1; "
                "\nwhile not __import__('os').path.exists(started) "
                "and time.monotonic()<deadline: time.sleep(.005)"
            )

            completed = run_process_group(
                [sys.executable, "-c", parent],
                capture_output=True,
                text=True,
                timeout=3,
            )

            self.assertEqual(0, completed.returncode)
            self.assertTrue(started.exists())
            time.sleep(1.2)
            self.assertFalse(residue.exists())
            child_pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    def test_success_reaps_immediate_background_child_without_handshake(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pid_file = root / "child.pid"
            residue = root / "late.txt"
            child = (
                "import os, time; "
                "os.setsid(); time.sleep(.3); "
                f"open({str(residue)!r}, 'w').write('late')"
            )
            parent = (
                "import subprocess, sys; "
                f"child=subprocess.Popen([sys.executable, '-c', {child!r}], "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                f"open({str(pid_file)!r}, 'w').write(str(child.pid))"
            )

            completed = run_process_group(
                [sys.executable, "-c", parent],
                capture_output=True,
                text=True,
                timeout=3,
            )

            self.assertEqual(0, completed.returncode)
            child_pid = int(pid_file.read_text())
            time.sleep(.4)
            self.assertFalse(residue.exists())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    @unittest.skipUnless(
        sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file(),
        "immutable policy-tag containment requires macOS sandbox-exec",
    )
    def test_success_reaps_immediate_detach_after_child_removes_env_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pid_file = root / "child.pid"
            release = root / "release"
            residue = root / "late.txt"
            child = (
                "import os, time\n"
                "os.environ.pop('CODEX_PROCESS_TREE_LEASE', None)\n"
                "os.setsid()\n"
                f"release={str(release)!r}\n"
                "deadline=time.monotonic()+5\n"
                "while not os.path.exists(release) and time.monotonic()<deadline:\n"
                "    time.sleep(.002)\n"
                "if os.path.exists(release):\n"
                f"    open({str(residue)!r}, 'w').write('late')\n"
            )
            parent = (
                "import os, subprocess, sys; "
                "env=dict(os.environ); "
                "env.pop('CODEX_PROCESS_TREE_LEASE', None); "
                f"child=subprocess.Popen([sys.executable, '-c', {child!r}], env=env, "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                f"open({str(pid_file)!r}, 'w').write(str(child.pid))"
            )

            with (
                patch(
                    "supervisor.process_runner._process_tree",
                    side_effect=lambda root_pid, seeds=None: (
                        set(seeds) if seeds is not None else {root_pid}
                    ),
                ),
                patch(
                    "supervisor.process_runner._tagged_lease_processes",
                    side_effect=lambda token: {},
                ),
            ):
                completed = run_process_group(
                    [sys.executable, "-c", parent],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

            self.assertEqual(0, completed.returncode)
            child_pid = int(pid_file.read_text())
            release.write_text("release")
            time.sleep(.2)
            self.assertFalse(residue.exists())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    @unittest.skipUnless(
        sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file(),
        "immutable policy-tag containment requires macOS sandbox-exec",
    )
    def test_timeout_reaps_detached_child_after_env_tag_removal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pid_file = root / "child.pid"
            release = root / "release"
            residue = root / "late.txt"
            child = (
                "import os, time\n"
                "os.environ.pop('CODEX_PROCESS_TREE_LEASE', None)\n"
                "os.setsid()\n"
                f"release={str(release)!r}\n"
                "deadline=time.monotonic()+5\n"
                "while not os.path.exists(release) and time.monotonic()<deadline:\n"
                "    time.sleep(.002)\n"
                "if os.path.exists(release):\n"
                f"    open({str(residue)!r}, 'w').write('late')\n"
            )
            parent = (
                "import os, subprocess, sys, time; "
                "env=dict(os.environ); "
                "env.pop('CODEX_PROCESS_TREE_LEASE', None); "
                f"child=subprocess.Popen([sys.executable, '-c', {child!r}], env=env, "
                "stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); "
                f"open({str(pid_file)!r}, 'w').write(str(child.pid)); "
                "time.sleep(30)"
            )

            with (
                patch(
                    "supervisor.process_runner._process_tree",
                    side_effect=lambda root_pid, seeds=None: (
                        set(seeds) if seeds is not None else {root_pid}
                    ),
                ),
                patch(
                    "supervisor.process_runner._tagged_lease_processes",
                    side_effect=lambda token: {},
                ),
                self.assertRaises(subprocess.TimeoutExpired),
            ):
                run_process_group(
                    [sys.executable, "-c", parent],
                    capture_output=True,
                    text=True,
                    timeout=0.3,
                )

            child_pid = int(pid_file.read_text())
            release.write_text("release")
            time.sleep(.2)
            self.assertFalse(residue.exists())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    @unittest.skipUnless(
        os.environ.get("PROCESS_CONTAINMENT_STRESS") == "1",
        "set PROCESS_CONTAINMENT_STRESS=1 for the 100-run containment gate",
    )
    def test_tag_only_containment_stress_100_runs(self) -> None:
        for _ in range(100):
            self.test_success_reaps_immediate_detach_after_child_removes_env_tag()

    def test_timeout_kills_descendant_that_escapes_the_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            started = root / "started"
            residue = root / "residue"
            pid_file = root / "child.pid"
            child = (
                "import os, signal, time; "
                "os.setsid(); "
                f"open({str(pid_file)!r}, 'w').write(str(os.getpid())); "
                f"open({str(started)!r}, 'w').write('started'); "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                "time.sleep(3); "
                f"open({str(residue)!r}, 'w').write('late')"
            )
            parent = (
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
                "time.sleep(30)"
            )

            with self.assertRaises(subprocess.TimeoutExpired):
                run_process_group(
                    [sys.executable, "-c", parent],
                    capture_output=True,
                    text=True,
                    timeout=1.0,
                )

            time.sleep(1)
            self.assertTrue(started.exists())
            self.assertFalse(residue.exists())
            child_pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)

    def test_timeout_freezes_tree_before_term_handler_can_fork_and_detach(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            started = root / "started"
            escaped_pid = root / "escaped.pid"
            residue = root / "residue"
            child = (
                "import os, signal, time; "
                f"started={str(started)!r}; escaped={str(escaped_pid)!r}; "
                f"residue={str(residue)!r}; "
                "\n"
                "def on_term(signum, frame):\n"
                "    pid = os.fork()\n"
                "    if pid == 0:\n"
                "        os.setsid()\n"
                "        open(escaped, 'w').write(str(os.getpid()))\n"
                "        time.sleep(0.8)\n"
                "        open(residue, 'w').write('late')\n"
                "        os._exit(0)\n"
                "    os._exit(0)\n"
                "signal.signal(signal.SIGTERM, on_term)\n"
                "open(started, 'w').write('started')\n"
                "time.sleep(30)\n"
            )
            parent = (
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {child!r}]); "
                "time.sleep(30)"
            )

            real_signal_group = process_runner._signal_process_group
            saw_stop = False

            def synchronized_signal_group(
                pid: int,
                requested_signal: signal.Signals,
                *,
                expected_identity: str | None = None,
            ) -> None:
                nonlocal saw_stop
                real_signal_group(
                    pid,
                    requested_signal,
                    expected_identity=expected_identity,
                )
                if requested_signal == signal.SIGSTOP:
                    saw_stop = True
                if requested_signal == signal.SIGTERM and not saw_stop:
                    deadline = time.monotonic() + 0.5
                    while time.monotonic() < deadline and not escaped_pid.exists():
                        time.sleep(0.005)

            with (
                patch(
                    "supervisor.process_runner._signal_process_group",
                    side_effect=synchronized_signal_group,
                ),
                self.assertRaises(subprocess.TimeoutExpired),
            ):
                run_process_group(
                    [sys.executable, "-c", parent],
                    capture_output=True,
                    text=True,
                    timeout=1.0,
                )

            time.sleep(1)
            self.assertTrue(started.exists())
            self.assertFalse(escaped_pid.exists())
            self.assertFalse(residue.exists())


if __name__ == "__main__":
    unittest.main()

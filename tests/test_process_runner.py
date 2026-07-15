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
from supervisor.process_runner import run_process_group


class ProcessRunnerTests(unittest.TestCase):
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
        lease = process_runner._ProcessTreeLease(process.pid, "test-token")
        lease._owned = {123}
        with (
            patch(
                "supervisor.process_runner._spawn_with_process_tree_lease",
                return_value=(process, lease),
            ),
            patch("supervisor.process_runner._process_tree", return_value={123}),
            patch("supervisor.process_runner._signal_process_group") as signal_group,
            patch("supervisor.process_runner._signal_processes") as signal_processes,
            patch.object(lease, "stop"),
            patch.object(lease, "tagged_processes", return_value=set()),
            self.assertRaises(KeyboardInterrupt),
        ):
            run_process_group(["ignored"], capture_output=True, text=True)

        self.assertEqual(
            [
                call(123, signal.SIGSTOP),
                call(123, signal.SIGSTOP),
                call(123, signal.SIGTERM),
                call(123, signal.SIGKILL),
            ],
            signal_group.call_args_list,
        )
        self.assertEqual(
            [
                call({123}, signal.SIGSTOP),
                call({123}, signal.SIGSTOP),
                call({123}, signal.SIGTERM),
                call({123}, signal.SIGKILL),
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
                pid: int, requested_signal: signal.Signals
            ) -> None:
                nonlocal saw_stop
                real_signal_group(pid, requested_signal)
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

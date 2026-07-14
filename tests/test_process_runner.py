from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import call, patch

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
        with (
            patch("supervisor.process_runner.subprocess.Popen", return_value=process),
            patch("supervisor.process_runner._process_tree", return_value={123}),
            patch("supervisor.process_runner._signal_process_group") as signal_group,
            patch("supervisor.process_runner._signal_processes") as signal_processes,
            self.assertRaises(KeyboardInterrupt),
        ):
            run_process_group(["ignored"], capture_output=True, text=True)

        self.assertEqual(
            [
                call(123, signal.SIGTERM),
                call(123, signal.SIGSTOP),
                call(123, signal.SIGSTOP),
                call(123, signal.SIGKILL),
            ],
            signal_group.call_args_list,
        )
        self.assertEqual(
            [
                call({123}, signal.SIGTERM),
                call({123}, signal.SIGSTOP),
                call({123}, signal.SIGSTOP),
                call({123}, signal.SIGKILL),
            ],
            signal_processes.call_args_list,
        )
        self.assertEqual(3, process.calls)

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
                "time.sleep(0.8); "
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
                    timeout=0.3,
                )

            time.sleep(1)
            self.assertTrue(started.exists())
            self.assertFalse(residue.exists())
            child_pid = int(pid_file.read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)


if __name__ == "__main__":
    unittest.main()

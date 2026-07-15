from __future__ import annotations

import os
import platform
import shlex
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from supervisor.partner_sandbox import PartnerCommandSandbox


class PartnerCommandSandboxValidationTests(unittest.TestCase):
    def test_runtime_ancestry_cannot_escape_through_symlink(self) -> None:
        with (
            tempfile.TemporaryDirectory() as repo_tmp,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            repo_root = Path(repo_tmp)
            outside_root = Path(outside_tmp)
            (repo_root / "src").mkdir()
            (repo_root / ".autoclaw").symlink_to(
                outside_root, target_is_directory=True
            )

            with self.assertRaisesRegex(ValueError, "cannot traverse symlink"):
                PartnerCommandSandbox(
                    repo_root=repo_root,
                    allowed_paths=("src",),
                    runtime_dir=repo_root / ".autoclaw" / "sandbox-test",
                )

            self.assertEqual([], list(outside_root.iterdir()))

    def test_allowed_scope_cannot_escape_through_symlink(self) -> None:
        with (
            tempfile.TemporaryDirectory() as repo_tmp,
            tempfile.TemporaryDirectory() as outside_tmp,
        ):
            repo_root = Path(repo_tmp)
            (repo_root / "src").symlink_to(Path(outside_tmp), target_is_directory=True)

            with self.assertRaisesRegex(ValueError, "cannot traverse symlinks"):
                PartnerCommandSandbox(
                    repo_root=repo_root,
                    allowed_paths=("src",),
                    runtime_dir=repo_root / ".autoclaw" / "sandbox-test",
                )


@unittest.skipUnless(platform.system() == "Darwin", "macOS Seatbelt boundary test")
class PartnerCommandSandboxTests(unittest.TestCase):

    def test_injected_runner_receives_one_explicit_sandbox_wrapper(self) -> None:
        captured: dict[str, object] = {}

        def runner(args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return subprocess.CompletedProcess(args, 0, "", "")

        with tempfile.TemporaryDirectory() as repo_tmp:
            repo_root = Path(repo_tmp)
            (repo_root / "src").mkdir()
            sandbox = PartnerCommandSandbox(
                repo_root=repo_root,
                allowed_paths=("src",),
                runtime_dir=repo_root / ".autoclaw" / "sandbox-test",
                runner=runner,
            )

            completed = sandbox.run(
                "printf ok",
                environment={"AUTOCLAW_RUN_ID": "injected-runner"},
                timeout=3,
            )

        self.assertEqual(0, completed.returncode)
        args = captured["args"]
        self.assertEqual("/usr/bin/sandbox-exec", args[0])
        self.assertEqual("-f", args[1])
        self.assertEqual(str(sandbox.profile_path), args[2])
        self.assertNotIn("/usr/bin/sandbox-exec", args[3:])
        self.assertNotIn("sandbox_profile_builder", captured["kwargs"])

    def test_scrubs_host_env_denies_outside_reads_writes_network_and_control_residue(
        self,
    ) -> None:
        with (
            tempfile.TemporaryDirectory() as repo_tmp,
            tempfile.TemporaryDirectory(dir="/private/tmp") as outside_tmp,
        ):
            repo_root = Path(repo_tmp)
            outside_root = Path(outside_tmp)
            (repo_root / "src").mkdir()
            (repo_root / "src" / "nested").mkdir()
            (repo_root / "tests").mkdir()
            (repo_root / ".autoclaw").mkdir()
            (repo_root / ".autoclaw" / "operator-secret.txt").write_text(
                "partner-control-secret\n"
            )
            sentinel = outside_root / "sentinel.txt"
            sentinel.write_text("outside-secret-marker\n")
            script = repo_root / "tests" / "sandbox_probe.py"
            script.write_text(
                "\n".join(
                    (
                        "import os, socket",
                        "import subprocess",
                        "from pathlib import Path",
                        "print('HOST_ENV=' + str(os.environ.get('ACA_HOST_SECRET')))",
                        f"outside = Path({str(sentinel)!r})",
                        "for label, action in (",
                        "    ('READ', lambda: outside.read_text()),",
                        "    ('WRITE', lambda: Path('OUTSIDE.txt').write_text('no')),",
                        "    ('ENV', lambda: Path('src/.env').write_text('no')),",
                        "    ('GIT', lambda: Path('src/nested/.git').mkdir()),",
                        "    ('AUTOCLAW_READ', lambda: Path('.autoclaw/operator-secret.txt').read_text()),",
                        "    ('AUTOCLAW_WRITE', lambda: Path('src/nested/.autoclaw').mkdir()),",
                        "):",
                        "    try:",
                        "        value = action()",
                        "        print(label + '=UNEXPECTED:' + str(value))",
                        "    except Exception as exc:",
                        "        print(label + '=' + type(exc).__name__)",
                        "try:",
                        "    socket.create_connection(('127.0.0.1', 9), timeout=0.1)",
                        "    print('NETWORK=UNEXPECTED')",
                        "except Exception as exc:",
                        "    print('NETWORK=' + type(exc).__name__)",
                        "side_channels = subprocess.run(",
                        "    '/bin/ps eww -p $PPID; /usr/bin/security list-keychains -d user',",
                        "    shell=True, text=True, capture_output=True, check=False,",
                        ")",
                        "print('SIDE_CHANNEL_OUT=' + side_channels.stdout.strip())",
                        "print('SIDE_CHANNEL_ERR=' + side_channels.stderr.strip())",
                        "Path('src/allowed.txt').write_text('ok\\n')",
                    )
                )
                + "\n"
            )
            sandbox = PartnerCommandSandbox(
                repo_root=repo_root,
                allowed_paths=("src", "tests"),
                runtime_dir=repo_root / ".autoclaw" / "sandbox-test",
            )
            launch_environment = sandbox.launch_environment(
                {"AUTOCLAW_RUN_ID": "sandbox-test"}
            )
            self.assertEqual("/dev/null", launch_environment["GIT_CONFIG_GLOBAL"])
            self.assertEqual("core.hooksPath", launch_environment["GIT_CONFIG_KEY_0"])
            self.assertEqual("/dev/null", launch_environment["GIT_CONFIG_VALUE_0"])
            self.assertEqual("core.fsmonitor", launch_environment["GIT_CONFIG_KEY_1"])
            self.assertEqual("false", launch_environment["GIT_CONFIG_VALUE_1"])
            profile = sandbox.profile_path.read_text(encoding="utf-8")
            self.assertIn("(deny appleevent-send)", profile)
            self.assertIn("(deny distributed-notification-post)", profile)
            original = os.environ.get("ACA_HOST_SECRET")
            os.environ["ACA_HOST_SECRET"] = "host-secret-marker"
            try:
                completed = sandbox.run(
                    f"python3 {shlex.quote(str(script.relative_to(repo_root)))}",
                    environment={"AUTOCLAW_RUN_ID": "sandbox-test"},
                    timeout=30,
                )
            finally:
                if original is None:
                    os.environ.pop("ACA_HOST_SECRET", None)
                else:
                    os.environ["ACA_HOST_SECRET"] = original

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("HOST_ENV=None", completed.stdout)
            self.assertNotIn("host-secret-marker", completed.stdout + completed.stderr)
            self.assertNotIn(
                "outside-secret-marker", completed.stdout + completed.stderr
            )
            self.assertNotIn(
                "partner-control-secret", completed.stdout + completed.stderr
            )
            self.assertIn("READ=PermissionError", completed.stdout)
            self.assertIn("WRITE=PermissionError", completed.stdout)
            self.assertIn("ENV=PermissionError", completed.stdout)
            self.assertIn("GIT=", completed.stdout)
            self.assertNotIn("GIT=UNEXPECTED", completed.stdout)
            self.assertIn("AUTOCLAW_READ=PermissionError", completed.stdout)
            self.assertIn("AUTOCLAW_WRITE=", completed.stdout)
            self.assertNotIn("AUTOCLAW_WRITE=UNEXPECTED", completed.stdout)
            self.assertNotIn("NETWORK=UNEXPECTED", completed.stdout)
            self.assertNotIn(".keychain", completed.stdout.lower())
            self.assertTrue((repo_root / "src" / "allowed.txt").is_file())
            self.assertFalse((repo_root / "OUTSIDE.txt").exists())
            self.assertFalse((repo_root / "src" / ".env").exists())
            self.assertFalse((repo_root / "src" / "nested" / ".git").exists())
            self.assertFalse((repo_root / "src" / "nested" / ".autoclaw").exists())

    def test_timeout_stops_descendants_before_they_can_write(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo_root = Path(repo_tmp)
            (repo_root / "src").mkdir()
            started = repo_root / "src" / "descendant-started.txt"
            sentinel = repo_root / "src" / "escaped-after-timeout.txt"
            child = "; ".join(
                (
                    "import os",
                    "import signal, time",
                    "from pathlib import Path",
                    "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
                    "Path('src/descendant.pid').write_text(str(os.getpid()))",
                    "Path('src/descendant-started.txt').write_text('started\\n')",
                    "time.sleep(3)",
                    "Path('src/escaped-after-timeout.txt').write_text('escaped\\n')",
                )
            )
            sandbox = PartnerCommandSandbox(
                repo_root=repo_root,
                allowed_paths=("src",),
                runtime_dir=repo_root / ".autoclaw" / "sandbox-test",
            )

            with self.assertRaises(subprocess.TimeoutExpired):
                sandbox.run(
                    f"python3 -c {shlex.quote(child)} & /bin/sleep 30",
                    environment={"AUTOCLAW_RUN_ID": "sandbox-timeout-test"},
                    timeout=1.0,
                )
            time.sleep(1)

            self.assertTrue(started.exists())
            self.assertFalse(sentinel.exists())
            descendant_pid = int((repo_root / "src/descendant.pid").read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(descendant_pid, 0)

    def test_success_stops_detached_descendant_before_late_write(self) -> None:
        with tempfile.TemporaryDirectory() as repo_tmp:
            repo_root = Path(repo_tmp)
            (repo_root / "src").mkdir()
            started = repo_root / "src" / "success-child-started.txt"
            sentinel = repo_root / "src" / "escaped-after-success.txt"
            worker = repo_root / "src" / "success_worker.py"
            worker.write_text(
                "\n".join(
                    (
                        "import os, signal, time",
                        "from pathlib import Path",
                        "os.setsid()",
                        "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
                        "Path('src/success-child.pid').write_text(str(os.getpid()))",
                        "Path('src/success-child-started.txt').write_text('started\\n')",
                        "time.sleep(1)",
                        "Path('src/escaped-after-success.txt').write_text('escaped\\n')",
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            sandbox = PartnerCommandSandbox(
                repo_root=repo_root,
                allowed_paths=("src",),
                runtime_dir=repo_root / ".autoclaw" / "sandbox-test",
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
                    return_value={},
                ),
            ):
                completed = sandbox.run(
                    "python3 src/success_worker.py >/dev/null 2>&1 & "
                    "while [ ! -f src/success-child-started.txt ]; do sleep .01; done",
                    environment={"AUTOCLAW_RUN_ID": "sandbox-success-test"},
                    timeout=3,
                )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(started.exists())
            time.sleep(1.2)
            self.assertFalse(sentinel.exists())
            descendant_pid = int((repo_root / "src" / "success-child.pid").read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(descendant_pid, 0)


if __name__ == "__main__":
    unittest.main()

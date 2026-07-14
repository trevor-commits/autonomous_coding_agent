from __future__ import annotations

import os
import platform
import shlex
import tempfile
import unittest
from pathlib import Path

from supervisor.partner_sandbox import PartnerCommandSandbox


@unittest.skipUnless(platform.system() == "Darwin", "macOS Seatbelt boundary test")
class PartnerCommandSandboxTests(unittest.TestCase):
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
            self.assertIn("READ=PermissionError", completed.stdout)
            self.assertIn("WRITE=PermissionError", completed.stdout)
            self.assertIn("ENV=PermissionError", completed.stdout)
            self.assertIn("GIT=", completed.stdout)
            self.assertNotIn("GIT=UNEXPECTED", completed.stdout)
            self.assertNotIn("NETWORK=UNEXPECTED", completed.stdout)
            self.assertNotIn(".keychain", completed.stdout.lower())
            self.assertTrue((repo_root / "src" / "allowed.txt").is_file())
            self.assertFalse((repo_root / "OUTSIDE.txt").exists())
            self.assertFalse((repo_root / "src" / ".env").exists())
            self.assertFalse((repo_root / "src" / "nested" / ".git").exists())


if __name__ == "__main__":
    unittest.main()

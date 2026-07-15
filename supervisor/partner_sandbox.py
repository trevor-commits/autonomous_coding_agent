from __future__ import annotations

import json
import platform
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping, Sequence

from supervisor.path_safety import PathSafetyError, ensure_safe_directory
from supervisor.process_runner import run_process_group


Runner = Callable[..., subprocess.CompletedProcess[str]]


class PartnerSandboxUnavailableError(RuntimeError):
    """Raised when a partner command cannot be confined by the host."""


class PartnerCommandSandbox:
    """Run builder/verifier commands with scrubbed env, closed network, and scoped files."""

    _SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
    _SYSTEM_READ_ROOTS = (
        "/System",
        "/Library/Apple",
        "/Library/Developer",
        "/usr",
        "/bin",
        "/sbin",
        "/opt/homebrew",
        "/usr/local",
        "/private/etc/hosts",
        "/private/etc/localtime",
        "/private/etc/master.passwd",
        "/private/etc/passwd",
        "/private/etc/protocols",
        "/private/etc/services",
        "/private/etc/zshenv",
        "/private/var/db/timezone",
        "/dev",
    )
    _PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

    def __init__(
        self,
        *,
        repo_root: Path | str,
        allowed_paths: Sequence[str],
        runtime_dir: Path | str,
        runner: Runner | None = None,
    ) -> None:
        source_repo_root = Path(repo_root).absolute()
        self.repo_root = Path(repo_root).resolve()
        self.allowed_roots = self._resolve_allowed_paths(allowed_paths)
        runtime_path = Path(runtime_dir)
        if any(part in {".", ".."} for part in runtime_path.parts):
            raise ValueError(
                "Partner sandbox runtime must not contain traversal components."
            )
        if not runtime_path.is_absolute():
            runtime_path = source_repo_root / runtime_path
        runtime_root = source_repo_root / ".autoclaw"
        try:
            runtime_relative = runtime_path.relative_to(runtime_root)
        except ValueError as exc:
            raise ValueError(
                "Partner sandbox runtime must stay under repo-local .autoclaw."
            ) from exc
        runtime_path = self.repo_root / ".autoclaw" / runtime_relative
        try:
            ensure_safe_directory(runtime_path, boundary=self.repo_root)
        except PathSafetyError as exc:
            raise ValueError(str(exc)) from exc
        self.runtime_dir = runtime_path
        self.home_dir = self.runtime_dir / "home"
        self.temp_dir = self.runtime_dir / "tmp"
        self.cache_dir = self.home_dir / "cache"
        self.profile_path = self.runtime_dir / "partner-command.sb"
        self._uses_managed_containment = runner is None or runner is run_process_group
        self.runner = runner or run_process_group

        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(self._build_profile(), encoding="utf-8")
        self.profile_path.chmod(0o600)

    def run(
        self,
        command: str,
        *,
        environment: Mapping[str, str],
        timeout: int | float | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self._require_supported_host()
        command_args = self.command_args(command, environment=environment)
        run_options = {
            "cwd": self.repo_root,
            "stdin": subprocess.DEVNULL,
            "capture_output": True,
            "text": True,
            "timeout": timeout,
            "check": False,
            "env": self.launch_environment(environment),
        }
        if self._uses_managed_containment:
            run_options["sandbox_profile_builder"] = self._profile_for_containment
        else:
            command_args = [
                str(self._SANDBOX_EXEC),
                "-f",
                str(self.profile_path),
                *command_args,
            ]
        return self.runner(
            command_args,
            **run_options,
        )

    def command_args(
        self, command: str, *, environment: Mapping[str, str]
    ) -> list[str]:
        self._require_supported_host()
        clean_env = self.launch_environment(environment)
        assignments = [f"{key}={value}" for key, value in sorted(clean_env.items())]
        return [
            "/usr/bin/env",
            "-i",
            *assignments,
            "/bin/zsh",
            "-c",
            command,
        ]

    def launch_environment(self, environment: Mapping[str, str]) -> dict[str, str]:
        clean = {
            "PATH": self._PATH,
            "HOME": str(self.home_dir),
            "TMPDIR": str(self.temp_dir),
            "TMP": str(self.temp_dir),
            "TEMP": str(self.temp_dir),
            "XDG_CACHE_HOME": str(self.cache_dir),
            "DARWIN_USER_CACHE_DIR": str(self.temp_dir),
            "CFFIXED_USER_HOME": str(self.home_dir),
            "PYTHONDONTWRITEBYTECODE": "1",
            "CI": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": "/dev/null",
            "GIT_CONFIG_KEY_1": "core.fsmonitor",
            "GIT_CONFIG_VALUE_1": "false",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8",
        }
        for key, value in environment.items():
            if not key.startswith("AUTOCLAW_") or not isinstance(value, str):
                raise ValueError(
                    "Partner command environment only accepts AUTOCLAW_ text values."
                )
            clean[key] = value
        return clean

    def _resolve_allowed_paths(self, values: Sequence[str]) -> tuple[Path, ...]:
        resolved: list[Path] = []
        for value in values:
            pure = PurePosixPath(str(value).replace("\\", "/"))
            if (
                not pure.parts
                or pure.is_absolute()
                or "." in pure.parts
                or ".." in pure.parts
            ):
                raise ValueError(
                    "Partner sandbox allowed paths must be bounded relative paths."
                )
            if any(part in {".git", ".agent", ".autoclaw"} for part in pure.parts):
                raise ValueError(
                    "Partner sandbox allowed paths cannot include control metadata."
                )
            candidate = self.repo_root.joinpath(*pure.parts)
            cursor = self.repo_root
            for part in pure.parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise ValueError(
                        "Partner sandbox allowed paths cannot traverse symlinks."
                    )
            resolved_candidate = candidate.resolve(strict=False)
            try:
                resolved_candidate.relative_to(self.repo_root)
            except ValueError as exc:
                raise ValueError(
                    "Partner sandbox allowed paths must stay inside the repo."
                ) from exc
            resolved.append(resolved_candidate)
        if not resolved:
            raise ValueError("Partner sandbox requires at least one allowed path.")
        return tuple(dict.fromkeys(resolved))

    def _require_supported_host(self) -> None:
        if platform.system() != "Darwin" or not self._SANDBOX_EXEC.is_file():
            raise PartnerSandboxUnavailableError(
                "Partner execution requires the macOS sandbox-exec confinement boundary."
            )

    def _profile_for_containment(self, tag_root: Path) -> str:
        return self._build_profile(containment_tag_root=tag_root)

    def _build_profile(self, *, containment_tag_root: Path | None = None) -> str:
        read_roots = [self.repo_root, self.home_dir, self.temp_dir]
        if containment_tag_root is not None:
            read_roots.append(containment_tag_root)
        git_dir = self._git_directory()
        if git_dir is not None:
            read_roots.append(git_dir)
        read_roots.extend(Path(path) for path in self._SYSTEM_READ_ROOTS)

        read_exclusions = self._path_exclusions(read_roots)
        write_exclusions = self._path_exclusions(
            [*self.allowed_roots, self.home_dir, self.temp_dir],
            include_device_files=True,
        )
        sensitive_pattern = re.escape(str(self.repo_root)) + (
            r"/(.*/)?(\.env.*|\.git(/.*)?|\.agent(/.*)?|\.autoclaw(/.*)?)$"
        )
        sensitive_pattern = sensitive_pattern.replace('"', r"\"")
        sensitive_read_filter = f'(regex #"{sensitive_pattern}")'
        if containment_tag_root is not None:
            tag_literal = json.dumps(str(containment_tag_root))
            sensitive_read_filter = (
                f"(require-all {sensitive_read_filter} "
                f"(require-not (literal {tag_literal})) "
                f"(require-not (subpath {tag_literal})))"
            )
        return "\n".join(
            (
                "(version 1)",
                "(allow default)",
                "(deny network*)",
                "(deny appleevent-send)",
                "(deny distributed-notification-post)",
                "(deny user-preference-read)",
                "(deny mach-lookup "
                '(global-name "com.apple.securityd") '
                '(global-name "com.apple.securityd.xpc") '
                '(global-name "com.apple.pboard") '
                '(global-name "com.apple.coreservices.launchservicesd"))',
                f"(deny file-read* file-test-existence (require-all {read_exclusions}))",
                f"(deny file-read* file-test-existence {sensitive_read_filter})",
                f"(deny file-write* (require-all {write_exclusions}))",
                f'(deny file-write* (regex #"{sensitive_pattern}"))',
                "",
            )
        )

    def _git_directory(self) -> Path | None:
        completed = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-dir"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        candidate = Path(completed.stdout.strip())
        return candidate.resolve() if candidate.exists() else None

    def _path_exclusions(
        self,
        roots: Sequence[Path],
        *,
        include_device_files: bool = False,
    ) -> str:
        rules: list[str] = []
        seen: set[str] = set()
        for root in roots:
            value = str(root)
            if value in seen:
                continue
            seen.add(value)
            literal = json.dumps(value)
            rules.extend(
                (
                    f"(require-not (literal {literal}))",
                    f"(require-not (subpath {literal}))",
                )
            )
            for ancestor in root.parents:
                ancestor_value = str(ancestor)
                if ancestor_value in seen:
                    continue
                seen.add(ancestor_value)
                rules.append(f"(require-not (literal {json.dumps(ancestor_value)}))")
        if include_device_files:
            rules.extend(
                (
                    '(require-not (literal "/dev/null"))',
                    '(require-not (literal "/dev/zero"))',
                    '(require-not (subpath "/dev/fd"))',
                )
            )
        return " ".join(rules)

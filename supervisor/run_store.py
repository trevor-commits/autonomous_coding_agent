from __future__ import annotations

import json
import os
import secrets
import stat
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, TextIO

from supervisor.path_safety import (
    PathSafetyError,
    ensure_safe_directory,
    require_single_link_regular_file,
)


class RunStoreError(RuntimeError):
    """Raised when the supervisor cannot create or update run storage."""


class RunStore:
    """Supervisor-owned runtime storage rooted at `.autoclaw/runs/<run_id>/`."""

    def __init__(self, repo_root: Path | str, run_id: str) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.run_id = run_id
        self.root = self.repo_root / ".autoclaw" / "runs" / run_id
        self.defects_dir = self.root / "defects"
        self.artifacts_dir = self.root / "artifacts"
        self.reports_dir = self.root / "reports"
        self.logs_dir = self.artifacts_dir / "logs"
        self.screenshots_dir = self.artifacts_dir / "screenshots"
        self.videos_dir = self.artifacts_dir / "videos"
        self.traces_dir = self.artifacts_dir / "traces"
        self.contract_path = self.root / "contract.json"
        self.state_path = self.root / "state.json"
        self.execution_log_path = self.root / "execution.log"

    def initialize(
        self,
        *,
        repo_contract: Any,
        run_contract: Any,
        initial_state: Any | None = None,
    ) -> None:
        try:
            for directory in (
                self.defects_dir,
                self.logs_dir,
                self.screenshots_dir,
                self.videos_dir,
                self.traces_dir,
                self.reports_dir,
            ):
                ensure_safe_directory(directory, boundary=self.repo_root)
            self.write_json(
                self.contract_path,
                {
                    "repo_contract": self._serialize(repo_contract),
                    "run_contract": self._serialize(run_contract),
                },
            )
            if initial_state is not None:
                self.write_state(initial_state)
            self._open_text_file(self.execution_log_path, os.O_APPEND).close()
        except PathSafetyError as exc:
            raise RunStoreError(str(exc)) from exc

    def write_state(self, state: Any) -> None:
        self.write_json(self.state_path, self._serialize(state))

    def append_execution_log(self, message: str) -> None:
        with self._open_text_file(self.execution_log_path, os.O_APPEND) as handle:
            handle.write(message.rstrip() + "\n")

    def write_report(self, name: str, payload: Any) -> Path:
        path = self.reports_dir / name
        self.write_json(path, self._serialize(payload))
        return path

    def write_json(self, path: Path, payload: Any) -> None:
        directory_fd: int | None = None
        descriptor: int | None = None
        temp_name: str | None = None
        try:
            ensure_safe_directory(path.parent, boundary=self.repo_root)
            require_single_link_regular_file(path, boundary=self.repo_root)
            serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            directory_fd = os.open(
                path.parent,
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0),
            )
            for _ in range(100):
                temp_name = f".{path.name}.{secrets.token_hex(8)}.tmp"
                try:
                    descriptor = os.open(
                        temp_name,
                        os.O_WRONLY
                        | os.O_CREAT
                        | os.O_EXCL
                        | getattr(os, "O_NOFOLLOW", 0)
                        | getattr(os, "O_CLOEXEC", 0),
                        0o600,
                        dir_fd=directory_fd,
                    )
                except FileExistsError:
                    continue
                break
            else:  # pragma: no cover - cryptographic names should not collide.
                raise RunStoreError("Could not allocate a unique state temp file.")

            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = None
                handle.write(serialized)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(
                temp_name,
                path.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            os.fsync(directory_fd)
        except PathSafetyError as exc:
            raise RunStoreError(str(exc)) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temp_name is not None and directory_fd is not None:
                try:
                    os.unlink(temp_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            if directory_fd is not None:
                os.close(directory_fd)

    def _open_text_file(self, path: Path, flags: int) -> TextIO:
        descriptor: int | None = None
        try:
            require_single_link_regular_file(path, boundary=self.repo_root)
            descriptor = os.open(
                path,
                flags | os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW,
                0o600,
            )
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise PathSafetyError(f"Path `{path}` must be a regular file.")
            if metadata.st_nlink != 1:
                raise PathSafetyError(
                    f"Path `{path}` must be a single-link regular file."
                )
        except (OSError, PathSafetyError) as exc:
            if descriptor is not None:
                os.close(descriptor)
            raise RunStoreError(str(exc)) from exc
        return os.fdopen(descriptor, "a", encoding="utf-8")

    def _serialize(self, payload: Any) -> Any:
        if is_dataclass(payload) and not isinstance(payload, type):
            return asdict(payload)
        return payload

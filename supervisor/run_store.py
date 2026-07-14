from __future__ import annotations

import json
import os
import stat
import tempfile
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
        try:
            ensure_safe_directory(path.parent, boundary=self.repo_root)
            require_single_link_regular_file(path, boundary=self.repo_root)
            serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            descriptor, temp_name = tempfile.mkstemp(
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
            )
            os.close(descriptor)
            temp_path = Path(temp_name)
            try:
                temp_path.write_text(serialized, encoding="utf-8")
                with temp_path.open("rb+") as handle:
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_path, path)
            finally:
                temp_path.unlink(missing_ok=True)
        except PathSafetyError as exc:
            raise RunStoreError(str(exc)) from exc

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

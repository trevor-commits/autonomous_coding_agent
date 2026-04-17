from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


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
        for directory in (
            self.defects_dir,
            self.logs_dir,
            self.screenshots_dir,
            self.videos_dir,
            self.traces_dir,
            self.reports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        self.write_json(
            self.contract_path,
            {
                "repo_contract": self._serialize(repo_contract),
                "run_contract": self._serialize(run_contract),
            },
        )
        if initial_state is not None:
            self.write_state(initial_state)
        self.execution_log_path.touch(exist_ok=True)

    def write_state(self, state: Any) -> None:
        self.write_json(self.state_path, self._serialize(state))

    def append_execution_log(self, message: str) -> None:
        with self.execution_log_path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")

    def write_report(self, name: str, payload: Any) -> Path:
        path = self.reports_dir / name
        self.write_json(path, self._serialize(payload))
        return path

    def write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def _serialize(self, payload: Any) -> Any:
        if is_dataclass(payload):
            return asdict(payload)
        return payload

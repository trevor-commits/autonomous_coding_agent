from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class WorktreeError(RuntimeError):
    """Raised when the supervisor cannot create or manage the builder worktree."""


@dataclass(frozen=True)
class BuilderWorkspace:
    run_id: str
    branch_name: str
    worktree_path: Path
    lease_path: Path


class WorktreeManager:
    """Manage builder worktrees and the single-writer lease."""

    def __init__(self, repo_root: Path | str) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.worktrees_root = self.repo_root / "worktrees"
        self.leases_root = self.repo_root / ".autoclaw" / "locks"

    def create_builder_worktree(
        self,
        *,
        run_id: str,
        task_slug: str,
        base_ref: str = "HEAD",
    ) -> BuilderWorkspace:
        branch_name = f"run/{_slugify(task_slug)}/{run_id}"
        worktree_path = self.worktrees_root / run_id / "builder"
        lease_path = self.acquire_lease(run_id, worktree_path, branch_name)
        try:
            self.worktrees_root.mkdir(parents=True, exist_ok=True)
            self._git("worktree", "add", "-b", branch_name, str(worktree_path), base_ref)
        except Exception:
            self.release_lease(run_id)
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise
        return BuilderWorkspace(
            run_id=run_id,
            branch_name=branch_name,
            worktree_path=worktree_path,
            lease_path=lease_path,
        )

    def remove_builder_worktree(
        self,
        workspace: BuilderWorkspace,
        *,
        delete_branch: bool = True,
    ) -> None:
        if workspace.worktree_path.exists():
            self._git("worktree", "remove", "--force", str(workspace.worktree_path))
        self.release_lease(workspace.run_id)
        if delete_branch:
            self._git("branch", "-D", workspace.branch_name)

    def acquire_lease(
        self,
        run_id: str,
        worktree_path: Path,
        branch_name: str,
    ) -> Path:
        self.leases_root.mkdir(parents=True, exist_ok=True)
        lease_path = self.leases_root / f"{run_id}.json"
        try:
            with lease_path.open("x", encoding="utf-8") as handle:
                json.dump(
                    {
                        "run_id": run_id,
                        "worktree_path": str(worktree_path),
                        "branch_name": branch_name,
                        "pid": os.getpid(),
                    },
                    handle,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
        except FileExistsError as exc:
            raise WorktreeError(
                f"Single-writer lease already exists for run `{run_id}`."
            ) from exc
        return lease_path

    def release_lease(self, run_id: str) -> None:
        lease_path = self.leases_root / f"{run_id}.json"
        if lease_path.exists():
            lease_path.unlink()

    def _git(self, *args: str) -> None:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            raise WorktreeError(
                f"`git {' '.join(args)}` failed in `{self.repo_root}`: {stderr}"
            )


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "task"

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from supervisor.path_safety import (
    PathSafetyError,
    ensure_safe_directory,
    require_missing_path,
    require_safe_directory,
    require_single_link_regular_file,
)


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
        try:
            ensure_safe_directory(worktree_path.parent, boundary=self.repo_root)
            require_missing_path(worktree_path, boundary=self.repo_root)
        except PathSafetyError as exc:
            raise WorktreeError(str(exc)) from exc
        lease_path = self.acquire_lease(run_id, worktree_path, branch_name)
        try:
            self._git(
                "worktree", "add", "-b", branch_name, str(worktree_path), base_ref
            )
            require_safe_directory(worktree_path, boundary=self.repo_root)
        except PathSafetyError as exc:
            self.release_lease(run_id)
            raise WorktreeError(str(exc)) from exc
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
        try:
            workspace.worktree_path.lstat()
        except FileNotFoundError:
            pass
        else:
            try:
                require_safe_directory(workspace.worktree_path, boundary=self.repo_root)
            except PathSafetyError as exc:
                raise WorktreeError(str(exc)) from exc
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
        lease_path = self.leases_root / f"{run_id}.json"
        try:
            ensure_safe_directory(lease_path.parent, boundary=self.repo_root)
            try:
                descriptor = os.open(
                    lease_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    0o600,
                )
            except FileExistsError as exc:
                require_single_link_regular_file(lease_path, boundary=self.repo_root)
                raise WorktreeError(
                    f"Single-writer lease already exists for run `{run_id}`."
                ) from exc
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
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
            require_single_link_regular_file(lease_path, boundary=self.repo_root)
        except PathSafetyError as exc:
            raise WorktreeError(str(exc)) from exc
        return lease_path

    def release_lease(self, run_id: str) -> None:
        lease_path = self.leases_root / f"{run_id}.json"
        try:
            require_single_link_regular_file(lease_path, boundary=self.repo_root)
            lease_path.lstat()
        except FileNotFoundError:
            return
        except PathSafetyError as exc:
            raise WorktreeError(str(exc)) from exc
        else:
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


def _slugify(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = slug or "task"
    if len(slug) <= max_length:
        return slug
    digest = hashlib.sha256(slug.encode("utf-8")).hexdigest()[:12]
    return f"{slug[: max_length - len(digest) - 1].rstrip('-')}-{digest}"

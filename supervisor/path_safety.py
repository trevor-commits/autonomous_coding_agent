from __future__ import annotations

import stat
from pathlib import Path


class PathSafetyError(RuntimeError):
    """Raised when supervisor-owned storage cannot prove no-follow path safety."""


def ensure_safe_directory(path: Path, *, boundary: Path) -> None:
    boundary = boundary.resolve()
    path = Path(path)
    try:
        relative = path.relative_to(boundary)
    except ValueError as exc:
        raise PathSafetyError(f"Path `{path}` escapes `{boundary}`.") from exc

    current = boundary
    for part in relative.parts:
        if part in {".", ".."}:
            raise PathSafetyError(
                f"Path `{path}` contains unsafe traversal components."
            )
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir()
            except FileExistsError:
                metadata = current.lstat()
            else:
                metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise PathSafetyError(
                f"Directory ancestry cannot traverse symlink `{current}`."
            )
        if not stat.S_ISDIR(metadata.st_mode):
            raise PathSafetyError(f"Path `{current}` must be a directory.")


def require_safe_directory(path: Path, *, boundary: Path) -> None:
    ensure_safe_directory(path.parent, boundary=boundary)
    try:
        metadata = path.lstat()
    except FileNotFoundError as exc:
        raise PathSafetyError(f"Path `{path}` must be an existing directory.") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise PathSafetyError(f"Directory path cannot be symlink `{path}`.")
    if not stat.S_ISDIR(metadata.st_mode):
        raise PathSafetyError(f"Path `{path}` must be a directory.")


def require_single_link_regular_file(path: Path, *, boundary: Path) -> None:
    ensure_safe_directory(path.parent, boundary=boundary)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(metadata.st_mode):
        raise PathSafetyError(
            f"Path `{path}` must be a regular file, not a symlink or device."
        )
    if metadata.st_nlink != 1:
        raise PathSafetyError(f"Path `{path}` must be a single-link regular file.")


def require_missing_path(path: Path, *, boundary: Path) -> None:
    ensure_safe_directory(path.parent, boundary=boundary)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode):
        raise PathSafetyError(f"Path `{path}` cannot be a symlink.")
    raise PathSafetyError(f"Path `{path}` must not exist before creation.")

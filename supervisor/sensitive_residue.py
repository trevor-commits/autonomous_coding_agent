from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path


class SensitiveResidueError(RuntimeError):
    """Raised when a sensitive residue scan cannot prove a stable tree."""


@dataclass(frozen=True)
class SensitiveResidueEntry:
    kind: str
    mode: int
    size: int
    digest: str


SensitiveResidueSnapshot = dict[str, SensitiveResidueEntry]

_CONTROL_COMPONENTS = {".git", ".agent"}
_ROOT_SCAN_EXCLUSIONS = {".git", ".autoclaw"}


def snapshot_sensitive_residue(repo_root: Path | str) -> SensitiveResidueSnapshot:
    """Fingerprint nested secrets/control metadata without following symlinks."""

    root = Path(repo_root).resolve()
    snapshot: SensitiveResidueSnapshot = {}
    try:
        _scan_directory(root, root=root, snapshot=snapshot, inside_sensitive=False)
    except OSError as exc:
        raise SensitiveResidueError(f"Sensitive residue scan failed: {exc}.") from exc
    return snapshot


def changed_sensitive_residue(
    baseline: SensitiveResidueSnapshot,
    current: SensitiveResidueSnapshot,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            path
            for path in set(baseline) | set(current)
            if baseline.get(path) != current.get(path)
        )
    )


def _scan_directory(
    directory: Path,
    *,
    root: Path,
    snapshot: SensitiveResidueSnapshot,
    inside_sensitive: bool,
) -> None:
    with os.scandir(directory) as entries:
        for entry in entries:
            if directory == root and entry.name in _ROOT_SCAN_EXCLUSIONS:
                continue
            path = Path(entry.path)
            relative = path.relative_to(root).as_posix()
            sensitive = inside_sensitive or _is_sensitive_name(entry.name)
            metadata = entry.stat(follow_symlinks=False)
            if sensitive:
                snapshot[relative] = _fingerprint(path, metadata)
            if stat.S_ISDIR(metadata.st_mode):
                _scan_directory(
                    path,
                    root=root,
                    snapshot=snapshot,
                    inside_sensitive=sensitive,
                )


def _is_sensitive_name(name: str) -> bool:
    return name in _CONTROL_COMPONENTS or name.startswith(".env")


def _fingerprint(path: Path, metadata: os.stat_result) -> SensitiveResidueEntry:
    mode = stat.S_IFMT(metadata.st_mode)
    if stat.S_ISREG(metadata.st_mode):
        digest = _file_digest(path)
        kind = "file"
    elif stat.S_ISLNK(metadata.st_mode):
        digest = hashlib.sha256(
            os.readlink(path).encode("utf-8", errors="surrogateescape")
        ).hexdigest()
        kind = "symlink"
    elif stat.S_ISDIR(metadata.st_mode):
        digest = ""
        kind = "directory"
    else:
        digest = ""
        kind = "other"
    return SensitiveResidueEntry(
        kind=kind, mode=mode, size=metadata.st_size, digest=digest
    )


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

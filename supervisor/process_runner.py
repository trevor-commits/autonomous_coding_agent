from __future__ import annotations

import os
import signal
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO, Literal, Mapping, Sequence


_TERMINATION_GRACE_SECONDS = 0.25
_MAX_ERROR_OUTPUT = 1_000_000


def _process_tree(root_pid: int, seeds: set[int] | None = None) -> set[int]:
    try:
        listed = subprocess.run(
            ["/bin/ps", "-axo", "pid=,ppid="],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            env={"PATH": "/usr/bin:/bin"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return set(seeds or {root_pid})
    children: dict[int, set[int]] = {}
    for line in listed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            pid, parent = (int(value) for value in fields)
        except ValueError:
            continue
        children.setdefault(parent, set()).add(pid)
    owned = set(seeds or {root_pid})
    frontier = list(owned)
    while frontier:
        for child in children.get(frontier.pop(), set()):
            if child not in owned:
                owned.add(child)
                frontier.append(child)
    return owned


def _signal_processes(process_ids: set[int], sig: signal.Signals) -> None:
    for pid in sorted(process_ids, reverse=True):
        try:
            os.kill(pid, sig)
        except (PermissionError, ProcessLookupError):
            pass


def run_process_group(
    args: Sequence[str],
    *,
    cwd: str | Path | None = None,
    stdin: int | None = None,
    capture_output: bool = False,
    text: Literal[True] = True,
    timeout: int | float | None = None,
    check: bool = False,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one command with bounded capture and observed process-tree cleanup."""
    stdout_file = tempfile.TemporaryFile(mode="w+b") if capture_output else None
    stderr_file = tempfile.TemporaryFile(mode="w+b") if capture_output else None
    stdout: str | None
    stderr: str | None
    try:
        process = subprocess.Popen(
            args,
            cwd=cwd,
            stdin=stdin,
            stdout=stdout_file,
            stderr=stderr_file,
            text=text,
            env=env,
            start_new_session=True,
        )
        try:
            process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _stop_process_group(process)
            if (
                timeout is None
            ):  # pragma: no cover - TimeoutExpired cannot arise without a timeout.
                raise RuntimeError("subprocess timeout omitted its deadline") from exc
            stdout = _read_bounded(stdout_file)
            stderr = _read_bounded(stderr_file)
            raise subprocess.TimeoutExpired(
                cmd=args,
                timeout=float(timeout),
                output=stdout,
                stderr=stderr,
            ) from None
        except BaseException:
            _stop_process_group(process)
            raise

        stdout = _read_bounded(stdout_file)
        stderr = _read_bounded(stderr_file)
    finally:
        if stdout_file is not None:
            stdout_file.close()
        if stderr_file is not None:
            stderr_file.close()

    completed = subprocess.CompletedProcess(
        args=args,
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )
    if check:
        completed.check_returncode()
    return completed


def _stop_process_group(
    process: subprocess.Popen[str],
) -> None:
    owned = _process_tree(process.pid)
    _signal_process_group(process.pid, signal.SIGTERM)
    _signal_processes(owned, signal.SIGTERM)
    _signal_process_group(process.pid, signal.SIGSTOP)
    _signal_processes(owned, signal.SIGSTOP)
    try:
        process.communicate(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        pass
    # The direct parent may exit while a setsid() descendant remains stopped.
    # Re-scan and kill the observed tree even when communicate() already returned.
    owned = _process_tree(process.pid, owned)
    _signal_process_group(process.pid, signal.SIGSTOP)
    _signal_processes(owned, signal.SIGSTOP)
    owned = _process_tree(process.pid, owned)
    _signal_process_group(process.pid, signal.SIGKILL)
    _signal_processes(owned, signal.SIGKILL)
    try:
        process.communicate(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)


def _signal_process_group(pid: int, sig: signal.Signals) -> None:
    try:
        os.killpg(pid, sig)
    except (PermissionError, ProcessLookupError):
        pass


def _read_bounded(handle: BinaryIO | None) -> str | None:
    if handle is None:
        return None
    handle.flush()
    size = handle.tell()
    handle.seek(0)
    if size <= _MAX_ERROR_OUTPUT:
        return handle.read().decode("utf-8", errors="replace")
    marker = b"\n...[subprocess output truncated]...\n"
    remaining = _MAX_ERROR_OUTPUT - len(marker)
    head_size = remaining // 2
    head = handle.read(head_size)
    handle.seek(size - (remaining - head_size))
    tail = handle.read(remaining - head_size)
    return (head + marker + tail).decode("utf-8", errors="replace")

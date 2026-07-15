from __future__ import annotations

import os
import select
import signal
import subprocess
import threading
from pathlib import Path
from typing import Literal, Mapping, Sequence


_TERMINATION_GRACE_SECONDS = 0.25
_MAX_ERROR_OUTPUT = 1_000_000
_TRUNCATION_MARKER = b"\n...[subprocess output truncated]...\n"


class _BoundedCapture:
    """Drain a child pipe continuously while retaining only bounded head/tail bytes."""

    def __init__(self, limit: int) -> None:
        if limit <= len(_TRUNCATION_MARKER):
            raise ValueError("Capture limit must exceed the truncation marker.")
        self.limit = limit
        retained = limit - len(_TRUNCATION_MARKER)
        self._head_limit = retained // 2
        self._tail_limit = retained - self._head_limit
        self._head = bytearray()
        self._tail = bytearray()
        self._total_bytes = 0
        self._peak_stored_bytes = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._read_fd, self._write_fd = os.pipe()
        self._thread = threading.Thread(target=self._drain, daemon=True)

    @property
    def write_fd(self) -> int:
        return self._write_fd

    @property
    def stored_bytes(self) -> int:
        with self._lock:
            return len(self._head) + len(self._tail)

    @property
    def peak_stored_bytes(self) -> int:
        with self._lock:
            return self._peak_stored_bytes

    @property
    def total_bytes(self) -> int:
        with self._lock:
            return self._total_bytes

    def start(self) -> None:
        self._thread.start()

    def close_parent_writer(self) -> None:
        if self._write_fd < 0:
            return
        try:
            os.close(self._write_fd)
        except OSError:
            pass
        self._write_fd = -1

    def finish(self) -> None:
        self.close_parent_writer()
        self._stop.set()
        self._thread.join(timeout=1.0)
        if self._thread.is_alive():
            try:
                os.close(self._read_fd)
            except OSError:
                pass
            self._thread.join(timeout=1.0)
        else:
            try:
                os.close(self._read_fd)
            except OSError:
                pass
        self._read_fd = -1

    def text(self) -> str:
        with self._lock:
            if self._total_bytes <= self.limit:
                payload = bytes(self._head + self._tail)
            else:
                payload = bytes(self._head + _TRUNCATION_MARKER + self._tail)
        return payload.decode("utf-8", errors="replace")

    def _drain(self) -> None:
        descriptor = self._read_fd
        while True:
            try:
                readable, _, _ = select.select(
                    [descriptor], [], [], 0 if self._stop.is_set() else 0.05
                )
            except (OSError, ValueError):
                return
            if not readable:
                if self._stop.is_set():
                    return
                continue
            try:
                chunk = os.read(descriptor, 64 * 1024)
            except OSError:
                return
            if not chunk:
                return
            self._retain(chunk)

    def _retain(self, chunk: bytes) -> None:
        with self._lock:
            self._total_bytes += len(chunk)
            head_remaining = self._head_limit - len(self._head)
            if head_remaining > 0:
                self._head.extend(chunk[:head_remaining])
                chunk = chunk[head_remaining:]
            if chunk:
                self._tail.extend(chunk)
                if len(self._tail) > self._tail_limit:
                    del self._tail[: len(self._tail) - self._tail_limit]
            self._peak_stored_bytes = max(
                self._peak_stored_bytes, len(self._head) + len(self._tail)
            )


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
    """Run one command with bounded capture and freeze-before-kill cleanup."""
    stdout_capture = _BoundedCapture(_MAX_ERROR_OUTPUT) if capture_output else None
    stderr_capture = _BoundedCapture(_MAX_ERROR_OUTPUT) if capture_output else None
    captures = tuple(
        capture
        for capture in (stdout_capture, stderr_capture)
        if capture is not None
    )
    for capture in captures:
        capture.start()
    stdout: str | None
    stderr: str | None
    try:
        try:
            process = subprocess.Popen(
                args,
                cwd=cwd,
                stdin=stdin,
                stdout=stdout_capture.write_fd if stdout_capture else None,
                stderr=stderr_capture.write_fd if stderr_capture else None,
                text=text,
                env=env,
                start_new_session=True,
            )
        finally:
            for capture in captures:
                capture.close_parent_writer()

        timeout_failure: subprocess.TimeoutExpired | None = None
        try:
            process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _stop_process_group(process)
            timeout_failure = exc
        except BaseException:
            _stop_process_group(process)
            raise
    finally:
        for capture in captures:
            capture.finish()

    stdout = stdout_capture.text() if stdout_capture else None
    stderr = stderr_capture.text() if stderr_capture else None
    if timeout_failure is not None:
        if timeout is None:  # pragma: no cover - impossible without a deadline.
            raise RuntimeError(
                "subprocess timeout omitted its deadline"
            ) from timeout_failure
        raise subprocess.TimeoutExpired(
            cmd=args,
            timeout=float(timeout),
            output=stdout,
            stderr=stderr,
        ) from None

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
    owned = _freeze_process_tree(process.pid)
    # TERM is delivered only after the tree is frozen. Do not resume it: a TERM
    # handler could otherwise fork, detach, and become reparented before KILL.
    _signal_process_group(process.pid, signal.SIGTERM)
    _signal_processes(owned, signal.SIGTERM)
    _signal_process_group(process.pid, signal.SIGKILL)
    _signal_processes(owned, signal.SIGKILL)
    try:
        process.communicate(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)


def _freeze_process_tree(root_pid: int) -> set[int]:
    """Stop the group, then expand and stop descendants until the set is stable."""

    owned = {root_pid}
    _signal_process_group(root_pid, signal.SIGSTOP)
    for _ in range(32):
        observed = _process_tree(root_pid, owned)
        _signal_processes(observed, signal.SIGSTOP)
        confirmed = _process_tree(root_pid, observed)
        if confirmed == observed:
            return confirmed
        owned = confirmed
    _signal_processes(owned, signal.SIGSTOP)
    return owned


def _signal_process_group(pid: int, sig: signal.Signals) -> None:
    try:
        os.killpg(pid, sig)
    except (PermissionError, ProcessLookupError):
        pass

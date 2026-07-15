from __future__ import annotations

import os
import secrets
import select
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Literal, Mapping, Sequence


_TERMINATION_GRACE_SECONDS = 0.25
_MAX_ERROR_OUTPUT = 1_000_000
_TRUNCATION_MARKER = b"\n...[subprocess output truncated]...\n"
_PROCESS_TREE_POLL_SECONDS = 0.005
_LAUNCH_GATE = (
    "import os,sys; "
    "fd=int(sys.argv[1]); "
    "released=os.read(fd,1); "
    "os.close(fd); "
    "released or sys.exit(125); "
    "os.execvpe(sys.argv[2],sys.argv[2:],os.environ)"
)
_LEASE_ENV_KEY = "CODEX_PROCESS_TREE_LEASE"
_LEASE_SCAN_ATTEMPTS = 8


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


def _tagged_lease_processes(token: str) -> set[int]:
    """Find same-user descendants that retained the per-run inherited lease tag."""

    marker = f"{_LEASE_ENV_KEY}={token}".encode()
    if sys.platform.startswith("linux"):
        found: set[int] = set()
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                environ = (entry / "environ").read_bytes()
            except (FileNotFoundError, PermissionError, ProcessLookupError):
                continue
            if marker in environ.split(b"\0"):
                found.add(int(entry.name))
        return found
    if sys.platform != "darwin":
        return set()

    # macOS has no /proc. KERN_PROCARGS2 exposes argv/environment for same-user,
    # non-platform processes; the ancestry tracker remains the complementary path
    # for protected system executables and descendants observed before reparenting.
    import ctypes

    try:
        listed = subprocess.run(
            ["/bin/ps", "-axo", "pid="],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return set()
    libc = ctypes.CDLL(None, use_errno=True)
    found = set()
    for value in listed.stdout.split():
        try:
            pid = int(value)
        except ValueError:
            continue
        mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2, pid
        size = ctypes.c_size_t(0)
        if libc.sysctl(mib, 3, None, ctypes.byref(size), None, 0) != 0:
            continue
        if size.value <= 0 or size.value > _MAX_ERROR_OUTPUT:
            continue
        payload = ctypes.create_string_buffer(size.value)
        if libc.sysctl(mib, 3, payload, ctypes.byref(size), None, 0) != 0:
            continue
        if marker in payload.raw[: size.value].split(b"\0"):
            found.add(pid)
    return found


class _ProcessTreeLease:
    """Continuously retain descendant identities even after they reparent."""

    def __init__(self, root_pid: int, token: str) -> None:
        self.root_pid = root_pid
        self.token = token
        self._owned = {root_pid}
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._track, daemon=True)

    def start(self) -> None:
        self._thread.start()
        if not self._ready.wait(timeout=1.0):
            self._stop.set()
            raise RuntimeError("process-tree lease failed to start")

    def snapshot(self) -> set[int]:
        with self._lock:
            return set(self._owned)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)

    def tagged_processes(self) -> set[int]:
        return _tagged_lease_processes(self.token)

    def _track(self) -> None:
        try:
            while not self._stop.is_set():
                observed = _process_tree(self.root_pid, self.snapshot())
                with self._lock:
                    self._owned.update(observed)
                self._ready.set()
                self._stop.wait(_PROCESS_TREE_POLL_SECONDS)
        finally:
            self._ready.set()


def _spawn_with_process_tree_lease(
    args: Sequence[str],
    **popen_kwargs: object,
) -> tuple[subprocess.Popen[str], _ProcessTreeLease]:
    """Gate command execution until continuous descendant tracking is active."""

    gate_read, gate_write = os.pipe()
    process: subprocess.Popen[str] | None = None
    lease: _ProcessTreeLease | None = None
    try:
        token = secrets.token_hex(16)
        supplied_env = popen_kwargs.get("env")
        launch_env = dict(os.environ if supplied_env is None else supplied_env)
        launch_env[_LEASE_ENV_KEY] = token
        popen_kwargs["env"] = launch_env
        process = subprocess.Popen(
            [sys.executable, "-c", _LAUNCH_GATE, str(gate_read), *args],
            pass_fds=(gate_read,),
            **popen_kwargs,
        )
        os.close(gate_read)
        gate_read = -1
        lease = _ProcessTreeLease(process.pid, token)
        lease.start()
        os.write(gate_write, b"1")
        os.close(gate_write)
        gate_write = -1
        return process, lease
    except BaseException:
        if gate_write >= 0:
            os.close(gate_write)
        if gate_read >= 0:
            os.close(gate_read)
        if lease is not None:
            lease.stop()
        if process is not None:
            _signal_process_group(process.pid, signal.SIGKILL)
            try:
                process.wait(timeout=_TERMINATION_GRACE_SECONDS)
            except (subprocess.TimeoutExpired, ChildProcessError):
                pass
        raise


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
            process, lease = _spawn_with_process_tree_lease(
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
            _stop_process_group(process, lease)
            timeout_failure = exc
        except BaseException:
            _stop_process_group(process, lease)
            raise
        else:
            _stop_process_group(process, lease)
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
    lease: _ProcessTreeLease,
) -> None:
    owned = _freeze_process_tree(process.pid, lease.snapshot())
    lease.stop()
    stable_scans = 0
    for _ in range(_LEASE_SCAN_ATTEMPTS):
        tagged = lease.tagged_processes()
        new = tagged - owned
        owned.update(tagged)
        if tagged:
            _signal_processes(tagged, signal.SIGSTOP)
        stable_scans = stable_scans + 1 if not new else 0
        if stable_scans >= 2:
            break
        threading.Event().wait(_PROCESS_TREE_POLL_SECONDS)
    # The tracker may have observed one last detached child while the known tree
    # was being frozen. Fold that final inventory into a second stable freeze.
    owned = _freeze_process_tree(process.pid, owned | lease.snapshot())
    # TERM is delivered only after the tree is frozen. Do not resume it: a TERM
    # handler could otherwise fork, detach, and become reparented before KILL.
    _signal_process_group(process.pid, signal.SIGTERM)
    _signal_processes(owned, signal.SIGTERM)
    _signal_process_group(process.pid, signal.SIGKILL)
    _signal_processes(owned, signal.SIGKILL)
    for _ in range(_LEASE_SCAN_ATTEMPTS):
        remaining = lease.tagged_processes()
        if not remaining:
            break
        _signal_processes(remaining, signal.SIGKILL)
        threading.Event().wait(_PROCESS_TREE_POLL_SECONDS)
    try:
        process.communicate(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)


def _freeze_process_tree(root_pid: int, seeds: set[int] | None = None) -> set[int]:
    """Stop the group, then expand and stop descendants until the set is stable."""

    owned = set(seeds or {root_pid})
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

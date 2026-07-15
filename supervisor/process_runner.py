from __future__ import annotations

import ctypes
import json
import os
import secrets
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Mapping, Sequence


_TERMINATION_GRACE_SECONDS = 0.25
# A macOS ownership scan inventories every same-user process twice (environment
# plus Seatbelt policy). Keep this separate from the child wait grace so two
# real post-kill empty scans remain possible on a loaded host.
_CLEANUP_CONFIRMATION_SECONDS = 3.0
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
_SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")


class ProcessContainmentError(RuntimeError):
    """Raised when owned descendant cleanup cannot be proven complete."""


@dataclass(frozen=True)
class _SandboxContainmentTag:
    root: Path
    denied_path: Path
    allowed_path: Path

    @property
    def rules(self) -> str:
        root = json.dumps(str(self.root))
        denied = json.dumps(str(self.denied_path))
        return "\n".join(
            (
                f"(deny file-read* (literal {denied}))",
                f"(deny file-write* (literal {root}) (subpath {root}))",
            )
        )

    @property
    def profile(self) -> str:
        return "\n".join(("(version 1)", "(allow default)", self.rules, ""))

    def remove(self) -> None:
        for path in (self.denied_path, self.allowed_path):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            self.root.rmdir()
        except FileNotFoundError:
            pass


def _create_sandbox_containment_tag(
    *, token: str, env: Mapping[str, str] | None
) -> _SandboxContainmentTag | None:
    """Create an immutable kernel-policy tag inherited across fork/exec on macOS."""

    if sys.platform != "darwin":
        return None
    if not _SANDBOX_EXEC.is_file():
        raise ProcessContainmentError(
            "macOS immutable process containment requires `/usr/bin/sandbox-exec`"
        )
    temp_root = Path((env or {}).get("TMPDIR", tempfile.gettempdir())).resolve()
    if not temp_root.is_dir():
        temp_root = Path(tempfile.gettempdir()).resolve()
    root = Path(tempfile.mkdtemp(prefix=f".aca-process-tree-{token}-", dir=temp_root))
    root.chmod(0o700)
    denied_path = root / "denied.tag"
    allowed_path = root / "allowed.tag"
    try:
        for path in (denied_path, allowed_path):
            descriptor = os.open(
                path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                0o400,
            )
            os.close(descriptor)
    except BaseException:
        for path in (denied_path, allowed_path):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        root.rmdir()
        raise
    return _SandboxContainmentTag(root, denied_path, allowed_path)


SandboxProfileBuilder = Callable[[Path], str]


def _compose_sandbox_profile(
    tag: _SandboxContainmentTag,
    supplemental_profile: str | None,
) -> str:
    """Compose one Seatbelt profile without allowing later rules to erase the tag."""

    if supplemental_profile is None:
        return tag.profile
    lines = supplemental_profile.splitlines()
    first_rule = next(
        (index for index, line in enumerate(lines) if line.strip()),
        None,
    )
    if first_rule is None or lines[first_rule].strip() != "(version 1)":
        raise ProcessContainmentError(
            "supplemental sandbox profile must begin with `(version 1)`"
        )
    if any(
        line.strip().startswith("(version ")
        for line in lines[first_rule + 1 :]
    ):
        raise ProcessContainmentError(
            "supplemental sandbox profile must contain exactly one version rule"
        )
    return "\n".join((*lines, tag.rules, ""))


class _BoundedCapture:
    """Drain a child pipe continuously while retaining only bounded head/tail bytes."""

    def __init__(self, limit: int) -> None:
        if limit <= len(_TRUNCATION_MARKER):
            raise ValueError("Capture limit must exceed the truncation marker.")
        self.limit = limit
        self._head_limit = limit // 2
        self._tail_limit = limit - self._head_limit
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
                retained = self.limit - len(_TRUNCATION_MARKER)
                head_limit = retained // 2
                tail_limit = retained - head_limit
                payload = bytes(
                    self._head[:head_limit]
                    + _TRUNCATION_MARKER
                    + self._tail[-tail_limit:]
                )
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
    owned = set(seeds) if seeds is not None else {root_pid}
    frontier = list(owned)
    while frontier:
        for child in children.get(frontier.pop(), set()):
            if child not in owned:
                owned.add(child)
                frontier.append(child)
    return owned


def _darwin_process_start_identity(pid: int) -> str | None:
    """Return the microsecond-resolution start identity for a Darwin process."""

    class _ProcBSDInfo(ctypes.Structure):
        _fields_ = [
            ("pbi_flags", ctypes.c_uint32),
            ("pbi_status", ctypes.c_uint32),
            ("pbi_xstatus", ctypes.c_uint32),
            ("pbi_pid", ctypes.c_uint32),
            ("pbi_ppid", ctypes.c_uint32),
            ("pbi_uid", ctypes.c_uint32),
            ("pbi_gid", ctypes.c_uint32),
            ("pbi_ruid", ctypes.c_uint32),
            ("pbi_rgid", ctypes.c_uint32),
            ("pbi_svuid", ctypes.c_uint32),
            ("pbi_svgid", ctypes.c_uint32),
            ("rfu_1", ctypes.c_uint32),
            ("pbi_comm", ctypes.c_char * 16),
            ("pbi_name", ctypes.c_char * 32),
            ("pbi_nfiles", ctypes.c_uint32),
            ("pbi_pgid", ctypes.c_uint32),
            ("pbi_pjobc", ctypes.c_uint32),
            ("e_tdev", ctypes.c_uint32),
            ("e_tpgid", ctypes.c_uint32),
            ("pbi_nice", ctypes.c_int32),
            ("pbi_start_tvsec", ctypes.c_uint64),
            ("pbi_start_tvusec", ctypes.c_uint64),
        ]

    try:
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        info = _ProcBSDInfo()
        result = libproc.proc_pidinfo(
            pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info)
        )
    except OSError:
        return None
    if result != ctypes.sizeof(info) or info.pbi_pid != pid:
        return None
    return f"darwin:{info.pbi_start_tvsec}:{info.pbi_start_tvusec}"


def _process_start_identity(pid: int) -> str | None:
    """Return a PID-reuse-resistant process start identity."""

    if sys.platform.startswith("linux"):
        try:
            payload = Path(f"/proc/{pid}/stat").read_text()
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            return None
        close_paren = payload.rfind(")")
        fields = payload[close_paren + 2 :].split() if close_paren >= 0 else []
        if len(fields) <= 19:
            return None
        return f"linux:{fields[19]}"
    if sys.platform == "darwin":
        return _darwin_process_start_identity(pid)
    try:
        listed = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "lstart="],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    started = " ".join(listed.stdout.split())
    return f"ps:{started}" if listed.returncode == 0 and started else None


def _live_process_identities(
    identities: Mapping[int, str],
) -> dict[int, str]:
    return {
        pid: identity
        for pid, identity in identities.items()
        if _process_start_identity(pid) == identity
    }


def _capture_process_identities(process_ids: set[int]) -> dict[int, str]:
    captured: dict[int, str] = {}
    for pid in process_ids:
        identity = _process_start_identity(pid)
        if identity is not None:
            captured[pid] = identity
    return captured


def _capture_required_process_identities(
    process_ids: set[int], *, source: str
) -> dict[int, str]:
    captured = _capture_process_identities(process_ids)
    missing = process_ids - set(captured)
    if missing:
        raise ProcessContainmentError(
            f"{source} found processes without stable identities: "
            f"{sorted(missing)}"
        )
    return captured


def _sandbox_tagged_processes(
    tag: _SandboxContainmentTag | None,
) -> dict[int, str]:
    """Find same-user processes carrying the immutable per-run macOS policy tag."""

    if tag is None or sys.platform != "darwin":
        return {}
    try:
        listed = subprocess.run(
            ["/bin/ps", "-axo", "pid=,uid=,state="],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
        sandbox = ctypes.CDLL(
            "/usr/lib/system/libsystem_sandbox.dylib", use_errno=True
        )
        sandbox.sandbox_check.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        ]
        sandbox.sandbox_check.restype = ctypes.c_int
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProcessContainmentError(
            f"sandbox containment discovery unavailable for `{tag.root}`: {exc}"
        ) from exc
    if listed.returncode != 0:
        raise ProcessContainmentError(
            f"sandbox containment process inventory failed for `{tag.root}`"
        )

    denied_path = ctypes.c_char_p(str(tag.denied_path).encode())
    allowed_path = ctypes.c_char_p(str(tag.allowed_path).encode())
    found: dict[int, str] = {}
    for line in listed.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        try:
            pid, uid = (int(value) for value in fields[:2])
        except ValueError:
            continue
        if fields[2].startswith("Z"):
            continue
        if uid != os.getuid() or pid == os.getpid():
            continue
        identity = _process_start_identity(pid)
        if identity is None:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                continue
            except PermissionError as exc:
                raise ProcessContainmentError(
                    f"could not verify sandbox-tagged pid {pid} identity"
                ) from exc
            raise ProcessContainmentError(
                f"could not capture sandbox-tagged live pid {pid} identity"
            )
        denied = sandbox.sandbox_check(
            pid, b"file-read-data", 1, denied_path
        )
        allowed = sandbox.sandbox_check(
            pid, b"file-read-data", 1, allowed_path
        )
        if denied < 0 or allowed < 0:
            if _process_start_identity(pid) == identity:
                raise ProcessContainmentError(
                    f"sandbox containment check failed for live pid {pid} "
                    f"under `{tag.root}`"
                )
            continue
        if denied == 1 and allowed == 0:
            found[pid] = identity
    return found


def _signal_processes(
    process_identities: Mapping[int, str], sig: signal.Signals
) -> None:
    for pid, identity in sorted(process_identities.items(), reverse=True):
        if _process_start_identity(pid) != identity:
            continue
        try:
            os.kill(pid, sig)
        except (PermissionError, ProcessLookupError):
            pass


def _tagged_lease_processes(token: str) -> dict[int, str]:
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
        return _capture_required_process_identities(
            found, source="environment containment discovery"
        )
    if sys.platform != "darwin":
        return {}

    # macOS has no /proc. KERN_PROCARGS2 exposes argv/environment for same-user,
    # non-platform processes; the ancestry tracker remains the complementary path
    # for protected system executables and descendants observed before reparenting.
    try:
        listed = subprocess.run(
            ["/bin/ps", "-axo", "pid="],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProcessContainmentError(
            f"environment containment discovery unavailable: {exc}"
        ) from exc
    if listed.returncode != 0:
        raise ProcessContainmentError(
            "environment containment process inventory failed"
        )
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
    return _capture_required_process_identities(
        found, source="environment containment discovery"
    )


class _ProcessTreeLease:
    """Continuously retain descendant identities even after they reparent."""

    def __init__(
        self,
        root_pid: int,
        token: str,
        sandbox_tag: _SandboxContainmentTag | None = None,
    ) -> None:
        self.root_pid = root_pid
        self.token = token
        self.sandbox_tag = sandbox_tag
        root_identity = _process_start_identity(root_pid)
        if root_identity is None:
            raise RuntimeError("could not capture process-tree root identity")
        self.root_identity = root_identity
        self._owned = {root_pid: root_identity}
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._track, daemon=True)

    def start(self) -> None:
        self._thread.start()
        if not self._ready.wait(timeout=1.0):
            self._stop.set()
            raise RuntimeError("process-tree lease failed to start")

    def snapshot(self) -> dict[int, str]:
        with self._lock:
            return dict(self._owned)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)

    def tagged_processes(self) -> dict[int, str]:
        sandbox_tagged = _sandbox_tagged_processes(self.sandbox_tag)
        try:
            tagged = _tagged_lease_processes(self.token)
        except ProcessContainmentError:
            if self.sandbox_tag is None:
                raise
            tagged = {}
        tagged.update(sandbox_tagged)
        return tagged

    def remove_sandbox_tag(self) -> None:
        if self.sandbox_tag is not None:
            self.sandbox_tag.remove()

    def _track(self) -> None:
        try:
            while not self._stop.is_set():
                current = self.snapshot()
                live = _live_process_identities(current)
                observed = _capture_process_identities(
                    _process_tree(self.root_pid, set(live))
                )
                with self._lock:
                    for pid, identity in observed.items():
                        self._owned[pid] = identity
                self._ready.set()
                self._stop.wait(_PROCESS_TREE_POLL_SECONDS)
        finally:
            self._ready.set()


def _spawn_with_process_tree_lease(
    args: Sequence[str],
    *,
    sandbox_profile_builder: SandboxProfileBuilder | None = None,
    immutable_sandbox_tag: bool = True,
    **popen_kwargs: object,
) -> tuple[subprocess.Popen[str], _ProcessTreeLease]:
    """Gate command execution until continuous descendant tracking is active."""

    gate_read, gate_write = os.pipe()
    process: subprocess.Popen[str] | None = None
    lease: _ProcessTreeLease | None = None
    sandbox_tag: _SandboxContainmentTag | None = None
    try:
        token = secrets.token_hex(16)
        supplied_env = popen_kwargs.get("env")
        launch_env = dict(os.environ if supplied_env is None else supplied_env)
        launch_env[_LEASE_ENV_KEY] = token
        popen_kwargs["env"] = launch_env
        sandbox_tag = (
            _create_sandbox_containment_tag(token=token, env=launch_env)
            if immutable_sandbox_tag
            else None
        )
        launch_args = list(args)
        if sandbox_tag is not None:
            supplemental_profile = (
                sandbox_profile_builder(sandbox_tag.root)
                if sandbox_profile_builder is not None
                else None
            )
            launch_args = [
                str(_SANDBOX_EXEC),
                "-p",
                _compose_sandbox_profile(sandbox_tag, supplemental_profile),
                *launch_args,
            ]
        elif sandbox_profile_builder is not None:
            raise ProcessContainmentError(
                "supplemental sandbox profile requires macOS Seatbelt containment"
            )
        process = subprocess.Popen(
            [sys.executable, "-c", _LAUNCH_GATE, str(gate_read), *launch_args],
            pass_fds=(gate_read,),
            **popen_kwargs,
        )
        os.close(gate_read)
        gate_read = -1
        lease = _ProcessTreeLease(process.pid, token, sandbox_tag)
        lease.start()
        os.write(gate_write, b"1")
        os.close(gate_write)
        gate_write = -1
        return process, lease
    except BaseException as exc:
        if gate_write >= 0:
            os.close(gate_write)
        if gate_read >= 0:
            os.close(gate_read)
        if lease is not None and process is not None:
            try:
                _stop_process_group(process, lease)
            except BaseException as cleanup_exc:
                raise ProcessContainmentError(
                    f"launch failed and containment cleanup was incomplete: "
                    f"{cleanup_exc}"
                ) from exc
        elif process is not None:
            if process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=_TERMINATION_GRACE_SECONDS)
            except (subprocess.TimeoutExpired, ChildProcessError):
                pass
        if sandbox_tag is not None and lease is None:
            sandbox_tag.remove()
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
    sandbox_profile_builder: SandboxProfileBuilder | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run one command with immutable ownership and freeze-before-kill cleanup."""

    return _run_process_group(
        args,
        cwd=cwd,
        stdin=stdin,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        check=check,
        env=env,
        sandbox_profile_builder=sandbox_profile_builder,
        immutable_sandbox_tag=True,
    )


def run_child_sandbox_process_group(
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
    """Run a trusted child-sandbox host without nesting macOS Seatbelt profiles."""

    return _run_process_group(
        args,
        cwd=cwd,
        stdin=stdin,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        check=check,
        env=env,
        sandbox_profile_builder=None,
        immutable_sandbox_tag=False,
    )


def _run_process_group(
    args: Sequence[str],
    *,
    cwd: str | Path | None,
    stdin: int | None,
    capture_output: bool,
    text: Literal[True],
    timeout: int | float | None,
    check: bool,
    env: Mapping[str, str] | None,
    sandbox_profile_builder: SandboxProfileBuilder | None,
    immutable_sandbox_tag: bool,
) -> subprocess.CompletedProcess[str]:
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
                sandbox_profile_builder=sandbox_profile_builder,
                immutable_sandbox_tag=immutable_sandbox_tag,
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
    _stop_process_group_inner(process, lease)
    lease.remove_sandbox_tag()


def _stop_process_group_inner(
    process: subprocess.Popen[str],
    lease: _ProcessTreeLease,
) -> None:
    owned = _freeze_process_tree(process.pid, lease.snapshot())
    lease.stop()
    stable_scans = 0
    for _ in range(_LEASE_SCAN_ATTEMPTS):
        try:
            tagged = lease.tagged_processes()
        except ProcessContainmentError:
            stable_scans = 0
            threading.Event().wait(_PROCESS_TREE_POLL_SECONDS)
            continue
        new = {
            pid: identity
            for pid, identity in tagged.items()
            if owned.get(pid) != identity
        }
        owned.update(tagged)
        if tagged:
            _signal_processes(tagged, signal.SIGSTOP)
        stable_scans = stable_scans + 1 if not new else 0
        if stable_scans >= 2:
            break
        threading.Event().wait(_PROCESS_TREE_POLL_SECONDS)
    # The tracker may have observed one last detached child while the known tree
    # was being frozen. Fold that final inventory into a second stable freeze.
    final_inventory = lease.snapshot()
    final_inventory.update(owned)
    owned = _freeze_process_tree(process.pid, final_inventory)
    # TERM is delivered only after the tree is frozen. Do not resume it: a TERM
    # handler could otherwise fork, detach, and become reparented before KILL.
    _signal_process_group(
        process.pid, signal.SIGTERM, expected_identity=lease.root_identity
    )
    _signal_processes(owned, signal.SIGTERM)
    _signal_process_group(
        process.pid, signal.SIGKILL, expected_identity=lease.root_identity
    )
    _signal_processes(owned, signal.SIGKILL)
    try:
        process.communicate(timeout=_TERMINATION_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        process.wait(timeout=_TERMINATION_GRACE_SECONDS)
    clean_scans = 0
    last_discovery_error: ProcessContainmentError | None = None
    remaining: dict[int, str] = {}
    confirmation_deadline = time.monotonic() + _CLEANUP_CONFIRMATION_SECONDS
    while clean_scans < 2 and time.monotonic() < confirmation_deadline:
        try:
            remaining = lease.tagged_processes()
        except ProcessContainmentError as exc:
            last_discovery_error = exc
            clean_scans = 0
            threading.Event().wait(_PROCESS_TREE_POLL_SECONDS)
            continue
        last_discovery_error = None
        if remaining:
            clean_scans = 0
            _signal_processes(remaining, signal.SIGSTOP)
            _signal_processes(remaining, signal.SIGKILL)
        else:
            clean_scans += 1
            if clean_scans >= 2:
                break
        threading.Event().wait(_PROCESS_TREE_POLL_SECONDS)
    remaining = _live_process_identities(remaining)
    if clean_scans < 2:
        tag = getattr(lease, "sandbox_tag", None)
        tag_root = f"; retained tag `{tag.root}`" if tag is not None else ""
        if last_discovery_error is not None:
            raise ProcessContainmentError(
                f"could not prove descendant cleanup: {last_discovery_error}"
                f"{tag_root}"
            ) from last_discovery_error
        if remaining:
            raise ProcessContainmentError(
                "tagged descendants survived cleanup: "
                f"{sorted(remaining)}{tag_root}"
            )
        raise ProcessContainmentError(
            "could not prove descendant cleanup with two consecutive empty "
            f"scans before deadline{tag_root}"
        )


def _freeze_process_tree(
    root_pid: int, seeds: Mapping[int, str] | None = None
) -> dict[int, str]:
    """Stop the group, then expand and stop descendants until the set is stable."""

    owned = _live_process_identities(seeds or {})
    if seeds is None:
        owned = _capture_process_identities({root_pid})
    root_identity = seeds.get(root_pid) if seeds is not None else owned.get(root_pid)
    _signal_process_group(
        root_pid, signal.SIGSTOP, expected_identity=root_identity
    )
    for _ in range(32):
        observed = _capture_process_identities(
            _process_tree(root_pid, set(_live_process_identities(owned)))
        )
        _signal_processes(observed, signal.SIGSTOP)
        confirmed = _capture_process_identities(
            _process_tree(root_pid, set(_live_process_identities(observed)))
        )
        if confirmed == observed:
            return confirmed
        owned = confirmed
    _signal_processes(owned, signal.SIGSTOP)
    return owned


def _signal_process_group(
    pid: int,
    sig: signal.Signals,
    *,
    expected_identity: str | None = None,
) -> None:
    if (
        expected_identity is not None
        and _process_start_identity(pid) != expected_identity
    ):
        return
    try:
        os.killpg(pid, sig)
    except (PermissionError, ProcessLookupError):
        pass

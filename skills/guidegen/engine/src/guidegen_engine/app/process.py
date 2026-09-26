"""Process helpers: detached spawn, whole-tree kill, build runner, free ports, readiness polling."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

WIN = sys.platform == "win32"
# Local URLs (the app, CDP, the session daemon) must never go through an HTTP(S)_PROXY from the environment.
LOCAL_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def spawn(cmd: str | list[str], cwd: Path, log_path: Path, env: dict[str, str] | None = None) -> subprocess.Popen:
    """Start a process that outlives this CLI call; stdout/stderr go to log_path."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "ab") as log:  # the child keeps its own handle; ours is closed right away
        kwargs: dict = {"cwd": str(cwd), "stdout": log, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL, "env": env}
        if WIN:
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        else:
            kwargs["start_new_session"] = True
        return subprocess.Popen(cmd, shell=isinstance(cmd, str), **kwargs)


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    if WIN:
        return _win_pid_alive(int(pid))
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _win_pid_alive(pid: int) -> bool:
    """Exact check via OpenProcess/GetExitCodeProcess (tasklist output matched PIDs as substrings)."""
    import ctypes
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED: exists but belongs to someone else
    try:
        code = wintypes.DWORD()
        return bool(k32.GetExitCodeProcess(h, ctypes.byref(code))) and code.value == 259  # STILL_ACTIVE
    finally:
        k32.CloseHandle(h)


def kill_tree(pid: int | None) -> None:
    """Kill pid and all its descendants so no orphan dev servers are left behind."""
    if not pid:
        return
    if WIN:
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
            time.sleep(1)
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def run_command(cmd: str, cwd: Path, timeout: int = 900) -> tuple[int, str]:
    """Run a build/seed command. Output goes to a temp file, not a pipe: on timeout the whole process tree is
    killed, and grandchildren (dotnet, node) holding a pipe open can no longer hang us."""
    with tempfile.TemporaryFile() as out:
        kwargs: dict = {"cwd": str(cwd), "stdout": out, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
        if WIN:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs["start_new_session"] = True  # own process group, so kill_tree gets every child
        p = subprocess.Popen(cmd, shell=True, **kwargs)
        suffix = ""
        try:
            rc = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_tree(p.pid)
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
            rc, suffix = 124, f"\n[timed out after {timeout}s]"
        out.seek(0)
        return rc, out.read().decode("utf-8", "replace") + suffix


def tail(text: str, n: int = 40) -> str:
    return "\n".join(text.rstrip().splitlines()[-n:])


def url_ready(url: str, timeout: float = 5) -> bool:
    """Any HTTP answer below 500 counts as ready (login redirects and 401s are fine)."""
    try:
        with LOCAL_OPENER.open(urllib.request.Request(url, method="GET"), timeout=timeout) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def wait_for(predicate, timeout: float, interval: float = 1.0, alive=None) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        if alive is not None and not alive():
            return False
        time.sleep(interval)
    return False

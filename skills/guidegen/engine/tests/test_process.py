"""Process, session-client and path robustness (review findings)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pytest

from guidegen_engine.app import _read_json, electron_command
from guidegen_engine.app import process as proc
from guidegen_engine.cli import G, _extract_globals
from guidegen_engine.errors import GuideGenError, HardBlocker
from guidegen_engine.paths import contained, is_inside
from guidegen_engine.session import client


def test_pid_alive_is_exact():
    assert proc.pid_alive(os.getpid())
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    assert not proc.pid_alive(p.pid)
    assert not proc.pid_alive(None) and not proc.pid_alive(0)


def test_run_command_output_and_exit_code(tmp_path):
    rc, out = proc.run_command(f'"{sys.executable}" -c "print(123); raise SystemExit(3)"', tmp_path)
    assert rc == 3 and "123" in out


def test_run_command_timeout_kills_tree(tmp_path):
    # the child spawns a grandchild that would keep a pipe open forever
    script = tmp_path / "spawn.py"
    script.write_text(
        "import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "print('started', flush=True)\n"
        "time.sleep(60)\n",
        encoding="utf-8",
    )
    t = time.time()
    rc, out = proc.run_command(f'"{sys.executable}" "{script}"', tmp_path, timeout=3)
    assert rc == 124 and "timed out" in out
    assert time.time() - t < 30


def test_spawn_does_not_keep_log_open(tmp_path):
    log = tmp_path / "app.log"
    p = proc.spawn([sys.executable, "-c", "print('hi')"], tmp_path, log)
    p.wait()
    log.unlink()  # would fail on Windows if the parent still held the handle
    assert not log.exists()


@pytest.mark.parametrize("start,expected", [
    (None, "npx electron . --remote-debugging-port=9222"),
    ("npm start", "npm start -- --remote-debugging-port=9222"),
    ("yarn start", "yarn start -- --remote-debugging-port=9222"),
    ("npm run dev -- --inspect", "npm run dev -- --inspect --remote-debugging-port=9222"),
    ("electron .", "electron . --remote-debugging-port=9222"),
])
def test_electron_command(start, expected):
    assert electron_command(start, 9222) == expected


def test_corrupt_state_files_are_empty(tmp_path):
    f = tmp_path / "app.json"
    f.write_text("{not json", encoding="utf-8")
    assert _read_json(f, {}) == {}
    assert _read_json(tmp_path / "missing.json", []) == []


def test_session_call_network_error_is_guidegen_error(ctx, monkeypatch):
    info = {"port": 1, "token": "t", "pid": os.getpid(), "kind": "web"}
    monkeypatch.setattr(client, "running", lambda c: info)
    with pytest.raises(GuideGenError, match="session call 'tree' failed"):
        client.call(ctx, "tree", {}, timeout=2)


def test_session_client_ignores_proxy_env(ctx, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:9")
    monkeypatch.setenv("http_proxy", "http://proxy.invalid:9")
    assert proc.LOCAL_OPENER.handlers  # built with an empty ProxyHandler
    assert not any(getattr(h, "proxies", None) for h in proc.LOCAL_OPENER.handlers)


def test_contained_rejects_links_out_of_repo(tmp_path):
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    link = repo / "link"
    try:
        if sys.platform == "win32":
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
            if r.returncode != 0:
                pytest.skip("cannot create a junction here")
        else:
            link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("cannot create links here")
    assert not is_inside(link / "x.png", repo)
    with pytest.raises(GuideGenError):
        contained("link/x.png", repo)
    assert contained("sub/x.png", repo) == repo / "sub" / "x.png"


def test_extract_globals_stops_at_double_dash():
    old = dict(G)
    try:
        rest = _extract_globals(["--json", "config", "set", "--", "app.args", "--out"])
        assert G["json"] is True and G["out"] is None
        assert rest == ["config", "set", "--", "app.args", "--out"]
    finally:
        G.clear()
        G.update(old)


def test_config_init_force_redetects(ctx, monkeypatch):
    from guidegen_engine import configinit

    (ctx.work / "detect.json").write_text(json.dumps({"candidates": []}), encoding="utf-8")
    calls = []
    monkeypatch.setattr(configinit, "detect", lambda repo: calls.append(repo) or {"candidates": []})
    with pytest.raises(HardBlocker):
        configinit.init_config(ctx, force=True)
    assert calls  # cache ignored with --force

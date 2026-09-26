"""CLI side of the session daemon: start/stop it and forward act/tree/shot/login calls."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from guidegen_engine.app import process as proc
from guidegen_engine.context import Ctx
from guidegen_engine.errors import GuideGenError, HardBlocker
from guidegen_engine.session.daemon import TOKEN_HEADER


def _info(ctx: Ctx) -> dict[str, Any] | None:
    f = ctx.work / "session.json"
    if not f.exists():
        return None
    try:
        info = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return info if info.get("port") else None


def _post(info: dict[str, Any], method: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{info['port']}/",
        data=json.dumps({"method": method, "params": params}).encode(),
        headers={"Content-Type": "application/json", TOKEN_HEADER: info["token"]},
        method="POST",
    )
    with proc.LOCAL_OPENER.open(req, timeout=timeout) as r:  # never via HTTP_PROXY: the token stays local
        return json.loads(r.read())


def running(ctx: Ctx) -> dict[str, Any] | None:
    info = _info(ctx)
    if not info or not proc.pid_alive(info.get("pid")):
        return None
    try:
        return info if _post(info, "ping", {}, 5).get("ok") else None
    except Exception:
        return None


def raise_from(res: dict[str, Any]) -> None:
    code = res.get("exitCode", 1)
    if code == 2 and res.get("blocker"):
        raise HardBlocker(
            res["blocker"], res.get("message", ""), res.get("question", ""), res.get("tried"), res.get("saveTo"),
            **{k: v for k, v in res.items() if k not in ("ok", "blocker", "message", "question", "tried", "saveTo", "exitCode")},
        )
    raise GuideGenError(res.get("error") or res.get("message") or "session error",
                        **{k: v for k, v in res.items() if k not in ("ok", "error", "exitCode")})


def call(ctx: Ctx, method: str, params: dict[str, Any] | None = None, timeout: float = 180) -> dict[str, Any]:
    info = running(ctx)
    if info is None:
        raise GuideGenError("No live session. Run `guidegen session start` first.")
    try:
        res = _post(info, method, params or {}, timeout)
    except urllib.error.HTTPError as e:
        raise GuideGenError(f"session daemon answered HTTP {e.code} to '{method}'. Run `guidegen session stop` and "
                            "`guidegen session start`.") from e
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        raise GuideGenError(f"session call '{method}' failed: {type(e).__name__}: {e}. If this repeats, restart the "
                            f"session (`guidegen session stop`, then `session start`); see {ctx.work / 'daemon.log'}.") from e
    if "exitCode" in res and not res.get("ok", False):
        raise_from(res)
    return res


def start(ctx: Ctx, timeout: float = 300) -> dict[str, Any]:
    info = running(ctx)
    if info:
        return {"ok": True, "alreadyRunning": True, "port": info["port"], "kind": info["kind"]}
    (ctx.work / "session.json").unlink(missing_ok=True)
    err_file = ctx.work / "session-error.json"
    err_file.unlink(missing_ok=True)
    ctx.work.mkdir(parents=True, exist_ok=True)
    p = proc.spawn(
        [sys.executable, "-m", "guidegen_engine.session.daemon", "--repo", str(ctx.repo), "--out", str(ctx.out)],
        ctx.repo, ctx.work / "daemon.out.log",
    )
    end = time.time() + timeout
    while time.time() < end:
        if err_file.exists():
            try:
                err = json.loads(err_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.3)  # the daemon may still be writing it
                continue
            raise_from(err)
        info = running(ctx)
        if info:
            return {"ok": True, "port": info["port"], "kind": info["kind"], "pid": info["pid"]}
        if p.poll() is not None and not err_file.exists():
            log = (ctx.work / "daemon.out.log").read_text(encoding="utf-8", errors="replace") if (ctx.work / "daemon.out.log").exists() else ""
            raise GuideGenError("session daemon exited during startup", output=proc.tail(log, 30))
        time.sleep(0.5)
    proc.kill_tree(p.pid)
    raise GuideGenError(f"session did not start within {timeout}s")


def stop(ctx: Ctx) -> dict[str, Any]:
    info = running(ctx)
    if info is None:
        (ctx.work / "session.json").unlink(missing_ok=True)
        return {"ok": True, "wasRunning": False}
    try:
        _post(info, "stop", {}, 10)
    except Exception:
        pass
    end = time.time() + 15
    while time.time() < end and proc.pid_alive(info["pid"]):
        time.sleep(0.3)
    if proc.pid_alive(info["pid"]):
        proc.kill_tree(info["pid"])
    (ctx.work / "session.json").unlink(missing_ok=True)
    return {"ok": True, "wasRunning": True}

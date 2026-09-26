"""Session daemon: keeps one driver alive across many short `guidegen act/tree/shot/login` CLI calls.

Security: binds 127.0.0.1 on a random port; every request must carry the random per-session token from
.work/session.json (readable by the current user only). Single-threaded on purpose: Playwright's sync
API and UIA calls must stay on one thread.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import secrets
import time
import traceback
from datetime import datetime, UTC
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from guidegen_engine.actions import Action
from guidegen_engine.errors import GuideGenError
from guidegen_engine.masking import mask, redact_text
from guidegen_engine.paths import contained, restrict_to_user

IDLE_TIMEOUT_SEC = 2 * 60 * 60
TOKEN_HEADER = "X-GuideGen-Token"


class Api:
    """RPC methods. `session` is a runtime.Session (or anything with the same shape in tests)."""

    def __init__(self, ctx, session) -> None:
        self.ctx = ctx
        self.session = session
        self.stopping = False
        self.shot_n = 0

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        fn = getattr(self, f"m_{method}", None)
        if fn is None:
            raise GuideGenError(f"unknown method {method}")
        return fn(**params)

    def m_ping(self) -> dict[str, Any]:
        return {"ok": True, "pid": os.getpid()}

    def m_act(self, action: dict[str, Any]) -> dict[str, Any]:
        a = Action.model_validate(action)
        res = self.session.perform(a, "explore")
        res.setdefault("view", self._view())
        return res

    def m_tree(self, depth: int = 6) -> dict[str, Any]:
        # field values in the tree (emails, IDs...) get the same redactPatterns as screenshots
        tree, _ = redact_text(self.session.driver.tree(depth), self.session.cfg.safety.redact_patterns)
        return {"ok": True, "view": self._view(), "tree": tree}

    def m_shot(self, file: str | None = None) -> dict[str, Any]:
        self.shot_n += 1
        target = contained(file, self.ctx.out, "--file") if file else self.ctx.work / "shots" / f"shot-{self.shot_n:03d}.png"
        img, n, _ = self.session.shot()
        self.session.save(img, target)
        return {"ok": True, "file": str(target), "redactions": n, "view": self._view()}

    def m_login(self, force: bool = False) -> dict[str, Any]:
        return self.session.login(force=force)

    def m_reset(self) -> dict[str, Any]:
        self.session.reset()
        return {"ok": True, "view": self._view()}

    def m_stop(self) -> dict[str, Any]:
        self.stopping = True
        return {"ok": True}

    def _view(self) -> str:
        try:
            return self.session.driver.current_view_id()
        except Exception:
            return "?"


def make_handler(api: Api, token: str, log):
    class Handler(BaseHTTPRequestHandler):
        # a local client that connects and sends nothing must not block this single-threaded server forever
        timeout = 30

        def do_POST(self) -> None:  # noqa: N802
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = 0
            # Always read the body first: replying with unread request data makes Windows reset the
            # connection, so the client sees ConnectionAborted instead of the 403.
            raw = self.rfile.read(min(max(length, 0), 1_000_000)) if length else b""
            if not hmac.compare_digest(self.headers.get(TOKEN_HEADER, ""), token):
                self._send(403, {"ok": False, "error": "invalid session token"})
                return
            try:
                body = json.loads(raw or b"{}")
                result = api.call(body.get("method", ""), body.get("params") or {})
                self._send(200, result)
            except GuideGenError as e:
                self._send(200, {**e.to_dict(), "exitCode": e.exit_code})
            except Exception as e:
                log(mask(traceback.format_exc()))
                self._send(200, {"ok": False, "error": f"{type(e).__name__}: {e}", "exitCode": 1})

        def do_GET(self) -> None:  # noqa: N802
            self._send(405, {"ok": False, "error": "POST only"})

        def _send(self, code: int, obj: dict[str, Any]) -> None:
            data = json.dumps(mask(obj), default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, fmt: str, *args: Any) -> None:
            log(mask(fmt % args))

    return Handler


def serve(ctx, session, on_ready=None) -> None:
    session_file = ctx.work / "session.json"
    log_file = ctx.work / "daemon.log"

    def log(msg: str) -> None:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")

    token = secrets.token_urlsafe(32)
    api = Api(ctx, session)
    server = HTTPServer(("127.0.0.1", 0), make_handler(api, token, log))
    server.timeout = 30
    port = server.server_address[1]
    session_file.write_text("{}", encoding="utf-8")
    restrict_to_user(session_file)
    session_file.write_text(
        json.dumps({"port": port, "token": token, "pid": os.getpid(), "kind": session.driver.kind,
                    "startedAt": datetime.now(UTC).isoformat()}),
        encoding="utf-8",
    )
    log(f"listening on 127.0.0.1:{port}")
    if on_ready:
        on_ready(port, token)
    last = time.time()
    try:
        while not api.stopping:
            before = time.time()
            server.handle_request()
            if time.time() - before < server.timeout - 0.5:
                last = time.time()
            elif time.time() - last > IDLE_TIMEOUT_SEC:
                log("idle timeout")
                break
    finally:
        server.server_close()
        try:
            session.driver.close()
        except Exception:
            pass
        session_file.unlink(missing_ok=True)
        log("stopped")


def main() -> None:
    from guidegen_engine.app import controller
    from guidegen_engine.config import load_config
    from guidegen_engine.context import Ctx
    from guidegen_engine.drivers import make_driver
    from guidegen_engine.runtime import Session

    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    ctx = Ctx.create(args.repo, args.out)
    err_file = ctx.work / "session-error.json"
    err_file.unlink(missing_ok=True)
    try:
        cfg = load_config(ctx.config_path)
        ctl = controller(ctx, cfg)
        if not ctl.is_running():
            ctl.start()
        driver = make_driver(cfg, ctl)
        try:
            driver.launch()
        except Exception:
            driver.close()  # never leave a half-started browser behind
            raise
        session = Session(cfg, driver)
    except GuideGenError as e:
        err_file.write_text(json.dumps({**mask(e.to_dict()), "exitCode": e.exit_code}), encoding="utf-8")
        raise SystemExit(e.exit_code) from e
    except Exception as e:
        err_file.write_text(json.dumps({"ok": False, "error": mask(f"{type(e).__name__}: {e}"), "exitCode": 1}), encoding="utf-8")
        raise SystemExit(1) from e
    serve(ctx, session)


if __name__ == "__main__":
    main()

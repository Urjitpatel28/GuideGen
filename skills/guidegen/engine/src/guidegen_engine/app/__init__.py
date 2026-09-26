"""`guidegen app start|stop|status`: build, seed, launch, wait for ready, stop the whole process tree."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from guidegen_engine.app import process as proc
from guidegen_engine.app.guard import check_localhost
from guidegen_engine.config.models import Config
from guidegen_engine.context import Ctx
from guidegen_engine.errors import GuideGenError, HardBlocker
from guidegen_engine.paths import contained, rel


class AppController:
    def __init__(self, ctx: Ctx, cfg: Config) -> None:
        self.ctx = ctx
        self.cfg = cfg
        self.state_path = ctx.work / "app.json"
        self.log_path = ctx.work / "app.log"
        self.notes_path = ctx.work / "notes.json"

    # ---------- state ----------
    def state(self) -> dict[str, Any]:
        return _read_json(self.state_path, {})

    def _save_state(self, st: dict[str, Any]) -> None:
        self.ctx.work.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(st, indent=2), encoding="utf-8")

    def note(self, kind: str, message: str) -> None:
        notes = _read_json(self.notes_path, [])
        if not any(n["kind"] == kind and n["message"] == message for n in notes):
            notes.append({"kind": kind, "message": message})
        self.notes_path.write_text(json.dumps(notes, indent=2), encoding="utf-8")

    @property
    def cwd(self) -> Path:
        return contained(self.cfg.app.working_dir, self.ctx.repo, "app.workingDir")

    def is_running(self) -> bool:
        st = self.state()
        if st.get("external"):
            return proc.url_ready(st.get("url") or "")
        return proc.pid_alive(st.get("pid"))

    # ---------- phases ----------
    def guard(self) -> list[dict[str, str]]:
        return check_localhost(self.ctx.repo, self.cfg.app.url, self.cfg.safety.allow_remote_backends)

    def build(self) -> dict[str, Any]:
        cmd = self.cfg.app.build
        if not cmd:
            return {"skipped": True}
        t = time.time()
        rc, out = proc.run_command(cmd, self.cwd)
        (self.ctx.work / "build.log").write_text(out, encoding="utf-8")
        if rc != 0:
            raise HardBlocker(
                "build",
                f"Build failed (exit {rc}): {cmd}",
                question="The build failed. Fix the error below (or tell me the correct build command and I'll save it to app.build), then say 'continue'.",
                tried=[cmd],
                save_to="app.build",
                output=proc.tail(out, 40),
            )
        return {"command": cmd, "seconds": round(time.time() - t, 1)}

    def seed(self) -> dict[str, Any]:
        s = self.cfg.seed
        if not (s.enabled and s.command):
            return {"skipped": True, "reason": "seed disabled or no command"}
        rc, out = proc.run_command(s.command, self.cwd)
        (self.ctx.work / "seed.log").write_text(out, encoding="utf-8")
        if rc != 0:
            self.note("seed", f"Seed command failed (exit {rc}); screenshots may show empty lists. See .work/seed.log.")
            return {"ok": False, "exit": rc, "output": proc.tail(out, 15)}
        return {"ok": True, "command": s.command}

    def resolve_executable(self) -> Path:
        exe = self.cfg.app.executable
        if not exe:
            raise HardBlocker("config", "app.executable is not set.", question="Which .exe should I launch? I'll save it to app.executable.", save_to="app.executable")
        p = contained(exe, self.ctx.repo, "app.executable")
        if p.exists():
            return p
        # TFM / RID / configuration may differ from the guess: look for the same file name under bin/.
        proj_dir = p
        while proj_dir.name.lower() != "bin" and proj_dir != self.ctx.repo and proj_dir.parent != proj_dir:
            proj_dir = proj_dir.parent
        search_root = proj_dir.parent if proj_dir.name.lower() == "bin" else self.ctx.repo
        hits = sorted(search_root.rglob(p.name), key=lambda x: x.stat().st_mtime, reverse=True)
        hits = [h for h in hits if "obj" not in h.parts and "ref" not in h.parts]
        if hits:
            return hits[0]
        raise HardBlocker(
            "start",
            f"Executable not found: {exe}",
            question="The build succeeded but I can't find the .exe. What is its path (relative to the repo)? I'll save it to app.executable.",
            tried=[f"looked for {p.name} under {rel(search_root, self.ctx.repo)}"],
            save_to="app.executable",
        )

    def launch(self) -> dict[str, Any]:
        app = self.cfg.app
        env = dict(os.environ)
        timeout = (app.ready_when.timeout_sec if app.ready_when else 120)
        st: dict[str, Any] = {"kind": app.kind, "startedAt": datetime.now(UTC).isoformat()}
        t = time.time()

        if app.kind == "web":
            url = (app.ready_when.url if app.ready_when and app.ready_when.url else None) or app.url
            if not url:
                raise HardBlocker("config", "app.url is not set.", question="What URL does the app serve on locally? I'll save it to app.url.", save_to="app.url")
            if proc.url_ready(url, 2):
                st.update({"external": True, "url": url, "pid": None})
                self._save_state(st)
                return {"ready": True, "url": url, "reused": True, "seconds": 0}
            if not app.start:
                raise HardBlocker("config", "app.start is not set.", question="What command starts the app locally? I'll save it to app.start.", save_to="app.start")
            p = proc.spawn(app.start, self.cwd, self.log_path, env)
            st.update({"pid": p.pid, "url": url})
            self._save_state(st)
            if not proc.wait_for(lambda: proc.url_ready(url, 3), timeout, 1.5, alive=lambda: p.poll() is None):
                self._fail_start(p.pid, app.start, f"{url} did not answer within {timeout}s")
            return {"ready": True, "url": url, "pid": p.pid, "seconds": round(time.time() - t, 1)}

        if app.kind == "electron":
            port = proc.free_port()
            cmd = electron_command(app.start, port)
            p = proc.spawn(cmd, self.cwd, self.log_path, env)
            st.update({"pid": p.pid, "cdpPort": port})
            self._save_state(st)
            cdp = f"http://127.0.0.1:{port}/json/version"
            if not proc.wait_for(lambda: proc.url_ready(cdp, 2), timeout, 1.0, alive=lambda: p.poll() is None):
                self._fail_start(p.pid, cmd, f"Electron did not open a debugging port within {timeout}s")
            time.sleep(1.5)  # first window
            return {"ready": True, "cdpPort": port, "pid": p.pid, "seconds": round(time.time() - t, 1)}

        # desktop
        exe = self.resolve_executable()
        p = proc.spawn([str(exe), *app.args], exe.parent, self.log_path, env)
        st.update({"pid": p.pid, "executable": rel(exe, self.ctx.repo)})
        self._save_state(st)
        title = app.ready_when.window_title if app.ready_when else None
        if not proc.wait_for(lambda: _window_visible(p.pid, title), timeout, 1.0, alive=lambda: p.poll() is None):
            self._fail_start(p.pid, str(exe), f"no main window{f' titled {title!r}' if title else ''} within {timeout}s")
        return {"ready": True, "pid": p.pid, "executable": rel(exe, self.ctx.repo), "seconds": round(time.time() - t, 1)}

    def _fail_start(self, pid: int, cmd: str, why: str) -> None:
        proc.kill_tree(pid)
        log = self.log_path.read_text(encoding="utf-8", errors="replace") if self.log_path.exists() else ""
        self.state_path.unlink(missing_ok=True)
        raise HardBlocker(
            "start",
            f"App did not become ready: {why}",
            question="The app failed to start. Check the output below; tell me the correct start command/URL/exe (saved to app.*) or fix the error, then say 'continue'.",
            tried=[cmd],
            save_to="app.start",
            output=proc.tail(log, 40),
        )

    def start(self, build: bool = True) -> dict[str, Any]:
        result: dict[str, Any] = {"ok": True}
        if self.is_running():
            return {"ok": True, "alreadyRunning": True, **self.state()}
        result["guard"] = self.guard()
        if build:
            result["build"] = self.build()
        result["seed"] = self.seed()
        result.update(self.launch())
        return result

    def stop(self) -> dict[str, Any]:
        st = self.state()
        if st.get("pid") and not st.get("external"):
            proc.kill_tree(st["pid"])
        self.state_path.unlink(missing_ok=True)
        return {"ok": True, "stopped": st.get("pid"), "external": bool(st.get("external"))}

    def restart(self) -> dict[str, Any]:
        """Used by capture to reset desktop/Electron apps to their start state (no rebuild)."""
        self.stop()
        time.sleep(0.5)
        return self.launch()


def _read_json(path: Path, default: Any) -> Any:
    """A missing or corrupt state file (e.g. a crash mid-write) counts as empty rather than crashing the CLI."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _window_visible(pid: int, title: str | None) -> bool:
    try:
        from pywinauto import Desktop

        for w in Desktop(backend="uia").windows(process=pid):
            if w.is_visible() and (not title or title.lower() in (w.window_text() or "").lower()):
                return True
    except Exception:
        return False
    return False


def electron_command(start: str | None, port: int) -> str:
    """Start command with the CDP flag. npm/yarn/pnpm scripts only pass flags on to the app after `--`
    (yarn and pnpm accept it too)."""
    base = (start or "npx electron .").strip()
    flag = f"--remote-debugging-port={port}"
    first = base.split()[0].lower() if base.split() else ""
    if first in ("npm", "npm.cmd", "yarn", "yarn.cmd", "pnpm", "pnpm.cmd") and " -- " not in f" {base} ":
        return f"{base} -- {flag}"
    return f"{base} {flag}"


def controller(ctx: Ctx, cfg: Config) -> AppController:
    if cfg.app.is_desktop and os.name != "nt":
        raise GuideGenError(f"{cfg.app.kind} apps can only be driven on Windows.")
    return AppController(ctx, cfg)

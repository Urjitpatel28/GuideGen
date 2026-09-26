"""`guidegen config init|set|show`: create the config from detection, persist blocker answers."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from guidegen_engine.brand import detect_brand
from guidegen_engine.config.loader import read_raw, save_config, validation_errors
from guidegen_engine.config.models import SCHEMA_URL, Config
from guidegen_engine.context import Ctx
from guidegen_engine.detect import detect
from guidegen_engine.errors import GuideGenError, HardBlocker
from guidegen_engine.paths import init_out_dir


def load_detect(ctx: Ctx, refresh: bool = False) -> dict[str, Any]:
    """Cached detection result; refresh (config init --force) detects again."""
    f = ctx.work / "detect.json"
    if f.exists() and not refresh:
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass  # corrupt cache: detect again
    init_out_dir(ctx.out)
    res = detect(ctx.repo)
    f.write_text(json.dumps(res, indent=2), encoding="utf-8")
    return res


def init_config(ctx: Ctx, candidate: int | None = None, force: bool = False) -> dict[str, Any]:
    if ctx.config_path.exists() and not force:
        return {"ok": True, "created": False, "config": str(ctx.config_path), "note": "config exists; use --force to recreate"}
    det = load_detect(ctx, refresh=force)
    cands = det.get("candidates", [])
    if not cands:
        raise HardBlocker(
            "config", "Could not detect a supported app (web, Electron, WPF, WinForms, WinUI).",
            question="What kind of app is this and how do I start it (command + URL, or path to the .exe)? I'll save it to guidegen.config.json.",
            tried=["package.json frameworks", "*.csproj (UseWPF / UseWindowsForms / WindowsAppSDK / Sdk.Web)"],
            save_to="app",
        )
    if candidate is None:
        if len(cands) > 1:
            raise HardBlocker(
                "config", f"Found {len(cands)} runnable apps in this repo.",
                question="Which app should the manual document? " + "; ".join(
                    f"[{c['rank']}] {c['kind']}/{c['framework']} at {c['project']}" for c in cands
                ) + ". Reply with the number.",
                tried=["guidegen detect"], save_to="app", candidates=cands,
            )
        candidate = 1
    try:
        c = next(x for x in cands if x["rank"] == candidate)
    except StopIteration:
        raise GuideGenError(f"no candidate {candidate}") from None

    app: dict[str, Any] = {"kind": c["kind"], "workingDir": c.get("workingDir") or "."}
    for k in ("build", "start", "url", "executable", "readyWhen"):
        if c.get(k):
            app[k] = c[k]
    seed = next((s for s in det.get("seedCandidates", []) if s.get("command")), None)
    cfg: dict[str, Any] = {
        "$schema": SCHEMA_URL,
        "app": app,
        "auth": {"required": False, "usernameEnv": "GUIDEGEN_USER", "passwordEnv": "GUIDEGEN_PASSWORD", "loginSteps": []},
        "seed": {"command": seed["command"], "enabled": True} if seed else {"command": None, "enabled": False},
        "safety": {"allowRemoteBackends": False, "allowDestructive": [], "redactPatterns": Config.model_fields["safety"].default.redact_patterns, "redactSelectors": []},
        "budget": {"maxScreens": 60, "maxTasks": 15},
        "brand": {k: v for k, v in detect_brand(ctx.repo)["brand"].items() if v},
        "graphify": {"use": "auto"},
    }
    if ctx.config_path.exists():
        # --force re-detects the app but must not forget the developer's intake answer (never ask twice)
        try:
            old_brief = read_raw(ctx.config_path).get("brief")
        except GuideGenError:
            old_brief = None
        if old_brief:
            cfg["brief"] = old_brief
    init_out_dir(ctx.out)
    save_config(ctx.config_path, cfg)
    return {"ok": True, "created": True, "config": str(ctx.config_path), "app": app, "seed": cfg["seed"], "brand": cfg["brand"],
            "authHints": det.get("authHints", [])}


def _parse_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def set_value(ctx: Ctx, key: str, raw: str) -> dict[str, Any]:
    """Dotted camelCase key, e.g. `auth.usernameEnv GUIDEGEN_USER` or `safety.allowDestructive '["Delete"]'`."""
    data = read_raw(ctx.config_path)
    cur = data
    parts = key.split(".")
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
        if not isinstance(cur, dict):
            raise GuideGenError(f"{key}: '{p}' is not an object")
    cur[parts[-1]] = _parse_value(raw)
    try:
        Config.model_validate(data)
    except ValidationError as e:
        raise GuideGenError(f"invalid value for {key}", errors=validation_errors(e)) from e
    save_config(ctx.config_path, data)
    return {"ok": True, "set": key}

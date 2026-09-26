"""Destructive-action guard, enforced in the engine for both `act` and `capture` (not only in SKILL.md).

A click/double-click/press/select on a control whose accessible name, text or target matches one of the
words below (whole word, case-insensitive) is refused unless the control is listed in safety.allowDestructive.
A key press with no target is checked against the focused control. Editable text inputs are never considered
destructive, so typing into an "Email" field is fine.

`goto` to an absolute URL is refused unless the host is local or the app's own host (see check_goto).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from guidegen_engine.actions import Action, Target
from guidegen_engine.drivers.base import ElementInfo

DESTRUCTIVE_WORDS = [
    "delete", "remove", "pay", "purchase", "buy", "checkout", "send", "email", "publish",
    "submit payment", "transfer", "unsubscribe", "deactivate", "reset", "drop",
]
_PATTERN = re.compile(r"\b(" + "|".join(re.escape(w) for w in sorted(DESTRUCTIVE_WORDS, key=len, reverse=True)) + r")\b", re.I)
GUARDED_ACTIONS = {"click", "double_click", "press", "select"}
# Roles that are editable fields. Only used as a fallback: ElementInfo.is_input is the primary signal, because
# a bare tag name like "input" also covers <input type=submit value="Delete">.
INPUT_ROLES = {"textbox", "searchbox", "combobox", "edit", "spinbutton", "textarea"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
SAFE_KEYS = {"tab", "escape", "esc", "arrowdown", "arrowup", "arrowleft", "arrowright", "down", "up", "left", "right", "home", "end", "pageup", "pagedown"}


def _allowed(allow: list[Any], candidates: list[str], target: Target | None) -> bool:
    lowered = {c.strip().lower() for c in candidates if c}
    for entry in allow:
        if isinstance(entry, str):
            if entry.strip().lower() in lowered:
                return True
        else:
            t = entry if isinstance(entry, Target) else Target.model_validate(entry)
            if target and t.by == target.by and t.value == target.value and (t.name is None or t.name == target.name):
                return True
    return False


def check(action: Action, info: ElementInfo | None, allow: list[Any]) -> str | None:
    """Return a refusal reason, or None when the action may run.

    `info` is the target element, or for a press with no target the focused element (None = nothing focused).
    """
    if action.action not in GUARDED_ACTIONS:
        return None
    if action.action == "press" and (action.value or "").replace(" ", "").lower() in SAFE_KEYS:
        return None
    if action.action == "select":
        # Choosing an option: only the option text matters (a field labelled "Email" is fine to use).
        candidates = [action.value or ""]
    else:
        if info is not None and (info.is_input or info.role.lower() in INPUT_ROLES):
            return None
        candidates = [info.name] if info is not None else []
        if action.target is not None:
            candidates += [action.target.value, action.target.name or ""]
    for c in candidates:
        m = _PATTERN.search(c or "")
        if m:
            if _allowed(allow, candidates, action.target):
                return None
            return (
                f"'{c.strip()[:60]}' looks destructive (matches '{m.group(1).lower()}'). Refused by the engine; "
                "add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app."
            )
    return None

def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().strip("[]")


def check_goto(action: Action, own_urls: list[str | None]) -> str | None:
    """Refuse `goto` to an absolute URL on another host. Relative paths always stay on the app."""
    value = (action.value or "").strip()
    if action.action != "goto" or "://" not in value:
        return None
    scheme = value.split("://", 1)[0].lower()
    if scheme not in ("http", "https"):
        return f"goto '{value[:80]}' uses scheme '{scheme}'. Refused by the engine; use a path inside the app."
    host = _host(value)
    own = {_host(u) for u in own_urls if u and "://" in u}
    if host in LOCAL_HOSTS or host.endswith(".localhost") or host.startswith("127.") or host in own:
        return None
    return (
        f"goto '{value[:80]}' leaves the app (host '{host}'). Refused by the engine so exploration cannot reach "
        "real sites; use a path relative to app.url instead."
    )

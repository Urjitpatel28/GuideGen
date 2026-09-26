"""Secret handling: `${VAR}` resolution and masking of resolved values everywhere we print or log."""

from __future__ import annotations

import os
import re
from typing import Any
from collections.abc import Iterable, Mapping

PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
MASK = "***"
REDACTED = "[redacted]"

_secret_values: set[str] = set()


def register_secret(value: str | None) -> None:
    if value and len(value) >= 3:
        _secret_values.add(value)


def register_env_secrets(names: list[str | None], env: Mapping[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    for name in names:
        if name and env.get(name):
            register_secret(env[name])


def clear_secrets() -> None:
    _secret_values.clear()


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER.findall(text or "")


def resolve(text: str, env: Mapping[str, str] | None = None) -> str:
    """Replace ${VAR} with the env value. Every resolved value is registered for masking."""
    env = os.environ if env is None else env

    def sub(m: re.Match[str]) -> str:
        name = m.group(1)
        if name not in env:
            from guidegen_engine.errors import HardBlocker

            raise HardBlocker(
                "login",
                f"Environment variable {name} is not set.",
                question=(
                    f"Set `{name}` in your shell (use a test account, never a real one), then say 'continue'. "
                    "Only the variable name is stored in guidegen-out/guidegen.config.json."
                ),
                tried=[f"read ${{{name}}} from the environment"],
                save_to="auth",
            )
        register_secret(env[name])
        return env[name]

    return PLACEHOLDER.sub(sub, text)


def mask(obj: Any) -> Any:
    """Return a copy of obj with every registered secret value replaced by ***."""
    if isinstance(obj, str):
        for value in sorted(_secret_values, key=len, reverse=True):
            obj = obj.replace(value, MASK)
        return obj
    if isinstance(obj, dict):
        return {k: mask(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [mask(v) for v in obj]
    return obj


def redact_text(text: str, patterns: Iterable[str]) -> tuple[str, int]:
    """Replace every match of the redaction regexes with [redacted]. Invalid patterns are skipped."""
    total = 0
    for pat in patterns:
        try:
            text, n = re.subn(pat, REDACTED, text)
        except re.error:
            continue
        total += n
    return text, total

"""Load/save/merge guidegen.config.json with field-level validation errors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from guidegen_engine.config.models import Config
from guidegen_engine.errors import GuideGenError, HardBlocker
from guidegen_engine.masking import register_env_secrets


def validation_errors(e: ValidationError) -> list[dict[str, str]]:
    return [
        {"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"]}
        for err in e.errors()
    ]


def config_exists(path: Path) -> bool:
    return path.exists()


def read_raw(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise GuideGenError(f"{path.name} is not valid JSON: {e}", file=str(path)) from e


def load_config(path: Path) -> Config:
    if not path.exists():
        raise HardBlocker(
            "config",
            f"No config at {path}.",
            question="Run `guidegen detect` and `guidegen config init` first (the skill does this automatically).",
            tried=[f"read {path}"],
        )
    try:
        cfg = Config.model_validate(read_raw(path))
    except ValidationError as e:
        raise GuideGenError(
            f"{path.name} is invalid", file=str(path), errors=validation_errors(e)
        ) from e
    register_env_secrets([cfg.auth.username_env, cfg.auth.password_env])
    return cfg


def save_config(path: Path, cfg: Config | dict[str, Any]) -> None:
    data = cfg.dump() if isinstance(cfg, Config) else cfg
    Config.model_validate(data)  # never write an invalid config
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def merge_config(path: Path, patch: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
    """Deep-merge patch into the existing config. Existing developer values win unless overwrite."""
    raw = read_raw(path) if path.exists() else {}

    def merge(dst: dict, src: dict) -> None:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                merge(dst[k], v)
            elif overwrite or dst.get(k) in (None, "", [], {}):
                dst[k] = v

    merge(raw, patch)
    save_config(path, raw)
    return raw

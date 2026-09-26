from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from guidegen_engine.config import load_config
from guidegen_engine.configinit import set_value
from guidegen_engine.errors import GuideGenError, HardBlocker
from guidegen_engine.masking import mask, register_env_secrets, resolve
from guidegen_engine.paths import OUT_GITIGNORE, contained, init_out_dir, resolve_out

from conftest import base_config, write_config


def test_defaults_and_roundtrip(ctx, cfg):
    write_config(ctx, cfg)
    loaded = load_config(ctx.config_path)
    assert loaded.budget.max_screens == 60
    assert loaded.app.viewport.width == 1440
    assert loaded.safety.redact_patterns  # email pattern by default
    assert json.loads(ctx.config_path.read_text())["$schema"].endswith("config.schema.json")


def test_field_level_errors(ctx):
    ctx.config_path.write_text(json.dumps({"app": {"kind": "mainframe"}, "budget": {"maxScreens": "lots"}}))
    with pytest.raises(GuideGenError) as e:
        load_config(ctx.config_path)
    fields = {err["field"] for err in e.value.data["errors"]}
    assert "app.kind" in fields and "budget.maxScreens" in fields


def test_env_names_only(ctx):
    with pytest.raises(ValidationError):
        base_config(auth={"usernameEnv": "hunter2 is my password"})


def test_out_must_stay_inside_repo(ctx):
    assert resolve_out(ctx.repo, None) == ctx.repo / "guidegen-out"
    assert resolve_out(ctx.repo, "docs/manual") == ctx.repo / "docs" / "manual"
    with pytest.raises(GuideGenError):
        resolve_out(ctx.repo, "../elsewhere")
    with pytest.raises(GuideGenError):
        contained("src/../../x", ctx.repo)


def test_out_folder_gitignore(ctx):
    assert (ctx.out / ".gitignore").read_text() == OUT_GITIGNORE
    assert "!brief.md" in OUT_GITIGNORE  # the distilled brief is kept so --update never asks again
    assert not (ctx.repo / ".gitignore").exists()
    # an old default is upgraded in place; a developer-edited one is left alone
    (ctx.out / ".gitignore").write_text("*\n!.gitignore\n!guidegen.config.json\n!manual.yaml\n", encoding="utf-8", newline="\n")
    init_out_dir(ctx.out)
    assert (ctx.out / ".gitignore").read_text() == OUT_GITIGNORE
    (ctx.out / ".gitignore").write_text("custom\n", encoding="utf-8")
    init_out_dir(ctx.out)
    assert (ctx.out / ".gitignore").read_text() == "custom\n"


def test_secret_values_never_printed(monkeypatch):
    monkeypatch.setenv("GUIDEGEN_PASSWORD", "S3cr3t-Value!")
    monkeypatch.setenv("GUIDEGEN_USER", "tester@example.com")
    register_env_secrets(["GUIDEGEN_USER", "GUIDEGEN_PASSWORD"])
    typed = resolve("${GUIDEGEN_PASSWORD}")
    assert typed == "S3cr3t-Value!"
    out = json.dumps(mask({"action": "type", "value": typed, "log": ["user tester@example.com logged in"]}))
    assert "S3cr3t-Value!" not in out and "tester@example.com" not in out


def test_missing_env_is_hard_blocker(monkeypatch):
    monkeypatch.delenv("NOPE_VAR", raising=False)
    with pytest.raises(HardBlocker) as e:
        resolve("${NOPE_VAR}")
    assert e.value.exit_code == 2 and e.value.blocker == "login"


def test_config_set(ctx, cfg):
    write_config(ctx, cfg)
    set_value(ctx, "safety.allowDestructive", '["Delete"]')
    set_value(ctx, "auth.required", "true")
    loaded = load_config(ctx.config_path)
    assert loaded.safety.allow_destructive == ["Delete"] and loaded.auth.required is True
    with pytest.raises(GuideGenError):
        set_value(ctx, "app.kind", "cobol")

"""Pydantic models for guidegen-out/guidegen.config.json. Secrets are only ever env var names."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import Field, field_validator

from guidegen_engine.actions import Action, Model, Target

SCHEMA_URL = "https://raw.githubusercontent.com/guidegen/guidegen/main/skills/guidegen/schema/config.schema.json"
EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

AppKind = Literal["web", "electron", "wpf", "winforms", "winui"]
DESKTOP_KINDS = ("wpf", "winforms", "winui")


class Size(Model):
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class ReadyWhen(Model):
    url: str | None = None
    window_title: str | None = None
    timeout_sec: int = Field(default=120, gt=0)


class AppConfig(Model):
    kind: AppKind
    build: str | None = None
    start: str | None = None
    working_dir: str = "."
    url: str | None = None
    executable: str | None = None
    args: list[str] = []
    ready_when: ReadyWhen | None = None
    window: Size = Size(width=1280, height=800)
    viewport: Size = Size(width=1440, height=900)

    @property
    def is_desktop(self) -> bool:
        return self.kind in DESKTOP_KINDS


class AuthConfig(Model):
    required: bool = False
    username_env: str | None = None
    password_env: str | None = None
    login_steps: list[Action] = []

    @field_validator("username_env", "password_env")
    @classmethod
    def _env_name(cls, v: str | None) -> str | None:
        if v is not None and not v.replace("_", "").isalnum():
            raise ValueError("must be an environment variable NAME, never a value")
        return v


class SeedConfig(Model):
    command: str | None = None
    enabled: bool = False
    # Re-run the seed before each task capture so data-changing tasks replay identically.
    rerun_before_tasks: bool = True


class SafetyConfig(Model):
    allow_remote_backends: bool = False
    allow_destructive: list[str | Target] = []
    redact_patterns: list[str] = [EMAIL_PATTERN]
    redact_selectors: list[str] = []

    @field_validator("redact_patterns")
    @classmethod
    def _regexes(cls, v: list[str]) -> list[str]:
        for p in v:
            try:
                re.compile(p)
            except re.error as e:
                raise ValueError(f"invalid regular expression {p!r}: {e}") from e
        return v


class BudgetConfig(Model):
    max_screens: int = Field(default=60, ge=0)
    max_tasks: int = Field(default=15, ge=0)


class BrandConfig(Model):
    product_name: str | None = None
    company_name: str | None = None
    logo: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    version: str | None = None

    @field_validator("primary_color", "accent_color")
    @classmethod
    def _hex(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v.startswith("#") or len(v) not in (4, 7):
            raise ValueError("must be a hex color like #1F4E79")
        int(v[1:], 16)
        return v.upper()


class GraphifyConfig(Model):
    use: Literal["auto"] | bool = "auto"


BriefKind = Literal["old-manual", "reference-manual", "outline", "process"]


class BriefSource(Model):
    """Something the developer already has that should steer the manual. Only a location, never the content."""

    kind: BriefKind
    path: str | None = None  # repo-relative or absolute file path
    url: str | None = None  # http(s) page or PDF
    note: str | None = None  # e.g. "chapters 1-3 only"

    @field_validator("url")
    @classmethod
    def _http(cls, v: str | None) -> str | None:
        if v is not None and not v.lower().startswith(("http://", "https://")):
            raise ValueError("must be an http:// or https:// URL")
        return v


class BriefConfig(Model):
    # true once the developer has answered the intake question (even with "none"): never ask again.
    asked: bool = False
    sources: list[BriefSource] = []
    notes: str | None = None  # short pasted guidance (audience, terms, what to skip). No secrets.


class Config(Model):
    schema_: str | None = Field(default=SCHEMA_URL, alias="$schema")
    app: AppConfig
    auth: AuthConfig = AuthConfig()
    seed: SeedConfig = SeedConfig()
    safety: SafetyConfig = SafetyConfig()
    budget: BudgetConfig = BudgetConfig()
    brand: BrandConfig = BrandConfig()
    graphify: GraphifyConfig = GraphifyConfig()
    brief: BriefConfig = BriefConfig()

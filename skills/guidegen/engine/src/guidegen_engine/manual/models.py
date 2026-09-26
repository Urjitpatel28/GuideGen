"""Pydantic models for guidegen-out/manual.yaml (the source of truth the developer edits)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator

from guidegen_engine.actions import Action, Model

ScreenKind = Literal["page", "window", "dialog", "tab"]
ScreenStatus = Literal["pending", "captured", "unreachable", "excluded", "budget-cut"]
StepStatus = Literal["pending", "captured", "refused", "failed"]
BUILTIN_CHAPTERS = ("getting-started", "tasks", "reference", "troubleshooting")

ID_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
# Same rule as _check_id, published in the JSON schema so editors flag bad ids while typing.
ID_FIELD = Field(json_schema_extra={"pattern": "^[a-z0-9_-]+$"})


def _check_id(v: str) -> str:
    if not v or not set(v) <= ID_CHARS:
        raise ValueError("ids must be lowercase letters, digits, '-' or '_'")
    return v


class Meta(Model):
    title: str = "User Manual"
    audience: str = "end users"
    generated_at: datetime | None = None
    intro: str | None = None


class Chapter(Model):
    """Built-in chapters (getting-started, tasks, reference, troubleshooting) render generated content.
    Any other id is a custom text chapter (glossary, about this manual, FAQ...) rendered from `body`."""

    id: str = ID_FIELD
    title: str | None = None
    body: str | None = None
    override: str | None = None
    exclude: bool = False
    locked: list[str] = []

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _check_id(v)

    @property
    def builtin(self) -> bool:
        return self.id in BUILTIN_CHAPTERS

    @property
    def text(self) -> str | None:
        return self.override or self.body


class Evidence(Model):
    type: str
    ref: str


class Element(Model):
    name: str
    type: str
    description: str | None = None
    override: str | None = None


class ScreenText(Model):
    summary: str | None = None
    override: str | None = None


class Screen(Model):
    id: str = ID_FIELD
    title: str
    kind: ScreenKind = "page"
    group: str | None = None
    source: list[str] = []
    source_hash: str | None = None
    status: ScreenStatus = "pending"
    unreachable_reason: str | None = None
    exclude: bool = False
    locked: list[str] = []
    navigate: list[Action] = []
    elements: list[Element] = []
    text: ScreenText = ScreenText()
    image: str | None = None
    no_uia: bool = False
    before_login: bool = False  # capture without signing in first (the sign-in screen itself)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _check_id(v)

    @property
    def body(self) -> str | None:
        return self.text.override or self.text.summary


class Step(Model):
    id: str = ID_FIELD
    screen: str | None = None
    action: Action | None = None
    text: str | None = None
    override: str | None = None
    image: str | None = None
    highlight: bool = True
    crop: bool = False
    status: StepStatus = "pending"
    note: str | None = None
    locked: list[str] = []

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _check_id(v)  # step ids become image paths (screens/<task>/<step>.png)

    @property
    def body(self) -> str | None:
        return self.override or self.text


class Task(Model):
    id: str = ID_FIELD
    title: str
    group: str | None = None  # optional sub-heading in How-To Tasks (e.g. an outline section)
    goal: str | None = None
    rank: int = 99
    evidence: list[Evidence] = []
    exclude: bool = False
    locked: list[str] = []
    status: Literal["pending", "captured", "partial", "budget-cut", "excluded"] = "pending"
    steps: list[Step] = []
    override: str | None = None
    before_login: bool = False

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        return _check_id(v)

    @property
    def body(self) -> str | None:
        return self.override or self.goal


class Troubleshooting(Model):
    message: str
    source: str | None = None
    cause: str | None = None
    fix: str | None = None
    text: str | None = None
    override: str | None = None
    exclude: bool = False
    locked: list[str] = []


class GettingStarted(Model):
    requirements: str | None = None
    launch: str | None = None
    sign_in: str | None = None
    tour: str | None = None
    tour_screen: str | None = None
    override: str | None = None


class BriefGap(Model):
    """An item from the developer's brief (old manual task, outline entry) that the live app does not have."""

    item: str
    source: str | None = None
    reason: str | None = None


class Manual(Model):
    version: int = 1
    meta: Meta = Meta()
    chapters: list[Chapter] = [
        Chapter(id="getting-started"),
        Chapter(id="tasks"),
        Chapter(id="reference"),
        Chapter(id="troubleshooting"),
    ]
    getting_started: GettingStarted = GettingStarted()
    screens: list[Screen] = []
    tasks: list[Task] = []
    troubleshooting: list[Troubleshooting] = []
    brief_gaps: list[BriefGap] = []

    def screen(self, sid: str) -> Screen | None:
        return next((s for s in self.screens if s.id == sid), None)

    def task(self, tid: str) -> Task | None:
        return next((t for t in self.tasks if t.id == tid), None)

    def duplicate_ids(self) -> list[str]:
        seen: set[str] = set()
        dup = []
        for i in [s.id for s in self.screens] + [t.id for t in self.tasks]:
            if i in seen:
                dup.append(i)
            seen.add(i)
        chapter_ids = [c.id for c in self.chapters]
        dup += [f"chapter {c}" for c in sorted(set(chapter_ids)) if chapter_ids.count(c) > 1]
        for t in self.tasks:  # edits address steps by id, so a repeated id makes the second one unreachable
            step_ids = [st.id for st in t.steps]
            dup += [f"step {t.id}/{i}" for i in sorted(set(step_ids)) if step_ids.count(i) > 1]
        messages = [e.message for e in self.troubleshooting]
        dup += [f"troubleshooting '{m}'" for m in sorted(set(messages)) if messages.count(m) > 1]
        return dup

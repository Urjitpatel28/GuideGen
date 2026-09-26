"""Action schema shared by exploration (`act`), screen `navigate` steps, task steps and login steps."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel

ActionName = Literal[
    "goto", "click", "double_click", "type", "select", "press", "hover", "wait", "screenshot", "close"
]
WEB_BY = ("role", "label", "text", "testid", "css")
DESKTOP_BY = ("automation_id", "name", "control_type", "path")
TargetBy = Literal["role", "label", "text", "testid", "css", "automation_id", "name", "control_type", "path"]

# Most stable first; used by docs and by `tree` hints.
TARGET_PREFERENCE = ["testid", "automation_id", "role", "label", "name", "text", "control_type", "css", "path"]

ACTIONS_NEEDING_TARGET = {"click", "double_click", "select", "hover"}


class Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, extra="forbid")

    def dump(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True, mode="json")


class Target(Model):
    by: TargetBy
    value: str
    name: str | None = None  # accessible name, used with by=role / by=control_type

    def describe(self) -> str:
        return f"{self.by}={self.value}" + (f" name={self.name}" if self.name else "")


class Action(Model):
    action: ActionName
    target: Target | None = None
    value: str | None = None
    redact: list[str] = []
    timeout_ms: int | None = None

    @model_validator(mode="after")
    def _check(self) -> Action:
        if self.action in ACTIONS_NEEDING_TARGET and self.target is None:
            raise ValueError(f"action '{self.action}' needs a target")
        if self.action == "goto" and not self.value:
            raise ValueError("goto needs a value (URL or path)")
        if self.action in ("type", "select", "press") and self.value is None:
            raise ValueError(f"action '{self.action}' needs a value")
        return self

    def describe(self) -> str:
        parts = [self.action]
        if self.target:
            parts.append(self.target.describe())
        if self.value is not None and self.action != "type":
            parts.append(repr(self.value))
        return " ".join(parts)

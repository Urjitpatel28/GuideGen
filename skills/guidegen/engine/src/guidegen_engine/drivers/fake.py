"""In-memory fake driver for unit tests: a tiny state machine of views with buttons and fields."""

from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

from guidegen_engine.actions import Action, Target
from guidegen_engine.drivers.base import Driver, DriverError, ElementInfo, Rect


class FakeDriver(Driver):
    kind = "fake"

    def __init__(self, views: dict[str, dict[str, Any]], start: str = "home") -> None:
        """views: {view_id: {"elements": {name: {"rect": [x,y,w,h], "role": "button", "goes": "view", "text": "..."}}}}"""
        self.views = views
        self.start = start
        self.view = start
        self.log: list[str] = []
        self.values: dict[str, str] = {}
        self.launched = False
        self.focused: str | None = None  # name of the focused element in the current view

    def launch(self) -> None:
        self.launched = True
        self.view = self.start

    def _el(self, target: Target) -> tuple[str, dict[str, Any]] | None:
        els = self.views[self.view]["elements"]
        key = target.name or target.value
        if key in els:
            return key, els[key]
        return None

    def act(self, action: Action) -> dict[str, Any]:
        self.log.append(action.describe())
        if action.action == "goto":
            path = action.value.strip("/") or self.start
            if path not in self.views:
                raise DriverError(f"no view {path}")
            self.view = path
            self.focused = None
        elif action.target is not None:
            found = self._el(action.target)
            if not found:
                raise DriverError(f"element not found: {action.target.describe()}")
            name, el = found
            self.focused = name
            if action.action in ("click", "double_click", "press") and el.get("goes"):
                self.view = el["goes"]
                self.focused = None
            if action.action == "type":
                self.values[name] = action.value or ""
        return {"ok": True, "view": self.view}

    def tree(self, depth: int = 6) -> str:
        return "\n".join(f"- {e.get('role', 'button')} \"{n}\"" for n, e in self.views[self.view]["elements"].items())

    def screenshot(self) -> Image.Image:
        img = Image.new("RGB", (400, 300), "white")
        d = ImageDraw.Draw(img)
        d.text((10, 10), self.view, fill="black")
        for n, e in self.views[self.view]["elements"].items():
            x, y, w, h = e["rect"]
            d.rectangle([x, y, x + w, y + h], outline="gray")
            d.text((x + 2, y + 2), e.get("text", n), fill="black")
        return img

    def element_info(self, target: Target, timeout_ms: int = 0) -> ElementInfo | None:
        found = self._el(target)
        if not found:
            return None
        name, el = found
        role = el.get("role", "button")
        return ElementInfo(name=name, role=role, rect=Rect(*el["rect"]), is_input=role in ("textbox", "edit"))

    def focused_info(self) -> ElementInfo | None:
        if self.focused is None:
            return None
        return self.element_info(Target(by="name", value=self.focused))

    def current_view_id(self) -> str:
        return self.view

    def redaction_rects(self, patterns: list[str], selectors: list[str]) -> list[Rect]:
        import re

        rects = []
        for n, e in self.views[self.view]["elements"].items():
            text = e.get("text", "")
            if e.get("role") == "password" or n in selectors or any(re.search(p, text) for p in patterns):
                rects.append(Rect(*e["rect"]))
        return rects

    def reset(self) -> None:
        self.view = self.start
        self.focused = None

    def close(self) -> None:
        self.launched = False

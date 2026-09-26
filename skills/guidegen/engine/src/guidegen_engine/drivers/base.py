"""The Driver interface every UI backend implements (web, Electron, Windows UIA, fake).

Coordinates returned by element_rect/redaction_rects are in the pixel space of screenshot():
viewport pixels for web, window-relative logical (100% DPI) pixels for desktop.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from PIL import Image

from guidegen_engine.actions import Action, Target


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    def as_box(self, pad: float = 0) -> tuple[int, int, int, int]:
        return (int(self.x - pad), int(self.y - pad), int(self.x + self.w + pad), int(self.y + self.h + pad))

    def valid(self) -> bool:
        return self.w > 0 and self.h > 0

    def to_list(self) -> list[float]:
        return [round(self.x, 1), round(self.y, 1), round(self.w, 1), round(self.h, 1)]


@dataclass
class ElementInfo:
    name: str
    role: str
    rect: Rect | None = None
    is_input: bool = False


class DriverError(Exception):
    """An action could not be performed (element not found, timeout...)."""


class Driver(ABC):
    kind: str = "abstract"

    @abstractmethod
    def launch(self) -> None:
        """Start the UI session (open a browser / attach to the running app)."""

    def attach(self) -> None:
        self.launch()

    @abstractmethod
    def act(self, action: Action) -> dict[str, Any]:
        """Perform one action (already guarded and with ${VAR}s resolved). Raise DriverError on failure."""

    @abstractmethod
    def tree(self, depth: int = 6) -> str:
        """Token-trimmed accessibility tree of the current view."""

    @abstractmethod
    def screenshot(self) -> Image.Image:
        """In-memory screenshot of the current view. Never written to disk unredacted."""

    @abstractmethod
    def element_info(self, target: Target, timeout_ms: int = 3000) -> ElementInfo | None:
        """Name/role/rect of the element a target resolves to, or None."""

    def focused_info(self) -> ElementInfo | None:
        """The element that has keyboard focus, or None when nothing (or only the page/window) is focused.
        Used to guard key presses that have no target."""
        return None

    def element_rect(self, target: Target) -> Rect | None:
        info = self.element_info(target)
        return info.rect if info else None

    @abstractmethod
    def current_view_id(self) -> str:
        """Stable id of the current view (URL path, window title...)."""

    @abstractmethod
    def redaction_rects(self, patterns: list[str], selectors: list[str]) -> list[Rect]:
        """Rects to blur: password fields, selector matches, text matching patterns."""

    @abstractmethod
    def reset(self) -> None:
        """Return to the app's start state (home page / fresh app instance)."""

    def limitations(self) -> list[str]:
        """Things this driver could not see (e.g. controls with no UIA support)."""
        return []

    @abstractmethod
    def close(self) -> None:
        ...

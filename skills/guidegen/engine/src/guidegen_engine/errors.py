"""Error types. Exit code 2 = hard blocker the agent must ask the developer about."""

from __future__ import annotations

from typing import Any


class GuideGenError(Exception):
    exit_code = 1

    def __init__(self, message: str, **data: Any) -> None:
        super().__init__(message)
        self.message = message
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        return {"ok": False, "error": self.message, **self.data}


class HardBlocker(GuideGenError):
    """Something only the developer can resolve (build broken, no credentials, remote DB...)."""

    exit_code = 2
    KINDS = ("build", "start", "login", "dependency", "safety", "config")

    def __init__(
        self,
        blocker: str,
        message: str,
        question: str,
        tried: list[str] | None = None,
        save_to: str | None = None,
        **data: Any,
    ) -> None:
        super().__init__(message, **data)
        if blocker not in self.KINDS:
            raise ValueError(blocker)
        self.blocker = blocker
        self.question = question
        self.tried = tried or []
        self.save_to = save_to

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "blocker": self.blocker,
            "message": self.message,
            "tried": self.tried,
            "question": self.question,
            "saveTo": self.save_to,
            **self.data,
        }

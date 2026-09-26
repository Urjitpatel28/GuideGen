"""A live UI session: guarded actions, login, redacted/annotated screenshots.

Used by the session daemon (exploration: act/tree/shot/login) and by capture (deterministic replay),
so the destructive-action guard and redaction apply on every path.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from PIL import Image

from guidegen_engine import annotate
from guidegen_engine.actions import Action, Target
from guidegen_engine.config.models import Config
from guidegen_engine.drivers.base import Driver, DriverError, Rect
from guidegen_engine.errors import HardBlocker
from guidegen_engine.guards import destructive
from guidegen_engine.masking import mask, resolve

PRE_ACTION_SHOT = {"click", "double_click", "hover", "select", "press"}


class Session:
    def __init__(self, cfg: Config, driver: Driver) -> None:
        self.cfg = cfg
        self.driver = driver
        self.refusals: list[dict[str, str]] = []

    @property
    def accent(self) -> str:
        return self.cfg.brand.accent_color or annotate.DEFAULT_ACCENT

    # ---------- actions ----------
    def perform(self, action: Action, context: str = "") -> dict[str, Any]:
        """Guard, resolve ${VAR}s, act. Returns {ok, refused?, reason?, error?}. Never raises DriverError."""
        info = None
        if action.action in destructive.GUARDED_ACTIONS:
            info = self.driver.element_info(action.target) if action.target is not None else self.driver.focused_info()
        reason = destructive.check(action, info, self.cfg.safety.allow_destructive) or destructive.check_goto(
            action, [self.cfg.app.url, getattr(self.driver, "base_url", None)]
        )
        if reason:
            self.refusals.append({"context": context, "action": action.describe(), "reason": reason})
            return {"ok": False, "refused": True, "reason": reason}
        resolved = action
        if action.value and "${" in action.value:
            resolved = action.model_copy(update={"value": resolve(action.value)})
        try:
            return self.driver.act(resolved)
        except DriverError as e:
            return {"ok": False, "error": mask(str(e))}

    def login_needed(self, navigate: bool = True) -> bool:
        """True when the login form (first targeted login step) is visible. With navigate, leading
        `goto` login steps run first; without, only the current view is checked."""
        auth = self.cfg.auth
        if not auth.required or not auth.login_steps:
            return False
        for step in auth.login_steps:
            if step.action == "goto":
                if navigate:
                    self.perform(step, "login")
                continue
            if step.target is None:
                continue
            return self.driver.element_info(step.target, timeout_ms=1500) is not None
        return False

    def login(self, force: bool = False) -> dict[str, Any]:
        auth = self.cfg.auth
        if not auth.required:
            return {"ok": True, "skipped": "auth.required is false"}
        if not auth.login_steps:
            raise HardBlocker(
                "login",
                "The app needs a login but auth.loginSteps is empty.",
                question="Explore the login screen with `guidegen tree`, then save the steps to auth.loginSteps using ${GUIDEGEN_USER}/${GUIDEGEN_PASSWORD} placeholders.",
                save_to="auth.loginSteps",
            )
        if not force and not self.login_needed():
            return {"ok": True, "alreadyLoggedIn": True}
        for i, step in enumerate(auth.login_steps, 1):
            res = self.perform(step, "login")
            if not res.get("ok"):
                raise HardBlocker(
                    "login",
                    f"Login step {i} ({step.describe()}) failed: {res.get('error') or res.get('reason')}",
                    question=(
                        f"Login failed. Check that {auth.username_env} and {auth.password_env} hold a working TEST account "
                        "and that auth.loginSteps match the login form, then say 'continue'."
                    ),
                    tried=[s.describe() for s in auth.login_steps],
                    save_to="auth.loginSteps",
                )
        deadline = time.time() + 15  # client-side redirects after sign-in can take a moment
        while self.login_needed(navigate=False) and time.time() < deadline:
            time.sleep(0.5)
        if self.login_needed(navigate=False):
            raise HardBlocker(
                "login",
                "Login steps ran but the login form is still shown (wrong credentials?).",
                question=f"Please set {auth.username_env}/{auth.password_env} to a valid test account and say 'continue'.",
                tried=[s.describe() for s in auth.login_steps],
                save_to="auth.usernameEnv",
            )
        return {"ok": True, "view": self.driver.current_view_id()}

    def reset(self, login: bool = True) -> None:
        """Back to the start state, logged in. Web resets are cheap (navigate home, cookies kept) and only
        sign in again when the app shows its login form; desktop resets restart the app."""
        self.driver.reset()
        auth = self.cfg.auth
        if not login:
            if self.driver.kind in ("web", "electron") and auth.required:
                self.driver.context.clear_cookies()  # signed-out start state
                self.driver.reset()
            return
        if auth.required and auth.login_steps and self.login_needed(navigate=False):
            self.login(force=True)
            if self.driver.kind in ("web", "electron"):
                self.driver.reset()

    # ---------- screenshots ----------
    def shot(
        self,
        extra_redact: list[str] | None = None,
        highlight: Target | None = None,
        number: int | None = None,
        crop: bool = False,
        rect: Rect | None = None,
    ) -> tuple[Image.Image, int, Rect | None]:
        """Redacted (always) and optionally annotated screenshot, in memory only."""
        if highlight is not None and rect is None:
            rect = self.driver.element_rect(highlight)
        safety = self.cfg.safety
        rects = self.driver.redaction_rects(safety.redact_patterns, [*safety.redact_selectors, *(extra_redact or [])])
        img = self.driver.screenshot()
        img, n = annotate.redact(img, rects)
        if rect is not None and highlight is not None:
            img = annotate.highlight(img, rect, self.accent)
        if number is not None:
            img = annotate.badge(img, number, rect if highlight is not None else None, self.accent)
        if crop and rect is not None:
            img = annotate.crop_around(img, rect)
        return img, n, rect

    @staticmethod
    def save(img: Image.Image, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path, "PNG", optimize=True)

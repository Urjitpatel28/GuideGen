"""Electron apps: started with --remote-debugging-port by `app start`, attached over CDP, driven like web."""

from __future__ import annotations

import time

from guidegen_engine.drivers.base import DriverError
from guidegen_engine.drivers.web import WebDriver


class ElectronDriver(WebDriver):
    kind = "electron"

    def __init__(self, cdp_port: int, viewport: tuple[int, int] = (1280, 800)) -> None:
        super().__init__("about:blank", viewport)
        self.cdp_port = cdp_port
        self.start_url: str | None = None

    def _launch(self) -> None:  # WebDriver.launch wraps this and cleans up on failure
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self.browser = self._pw.chromium.connect_over_cdp(f"http://127.0.0.1:{self.cdp_port}")
        deadline = time.time() + 20
        while time.time() < deadline:
            pages = [p for ctx in self.browser.contexts for p in ctx.pages if not p.url.startswith("devtools://")]
            if pages:
                self.page = pages[0]
                self.context = self.page.context
                break
            time.sleep(0.5)
        else:
            raise DriverError("Electron app exposed no window over CDP")
        self._wire_context()
        try:
            self.page.set_viewport_size({"width": self.viewport[0], "height": self.viewport[1]})
        except Exception:
            pass  # some Electron versions do not allow overriding the window size
        self.page.wait_for_load_state("load")
        self.start_url = self.page.url
        self.base_url = self.start_url
        self._settle()

    def reset(self) -> None:
        self.page.goto(self.start_url, wait_until="load")
        self._settle()

    def close(self) -> None:
        # Disconnect only; the app process is stopped by `app stop`.
        if self._pw:
            self._pw.stop()
            self._pw = None

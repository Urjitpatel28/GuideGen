"""Driver factory."""

from __future__ import annotations

import os

from guidegen_engine.drivers.base import Driver, DriverError, ElementInfo, Rect

__all__ = ["Driver", "DriverError", "ElementInfo", "Rect", "make_driver"]


def make_driver(cfg, controller) -> Driver:
    """Build the driver for cfg.app.kind using the running app's state (url / CDP port / pid)."""
    from guidegen_engine.errors import HardBlocker

    st = controller.state()
    kind = cfg.app.kind
    if kind == "web":
        from guidegen_engine.drivers.web import WebDriver

        vp = cfg.app.viewport
        return WebDriver(st.get("url") or cfg.app.url, (vp.width, vp.height), headless=os.environ.get("GUIDEGEN_HEADED") != "1")
    if kind == "electron":
        from guidegen_engine.drivers.electron import ElectronDriver

        if not st.get("cdpPort"):
            raise HardBlocker("start", "Electron app is not running.", question="Run `guidegen app start` first.")
        w = cfg.app.window
        return ElectronDriver(st["cdpPort"], (w.width, w.height))
    from guidegen_engine.drivers.desktop import DesktopDriver

    if not st.get("pid"):
        raise HardBlocker("start", "Desktop app is not running.", question="Run `guidegen app start` first.")
    w = cfg.app.window
    return DesktopDriver(st["pid"], (w.width, w.height), restart=lambda: controller.restart()["pid"])

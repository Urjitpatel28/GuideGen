"""`guidegen doctor`: environment checks. Installs Playwright Chromium if it is missing."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from typing import Any


def _check(name: str, status: str, detail: str) -> dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def dpi_scale() -> float | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    try:
        import ctypes

        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except Exception:
        return None


def chromium_ok() -> tuple[bool, str]:
    try:
        from playwright.sync_api import sync_playwright

        from guidegen_engine.drivers.web import launch_chromium

        with sync_playwright() as p:
            b = launch_chromium(p, headless=True)
            v = b.version
            b.close()
        return True, f"Chromium {v}"
    except Exception as e:  # missing executable or driver problem
        return False, str(e).splitlines()[0][:200]


def _bundled_ok() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            return __import__("os").path.exists(p.chromium.executable_path)
    except Exception:
        return False


def install_chromium() -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, text=True
    )
    lines = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode == 0, lines[-1] if lines else ""


def run_doctor(install: bool = True) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    v = sys.version_info
    checks.append(
        _check("python", "ok" if v >= (3, 11) else "fail", f"{platform.python_version()} ({sys.executable})")
    )
    uv = shutil.which("uv")
    checks.append(_check("uv", "ok" if uv else "warn", uv or "uv not on PATH (only needed to launch the engine)"))

    ok, detail = chromium_ok()
    bundled = ok and _bundled_ok()
    if ok and not bundled:
        detail += " (system Edge/Chrome; bundled Chromium not installed)"
    if not ok and install:
        inst_ok, inst_detail = install_chromium()
        ok, detail = chromium_ok() if inst_ok else (False, f"install failed: {inst_detail}")
        if ok:
            detail += " (installed now)"
    checks.append(_check("playwright-chromium", "ok" if ok else "fail", detail))

    osname = f"{platform.system()} {platform.release()}"
    if sys.platform == "win32":
        checks.append(_check("os", "ok", osname))
        try:
            import pywinauto  # noqa: F401

            checks.append(_check("desktop-driver", "ok", "pywinauto (UIA backend) available"))
        except Exception as e:
            checks.append(_check("desktop-driver", "fail", f"pywinauto import failed: {e}"))
        scale = dpi_scale()
        if scale is not None:
            status = "ok" if scale == 1.0 else "warn"
            checks.append(
                _check(
                    "dpi-scale",
                    status,
                    f"{int(scale * 100)}%"
                    + ("" if scale == 1.0 else " - screenshots are normalised to 100%; display settings are not changed"),
                )
            )
    else:
        checks.append(_check("os", "ok", osname))
        checks.append(
            _check("desktop-driver", "unsupported", "Windows desktop apps (WPF/WinForms/WinUI) can only be captured on Windows; web and Electron work here.")
        )

    return {"ok": all(c["status"] != "fail" for c in checks), "checks": checks}

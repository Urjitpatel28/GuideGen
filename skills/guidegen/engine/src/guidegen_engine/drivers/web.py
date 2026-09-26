"""Playwright (Chromium) driver for web apps; the Electron driver reuses it over CDP."""

from __future__ import annotations

import io
from typing import Any
from urllib.parse import urljoin, urlparse

from PIL import Image

from guidegen_engine.actions import WEB_BY, Action, Target
from guidegen_engine.drivers.base import Driver, DriverError, ElementInfo, Rect

TREE_CHAR_BUDGET = 14000  # ~3.5k tokens

REDACT_JS = r"""
(args) => {
  const rects = [];
  const add = (r) => { if (r && r.width > 0 && r.height > 0 && r.bottom > 0 && r.right > 0 &&
                            r.top < innerHeight && r.left < innerWidth) rects.push([r.x, r.y, r.width, r.height]); };
  document.querySelectorAll('input[type=password]').forEach(e => add(e.getBoundingClientRect()));
  for (const sel of args.selectors) {
    try { document.querySelectorAll(sel).forEach(e => add(e.getBoundingClientRect())); } catch (e) {}
  }
  const res = [];
  for (const p of args.patterns) { try { res.push(new RegExp(p, 'g')); } catch (e) {} }
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const parent = n.parentElement;
    if (!parent || ['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(parent.tagName)) continue;
    for (const re of res) {
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(n.data))) {
        if (m[0].length === 0) { re.lastIndex++; continue; }
        const range = document.createRange();
        range.setStart(n, m.index);
        range.setEnd(n, m.index + m[0].length);
        for (const r of range.getClientRects()) add(r);
      }
    }
  }
  document.querySelectorAll('input, textarea').forEach(e => {
    for (const re of res) { re.lastIndex = 0; if (e.value && re.test(e.value)) { add(e.getBoundingClientRect()); break; } }
  });
  return rects;
}
"""

INFO_JS = r"""
(e) => {
  const label = e.labels && e.labels.length ? e.labels[0].innerText : '';
  const name = (e.getAttribute('aria-label') || e.innerText || label || e.value || e.getAttribute('title') ||
                e.getAttribute('alt') || e.getAttribute('placeholder') || '').trim().slice(0, 200);
  const tag = e.tagName.toLowerCase();
  const type = (e.getAttribute('type') || '').toLowerCase();
  const role = e.getAttribute('role') || tag;
  const isInput = (tag === 'input' && !['button', 'submit', 'reset', 'image', 'checkbox', 'radio'].includes(type)) ||
                  tag === 'textarea' || tag === 'select' || e.isContentEditable;
  return { name, role, isInput };
}
"""

FOCUSED_JS = r"""
() => {
  let e = document.activeElement;
  while (e && e.shadowRoot && e.shadowRoot.activeElement) e = e.shadowRoot.activeElement;
  if (!e || e === document.body || e === document.documentElement) return null;
  return e;
}
"""

TESTIDS_JS = r"""
() => Array.from(document.querySelectorAll('[data-testid]')).filter(e => e.offsetParent !== null).slice(0, 80)
  .map(e => `testid=${e.getAttribute('data-testid')} <${e.tagName.toLowerCase()}> ${(e.innerText || e.getAttribute('aria-label') || e.value || '').trim().replace(/\s+/g, ' ').slice(0, 50)}`)
"""

def launch_chromium(pw, **kwargs):
    """Playwright's bundled Chromium, falling back to an installed Edge/Chrome (always present on Windows).
    GUIDEGEN_BROWSER_CHANNEL=msedge|chrome forces a channel."""
    import os

    forced = os.environ.get("GUIDEGEN_BROWSER_CHANNEL")
    channels = [forced] if forced else [None, "msedge", "chrome"]
    last: Exception | None = None
    for ch in channels:
        try:
            return pw.chromium.launch(channel=ch, **kwargs) if ch else pw.chromium.launch(**kwargs)
        except Exception as e:  # executable missing -> try the next channel
            last = e
    raise last  # type: ignore[misc]


KEY_ALIASES = {"esc": "Escape", "return": "Enter", "ctrl": "Control", "del": "Delete"}


class WebDriver(Driver):
    kind = "web"

    def __init__(self, base_url: str, viewport: tuple[int, int] = (1440, 900), headless: bool = True) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.viewport = viewport
        self.headless = headless
        self._pw = None
        self.browser = None
        self.context = None
        self.page = None

    # ---------- lifecycle ----------
    def launch(self) -> None:
        try:
            self._launch()
        except Exception:
            self.close()  # stop Playwright and the browser when launch fails part-way
            raise

    def _launch(self) -> None:
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self.browser = launch_chromium(self._pw, headless=self.headless)
        self.context = self.browser.new_context(
            viewport={"width": self.viewport[0], "height": self.viewport[1]},
            device_scale_factor=1,
            reduced_motion="reduce",
            locale="en-US",
            timezone_id="UTC",
            color_scheme="light",
        )
        self._wire_context()
        self.page = self.context.new_page()
        self.page.goto(self.base_url, wait_until="load")
        self._settle()

    def _wire_context(self) -> None:
        self.context.set_default_timeout(10000)
        self.context.on("page", self._on_page)

    def _on_page(self, page) -> None:  # new tab / popup becomes the current page
        self.page = page
        page.on("close", self._on_close)
        try:
            page.wait_for_load_state("load", timeout=10000)
        except Exception:
            pass

    def _on_close(self, page) -> None:
        """A popup closed: fall back to the most recent open page instead of acting on a closed one."""
        if page is self.page and self.context is not None:
            open_pages = [p for p in self.context.pages if not p.is_closed()]
            if open_pages:
                self.page = open_pages[-1]

    def close(self) -> None:
        for obj in (self.context, self.browser):
            try:
                obj and obj.close()
            except Exception:
                pass
        if self._pw:
            self._pw.stop()
            self._pw = None

    def reset(self) -> None:
        pages = list(self.context.pages)
        for p in pages[1:]:
            p.close()
        self.page = pages[0] if pages else self.context.new_page()
        self.page.goto(self.base_url, wait_until="load")
        self._settle()

    def _settle(self) -> None:
        try:
            self.page.wait_for_load_state("networkidle", timeout=4000)
        except Exception:
            pass
        self.page.wait_for_timeout(150)

    # ---------- targeting ----------
    def locate(self, t: Target, timeout: int = 10000):
        if t.by not in WEB_BY:
            raise DriverError(f"target.by '{t.by}' is not valid for web apps (use {', '.join(WEB_BY)})")
        p = self.page

        def build(exact: bool):
            if t.by == "role":
                return p.get_by_role(t.value, name=t.name, exact=exact) if t.name else p.get_by_role(t.value)
            if t.by == "label":
                return p.get_by_label(t.value, exact=exact)
            if t.by == "text":
                return p.get_by_text(t.value, exact=exact)
            if t.by == "testid":
                return p.get_by_test_id(t.value)
            return p.locator(t.value)

        loc = build(True)
        if loc.count() == 0 and t.by in ("role", "label", "text"):
            loose = build(False)
            if loose.count() > 0:
                loc = loose
        loc = loc.first
        try:
            loc.wait_for(state="visible", timeout=timeout)
        except Exception as e:
            raise DriverError(f"element not found or not visible: {t.describe()}") from e
        return loc

    # ---------- actions ----------
    def act(self, a: Action) -> dict[str, Any]:
        timeout = a.timeout_ms or 10000
        try:
            if a.action == "goto":
                self.page.goto(urljoin(self.base_url, a.value.lstrip("/")) if not a.value.startswith("http") else a.value, wait_until="load")
            elif a.action == "wait":
                if a.target:
                    self.locate(a.target, timeout)
                else:
                    self.page.wait_for_timeout(int(a.value or 500))
            elif a.action == "press" and a.target is None:
                self.page.keyboard.press(_key(a.value))
            elif a.action == "close":
                self.page.keyboard.press("Escape")
            elif a.action == "screenshot":
                pass
            else:
                loc = self.locate(a.target, timeout)
                if a.action == "click":
                    loc.click(timeout=timeout)
                elif a.action == "double_click":
                    loc.dblclick(timeout=timeout)
                elif a.action == "type":
                    loc.fill(a.value or "", timeout=timeout)
                elif a.action == "select":
                    try:
                        loc.select_option(label=a.value, timeout=timeout)
                    except Exception:
                        loc.select_option(value=a.value, timeout=timeout)
                elif a.action == "press":
                    loc.press(_key(a.value), timeout=timeout)
                elif a.action == "hover":
                    loc.hover(timeout=timeout)
        except DriverError:
            raise
        except Exception as e:
            raise DriverError(f"{a.action} failed: {str(e).splitlines()[0][:300]}") from e
        self._settle()
        return {"ok": True, "view": self.current_view_id(), "title": self.page.title()}

    # ---------- inspection ----------
    def tree(self, depth: int = 6) -> str:
        snap = self.page.locator("body").aria_snapshot()
        lines = [ln for ln in snap.splitlines() if (len(ln) - len(ln.lstrip(" "))) // 2 < depth]
        testids = self.page.evaluate(TESTIDS_JS)
        head = [f"url: {self.page.url}", f"title: {self.page.title()}", "aria:"]
        body = "\n".join(lines)
        if len(body) > TREE_CHAR_BUDGET:
            body = body[:TREE_CHAR_BUDGET] + "\n... (trimmed; use --depth to go shallower)"
        out = "\n".join(head) + "\n" + body
        if testids:
            out += "\nstable targets:\n" + "\n".join(testids)
        return out

    def screenshot(self) -> Image.Image:
        png = self.page.screenshot(animations="disabled", caret="hide")
        return Image.open(io.BytesIO(png)).convert("RGB")

    def element_info(self, target: Target, timeout_ms: int = 3000) -> ElementInfo | None:
        try:
            loc = self.locate(target, timeout_ms)
        except DriverError:
            return None
        try:
            loc.scroll_into_view_if_needed(timeout=2000)
        except Exception:
            pass
        try:  # the page may navigate between locate() and here
            info = loc.evaluate(INFO_JS, timeout=2000)
            box = loc.bounding_box(timeout=2000)
        except Exception:
            return None
        rect = Rect(box["x"], box["y"], box["width"], box["height"]) if box else None
        return ElementInfo(name=info["name"], role=info["role"], rect=rect, is_input=info["isInput"])

    def focused_info(self) -> ElementInfo | None:
        try:
            handle = self.page.evaluate_handle(FOCUSED_JS)
            el = handle.as_element()
            if el is None:
                return None
            info = el.evaluate(INFO_JS)
        except Exception:
            return None
        return ElementInfo(name=info["name"], role=info["role"], is_input=info["isInput"])

    def current_view_id(self) -> str:
        u = urlparse(self.page.url)
        return (u.path or "/") + (f"#{u.fragment}" if u.fragment else "")

    def redaction_rects(self, patterns: list[str], selectors: list[str]) -> list[Rect]:
        raw = self.page.evaluate(REDACT_JS, {"patterns": patterns, "selectors": selectors})
        return [Rect(*r) for r in raw]


def _key(value: str | None) -> str:
    parts = (value or "Enter").replace(" ", "").split("+")
    return "+".join(KEY_ALIASES.get(p.lower(), p[:1].upper() + p[1:] if len(p) > 1 else p) for p in parts)

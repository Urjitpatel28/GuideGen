"""Windows desktop driver: pywinauto with the UIA backend (WPF, WinForms, WinUI).

- Attaches to the process started by `app start`, restores and resizes the main window to 1280x800 logical px.
- Targets: automation_id > name > control_type(+name) > path ("File/Open" menu path).
- Screenshots use PrintWindow(PW_RENDERFULLCONTENT) so they work even if the window is covered, then are
  scaled to 100% DPI. The system DPI / display settings are never changed.
"""

from __future__ import annotations

import ctypes
import re
import sys
import time
from ctypes import wintypes
from typing import Any
from collections.abc import Callable

from PIL import Image

from guidegen_engine.actions import DESKTOP_BY, Action, Target
from guidegen_engine.drivers.base import Driver, DriverError, ElementInfo, Rect

if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor aware: physical coordinates everywhere
    except Exception:
        pass

TREE_CHAR_BUDGET = 14000
MAX_ELEMENTS = 2500
# Editable controls. "Text" is a static label in UIA, so it is NOT an input (a label named "Delete" is guarded).
INPUT_TYPES = {"Edit", "ComboBox", "Document", "Spinner"}
NO_UIA_TYPES = {"Pane", "Custom", "Image"}
KEYMAP = {
    "enter": "{ENTER}", "return": "{ENTER}", "escape": "{ESC}", "esc": "{ESC}", "tab": "{TAB}",
    "space": "{SPACE}", "backspace": "{BACKSPACE}", "delete": "{DELETE}", "del": "{DELETE}",
    "up": "{UP}", "down": "{DOWN}", "left": "{LEFT}", "right": "{RIGHT}", "arrowup": "{UP}",
    "arrowdown": "{DOWN}", "arrowleft": "{LEFT}", "arrowright": "{RIGHT}", "home": "{HOME}", "end": "{END}",
    "pageup": "{PGUP}", "pagedown": "{PGDN}", **{f"f{i}": f"{{F{i}}}" for i in range(1, 13)},
}
MODS = {"control": "^", "ctrl": "^", "alt": "%", "shift": "+"}


def to_send_keys(value: str) -> str:
    """'Control+S' -> '^s', 'Enter' -> '{ENTER}', 'Alt+F4' -> '%{F4}'."""
    parts = value.replace(" ", "").split("+")
    mods = "".join(MODS.get(p.lower(), "") for p in parts[:-1])
    last = parts[-1]
    key = KEYMAP.get(last.lower(), last.lower() if len(last) == 1 else "{" + last.upper() + "}")
    return mods + key


def escape_text(text: str) -> str:
    return re.sub(r"([{}+^%~()\[\]])", r"{\1}", text)


class _BMI(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG), ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]


def frame_bounds(hwnd: int) -> tuple[int, int, int, int]:
    """Visible window bounds (without the invisible DWM resize border)."""
    r = wintypes.RECT()
    if ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) != 0:
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def _gdi():
    """user32/gdi32 with handle-sized argtypes/restypes, so 64-bit handles are not truncated to int."""
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    H = wintypes.HANDLE
    user32.GetWindowDC.argtypes, user32.GetWindowDC.restype = [wintypes.HWND], wintypes.HDC
    user32.ReleaseDC.argtypes, user32.ReleaseDC.restype = [wintypes.HWND, wintypes.HDC], ctypes.c_int
    user32.PrintWindow.argtypes, user32.PrintWindow.restype = [wintypes.HWND, wintypes.HDC, wintypes.UINT], wintypes.BOOL
    gdi32.CreateCompatibleDC.argtypes, gdi32.CreateCompatibleDC.restype = [wintypes.HDC], wintypes.HDC
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.SelectObject.argtypes, gdi32.SelectObject.restype = [wintypes.HDC, H], H
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT]
    gdi32.DeleteObject.argtypes, gdi32.DeleteObject.restype = [H], wintypes.BOOL
    gdi32.DeleteDC.argtypes, gdi32.DeleteDC.restype = [wintypes.HDC], wintypes.BOOL
    return user32, gdi32


def print_window(hwnd: int) -> Image.Image | None:
    user32, gdi32 = _gdi()
    wr = wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(wr))
    w, h = wr.right - wr.left, wr.bottom - wr.top
    if w <= 0 or h <= 0:
        return None
    hdc = user32.GetWindowDC(hwnd)
    if not hdc:
        return None
    mdc = bmp = old = None
    try:
        mdc = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
        if not mdc or not bmp:
            return None
        old = gdi32.SelectObject(mdc, bmp)
        ok = user32.PrintWindow(hwnd, mdc, 2)
        bmi = _BMI(biSize=ctypes.sizeof(_BMI), biWidth=w, biHeight=-h, biPlanes=1, biBitCount=32, biCompression=0)
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
    finally:
        # the bitmap must be deselected before it can be deleted
        if mdc and old:
            gdi32.SelectObject(mdc, old)
        if bmp:
            gdi32.DeleteObject(bmp)
        if mdc:
            gdi32.DeleteDC(mdc)
        user32.ReleaseDC(hwnd, hdc)
    if not ok:
        return None
    img = Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)
    fl, ft, fr, fb = frame_bounds(hwnd)
    return img.crop((fl - wr.left, ft - wr.top, fl - wr.left + (fr - fl), ft - wr.top + (fb - ft)))


class DesktopDriver(Driver):
    kind = "desktop"

    def __init__(self, pid: int, window_size: tuple[int, int] = (1280, 800), restart: Callable[[], int] | None = None) -> None:
        self.pid = pid
        self.window_size = window_size
        self._restart = restart
        self.app = None
        self._no_uia: set[str] = set()
        self._truncated = False

    # ---------- lifecycle ----------
    def launch(self) -> None:
        from pywinauto import Application

        self.app = Application(backend="uia").connect(process=self.pid, timeout=30)
        self._sized: set[int] = set()
        main = self.app.top_window()
        main.wait("visible", timeout=30)
        self._ensure_sized(main.wrapper_object())

    def _ensure_sized(self, wrapper) -> None:
        """Resize resizable top-level windows (not fixed-size dialogs) to the normalised size, once."""
        hwnd = wrapper.handle
        if hwnd in self._sized:
            return
        self._sized.add(hwnd)
        u = ctypes.windll.user32
        style = u.GetWindowLongW(hwnd, -16)  # GWL_STYLE
        if not style & 0x00040000:  # WS_THICKFRAME: fixed-size window, leave it alone
            return
        u.ShowWindow(hwnd, 9)  # SW_RESTORE
        scale = self._scale(hwnd)
        u.MoveWindow(hwnd, 40, 40, int(self.window_size[0] * scale), int(self.window_size[1] * scale), True)
        time.sleep(0.3)

    def close(self) -> None:
        self.app = None

    def reset(self) -> None:
        if self._restart is None:
            raise DriverError("desktop reset needs an app controller")
        self.pid = self._restart()
        self.launch()

    @staticmethod
    def _scale(hwnd: int) -> float:
        try:
            return ctypes.windll.user32.GetDpiForWindow(hwnd) / 96.0 or 1.0
        except Exception:
            return 1.0

    # ---------- windows ----------
    @staticmethod
    def _is_popup(hwnd: int) -> bool:
        """Menus, dropdowns and tooltips: WS_POPUP without a caption bar."""
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -16) & 0xFFFFFFFF
        return bool(style & 0x80000000) and (style & 0x00C00000) != 0x00C00000

    def _child_windows(self, w) -> list:
        try:
            return [c for c in w.children() if c.element_info.control_type == "Window" and c.is_visible() and c.handle]
        except Exception:
            return []

    def _popups(self) -> list:
        """Open menus/dropdowns. WPF exposes them as untitled child Windows of the owner; Win32/WinForms
        menus are top-level popup windows of the process."""
        out, seen = [], set()
        try:
            cands = list(self.app.windows())
            main = self._main()
            cands += self._child_windows(main)
            for c in self._child_windows(main):
                cands += self._child_windows(c)
            for w in cands:
                if w.handle in seen or not w.is_visible() or not self._is_popup(w.handle):
                    continue
                seen.add(w.handle)
                r = w.rectangle()
                if r.width() > 4 and r.height() > 4:
                    out.append(w)
        except Exception:
            pass
        return out

    def _main(self):
        try:
            top = self.app.top_window().wrapper_object()
            if not self._is_popup(top.handle):
                return top
            framed = [w for w in self.app.windows() if w.is_visible() and not self._is_popup(w.handle)]
            if framed:
                return framed[0]
            return top
        except Exception as e:
            raise DriverError(f"app has no visible window (did it exit?): {e}") from e

    def _top(self):
        """The window the user is looking at: owned modal dialogs (WPF ShowDialog, MessageBox) show up in
        UIA as child Window elements of their owner, so walk down to the innermost visible one."""
        top = self._main()
        for _ in range(5):
            kids = [c for c in self._child_windows(top) if not self._is_popup(c.handle)]
            if not kids:
                break
            top = kids[-1]
        return top

    def _windows(self) -> list:
        top = self._top()
        popups = self._popups()
        seen = {top.handle, *(p.handle for p in popups)}
        out = [*popups, top]
        main = self._main()
        if main.handle not in seen:
            out.append(main)
            seen.add(main.handle)
        out += [w for w in self.app.windows() if w.handle not in seen and w.is_visible()]
        return out

    # ---------- targeting ----------
    def _find(self, t: Target, timeout_ms: int = 10000):
        if t.by not in DESKTOP_BY:
            raise DriverError(f"target.by '{t.by}' is not valid for desktop apps (use {', '.join(DESKTOP_BY)})")
        if t.by == "path":
            raise DriverError("path targets are resolved step by step; use them with click")
        crit: dict[str, Any] = {
            "automation_id": {"auto_id": t.value},
            "name": {"title": t.value},
            "control_type": {"control_type": t.value, **({"title": t.name} if t.name else {})},
        }[t.by]
        end = time.time() + timeout_ms / 1000
        while True:
            for win in self._windows():
                ei = win.element_info
                if t.by == "automation_id" and ei.automation_id == t.value or t.by == "name" and ei.name == t.value:
                    return win
                spec = self.app.window(handle=win.handle).child_window(**crit, found_index=0)
                try:
                    if spec.exists(timeout=0):
                        return spec.wrapper_object()
                except Exception:
                    pass
            if time.time() > end:
                raise DriverError(f"element not found: {t.describe()}")
            time.sleep(0.3)

    # ---------- actions ----------
    def act(self, a: Action) -> dict[str, Any]:
        from pywinauto import keyboard, mouse

        timeout = a.timeout_ms or 10000
        try:
            if a.action == "goto":
                raise DriverError("goto is not available for desktop apps; navigate with click")
            if a.action == "wait":
                if a.target:
                    self._find(a.target, timeout)
                else:
                    time.sleep(int(a.value or 500) / 1000)
            elif a.action == "close":
                self._top().close()
            elif a.action == "screenshot":
                pass
            elif a.action == "press" and a.target is None:
                self._top().set_focus()
                keyboard.send_keys(to_send_keys(a.value or "Enter"))
            elif a.target and a.target.by == "path":
                for part in [p for p in a.target.value.split("/") if p]:
                    el = self._find(Target(by="name", value=part), timeout)
                    el.click_input()
                    time.sleep(0.3)
            else:
                el = self._find(a.target, timeout)
                if a.action == "click":
                    self._click(el)
                elif a.action == "double_click":
                    el.double_click_input()
                elif a.action == "type":
                    try:
                        el.set_edit_text(a.value or "")
                    except Exception:
                        el.click_input()
                        keyboard.send_keys("^a{BACKSPACE}" + escape_text(a.value or ""), with_spaces=True)
                elif a.action == "select":
                    try:
                        el.select(a.value)
                    except Exception:
                        el.expand()
                        time.sleep(0.2)
                        self._find(Target(by="name", value=a.value or ""), timeout).click_input()
                elif a.action == "press":
                    el.set_focus()
                    keyboard.send_keys(to_send_keys(a.value or "Enter"))
                elif a.action == "hover":
                    r = el.rectangle()
                    mouse.move(coords=(r.mid_point().x, r.mid_point().y))
        except DriverError:
            raise
        except Exception as e:
            raise DriverError(f"{a.action} failed: {str(e).splitlines()[0][:300] if str(e) else type(e).__name__}") from e
        time.sleep(0.6)
        return {"ok": True, "view": self.current_view_id()}

    def _click(self, el) -> None:
        """Mouse click, with the app in the foreground. A WPF menu header (File, Help...) is opened through UIA
        ExpandCollapse instead: a mouse click on a background window can close the popup as soon as it opens
        (seen on CI runners). Leaf items stay mouse clicks, because a synchronous UIA Invoke that opens a modal
        dialog would block until the dialog closes."""
        ei = el.element_info
        if ei.control_type == "MenuItem" and ei.framework_id == "WPF":
            try:
                if el.get_expand_state() == 0:  # ExpandCollapseState_Collapsed; leaf items have no pattern and raise
                    el.expand()
                    return
            except Exception:
                pass
        if not self._popups():  # focusing the window would close an open menu or dropdown
            try:
                self._top().set_focus()
            except Exception:
                pass
        el.click_input()

    # ---------- inspection ----------
    def _walk(self, ei, depth: int, max_depth: int, out: list, count: list[int]) -> None:
        if depth > max_depth:
            return
        if count[0] >= MAX_ELEMENTS:
            self._truncated = True
            return
        count[0] += 1
        try:
            children = ei.children()
        except Exception:
            children = []
        out.append((depth, ei, children))
        for c in children:
            self._walk(c, depth + 1, max_depth, out, count)

    def _elements(self, max_depth: int = 50, popups: bool = False):
        """Elements of the current window; with popups, also of open menus/dropdowns (they are captured too)."""
        out: list = []
        count = [0]
        roots = [self._top(), *(self._popups() if popups else [])]
        for w in roots:
            self._walk(w.element_info, 0, max_depth, out, count)
        return out

    def _is_no_uia(self, ei, children) -> bool:
        try:
            r = ei.rectangle
            return ei.control_type in NO_UIA_TYPES and not children and r.width() * r.height() > 40000
        except Exception:
            return False

    def tree(self, depth: int = 6) -> str:
        lines = [f"window: {self._top().window_text()!r} (pid {self.pid})"]
        top = self._top()
        others = [w.window_text() for w in self._windows() if w.handle != top.handle]
        if others:
            lines.append(f"other windows: {others}")
        for d, ei, children in self._elements(depth):
            flags = []
            if self._is_no_uia(ei, children):
                flags.append("no-uia")
                self._no_uia.add(ei.name or ei.automation_id or ei.control_type)
            try:
                if not ei.enabled:
                    flags.append("disabled")
                if ei.element.CurrentIsPassword:
                    flags.append("password")
            except Exception:
                pass
            # WinForms/Win32 generate numeric runtime ids for some elements: unstable, never offer them as targets.
            aid = ei.automation_id
            ident = f" [automation_id={aid}]" if aid and not aid.isdigit() else ""
            value = ""
            if ei.control_type in ("DataItem", "Edit", "ComboBox", "ListItem"):
                try:
                    v = ei.element.GetCurrentPropertyValue(30045)  # UIA_ValueValuePropertyId
                    if v and not self._looks_secret(ei):
                        value = f" = {str(v)[:40]!r}"
                except Exception:
                    pass
            lines.append(f"{'  ' * d}- {ei.control_type} {ei.name!r}{ident}{value}{' (' + ', '.join(flags) + ')' if flags else ''}")
        out = "\n".join(lines)
        return out if len(out) <= TREE_CHAR_BUDGET else out[:TREE_CHAR_BUDGET] + "\n... (trimmed; use --depth)"

    def _bounds(self) -> tuple[tuple[int, int, int, int], bool]:
        """Capture bounds: the current window, grown to include open popup menus/dropdowns."""
        top = self._top()
        l, t, r, b = frame_bounds(top.handle)
        popups = self._popups()
        for p in popups:
            pl, pt, pr, pb = frame_bounds(p.handle)
            l, t, r, b = min(l, pl), min(t, pt), max(r, pr), max(b, pb)
        return (l, t, r, b), bool(popups)

    @staticmethod
    def _looks_secret(ei) -> bool:
        try:
            return bool(ei.element.CurrentIsPassword)
        except Exception:
            return False

    def _origin(self) -> tuple[int, int, float]:
        (l, t, _, _), _ = self._bounds()
        return l, t, self._scale(self._top().handle)

    def _to_rect(self, r, origin) -> Rect:
        ox, oy, s = origin
        return Rect((r.left - ox) / s, (r.top - oy) / s, (r.right - r.left) / s, (r.bottom - r.top) / s)

    def screenshot(self) -> Image.Image:
        top = self._top()
        self._ensure_sized(top)
        (l, t, r, b), has_popups = self._bounds()
        img = None
        if has_popups:
            # Popups are separate windows: grab the screen area (they are topmost while open).
            from PIL import ImageGrab

            img = ImageGrab.grab(bbox=(l, t, r, b), all_screens=True)
        else:
            img = print_window(top.handle)
            if img is None or img.getbbox() is None:
                top.set_focus()
                time.sleep(0.2)
                from PIL import ImageGrab

                img = ImageGrab.grab(bbox=(l, t, r, b), all_screens=True)
        s = self._scale(top.handle)
        if s != 1.0:
            img = img.resize((round(img.width / s), round(img.height / s)), Image.Resampling.LANCZOS)
        return img.convert("RGB")

    def element_info(self, target: Target, timeout_ms: int = 2000) -> ElementInfo | None:
        if target.by == "path":
            name = [p for p in target.value.split("/") if p][-1]
            target = Target(by="name", value=name)
        try:
            el = self._find(target, timeout_ms)
        except DriverError:
            return None
        ei = el.element_info
        rect = self._to_rect(ei.rectangle, self._origin())
        return ElementInfo(name=ei.name or "", role=ei.control_type or "", rect=rect, is_input=ei.control_type in INPUT_TYPES)

    def current_view_id(self) -> str:
        top = self._top()
        return f"{top.window_text()}|{top.element_info.automation_id}"

    def redaction_rects(self, patterns: list[str], selectors: list[str]) -> list[Rect]:
        regs = []
        for p in patterns:
            try:
                regs.append(re.compile(p))
            except re.error:
                continue  # invalid patterns are rejected by config validation; never crash a capture
        origin = self._origin()
        rects: list[Rect] = []
        for _, ei, children in self._elements(popups=True):
            hit = False
            try:
                if ei.element.CurrentIsPassword:
                    hit = True
            except Exception:
                pass
            if not hit and (ei.automation_id in selectors or (ei.name and ei.name in selectors)):
                hit = True
            if not hit:
                texts = [ei.name or ""]
                if ei.control_type in ("Edit", "ComboBox", "DataItem", "Document"):
                    try:
                        texts.append(ei.element.GetCurrentPropertyValue(30045) or "")  # UIA_ValueValuePropertyId
                    except Exception:
                        pass
                hit = any(r.search(t) for r in regs for t in texts if t)
            if self._is_no_uia(ei, children):
                self._no_uia.add(ei.name or ei.automation_id or ei.control_type)
            if hit:
                rects.append(self._to_rect(ei.rectangle, origin))
        return rects

    def focused_info(self) -> ElementInfo | None:
        """Focused control of this app. Presses without a target go to the current window, so focus it first."""
        try:
            from pywinauto.uia_defines import IUIA
            from pywinauto.uia_element_info import UIAElementInfo

            self._top().set_focus()
            ei = UIAElementInfo(IUIA().iuia.GetFocusedElement())
            if ei.process_id != self.pid or ei.control_type == "Window":
                return None
            return ElementInfo(name=ei.name or "", role=ei.control_type or "", is_input=ei.control_type in INPUT_TYPES)
        except Exception:
            return None

    def limitations(self) -> list[str]:
        out = [f"control '{n}' exposes no UI Automation children; captured as part of the window only" for n in sorted(self._no_uia)]
        if self._truncated:
            out.append(f"a window has more than {MAX_ELEMENTS} UI elements; elements past that limit were not checked for redaction")
        return out

# Driver interface (for contributors)

`engine/src/guidegen_engine/drivers/base.py` defines `Driver`. The session daemon and capture use only
this interface, so a new backend (for example a FlaUI helper process) only has to implement it:

| Method | Contract |
|---|---|
| `launch()` / `attach()` | Open the UI session (browser to the URL, CDP connect, attach to the pid) |
| `act(action) -> dict` | Perform one `Action` (already guarded, `${VAR}`s resolved). Raise `DriverError` on failure |
| `tree(depth) -> str` | Token-trimmed (~14k chars) tree of the current view with stable targets |
| `screenshot() -> PIL.Image` | In memory only. The engine redacts before anything is written |
| `element_info(target, timeout_ms) -> ElementInfo \| None` | Accessible name, role, rect (screenshot pixel space), `is_input` |
| `current_view_id() -> str` | URL path or `window title\|automation id` |
| `redaction_rects(patterns, selectors) -> [Rect]` | Password fields, selector matches, text or values matching the patterns |
| `reset()` | Start state (web: home URL; desktop: restart the app via the controller) |
| `limitations() -> [str]` | For example controls without UIA support seen so far |
| `close()` | Release resources (the app itself is stopped by `app stop`) |

Implementations: `web.py` (Playwright Chromium, falls back to Edge/Chrome), `electron.py` (CDP),
`desktop.py` (pywinauto UIA; PrintWindow capture; popups captured with their window; DPI normalised to 100%),
`fake.py` (unit tests).

The guards live outside drivers (`guards/destructive.py`, `runtime.Session`), so every backend gets them.

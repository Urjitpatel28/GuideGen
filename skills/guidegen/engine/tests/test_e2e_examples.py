"""End-to-end benchmark on the example apps (run with `uv run pytest -m e2e`).

Replays the reference manual.yaml recorded by an agent run (tests/e2e/references/<app>/) against the real
example app and checks the PRD success metrics: 100% of expected screens captured, >= 8 tasks, >= 5
troubleshooting entries, no email addresses in the HTML, and `--update` re-capturing only what changed.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
REPO = ENGINE.parents[2]
REFS = Path(__file__).parent / "e2e" / "references"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

APPS = {
    "nextjs-shop": {"desktop": False, "env": {"GUIDEGEN_USER": "demo@shop.test", "GUIDEGEN_PASSWORD": "demo1234"}},
    "wpf-inventory": {"desktop": True, "env": {"GUIDEGEN_USER": "demo", "GUIDEGEN_PASSWORD": "stockroom"}},
    "winforms-crm": {"desktop": True, "env": {"GUIDEGEN_USER": "demo", "GUIDEGEN_PASSWORD": "clientdesk"}},
}
OUT = ".guidegen-e2e"


def gg(app: str, *args: str) -> dict:
    env = {**os.environ, **APPS[app]["env"]}
    r = subprocess.run(
        [sys.executable, "-m", "guidegen_engine", "--repo", str(REPO / "examples" / app), "--out", OUT, "--json", *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
    )
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"guidegen {' '.join(args)} failed ({r.returncode}):\n{r.stdout}\n{r.stderr[-2000:]}") from e


def capture_errors(out: Path) -> str:
    """Why screens failed, from capture-log.json, for assertion messages."""
    try:
        log = json.loads((out / "capture-log.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return f"(no capture-log.json: {e})"
    items = log.get("items", log) if isinstance(log, dict) else log
    bad = [i for i in items if isinstance(i, dict) and i.get("kind") == "screen" and i.get("status") != "captured"]
    return "\n".join(f"{i.get('id')}: {i.get('error')}" for i in bad) or "(no failed screens in capture-log.json)"


def prepare(app: str) -> Path:
    if APPS[app]["desktop"] and sys.platform != "win32":
        pytest.skip("desktop examples need Windows")
    out = REPO / "examples" / app / OUT
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    for f in ("manual.yaml", "guidegen.config.json"):
        shutil.copy(REFS / app / f, out / f)
    return out


@pytest.mark.e2e
@pytest.mark.parametrize("app", sorted(APPS))
def test_example_benchmark(app):
    out = prepare(app)
    expected = json.loads((REPO / "examples" / app / "expected-screens.json").read_text())
    try:
        assert gg(app, "app", "start")["ok"]
        cap = gg(app, "capture")
        assert cap["ok"] and cap["screensFailed"] == 0, capture_errors(out)
        rendered = gg(app, "render")
        rep = gg(app, "report")
    finally:
        gg(app, "app", "stop")

    assert rep["screens"]["captured"] == len(expected["screens"])
    assert rep["screens"]["unreachable"] == 0
    assert rendered["tasks"] >= expected["minTasks"]
    assert rendered["troubleshooting"] >= expected["minTroubleshooting"]
    assert rep["redactions"] > 0
    html = (out / "manual-html" / "index.html").read_text(encoding="utf-8")
    # name@company.com is the placeholder the manual's troubleshooting text uses ("type a full address such as
    # name@company.com"); any other address in the output is seed data that should have been redacted
    leaked = {e for e in EMAIL.findall(html) if e != "name@company.com"}
    assert not leaked, leaked
    assert (out / "manual.docx").stat().st_size > 50_000


UPDATE_CASES = {
    # app: (source file to touch, screen that must be re-captured)
    "wpf-inventory": ("src/Inventory/Views/ReceiveStockDialog.xaml", "receive-stock"),
    "nextjs-shop": ("app/settings/page.js", "settings"),
    "winforms-crm": ("src/Crm/OptionsForm.cs", "options"),
}


@pytest.mark.e2e
@pytest.mark.parametrize("app", sorted(UPDATE_CASES))
def test_update_recaptures_only_changed(app):
    out = prepare(app)
    src, screen = UPDATE_CASES[app]
    path = REPO / "examples" / app / src
    original = path.read_bytes()
    manual = out / "manual.yaml"
    manual.write_text(manual.read_text(encoding="utf-8").replace(
        "  - id: " + screen + "\n", "  - id: " + screen + "\n    # developer comment kept across updates\n", 1), encoding="utf-8")
    try:
        assert gg(app, "app", "start")["ok"]
        gg(app, "capture")
        assert gg(app, "changed")["screens"] == [], capture_errors(out)
        comment = b"\n<!-- touched by test -->\n" if src.endswith(".xaml") else b"\n// touched by test\n"
        path.write_bytes(original + comment)
        ch = gg(app, "changed")
        assert [s["id"] for s in ch["screens"]] == [screen]
        gg(app, "capture", *sum((["--only", i] for i in ch["only"]), []))
        assert gg(app, "changed")["screens"] == []
        assert "# developer comment kept across updates" in manual.read_text(encoding="utf-8")
    finally:
        path.write_bytes(original)
        gg(app, "app", "stop")

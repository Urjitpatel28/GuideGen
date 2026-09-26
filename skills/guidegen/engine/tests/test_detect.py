from __future__ import annotations

import pytest

from guidegen_engine.detect import detect

from conftest import FIXTURES

CASES = {
    "vite-react": ("web", "vite-react", "http://localhost:5199"),
    "angular": ("web", "angular", "http://localhost:4200"),
    "aspnet-razor": ("web", "aspnet-razor-pages", "http://localhost:5081"),
    "blazor-server": ("web", "blazor", "http://localhost:5000"),
    "electron-app": ("electron", "electron", None),
    "winui-app": ("winui", "winui", None),
    "wpf-app": ("wpf", "wpf", None),
    "winforms-app": ("winforms", "winforms", None),
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_detect_kind(name):
    kind, framework, url = CASES[name]
    res = detect(FIXTURES / name)
    top = res["candidates"][0]
    assert top["kind"] == kind
    assert top["framework"] == framework
    assert top["url"] == url
    assert top["evidence"]


def test_desktop_executable_guess():
    top = detect(FIXTURES / "wpf-app")["candidates"][0]
    assert top["executable"] == "WpfApp/bin/Debug/net8.0-windows/Inventory.exe"
    assert top["build"].startswith("dotnet build")


def test_multiple_candidates_are_ranked_not_guessed():
    res = detect(FIXTURES / "multi-app")
    assert res["ambiguous"] is True
    assert [c["rank"] for c in res["candidates"]] == [1, 2]
    assert {c["kind"] for c in res["candidates"]} == {"web", "wpf"}
    web = next(c for c in res["candidates"] if c["kind"] == "web")
    assert web["url"] == "http://localhost:3100"

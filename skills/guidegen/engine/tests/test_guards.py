from __future__ import annotations

import pytest

from guidegen_engine.actions import Action, Target
from guidegen_engine.app.guard import check_localhost, host_of, is_local
from guidegen_engine.drivers.base import ElementInfo
from guidegen_engine.errors import HardBlocker
from guidegen_engine.guards.destructive import check


def click(name: str, role: str = "button") -> tuple[Action, ElementInfo]:
    return Action(action="click", target=Target(by="role", value=role, name=name)), ElementInfo(name=name, role=role)


@pytest.mark.parametrize("name", ["Delete", "Remove item", "Pay now", "Checkout", "Send quote", "Publish", "Submit payment", "Reset data", "Deactivate account"])
def test_destructive_refused(name):
    a, info = click(name)
    assert check(a, info, []) is not None


@pytest.mark.parametrize("name", ["Save", "New Order", "Deleted items", "Sender settings", "Payments overview", "Resetting tips"])
def test_safe_or_not_whole_word(name):
    a, info = click(name)
    # "Deleted items" etc. do not match whole words
    assert check(a, info, []) is None


def test_inputs_never_destructive():
    a = Action(action="click", target=Target(by="label", value="Email"))
    assert check(a, ElementInfo(name="Email", role="textbox", is_input=True), []) is None
    assert check(Action(action="type", target=Target(by="label", value="Email"), value="x"), None, []) is None


def test_allow_list_by_name_and_target():
    a, info = click("Delete")
    assert check(a, info, ["delete"]) is None
    assert check(a, info, [{"by": "role", "value": "button", "name": "Delete"}]) is None
    assert check(a, info, ["Remove"]) is not None


def test_safe_keys_pass():
    assert check(Action(action="press", value="Escape"), None, []) is None


@pytest.mark.parametrize("value,host", [
    ("Server=(localdb)\\mssqllocaldb;Database=Shop;Trusted_Connection=True", "localhost"),
    ("Server=.\\SQLEXPRESS;Database=x", "localhost"),
    ("Data Source=app.db", None),
    ("Host=db.prod.example.com;Port=5432;Database=x", "db.prod.example.com"),
    ("postgres://user:pw@10.0.0.5:5432/app", "10.0.0.5"),
    ("tcp:myserver.database.windows.net,1433", None),
    ("Server=tcp:myserver.database.windows.net,1433;Database=x", "myserver.database.windows.net"),
    ("http://localhost:5000/api", "localhost"),
])
def test_host_of(value, host):
    assert host_of(value) == host


def test_localhost_guard_blocks_remote(tmp_path):
    (tmp_path / "appsettings.Development.json").write_text(
        '{"ConnectionStrings": {"Default": "Server=prod-sql.acme.com;Database=Shop"}}', encoding="utf-8")
    with pytest.raises(HardBlocker) as e:
        check_localhost(tmp_path, "http://localhost:5000", allow_remote=False)
    assert e.value.exit_code == 2
    assert e.value.data["file"] == "appsettings.Development.json" and e.value.data["host"] == "prod-sql.acme.com"
    assert check_localhost(tmp_path, "http://localhost:5000", allow_remote=True)


def test_localhost_guard_allows_compose_services_and_ignores_saas(tmp_path):
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://app:pw@db:5432/app\nSENTRY_DSN=https://abc@o1.ingest.sentry.io/1\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text("services:\n  db:\n    image: postgres\n", encoding="utf-8")
    checked = check_localhost(tmp_path, "http://127.0.0.1:3000", allow_remote=False)
    assert any(c["host"] == "db" for c in checked)
    assert is_local("db", {"db"}) and not is_local("api.acme.com", set())


def test_remote_app_url_blocked(tmp_path):
    with pytest.raises(HardBlocker):
        check_localhost(tmp_path, "https://app.acme.com", allow_remote=False)


# ---- guard gaps found in review ----
from guidegen_engine.guards.destructive import check_goto  # noqa: E402
from guidegen_engine.runtime import Session  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from conftest import base_config  # noqa: E402


def test_press_without_target_checks_focused_element():
    enter = Action(action="press", value="Enter")
    assert check(enter, ElementInfo(name="Delete account", role="button"), []) is not None
    assert check(enter, ElementInfo(name="Search", role="textbox", is_input=True), []) is None
    assert check(enter, None, []) is None  # nothing focused


def test_session_press_uses_focus(fake):
    s = Session(base_config(), fake)
    assert s.perform(Action(action="click", target=Target(by="name", value="Orders")))["ok"]
    fake.focused = "Delete"  # e.g. tabbed onto the Delete button
    res = s.perform(Action(action="press", value="Enter"))
    assert res.get("refused") is True


@pytest.mark.parametrize("role", ["label", "option", "text", "document", "input"])
def test_non_editable_roles_are_guarded(role):
    # <input type=submit value="Delete"> reports role "input" but is_input False
    a = Action(action="click", target=Target(by="text", value="Delete"))
    assert check(a, ElementInfo(name="Delete", role=role), []) is not None


def test_select_checks_option_text_only():
    field = ElementInfo(name="Email preferences", role="combobox", is_input=True)
    ok = Action(action="select", target=Target(by="label", value="Email preferences"), value="Weekly")
    bad = Action(action="select", target=Target(by="label", value="Bulk action"), value="Delete selected")
    assert check(ok, field, []) is None
    assert check(bad, field, []) is not None


@pytest.mark.parametrize("url,refused", [
    ("/orders", False),
    ("http://localhost:3000/orders", False),
    ("http://127.0.0.1:5000/x", False),
    ("https://app.local-dev.test/x", False),  # the app's own host (see own_urls)
    ("https://prod.acme.com/admin", True),
    ("file:///etc/passwd", True),
])
def test_goto_stays_on_app(url, refused):
    res = check_goto(Action(action="goto", value=url), ["https://app.local-dev.test", None])
    assert (res is not None) is refused


def test_base_appsettings_scanned_unless_overridden(tmp_path):
    (tmp_path / "appsettings.json").write_text(
        '{"ConnectionStrings": {"Default": "Server=prod-sql.acme.com;Database=Shop"}, "Docs": {"Url": "https://docs.acme.com"}}',
        encoding="utf-8")
    with pytest.raises(HardBlocker) as e:
        check_localhost(tmp_path, "http://localhost:5000", allow_remote=False)
    assert e.value.data["host"] == "prod-sql.acme.com"
    import json

    (tmp_path / "appsettings.Development.json").write_text(
        json.dumps({"ConnectionStrings": {"Default": r"Server=(localdb)\mssqllocaldb;Database=Shop"}}), encoding="utf-8")
    checked = check_localhost(tmp_path, "http://localhost:5000", allow_remote=False)
    assert not any(c["host"] == "docs.acme.com" for c in checked)  # unrelated URLs in the base file are ignored


def test_hosted_backend_env_keys_flagged(tmp_path):
    (tmp_path / ".env").write_text("SUPABASE_URL=https://xyz.supabase.co\n", encoding="utf-8")
    with pytest.raises(HardBlocker):
        check_localhost(tmp_path, "http://localhost:3000", allow_remote=False)


def test_invalid_redact_pattern_rejected():
    with pytest.raises(ValidationError, match="invalid regular expression"):
        base_config(safety={"redactPatterns": ["(unclosed"]})


def test_negative_budget_rejected():
    with pytest.raises(ValidationError):
        base_config(budget={"maxScreens": -1})

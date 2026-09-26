from __future__ import annotations

import pytest

from guidegen_engine.errors import GuideGenError
from guidegen_engine.manual import ManualStore

GOLDEN = """\
# Developer header comment - must survive.
version: 1
meta:
  title: Acme Quote User Manual   # inline comment
  audience: end users
chapters:
  - id: getting-started
  - id: tasks
  - id: reference
  - id: troubleshooting
screens:
  - id: orders-list
    title: Orders
    kind: page
    source: [src/Orders.xaml]
    status: pending
    exclude: false
    navigate:
      - {action: click, target: {by: name, value: Orders}}
    text:
      summary: Lists all orders.
      override: "My own words about orders."   # developer override
  # a comment between items
  - id: settings
    title: Settings
    exclude: true
tasks:
  - id: create-quote
    title: Create a quote
    rank: 1
    steps:
      - id: s1
        screen: orders-list
        action: {action: click, target: {by: name, value: New Order}}
        text: Click **New Order**.
        override: Press the big **New Order** button.
"""


def test_single_field_change_leaves_other_bytes(tmp_path):
    p = tmp_path / "manual.yaml"
    p.write_text(GOLDEN, encoding="utf-8")
    store = ManualStore.load(p)
    store.set_fields("screens", "orders-list", status="captured")
    store.save()
    after = p.read_text(encoding="utf-8")
    assert after == GOLDEN.replace("    status: pending", "    status: captured")


def test_protected_fields_survive_engine_writes(tmp_path):
    p = tmp_path / "manual.yaml"
    p.write_text(GOLDEN, encoding="utf-8")
    store = ManualStore.load(p)
    store.set_fields("screens", "settings", exclude=False, status="captured")
    store.set_fields("screens", "orders-list", text={"summary": "x", "override": "engine must not win"})
    m = store.model()
    assert m.screen("settings").exclude is True
    assert m.screen("orders-list").text.summary == "x"
    assert m.screen("orders-list").text.override == "My own words about orders."


def test_merge_keeps_overrides_and_comments(tmp_path):
    p = tmp_path / "manual.yaml"
    p.write_text(GOLDEN, encoding="utf-8")
    store = ManualStore.load(p)
    stats = store.merge({
        "screens": [
            {"id": "orders-list", "title": "Orders", "text": {"summary": "Regenerated summary.", "override": None}, "exclude": True},
            {"id": "customers", "title": "Customers", "source": ["src/Customers.xaml"]},
        ],
        "tasks": [{"id": "create-quote", "title": "Create a quote", "steps": [
            {"id": "s1", "text": "Click **New Order** (regenerated).", "override": None},
            {"id": "s2", "text": "Click **Save**.", "action": {"action": "click", "target": {"by": "name", "value": "Save"}}},
        ]}],
    })
    store.save()
    assert stats == {"added": 1, "updated": 2}
    m = store.model()
    orders = m.screen("orders-list")
    assert orders.text.override == "My own words about orders."
    assert orders.text.summary == "Regenerated summary."
    assert orders.exclude is False
    task = m.task("create-quote")
    assert [s.id for s in task.steps] == ["s1", "s2"]
    assert task.steps[0].override == "Press the big **New Order** button."
    text = p.read_text(encoding="utf-8")
    assert "# Developer header comment - must survive." in text
    assert "# developer override" in text
    assert "# a comment between items" in text


def test_locked_fields(tmp_path):
    p = tmp_path / "manual.yaml"
    p.write_text(GOLDEN.replace("    title: Orders\n", "    title: My Orders\n    locked: [title]\n"), encoding="utf-8")
    store = ManualStore.load(p)
    store.merge({"screens": [{"id": "orders-list", "title": "Orders (generated)"}]})
    assert store.model().screen("orders-list").title == "My Orders"


def test_new_manual_and_validation(tmp_path):
    store = ManualStore.load(tmp_path / "m.yaml")
    store.merge({"screens": [{"id": "Bad Id", "title": "x"}]})
    with pytest.raises(GuideGenError):
        store.save()


def test_merge_keeps_omitted_items_with_developer_edits(tmp_path):
    store = ManualStore.load(tmp_path / "manual.yaml")
    store.merge({"tasks": [{"id": "t", "title": "T", "steps": [
        {"id": "s1", "text": "One"}, {"id": "s2", "text": "Two"}, {"id": "s3", "text": "Three"}]}]})
    step2 = store.find("tasks", "t")["steps"][1]
    step2["override"] = "My own words."
    # regeneration drops s2 and s3: s3 had no edits and goes, s2 keeps its developer override
    store.merge({"tasks": [{"id": "t", "steps": [{"id": "s1", "text": "One!"}]}]})
    ids = [s["id"] for s in store.find("tasks", "t")["steps"]]
    assert ids == ["s1", "s2"]
    assert store.find("tasks", "t")["steps"][1]["override"] == "My own words."
    store.save()


def test_remove_refuses_developer_edited_items(tmp_path):
    store = ManualStore.load(tmp_path / "manual.yaml")
    store.merge({"screens": [{"id": "a", "title": "A"}, {"id": "b", "title": "B", "exclude": True}]})
    assert store.remove("screens", "a") is True
    with pytest.raises(GuideGenError, match="developer edits"):
        store.remove("screens", "b")
    assert store.remove("screens", "b", force=True) is True
    with pytest.raises(GuideGenError, match="unknown collection"):
        store.remove("steps", "x")

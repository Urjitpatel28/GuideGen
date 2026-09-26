from __future__ import annotations

import json

from PIL import Image

from guidegen_engine.capture import run_capture
from guidegen_engine.changed import changed
from guidegen_engine.manual import ManualStore
from guidegen_engine.runtime import Session

from conftest import base_config

MANUAL = {
    "meta": {"title": "Acme Quote User Manual"},
    "screens": [
        {"id": "home", "title": "Home", "source": ["src/Home.xaml"], "navigate": []},
        {"id": "orders-list", "title": "Orders", "source": ["src/Orders.xaml"],
         "navigate": [{"action": "click", "target": {"by": "name", "value": "Orders"}}]},
        {"id": "new-order", "title": "New Order", "kind": "dialog", "source": ["src/Orders.xaml"],
         "navigate": [{"action": "click", "target": {"by": "name", "value": "Orders"}},
                      {"action": "click", "target": {"by": "name", "value": "New Order"}}]},
        {"id": "ghost", "title": "Ghost", "navigate": [{"action": "click", "target": {"by": "name", "value": "Nope"}}]},
        {"id": "customers", "title": "Customers", "navigate": [{"action": "click", "target": {"by": "name", "value": "Customers"}}]},
        {"id": "hidden", "title": "Hidden", "exclude": True},
    ],
    "tasks": [
        {"id": "create-order", "title": "Create an order", "rank": 1, "evidence": [{"type": "e2e-test", "ref": "tests/order.spec.ts"}],
         "steps": [
             {"id": "s1", "screen": "home", "action": {"action": "click", "target": {"by": "name", "value": "Orders"}}, "text": "Click **Orders**."},
             {"id": "s2", "screen": "orders-list", "action": {"action": "click", "target": {"by": "name", "value": "New Order"}}, "text": "Click **New Order**."},
             {"id": "s3", "screen": "new-order", "action": {"action": "type", "target": {"by": "name", "value": "Customer"}, "value": "Contoso"}, "text": "Type the customer name."},
             {"id": "s4", "screen": "new-order", "action": {"action": "click", "target": {"by": "name", "value": "Save"}}, "text": "Click **Save**."},
         ]},
        {"id": "delete-order", "title": "Delete an order", "rank": 2, "steps": [
            {"id": "s1", "action": {"action": "click", "target": {"by": "name", "value": "Orders"}}, "text": "Click **Orders**."},
            {"id": "s2", "action": {"action": "click", "target": {"by": "name", "value": "Delete"}}, "text": "Click **Delete**."},
        ]},
        {"id": "third", "title": "Third", "rank": 3, "steps": [{"id": "s1", "text": "Look."}]},
    ],
}


def _setup(ctx, fake, **cfg_over):
    store = ManualStore.load(ctx.manual_path)
    store.merge(MANUAL)
    store.save()
    cfg = base_config(**cfg_over)
    return store, Session(cfg, fake)


def test_capture_statuses_images_and_log(ctx, fake):
    store, session = _setup(ctx, fake, budget={"maxScreens": 4, "maxTasks": 2})
    res = run_capture(ctx, session, store, progress=lambda m: None)
    m = ManualStore.load(ctx.manual_path).model()

    assert m.screen("home").status == "captured"
    assert m.screen("orders-list").image == "screens/orders-list.png"
    assert m.screen("orders-list").source_hash.startswith("sha256:")
    assert m.screen("ghost").status == "unreachable" and "Nope" in m.screen("ghost").unreachable_reason
    assert m.screen("customers").status == "budget-cut"
    assert m.screen("hidden").status == "excluded"
    assert m.task("third").status == "budget-cut"

    t = m.task("create-order")
    assert t.status == "captured" and all(s.status == "captured" for s in t.steps)
    d = m.task("delete-order")
    assert d.status == "captured"  # refused steps are documented, not failures
    assert d.steps[1].status == "refused" and "destructive" in d.steps[1].note
    assert (ctx.out / "screens/delete-order/s2.png").exists()  # state before the refused click

    log = json.loads((ctx.out / "capture-log.json").read_text())
    assert len(log["refusals"]) == 1
    assert res["redactions"] >= 1  # the support email on home + password field
    # only redacted/annotated images are ever written: every png under screens/ is referenced
    written = {p.relative_to(ctx.out).as_posix() for p in (ctx.out / "screens").rglob("*.png")}
    referenced = {s.image for s in m.screens if s.image} | {st.image for t in m.tasks for st in t.steps if st.image}
    assert written == referenced


def test_redaction_blurs_region(ctx, fake):
    store, session = _setup(ctx, fake)
    img, n, _ = session.shot()
    assert n == 1  # support@acme.test on home
    raw = fake.screenshot()
    box = (10, 260, 160, 280)
    assert list(img.crop(box).get_flattened_data()) != list(raw.crop(box).get_flattened_data())


def test_only_and_changed(ctx, fake):
    store, session = _setup(ctx, fake)
    run_capture(ctx, session, store, progress=lambda m: None)
    m = ManualStore.load(ctx.manual_path).model()
    before = changed(ctx.repo, m)
    assert "orders-list" not in before["only"]

    (ctx.repo / "src" / "Orders.xaml").write_text("<Page Title='changed'/>", encoding="utf-8")
    res = changed(ctx.repo, m)
    assert {s["id"] for s in res["screens"]} >= {"orders-list", "new-order"}
    assert "home" not in {s["id"] for s in res["screens"]}
    assert "create-order" in {t["id"] for t in res["tasks"]}

    fake.log.clear()
    store = ManualStore.load(ctx.manual_path)
    run_capture(ctx, Session(session.cfg, fake), store, only=["orders-list"], progress=lambda m: None)
    m2 = ManualStore.load(ctx.manual_path).model()
    assert m2.screen("orders-list").source_hash != m.screen("orders-list").source_hash
    assert m2.screen("home").source_hash == m.screen("home").source_hash
    assert {s["id"] for s in changed(ctx.repo, m2)["screens"]} == {"ghost", "new-order"}


def test_capture_deterministic(ctx, fake):
    store, session = _setup(ctx, fake)
    run_capture(ctx, session, store, progress=lambda m: None)
    first = {p.name: Image.open(p).tobytes() for p in (ctx.out / "screens").glob("*.png")}
    run_capture(ctx, session, ManualStore.load(ctx.manual_path), progress=lambda m: None)
    second = {p.name: Image.open(p).tobytes() for p in (ctx.out / "screens").glob("*.png")}
    assert first == second

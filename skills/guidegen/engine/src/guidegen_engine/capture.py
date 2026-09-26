"""`guidegen capture`: deterministic replay of manual.yaml (screens' `navigate`, tasks' `steps`).

Exploration (agent, adaptive) records the steps; capture only replays them, so captures are reproducible
and `--update` can re-capture a subset without exploring again.

Screenshot timing per task step:
- click / double_click / hover / select / press: shot BEFORE the action, acted-on element highlighted
  ("Click **Save**" shows the Save button). A refused destructive step keeps exactly this image.
- type: shot AFTER typing, field highlighted.
- goto / wait / screenshot / close / no action: shot after, no highlight.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
from collections.abc import Callable

from guidegen_engine.changed import hash_sources
from guidegen_engine.context import Ctx
from guidegen_engine.manual.store import ManualStore
from guidegen_engine.masking import mask
from guidegen_engine.runtime import PRE_ACTION_SHOT, Session


def _progress(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def plan_budget(manual, cfg) -> tuple[list, list, dict[str, str]]:
    """Return (screens_to_capture, tasks_to_capture, status_overrides) honouring exclude + budgets."""
    statuses: dict[str, str] = {}
    screens = []
    for s in manual.screens:
        if s.exclude:
            statuses[s.id] = "excluded"
        elif s.status == "unreachable" and not s.navigate:
            continue
        elif len(screens) >= cfg.budget.max_screens:
            statuses[s.id] = "budget-cut"
        else:
            screens.append(s)
    tasks = []
    for t in sorted(manual.tasks, key=lambda t: t.rank):
        if t.exclude:
            statuses[t.id] = "excluded"
        elif len(tasks) >= cfg.budget.max_tasks:
            statuses[t.id] = "budget-cut"
        else:
            tasks.append(t)
    return screens, tasks, statuses


def run_capture(
    ctx: Ctx,
    session: Session,
    store: ManualStore,
    only: list[str] | None = None,
    progress: Callable[[str], None] = _progress,
    reseed: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """reseed: called before the screens pass and before each task (restores seed data)."""
    manual = store.model()
    cfg = session.cfg
    screens, tasks, statuses = plan_budget(manual, cfg)
    for sid, st in statuses.items():
        coll = "screens" if manual.screen(sid) else "tasks"
        store.set_fields(coll, sid, status=st)

    if only:
        wanted = set(only)
        screens = [s for s in screens if s.id in wanted]
        tasks = [t for t in tasks if t.id in wanted or any(st.screen in wanted for st in t.steps)]

    items: list[dict[str, Any]] = []
    total = len(screens)
    started = time.time()
    if reseed and (screens or tasks):
        reseed()

    for i, s in enumerate(screens, 1):
        t0 = time.time()
        item: dict[str, Any] = {"kind": "screen", "id": s.id, "status": "captured", "redactions": 0}
        try:
            session.reset(login=not s.before_login)
            failure = None
            for n, nav in enumerate(s.navigate, 1):
                res = session.perform(nav, f"screen {s.id}")
                if not res.get("ok"):
                    failure = f"navigate step {n} ({nav.describe()}): {res.get('error') or res.get('reason')}"
                    break
            if failure:
                item.update(status="unreachable", error=failure)
                store.set_fields("screens", s.id, status="unreachable", unreachableReason=f"capture replay failed at {failure}")
            else:
                extra = [r for nav in s.navigate for r in nav.redact]
                before = set(session.driver.limitations())
                img, n_red, _ = session.shot(extra_redact=extra)
                if set(session.driver.limitations()) - before:
                    store.set_fields("screens", s.id, noUia=True)  # custom-drawn controls seen here
                rel_path = f"screens/{s.id}.png"
                session.save(img, ctx.out / rel_path)
                item.update(image=rel_path, redactions=n_red)
                store.set_fields(
                    "screens", s.id, status="captured", image=rel_path, unreachableReason=None,
                    sourceHash=hash_sources(ctx.repo, s.source),
                )
        except Exception as e:  # never abort the whole run for one screen
            item.update(status="error", error=mask(f"{type(e).__name__}: {e}"))
        item["durationMs"] = int((time.time() - t0) * 1000)
        items.append(item)
        progress(f"{'captured' if item['status'] == 'captured' else item['status']} {i}/{total} {s.id}")

    for t in tasks:
        t0 = time.time()
        task_item: dict[str, Any] = {"kind": "task", "id": t.id, "steps": []}
        ok_steps = 0
        try:
            if reseed:
                reseed()
            session.reset(login=not t.before_login)
            broken: str | None = None
            for idx, step in enumerate(t.steps, 1):
                s0 = time.time()
                rel_path = f"screens/{t.id}/{step.id}.png"
                entry: dict[str, Any] = {"id": step.id, "status": "captured", "redactions": 0, "image": rel_path}
                a = step.action
                if broken:
                    entry.update(status="failed", error=f"not reached: {broken}")
                    store.set_step_fields(t.id, step.id, status="failed", note=entry["error"])
                    task_item["steps"].append(entry)
                    continue
                extra = list(a.redact) if a else []
                highlight = a.target if (a and step.highlight and a.target is not None) else None
                if a is not None and a.action in PRE_ACTION_SHOT:
                    img, n_red, _ = session.shot(extra, highlight, idx, step.crop)
                    session.save(img, ctx.out / rel_path)
                    res = session.perform(a, f"task {t.id} step {step.id}")
                    if res.get("refused"):
                        entry.update(status="refused", reason=res["reason"])
                    elif not res.get("ok"):
                        entry.update(status="failed", error=res.get("error"))
                        broken = f"step {step.id} failed"
                else:
                    res = session.perform(a, f"task {t.id} step {step.id}") if a is not None else {"ok": True}
                    if not res.get("ok"):
                        entry.update(status="refused" if res.get("refused") else "failed", error=res.get("error") or res.get("reason"))
                        if not res.get("refused"):
                            broken = f"step {step.id} failed"
                    img, n_red, _ = session.shot(extra, highlight if a and a.action == "type" else None, idx, step.crop)
                    session.save(img, ctx.out / rel_path)
                entry["redactions"] = n_red
                entry["durationMs"] = int((time.time() - s0) * 1000)
                if entry["status"] in ("captured", "refused"):
                    ok_steps += 1
                store.set_step_fields(
                    t.id, step.id, status=entry["status"], image=rel_path,
                    note=entry.get("reason") or entry.get("error"),
                )
                task_item["steps"].append(entry)
        except Exception as e:
            task_item["error"] = mask(f"{type(e).__name__}: {e}")
        status = "captured" if t.steps and ok_steps == len(t.steps) else "partial"
        store.set_fields("tasks", t.id, status=status)
        task_item.update(status=status, durationMs=int((time.time() - t0) * 1000))
        items.append(task_item)
        progress(f"task {t.id}: {ok_steps}/{len(t.steps)} steps")

    store.set_meta(generatedAt=datetime.now(UTC).replace(microsecond=0))
    store.save()

    log = _merge_log(ctx.out / "capture-log.json", items, bool(only))
    log["refusals"] = _merge_refusals(log.get("refusals", []), session.refusals)
    log["limitations"] = sorted(set(log.get("limitations", [])) | set(session.driver.limitations()))
    (ctx.out / "capture-log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")

    captured = sum(1 for i in items if i["kind"] == "screen" and i["status"] == "captured")
    return {
        "ok": True,
        "screensCaptured": captured,
        "screensFailed": sum(1 for i in items if i["kind"] == "screen" and i["status"] != "captured"),
        "tasks": {i["id"]: i["status"] for i in items if i["kind"] == "task"},
        "refused": len(session.refusals),
        "redactions": sum(i.get("redactions", 0) for i in items) + sum(s.get("redactions", 0) for i in items for s in i.get("steps", [])),
        "seconds": round(time.time() - started, 1),
        "log": "capture-log.json",
    }


def _merge_log(path: Path, items: list[dict[str, Any]], partial: bool) -> dict[str, Any]:
    prev: dict[str, Any] = {}
    if partial and path.exists():
        try:
            prev = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prev = {}
    keep = {(i["kind"], i["id"]): i for i in prev.get("items", [])}
    for i in items:
        keep[(i["kind"], i["id"])] = i
    return {
        "capturedAt": datetime.now(UTC).isoformat(timespec="seconds"),
        "items": list(keep.values()),
        "refusals": prev.get("refusals", []),
        "limitations": prev.get("limitations", []),
    }


def _merge_refusals(prev: list[dict], new: list[dict]) -> list[dict]:
    seen = {(r["context"], r["action"]) for r in new}
    return [r for r in prev if (r["context"], r["action"]) not in seen] + new

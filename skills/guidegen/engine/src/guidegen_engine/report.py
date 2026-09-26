"""`guidegen report`: run-report.md - full accounting of what was captured, skipped, cut, refused and redacted."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from guidegen_engine.config.models import Config
from guidegen_engine.context import Ctx
from guidegen_engine.manual.models import Manual

STANDARD_LIMITATION = (
    "Text drawn inside images, charts or custom-drawn controls cannot be detected for redaction. "
    "Use seed data with fake values and review screenshots before publishing."
)


def _json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _md_cell(s: Any) -> str:
    return str(s or "").replace("|", "\\|").replace("\n", " ")


def build_report(ctx: Ctx, cfg: Config, manual: Manual) -> tuple[str, dict[str, Any]]:
    log = _json(ctx.out / "capture-log.json", {})
    notes = _json(ctx.work / "notes.json", [])
    render_notes = _json(ctx.work / "render-notes.json", [])
    items = log.get("items", [])

    by_status: dict[str, list] = {}
    for s in manual.screens:
        st = "excluded" if s.exclude else s.status
        by_status.setdefault(st, []).append(s)
    captured = by_status.get("captured", [])
    unreachable = by_status.get("unreachable", [])
    budget = by_status.get("budget-cut", [])
    excluded = by_status.get("excluded", [])
    pending = by_status.get("pending", [])

    tasks_ok = [t for t in manual.tasks if not t.exclude and t.status == "captured"]
    tasks_partial = [t for t in manual.tasks if not t.exclude and t.status == "partial"]
    tasks_cut = [t for t in manual.tasks if not t.exclude and t.status == "budget-cut"]

    redactions: list[tuple[str, int]] = []
    for it in items:
        if it.get("kind") == "screen" and it.get("redactions"):
            redactions.append((it.get("image") or it["id"], it["redactions"]))
        for st in it.get("steps", []):
            if st.get("redactions"):
                redactions.append((st.get("image") or f"{it['id']}/{st['id']}", st["redactions"]))
    total_red = sum(n for _, n in redactions)
    refusals = log.get("refusals", [])
    limitations = list(log.get("limitations", [])) + [n["message"] for n in notes] + list(render_notes)
    no_uia = [s for s in manual.screens if s.no_uia]

    L: list[str] = []
    L.append(f"# GuideGen run report - {cfg.brand.product_name or manual.meta.title}")
    L.append("")
    L.append(f"Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} · output folder `{ctx.out.name}/`")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append("| Item | Count |")
    L.append("|---|---|")
    for label, n in (
        ("Screens captured", len(captured)), ("Screens unreachable", len(unreachable)),
        ("Screens excluded (by you)", len(excluded)), ("Screens cut by budget", len(budget)),
        ("Screens not yet captured", len(pending)), ("Tasks complete", len(tasks_ok)),
        ("Tasks with failed or refused steps", len(tasks_partial)), ("Tasks cut by budget", len(tasks_cut)),
        ("Troubleshooting entries", len([t for t in manual.troubleshooting if not t.exclude])),
        ("Refused destructive actions", len(refusals)), ("Redactions applied", total_red),
    ):
        L.append(f"| {label} | {n} |")
    L.append("")

    L.append("## Captured")
    L.append("")
    if captured:
        L.append("| Screen | Title | Image |")
        L.append("|---|---|---|")
        for s in captured:
            L.append(f"| `{s.id}` | {_md_cell(s.title)} | `{s.image}` |")
    else:
        L.append("Nothing captured yet.")
    L.append("")

    L.append("## Unreachable")
    L.append("")
    if unreachable:
        L.append("| Screen | Reason | Source |")
        L.append("|---|---|---|")
        for s in unreachable:
            L.append(f"| `{s.id}` {_md_cell(s.title)} | {_md_cell(s.unreachable_reason or 'no reason recorded')} | {_md_cell(', '.join(s.source))} |")
    else:
        L.append("None - every inventoried screen was reached.")
    L.append("")

    L.append("## Budget-cut")
    L.append("")
    if budget or tasks_cut:
        L.append(f"Budget: {cfg.budget.max_screens} screens, {cfg.budget.max_tasks} tasks (`budget` in guidegen.config.json or `--max-screens/--max-tasks`).")
        L.append("")
        for s in budget:
            L.append(f"- screen `{s.id}` {s.title}")
        for t in tasks_cut:
            L.append(f"- task `{t.id}` {t.title}")
    else:
        L.append("None.")
    L.append("")

    if excluded:
        L.append("## Excluded by you")
        L.append("")
        for s in excluded:
            L.append(f"- `{s.id}` {s.title}")
        L.append("")

    L.append("## Tasks")
    L.append("")
    if manual.tasks:
        L.append("| Rank | Task | Status | Evidence | Problem steps |")
        L.append("|---|---|---|---|---|")
        for t in sorted(manual.tasks, key=lambda t: t.rank):
            bad = [f"{st.id}: {st.status}" + (f" ({st.note})" if st.note else "") for st in t.steps if st.status in ("failed", "refused")]
            ev = ", ".join(f"{e.type}" for e in t.evidence) or "-"
            status = "excluded" if t.exclude else t.status
            L.append(f"| {t.rank} | `{t.id}` {_md_cell(t.title)} | {status} | {_md_cell(ev)} | {_md_cell('; '.join(bad)) or '-'} |")
    else:
        L.append("No tasks planned.")
    L.append("")

    brief_tasks = [t for t in manual.tasks if not t.exclude and any(e.type == "brief" for e in t.evidence)]
    gaps = manual.brief_gaps
    if cfg.brief.sources or cfg.brief.notes or brief_tasks or gaps:
        L.append("## Your brief")
        L.append("")
        for src in cfg.brief.sources:
            where = src.url or src.path or "-"
            L.append(f"- {src.kind}: `{_md_cell(where)}`" + (f" ({_md_cell(src.note)})" if src.note else ""))
        if cfg.brief.notes:
            L.append("- notes you gave: " + _md_cell(cfg.brief.notes))
        L.append("")
        L.append(f"{len(brief_tasks)} task(s) come from your brief.")
        L.append("")
        if gaps:
            L.append("These items from your brief were **not found in the current app**, so they are not in the manual:")
            L.append("")
            L.append("| Item | From | Why |")
            L.append("|---|---|---|")
            for g in gaps:
                L.append(f"| {_md_cell(g.item)} | {_md_cell(g.source) or '-'} | {_md_cell(g.reason) or 'not found in the app'} |")
        else:
            L.append("Everything in your brief was found in the app.")
        L.append("")

    L.append("## Refused destructive actions")
    L.append("")
    if refusals:
        L.append("These were blocked by the engine. The step is documented from code with a screenshot of the state before the click.")
        L.append("")
        for r in refusals:
            L.append(f"- {_md_cell(r['context'])}: `{_md_cell(r['action'])}` - {_md_cell(r['reason'])}")
    else:
        L.append("None.")
    L.append("")

    L.append("## Redactions")
    L.append("")
    if redactions:
        L.append(f"{total_red} region(s) blurred across {len(redactions)} image(s). Values are never recorded.")
        L.append("")
        for img, n in redactions:
            L.append(f"- `{img}`: {n}")
    else:
        L.append("No redactions were needed.")
    L.append("")

    L.append("## Limitations")
    L.append("")
    for s in no_uia:
        L.append(f"- Screen `{s.id}` contains controls without UI Automation support; captured as a whole window and documented from code.")
    for lim in limitations:
        L.append(f"- {lim}")
    L.append(f"- {STANDARD_LIMITATION}")
    L.append("")

    L.append("## How to fix")
    L.append("")
    L.append("Edit `manual.yaml` in the output folder, then run `/guidegen --update`:")
    L.append("")
    L.append("- **Wrong or missing text** - set `override:` on the screen (`text.override`), task, step or troubleshooting entry. Overrides always win and are never touched by GuideGen.")
    L.append("- **Screen you do not want** - set `exclude: true`.")
    L.append("- **Unreachable screen** - add working `navigate:` steps (see references/manual-schema.md) and set `status: pending`.")
    L.append("- **Refused action that is safe** - add the button name to `safety.allowDestructive` in `guidegen.config.json`.")
    L.append("- **Text you edited directly** - add the field name to `locked:` on that item so regeneration keeps it.")
    L.append("- **Budget cuts** - raise `budget.maxScreens` / `budget.maxTasks`.")
    L.append("- **Different structure or terms** - add an old manual, outline or style guide: run `/guidegen --brief <file or URL>`.")
    L.append("")

    issues: list[str] = []
    for s in unreachable[:3]:
        issues.append(f"Screen '{s.title}' unreachable: {s.unreachable_reason or 'no reason'}")
    for t in tasks_partial[:3]:
        issues.append(f"Task '{t.title}' has failed or refused steps")
    if refusals:
        issues.append(f"{len(refusals)} destructive action(s) refused")
    if budget:
        issues.append(f"{len(budget)} screen(s) cut by budget")
    if gaps:
        issues.append(f"{len(gaps)} item(s) from your brief not found in the app")
    summary = {
        "screens": {"captured": len(captured), "unreachable": len(unreachable), "excluded": len(excluded),
                    "budgetCut": len(budget), "pending": len(pending)},
        "tasks": {"complete": len(tasks_ok), "partial": len(tasks_partial), "budgetCut": len(tasks_cut)},
        "redactions": total_red,
        "refused": len(refusals),
        "brief": {"sources": len(cfg.brief.sources), "tasksFromBrief": len(brief_tasks), "gaps": len(gaps)},
        "topIssues": issues[:3],
    }
    return "\n".join(L), summary


def write_report(ctx: Ctx, cfg: Config, manual: Manual) -> dict[str, Any]:
    md, summary = build_report(ctx, cfg, manual)
    path = ctx.out / "run-report.md"
    path.write_text(md, encoding="utf-8", newline="\n")
    outputs = {
        "docx": str(ctx.out / "manual.docx") if (ctx.out / "manual.docx").exists() else None,
        "html": next((str(p) for p in (ctx.out / "manual-html" / "index.html", ctx.out / "manual.html") if p.exists()), None),
        "report": str(path),
    }
    return {"ok": True, "outputs": outputs, **summary}

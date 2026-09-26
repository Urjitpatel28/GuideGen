"""Pure view model shared by the Word and HTML renderers: outputs = f(manual.yaml, screens, brand).
Text precedence everywhere: `override` > generated text."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from guidegen_engine.annotate import DEFAULT_ACCENT
from guidegen_engine.brand import contrast, logo_png, text_safe
from guidegen_engine.config.models import Config
from guidegen_engine.context import Ctx
from guidegen_engine.manual.models import BUILTIN_CHAPTERS, Manual

DEFAULT_PRIMARY = "#1F4E79"
CHAPTER_TITLES = {
    "getting-started": "Getting Started",
    "tasks": "How-To Tasks",
    "reference": "Screen Reference",
    "troubleshooting": "Troubleshooting",
}


@dataclass
class Figure:
    path: Path
    alt: str
    caption: str
    width: int = 0
    height: int = 0


@dataclass
class StepVM:
    n: int
    id: str
    text: str
    figure: Figure | None
    screen_id: str | None
    screen_title: str | None
    status: str
    anchor: str
    screen_anchor: str | None = None


@dataclass
class TaskVM:
    id: str
    title: str
    goal: str | None
    steps: list[StepVM]
    screens_used: list[tuple[str, str]]  # (screen anchor, title)
    anchor: str
    group: str | None = None


@dataclass
class ElementVM:
    name: str
    type: str
    description: str


@dataclass
class ScreenVM:
    id: str
    title: str
    kind: str
    group: str | None
    summary: str | None
    figure: Figure | None
    elements: list[ElementVM]
    used_in: list[tuple[str, str]]  # (task anchor, title)
    anchor: str
    no_uia: bool = False


@dataclass
class ViewModel:
    title: str
    product: str
    company: str | None
    version: str | None
    date: str
    logo: Path | None
    primary: str
    accent: str
    intro: str | None
    chapters: list[tuple[str, str]]
    getting_started: dict[str, Any]
    tasks: list[TaskVM]
    screens: list[ScreenVM]
    troubleshooting: list[dict[str, str]]
    notes: list[str] = field(default_factory=list)
    accent_fg: str = "#FFFFFF"
    audience: str | None = None
    # custom text chapters (id -> markdown body); built-in chapter ids never appear here
    custom: dict[str, str] = field(default_factory=dict)

    def screen_groups(self) -> list[tuple[str | None, list[ScreenVM]]]:
        return _groups(self.screens)

    def task_groups(self) -> list[tuple[str | None, list[TaskVM]]]:
        return _groups(self.tasks)

    @property
    def screens_grouped(self) -> bool:
        return _is_grouped(self.screen_groups())

    @property
    def tasks_grouped(self) -> bool:
        return _is_grouped(self.task_groups())

    def has_chapter(self, cid: str) -> bool:
        """Whether a chapter has anything to show (empty built-in chapters are skipped)."""
        if cid == "getting-started":
            return bool(self.intro or any(self.getting_started.get(k) for k in
                                          ("override", "requirements", "launch", "sign_in", "tour", "tour_figure")))
        if cid == "tasks":
            return bool(self.tasks)
        if cid == "reference":
            return bool(self.screens)
        if cid == "troubleshooting":
            return bool(self.troubleshooting)
        return bool(self.custom.get(cid))


def _groups(items: list) -> list[tuple[str | None, list]]:
    """Group by `.group`, keeping first-appearance order."""
    groups: dict[str | None, list] = {}
    for it in items:
        groups.setdefault(it.group, []).append(it)
    return list(groups.items())


def _is_grouped(groups: list[tuple[str | None, list]]) -> bool:
    return len(groups) > 1 or (bool(groups) and groups[0][0] is not None)


def chapter_anchor(cid: str) -> str:
    """Section id of a chapter. Built-ins keep their historic ids; custom ones get a prefix so they never
    collide with task-/screen- anchors."""
    return cid if cid in BUILTIN_CHAPTERS else anchor("chapter", cid)


def anchor(prefix: str, ident: str) -> str:
    """HTML id / Word bookmark source. Keeps `_` so ids like `a_b` and `a-b` stay distinct."""
    return f"{prefix}-{re.sub(r'[^a-z0-9_-]', '-', ident.lower())}"


_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
_RUNS = re.compile(f"{_BOLD.pattern}|{_ITAL.pattern}")
LIST_ITEM = re.compile(r"^\s*([-*]|\d+\.)\s+")


def md_inline_html(text: str | None) -> str:
    """Tiny markdown subset for manual text: **bold**, *italic*, blank-line paragraphs, '- ' lists."""
    if not text:
        return ""
    out: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.strip().splitlines()
        if all(LIST_ITEM.match(ln) for ln in lines):
            tag = "ol" if re.match(r"^\s*\d+\.", lines[0]) else "ul"
            # no backslashes inside the f-string: that is a SyntaxError before Python 3.12
            items = "".join(f"<li>{_inline(LIST_ITEM.sub('', ln))}</li>" for ln in lines)
            out.append(f"<{tag}>{items}</{tag}>")
        else:
            out.append(f"<p>{_inline(' '.join(ln.strip() for ln in lines))}</p>")
    return "".join(out)


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = _BOLD.sub(r"<strong>\1</strong>", s)
    return _ITAL.sub(r"<em>\1</em>", s)


def md_runs(text: str) -> list[tuple[str, bool, bool]]:
    """Split a line into (text, bold, italic) runs for Word."""
    runs: list[tuple[str, bool, bool]] = []
    pos = 0
    for m in _RUNS.finditer(text):
        if m.start() > pos:
            runs.append((text[pos : m.start()], False, False))
        runs.append((m.group(1) or m.group(2), bool(m.group(1)), bool(m.group(2))))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], False, False))
    return runs


def plain(text: str | None) -> str:
    return re.sub(r"\*\*?(.+?)\*\*?", r"\1", text or "").strip()


def build(ctx: Ctx, cfg: Config, manual: Manual) -> ViewModel:
    notes: list[str] = []
    b = cfg.brand
    primary_raw = b.primary_color or DEFAULT_PRIMARY
    primary, changed = text_safe(primary_raw)
    if changed:
        notes.append(f"Brand primary color {primary_raw} has contrast below 4.5:1 on white; text uses darkened {primary}.")
    accent = b.accent_color or DEFAULT_ACCENT

    logo = None
    try:
        logo = logo_png(ctx.repo, b.logo, ctx.work / "brand" / "logo.png")
    except Exception as e:
        notes.append(f"Logo {b.logo} could not be converted ({type(e).__name__}); rendered without a logo.")

    def fig(img: str | None, alt: str, caption: str) -> Figure | None:
        if not img:
            return None
        p = (ctx.out / img)
        if not p.exists():
            return None
        from PIL import Image

        with Image.open(p) as im:
            w, h = im.size
        return Figure(p, alt, caption, w, h)

    screens_by_id = {s.id: s for s in manual.screens}
    # cross-links only point at chapters that are rendered
    shown = {c.id for c in manual.chapters if not c.exclude}
    link_screens = "reference" in shown
    link_tasks = "tasks" in shown
    visible_screens = [s for s in manual.screens if not s.exclude and s.status == "captured"]
    visible_ids = {s.id for s in visible_screens}

    tasks: list[TaskVM] = []
    for t in sorted(manual.tasks, key=lambda t: t.rank):
        if t.exclude or t.status in ("budget-cut", "excluded", "pending") or not t.steps:
            continue
        steps: list[StepVM] = []
        used: dict[str, str] = {}
        for n, st in enumerate(t.steps, 1):
            text = st.body or (st.action.describe() if st.action else "")
            scr = screens_by_id.get(st.screen) if st.screen else None
            linked = scr is not None and scr.id in visible_ids and link_screens
            if linked:
                used[anchor("screen", scr.id)] = scr.title
            f = fig(st.image, f"{t.title}, step {n}: {plain(text)}", f"Step {n}: {plain(text)}") if st.status != "failed" else None
            steps.append(StepVM(n, st.id, text, f, scr.id if linked else None,
                                scr.title if scr else None, st.status, anchor("step", f"{t.id}-{st.id}"),
                                anchor("screen", scr.id) if linked else None))
        tasks.append(TaskVM(t.id, t.title, t.body, steps, list(used.items()), anchor("task", t.id), t.group))
    if any(t.group for t in tasks):
        # keep each group together, in the order of its best-ranked task
        first = {}
        for i, t in enumerate(tasks):
            first.setdefault(t.group, i)
        tasks.sort(key=lambda t: first[t.group])

    used_in: dict[str, list[tuple[str, str]]] = {}  # screen anchor -> [(task anchor, title)]
    if link_tasks:
        for t in tasks:
            for sa, _ in t.screens_used:
                used_in.setdefault(sa, []).append((t.anchor, t.title))

    screens: list[ScreenVM] = []
    for s in visible_screens:
        els = [ElementVM(e.name, e.type, e.override or e.description or "") for e in s.elements]
        screens.append(ScreenVM(
            s.id, s.title, s.kind, s.group, s.body,
            fig(s.image, f"{s.title} screen", s.title), els, used_in.get(anchor("screen", s.id), []), anchor("screen", s.id), s.no_uia,
        ))

    gs = manual.getting_started
    tour_fig = None
    tour_screen = screens_by_id.get(gs.tour_screen or "") if gs.tour_screen else (visible_screens[0] if visible_screens else None)
    if tour_screen and tour_screen.id in visible_ids:
        tour_fig = fig(tour_screen.image, f"{tour_screen.title} overview", f"The {tour_screen.title} screen")
    getting_started = {
        "override": gs.override,
        "requirements": gs.requirements,
        "launch": gs.launch,
        "sign_in": gs.sign_in,
        "tour": gs.tour,
        "tour_figure": tour_fig,
    }

    trouble = [
        {"message": e.message, "cause": e.cause or "", "fix": e.override or e.fix or e.text or ""}
        for e in manual.troubleshooting if not e.exclude
    ]

    chapters: list[tuple[str, str]] = []
    custom: dict[str, str] = {}
    for c in manual.chapters:
        if c.exclude:
            continue
        if c.builtin:
            chapters.append((c.id, c.title or CHAPTER_TITLES[c.id]))
        else:
            chapters.append((c.id, c.title or c.id.replace("-", " ").replace("_", " ").capitalize()))
            custom[c.id] = c.text or ""

    product = b.product_name or manual.meta.title.replace(" User Manual", "")
    gen = manual.meta.generated_at or datetime.now(UTC)
    return ViewModel(
        title=manual.meta.title if manual.meta.title != "User Manual" else f"{product} User Manual",
        product=product,
        company=b.company_name,
        version=b.version,
        date=gen.strftime("%B %d, %Y").replace(" 0", " "),
        logo=logo,
        primary=primary,
        accent=accent,
        intro=manual.meta.intro,
        chapters=chapters,
        getting_started=getting_started,
        tasks=tasks,
        screens=screens,
        troubleshooting=trouble,
        notes=notes,
        accent_fg="#FFFFFF" if contrast(accent) >= contrast(accent, "#000000") else "#000000",
        audience=manual.meta.audience if manual.meta.audience and manual.meta.audience.strip().lower() != "end users" else None,
        custom=custom,
    )


def write_notes(ctx: Ctx, notes: list[str]) -> None:
    (ctx.work).mkdir(parents=True, exist_ok=True)
    (ctx.work / "render-notes.json").write_text(json.dumps(notes, indent=2), encoding="utf-8")

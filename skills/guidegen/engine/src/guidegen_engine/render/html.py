"""HTML renderer: a static, offline (file://) single-page manual with sidebar, search and zoom."""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from guidegen_engine.paths import templates_dir
from guidegen_engine.render.common import ViewModel, chapter_anchor, md_inline_html, plain


def _search_index(vm: ViewModel) -> list[dict[str, str]]:
    idx = []
    shown = {cid for cid, _ in vm.chapters if vm.has_chapter(cid)}  # never index a section that is not rendered
    gs = vm.getting_started
    if "getting-started" in shown:
        idx.append({"t": "Getting Started", "u": "#getting-started", "s": "Getting Started",
                    "x": plain(" ".join(filter(None, [gs["override"], gs["requirements"], gs["launch"], gs["sign_in"], gs["tour"]])))[:400]})
    for t in vm.tasks if "tasks" in shown else []:
        idx.append({"t": t.title, "u": f"#{t.anchor}", "s": "How-To Tasks",
                    "x": plain(" ".join([t.goal or ""] + [s.text for s in t.steps]))[:600]})
    for s in vm.screens if "reference" in shown else []:
        idx.append({"t": s.title, "u": f"#{s.anchor}", "s": "Screen Reference",
                    "x": plain(" ".join([s.summary or ""] + [f"{e.name} {e.description}" for e in s.elements]))[:600]})
    for i, e in enumerate(vm.troubleshooting if "troubleshooting" in shown else []):
        idx.append({"t": e["message"], "u": f"#trouble-{i + 1}", "s": "Troubleshooting", "x": plain(f"{e['cause']} {e['fix']}")[:300]})
    for cid, ctitle in vm.chapters:
        if vm.custom.get(cid):
            idx.append({"t": ctitle, "u": f"#{chapter_anchor(cid)}", "s": ctitle, "x": plain(vm.custom[cid])[:600]})
    return idx


def render_html(vm: ViewModel, out_dir: Path, single_file: bool = False) -> Path:
    tdir = templates_dir() / "html"
    site = out_dir / "manual-html"
    images = site / "images"
    if site.exists():
        shutil.rmtree(site)  # a single-file render replaces the folder output too
    if not single_file:
        images.mkdir(parents=True)
    published: dict[Path, str] = {}  # the same image (e.g. tour = first screen) is copied/encoded once

    def src(path: Path | None) -> str:
        if path is None:
            return ""
        if path in published:
            return published[path]
        if single_file:
            published[path] = "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
            return published[path]
        try:
            rel = path.relative_to(out_dir)
        except ValueError:
            rel = None
        if rel is None or rel.parts[0] == ".work":
            # internal working files (the converted brand logo) are published as "brand-<name>",
            # never as a hidden ".work-..." file and never clashing with a screen image
            parts: tuple[str, ...] = (f"brand-{path.name}",)
        else:
            # keep the folder structure: flattening would map screens/a-b.png and screens/a/b.png to one name
            parts = rel.parts[1:] if rel.parts[0] == "screens" else rel.parts
        dest = images.joinpath(*parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        published[path] = "images/" + "/".join(parts)
        return published[path]

    env = Environment(loader=FileSystemLoader(str(tdir)), autoescape=select_autoescape(["html", "j2"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["md"] = lambda t: Markup(md_inline_html(t))
    env.filters["plain"] = plain
    env.globals["src"] = src
    env.globals["chapter_anchor"] = chapter_anchor

    css = (tdir / "style.css").read_text(encoding="utf-8")
    js = (tdir / "search.js").read_text(encoding="utf-8")
    html = env.get_template("layout.html.j2").render(
        vm=vm,
        css=Markup(css),
        js=Markup(js),
        index=Markup(json.dumps(_search_index(vm)).replace("</", "<\\/")),
        logo_src=src(vm.logo) if vm.logo else "",
    )
    target = out_dir / "manual.html" if single_file else site / "index.html"
    target.write_text(html, encoding="utf-8")
    return target

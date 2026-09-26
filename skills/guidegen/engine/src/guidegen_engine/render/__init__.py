"""`guidegen render`: build manual.docx and manual-html/ from manual.yaml + screens + brand."""

from __future__ import annotations

from typing import Any

from guidegen_engine.config.models import Config
from guidegen_engine.context import Ctx
from guidegen_engine.manual.models import Manual
from guidegen_engine.render.common import build, write_notes


def render(ctx: Ctx, cfg: Config, manual: Manual, formats: list[str], single_file: bool = False) -> dict[str, Any]:
    vm = build(ctx, cfg, manual)
    outputs: dict[str, str] = {}
    if "docx" in formats:
        from guidegen_engine.render.docx import render_docx

        path = ctx.out / "manual.docx"
        render_docx(vm, path)
        outputs["docx"] = str(path)
    if "html" in formats:
        from guidegen_engine.render.html import render_html

        outputs["html"] = str(render_html(vm, ctx.out, single_file=single_file))
    write_notes(ctx, vm.notes)
    return {
        "ok": True,
        "outputs": outputs,
        "screens": len(vm.screens),
        "tasks": len(vm.tasks),
        "troubleshooting": len(vm.troubleshooting),
        "notes": vm.notes,
    }

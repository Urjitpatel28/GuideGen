"""Cover page: logo, product, version, date, company."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Inches, Pt, RGBColor

from guidegen_engine.render.docx.ox import set_alt_text


def add_cover(doc, vm) -> None:
    for _ in range(4):
        doc.add_paragraph()
    if vm.logo:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        from PIL import Image

        with Image.open(vm.logo) as im:
            w, h = im.size
        # 1.1in tall, unless that makes a wide wordmark wider than the text column
        size = {"height": Inches(1.1)} if not h or 1.1 * w / h <= 6.0 else {"width": Inches(6.0)}
        shape = p.add_run().add_picture(str(vm.logo), **size)
        set_alt_text(shape, f"{vm.product} logo")
    doc.add_paragraph(vm.title, style="Title")
    sub = doc.add_paragraph()
    run = sub.add_run(" · ".join(x for x in (f"Version {vm.version}" if vm.version else None, vm.date) if x))
    run.font.size = Pt(13)
    run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    if getattr(vm, "audience", None):
        a = doc.add_paragraph().add_run(f"For {vm.audience}")
        a.font.size = Pt(12)
        a.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
    if vm.company:
        c = doc.add_paragraph()
        r = c.add_run(vm.company)
        r.font.size = Pt(12)
        r.bold = True
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

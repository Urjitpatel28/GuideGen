"""Header: small logo + product name. Footer: Page X of Y + version. No header/footer on the cover."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from guidegen_engine.render.docx.ox import add_field, set_alt_text


def add_header_footer(doc, vm) -> None:
    section = doc.sections[0]
    section.different_first_page_header_footer = True
    hp = section.header.paragraphs[0]
    if vm.logo:
        shape = hp.add_run().add_picture(str(vm.logo), height=Inches(0.28))
        set_alt_text(shape, f"{vm.product} logo")
        hp.add_run("  ")
    r = hp.add_run(vm.product)
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.add_run("Page ")
    add_field(fp, "PAGE", "1")
    fp.add_run(" of ")
    add_field(fp, "NUMPAGES", "1")
    if vm.version:
        fp.add_run(f"  ·  Version {vm.version}")
    for run in fp.runs:
        run.font.size = Pt(9)

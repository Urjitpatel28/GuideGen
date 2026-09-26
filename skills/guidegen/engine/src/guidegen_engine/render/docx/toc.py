"""Table of contents as a TOC field. Word offers to update fields on first open (documented in README)."""

from __future__ import annotations

from docx.enum.text import WD_BREAK
from docx.shared import Pt, RGBColor

from guidegen_engine.render.docx.ox import add_field, update_fields_on_open


def add_toc(doc, primary: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run("Contents")
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor.from_string(primary.lstrip("#"))
    add_field(doc.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u', "Right-click and choose Update Field to show the table of contents.")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    update_fields_on_open(doc)

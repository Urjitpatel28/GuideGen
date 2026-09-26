"""Tables with a brand-colored, repeating header row."""

from __future__ import annotations

import re

from docx.shared import RGBColor

from guidegen_engine.render.common import LIST_ITEM as _LIST_ITEM
from guidegen_engine.render.common import md_runs
from guidegen_engine.render.docx.ox import repeat_header, shade


def cell_rich(cell, text: str | None) -> None:
    """Cell text with the manual's markdown subset: **bold**, *italic*, paragraphs and simple lists."""
    cell.text = ""
    lines: list[str] = []
    for block in re.split(r"\n\s*\n", (text or "").strip()):
        blk = [ln for ln in block.strip().splitlines() if ln.strip()]
        if blk and all(_LIST_ITEM.match(ln) for ln in blk):
            for ln in blk:
                m = _LIST_ITEM.match(ln)
                marker = m.group(1) + " " if m.group(1)[0].isdigit() else "• "
                lines.append(marker + ln[m.end():])
        elif blk:
            lines.append(" ".join(x.strip() for x in blk))
    for i, line in enumerate(lines or [""]):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        for t, bold, italic in md_runs(line):
            r = p.add_run(t)
            r.bold = bold or None
            r.italic = italic or None


def add_table(doc, headers: list[str], rows: list[list[str]], primary: str):
    t = doc.add_table(rows=1, cols=len(headers))
    try:
        t.style = doc.styles["Table Grid"]
    except KeyError:
        pass
    hdr = t.rows[0]
    repeat_header(hdr)
    for cell, text in zip(hdr.cells, headers, strict=True):
        shade(cell, primary)
        cell.text = ""
        r = cell.paragraphs[0].add_run(text)
        r.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for row in rows:
        cells = t.add_row().cells
        for cell, text in zip(cells, row, strict=True):
            cell_rich(cell, text)
    doc.add_paragraph()
    return t

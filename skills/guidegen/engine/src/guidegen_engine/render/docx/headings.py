"""Brand-colored built-in styles (built-in heading styles keep the navigation pane and TOC working)."""

from __future__ import annotations

from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BODY_FONT = "Calibri"
HEADING_FONT = "Segoe UI"


def _font(style, name: str, size: float | None = None, color: str | None = None, bold: bool | None = None) -> None:
    f = style.font
    f.name = name
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is not None:
        for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rfonts.set(qn(attr), name)
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            rfonts.attrib.pop(qn(attr), None)
    if size:
        f.size = Pt(size)
    if color:
        f.color.rgb = RGBColor.from_string(color.lstrip("#").upper())
    if bold is not None:
        f.bold = bold


def apply_styles(doc, primary: str) -> None:
    styles = doc.styles
    _font(styles["Normal"], BODY_FONT, 11)
    styles["Normal"].paragraph_format.space_after = Pt(6)
    for level, size in ((1, 20), (2, 15), (3, 12.5)):
        st = styles[f"Heading {level}"]
        _font(st, HEADING_FONT, size, primary, True)
        st.paragraph_format.space_before = Pt(18 if level == 1 else 12)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.keep_with_next = True
    _font(styles["Title"], HEADING_FONT, 30, primary, True)
    try:
        _font(styles["Caption"], BODY_FONT, 9, "595959", False)
        styles["Caption"].font.italic = True
    except KeyError:
        pass


def heading(doc, text: str, level: int):
    return doc.add_heading(text, level=level)

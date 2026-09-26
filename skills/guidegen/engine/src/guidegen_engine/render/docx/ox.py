"""Low-level OOXML helpers: fields, bookmarks, internal hyperlinks, shading, alt text."""

from __future__ import annotations

import hashlib
import itertools

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

_bookmark_ids = itertools.count(1)


def add_field(paragraph, instr: str, placeholder: str = "") -> None:
    """Complex field (w:fldChar begin/separate/end) so Word can update it (TOC, PAGE, NUMPAGES)."""
    def fld(kind: str):
        r = OxmlElement("w:r")
        f = OxmlElement("w:fldChar")
        f.set(qn("w:fldCharType"), kind)
        if kind == "begin":
            f.set(qn("w:dirty"), "true")
        r.append(f)
        return r

    p = paragraph._p
    p.append(fld("begin"))
    r = OxmlElement("w:r")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    r.append(it)
    p.append(r)
    p.append(fld("separate"))
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = placeholder
    r.append(t)
    p.append(r)
    p.append(fld("end"))


def add_bookmark(paragraph, name: str) -> None:
    bid = str(next(_bookmark_ids))
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), bid)
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), bid)
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def bookmark_name(anchor: str) -> str:
    """Word bookmark names: letters/digits/underscore, max 40 chars. Anchors that would collide after
    mapping `-` to `_` (they contain `_`) or after truncation get a short hash suffix, so names stay unique."""
    name = "b_" + anchor.replace("-", "_")
    if "_" in anchor or len(name) > 40:
        name = name[:31] + "_" + hashlib.sha1(anchor.encode("utf-8")).hexdigest()[:8]
    return name


def add_internal_link(paragraph, text: str, anchor: str, color: str) -> None:
    link = OxmlElement("w:hyperlink")
    link.set(qn("w:anchor"), bookmark_name(anchor))
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    c = OxmlElement("w:color")
    c.set(qn("w:val"), color.lstrip("#"))
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rpr.append(c)
    rpr.append(u)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    link.append(r)
    paragraph._p.append(link)


def shade(cell, hex_color: str) -> None:
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    tcpr.append(shd)


def repeat_header(row) -> None:
    trpr = row._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader")
    h.set(qn("w:val"), "true")
    trpr.append(h)


def set_alt_text(inline_shape, alt: str, title: str = "") -> None:
    docpr = inline_shape._inline.docPr
    docpr.set("descr", alt[:1000])
    if title:
        docpr.set("title", title[:200])


def update_fields_on_open(document) -> None:
    settings = document.settings.element
    el = OxmlElement("w:updateFields")
    el.set(qn("w:val"), "true")
    settings.append(el)


def restart_numbering(doc, style_name: str) -> int | None:
    """New numbering instance for a list style that starts again at 1. None if the style has no numbering."""
    try:
        numpr = doc.styles[style_name].element.pPr.numPr
        numbering = doc.part.numbering_part.element
        style_num = numpr.numId.val
        abstract_id = next(n.abstractNumId.val for n in numbering.num_lst if n.numId == style_num)
        num = numbering.add_num(abstract_id)
        num.add_lvlOverride(ilvl=0).add_startOverride(1)
        return num.numId
    except Exception:
        return None


def set_num(paragraph, num_id: int, ilvl: int = 0) -> None:
    numpr = paragraph._p.get_or_add_pPr().get_or_add_numPr()
    numpr.get_or_add_numId().val = num_id
    numpr.get_or_add_ilvl().val = ilvl

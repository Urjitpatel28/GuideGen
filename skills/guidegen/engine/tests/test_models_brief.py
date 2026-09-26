"""Manual model validation and brief extraction edge cases (review findings)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pydantic import ValidationError

from guidegen_engine.brief import _slug, extract
from guidegen_engine.manual.models import Manual
from guidegen_engine.paths import skill_dir


def _docx_with_link(path):
    doc = Document()
    p = doc.add_paragraph()
    rid = doc.part.relate_to("https://example.test/help", RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "Open the help center"
    r.append(t)
    link.append(r)
    p._p.append(link)
    doc.save(str(path))
    return path


def test_docx_hyperlink_text_is_kept(ctx):
    src = _docx_with_link(ctx.repo / "old.docx")
    res = extract(ctx, str(src))
    text = Path(res["file"]).read_text(encoding="utf-8")
    assert "Open the help center" in text


def test_html_without_closing_head_keeps_body(ctx):
    src = ctx.repo / "page.html"
    src.write_text("<html><head><title>Old</title><body><h1>Orders</h1><p>Create an order.</p></body></html>", encoding="utf-8")
    res = extract(ctx, str(src))
    text = Path(res["file"]).read_text(encoding="utf-8")
    assert "Create an order." in text and "Orders" in text


def test_brief_names_do_not_collide():
    assert _slug("docs/manual.pdf") != _slug("docs/manual.docx")
    long_a = "https://docs.example.test/" + "a" * 80 + "/one"
    long_b = "https://docs.example.test/" + "a" * 80 + "/two"
    assert _slug(long_a) != _slug(long_b) and len(_slug(long_a)) <= 60


def test_step_ids_validated_and_duplicates_found():
    with pytest.raises(ValidationError):
        Manual.model_validate({"tasks": [{"id": "t", "title": "T", "steps": [{"id": "Bad Id"}]}]})
    m = Manual.model_validate({
        "tasks": [{"id": "t", "title": "T", "steps": [{"id": "s1"}, {"id": "s1"}]}],
        "troubleshooting": [{"message": "Oops"}, {"message": "Oops"}],
    })
    dup = m.duplicate_ids()
    assert "step t/s1" in dup and "troubleshooting 'Oops'" in dup


def test_schema_publishes_id_pattern():
    schema = json.loads((skill_dir() / "schema" / "manual.schema.json").read_text(encoding="utf-8"))
    for name in ("Screen", "Task", "Step", "Chapter"):
        assert schema["$defs"][name]["properties"]["id"]["pattern"] == "^[a-z0-9_-]+$", name

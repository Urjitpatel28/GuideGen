"""Images (max 6in wide, 8in tall, alt text) with a caption below."""

from __future__ import annotations

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches
from PIL import Image

from guidegen_engine.render.docx.ox import set_alt_text

MAX_WIDTH_IN = 6.0
MAX_HEIGHT_IN = 8.0  # letter/A4 body minus margins and the caption


def fit_inches(w_px: int, h_px: int, max_w: float = MAX_WIDTH_IN, max_h: float = MAX_HEIGHT_IN) -> float:
    """Display width in inches: 96 dpi, shrunk to fit both the max width and the max height."""
    width = min(max_w, w_px / 96)
    if w_px and h_px and width * h_px / w_px > max_h:
        width = max_h * w_px / h_px
    return width


class FigureCounter:
    def __init__(self) -> None:
        self.n = 0


def add_figure(doc, figure, counter: FigureCounter) -> None:
    w_px, h_px = figure.width, figure.height
    if not (w_px and h_px):
        with Image.open(figure.path) as im:
            w_px, h_px = im.size
    width = fit_inches(w_px, h_px)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    shape = p.add_run().add_picture(str(figure.path), width=Inches(width))
    set_alt_text(shape, figure.alt, figure.caption)
    counter.n += 1
    try:
        cap = doc.add_paragraph(f"Figure {counter.n}: {figure.caption}", style="Caption")
    except KeyError:
        cap = doc.add_paragraph(f"Figure {counter.n}: {figure.caption}")
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

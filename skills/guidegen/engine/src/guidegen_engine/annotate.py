"""Image post-processing: redaction blur (always first), highlight rectangle, step badge, crop, DPI normalisation."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from guidegen_engine.drivers.base import Rect

DEFAULT_ACCENT = "#E4572E"


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def redact(img: Image.Image, rects: list[Rect]) -> tuple[Image.Image, int]:
    """Pixelate then blur each rect. Irreversible for text. Returns (image, count)."""
    img = img.convert("RGB")
    n = 0
    for r in rects:
        if not r.valid():
            continue
        box = _clamp(r.as_box(pad=2), img.size)
        if box[2] - box[0] < 2 or box[3] - box[1] < 2:
            continue
        region = img.crop(box)
        w, h = region.size
        small = region.resize((max(1, w // 10), max(1, h // 10)), Image.Resampling.BILINEAR)
        region = small.resize((w, h), Image.Resampling.NEAREST).filter(ImageFilter.GaussianBlur(radius=6))
        img.paste(region, box)
        n += 1
    return img, n


def highlight(img: Image.Image, rect: Rect, color: str = DEFAULT_ACCENT, width: int = 3) -> Image.Image:
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    box = _clamp(rect.as_box(pad=4), img.size)
    d.rounded_rectangle(box, radius=6, outline=hex_to_rgb(color), width=width)
    return img


def badge(img: Image.Image, number: int, rect: Rect | None, color: str = DEFAULT_ACCENT) -> Image.Image:
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    r = 14
    if rect is not None:
        cx, cy = rect.x - 4, rect.y - 4
    else:
        cx, cy = r + 8, r + 8
    cx = min(max(cx, r + 2), img.width - r - 2)
    cy = min(max(cy, r + 2), img.height - r - 2)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hex_to_rgb(color), outline="white", width=2)
    font = _font(16)
    text = str(number)
    tb = d.textbbox((0, 0), text, font=font)
    d.text((cx - (tb[2] - tb[0]) / 2 - tb[0], cy - (tb[3] - tb[1]) / 2 - tb[1]), text, fill="white", font=font)
    return img


def crop_around(img: Image.Image, rect: Rect, margin: int = 160) -> Image.Image:
    box = _clamp(rect.as_box(pad=margin), img.size)
    return img.crop(box)


def normalize(img: Image.Image, width: int | None = None, height: int | None = None) -> Image.Image:
    """Scale a HiDPI capture back to the logical (100%) size."""
    if width and height and img.size != (width, height):
        return img.resize((width, height), Image.Resampling.LANCZOS)
    return img


def _clamp(box: tuple[int, int, int, int], size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = box
    return max(0, x0), max(0, y0), min(size[0], x1), min(size[1], y1)


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()

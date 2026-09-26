from __future__ import annotations

from PIL import Image

from guidegen_engine import annotate
from guidegen_engine.brand import contrast, detect_brand, logo_png, text_safe
from guidegen_engine.drivers.base import Rect
from guidegen_engine.drivers.desktop import to_send_keys

from conftest import FIXTURES


def test_contrast_fix():
    assert contrast("#000000") > 20
    c, changed = text_safe("#1F4E79")
    assert not changed and c == "#1F4E79"
    c, changed = text_safe("#F29F05")
    assert changed and contrast(c) >= 4.5


def test_brand_detect_names(tmp_path):
    res = detect_brand(FIXTURES / "aspnet-razor")
    assert res["brand"]["productName"] == "Razor Desk"
    assert res["brand"]["companyName"] == "Fixture Co"
    repo = tmp_path
    (repo / "public").mkdir()
    (repo / "public" / "logo.png").write_bytes(b"")
    (repo / "public" / "favicon.ico").write_bytes(b"")
    (repo / "package.json").write_text('{"name": "acme-quote", "version": "2.3.0", "author": "Acme Ltd <hi@acme.test>"}')
    (repo / "app.css").write_text(":root { --color-primary: #1f4e79; --accent: #F29F05; --bg: #fff }")
    (repo / "App.xaml").write_text('<SolidColorBrush x:Key="BrandBrush" Color="#123456"/>')
    b = detect_brand(repo)["brand"]
    assert b["logo"] == "public/logo.png"
    assert b["productName"] == "Acme Quote" and b["companyName"] == "Acme Ltd" and b["version"] == "2.3.0"
    assert b["primaryColor"] in ("#1F4E79", "#123456") and b["accentColor"] == "#F29F05"


def test_logo_png_conversion(tmp_path):
    img = Image.new("RGBA", (32, 32), (200, 0, 0, 255))
    img.save(tmp_path / "icon.ico")
    out = logo_png(tmp_path, "icon.ico", tmp_path / "out" / "logo.png")
    assert out and Image.open(out).size[0] >= 16


def test_annotations():
    img = Image.new("RGB", (300, 200), "white")
    r = Rect(50, 50, 80, 30)
    out = annotate.badge(annotate.highlight(img, r), 3, r)
    assert out.getpixel((46, 50)) != (255, 255, 255)
    red, n = annotate.redact(Image.new("RGB", (100, 100), "white"), [Rect(10, 10, 20, 20), Rect(0, 0, 0, 0)])
    assert n == 1
    assert annotate.crop_around(img, r, 20).size == (120, 70)


def test_send_keys_mapping():
    assert to_send_keys("Enter") == "{ENTER}"
    assert to_send_keys("Control+S") == "^s"
    assert to_send_keys("Alt+F4") == "%{F4}"

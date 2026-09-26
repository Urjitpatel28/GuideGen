"""`guidegen brand detect`: logo, product/company names, version and colors from the repo.
Also logo conversion (SVG via headless Chromium, ICO via Pillow) and WCAG contrast fixing."""

from __future__ import annotations

import base64
import hashlib
import colorsys
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image

from guidegen_engine.paths import contained, iter_repo_files, rel

LOGO_NAMES = re.compile(r"^(logo|brand|app[-_]?icon|icon|favicon)([-_.@\w]*)\.(svg|png|ico|jpg|jpeg|webp)$", re.I)
PRIMARY_KEYS = re.compile(r"(^|[-_.])(primary|brand|main|theme)([-_.]?(color|colour|500|600|default|base))?$", re.I)
ACCENT_KEYS = re.compile(r"(^|[-_.])(accent|secondary|highlight)([-_.]?(color|colour|500|default|base))?$", re.I)
HEX = r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b"


def _logo_score(p: Path) -> int:
    n = p.name.lower()
    score = 0
    score += 50 if n.startswith("logo") else 30 if n.startswith(("brand", "app-icon", "appicon", "app_icon")) else 10
    score += {".svg": 20, ".png": 15, ".ico": 5}.get(p.suffix.lower(), 0)
    if "favicon" in n:
        score -= 10
    if any(part.lower() in ("public", "assets", "images", "img", "resources", "static", "wwwroot") for part in p.parts):
        score += 5
    return score


def find_logo(repo: Path) -> tuple[str | None, list[str]]:
    evidence: list[str] = []
    cands = [p for p in iter_repo_files(repo) if LOGO_NAMES.match(p.name)]
    for proj in iter_repo_files(repo, ("*.csproj",)):
        m = re.search(r"<ApplicationIcon>([^<]+)</ApplicationIcon>", proj.read_text(encoding="utf-8", errors="ignore"))
        if m:
            p = (proj.parent / m.group(1).replace("\\", "/")).resolve()
            if p.exists():
                cands.append(p)
                evidence.append(f"{rel(proj, repo)} ApplicationIcon")
    if not cands:
        return None, evidence
    best = max(cands, key=_logo_score)
    evidence.append(f"logo: {rel(best, repo)}")
    return rel(best, repo), evidence


def find_names(repo: Path) -> tuple[dict[str, str], list[str]]:
    out: dict[str, str] = {}
    ev: list[str] = []
    for proj in sorted(iter_repo_files(repo, ("*.csproj",)), key=lambda p: len(p.parts)):
        t = proj.read_text(encoding="utf-8", errors="ignore")
        for tag, key in (("Product", "productName"), ("Company", "companyName"), ("Version", "version"), ("AssemblyTitle", "productName")):
            m = re.search(fr"<{tag}>([^<]+)</{tag}>", t)
            if m and key not in out:
                out[key] = m.group(1).strip()
                ev.append(f"{rel(proj, repo)} <{tag}>")
    for info in iter_repo_files(repo, ("AssemblyInfo.cs",)):
        t = info.read_text(encoding="utf-8", errors="ignore")
        for attr, key in (("AssemblyProduct", "productName"), ("AssemblyCompany", "companyName"), ("AssemblyInformationalVersion", "version")):
            m = re.search(fr'{attr}\("([^"]+)"\)', t)
            if m and key not in out:
                out[key] = m.group(1)
                ev.append(f"{rel(info, repo)} {attr}")
    pkgs = sorted(iter_repo_files(repo, ("package.json",)), key=lambda p: len(p.parts))
    for pkg in pkgs[:1]:
        try:
            d = json.loads(pkg.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = d.get("productName") or (d.get("build") or {}).get("productName") or d.get("displayName") or d.get("name")
        if name and "productName" not in out:
            out["productName"] = name if " " in name or name[:1].isupper() else name.replace("-", " ").replace("_", " ").title()
            ev.append(f"{rel(pkg, repo)} name")
        author = d.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        if author and "companyName" not in out:
            out["companyName"] = re.sub(r"\s*<.*?>|\s*\(.*?\)", "", author).strip()
            ev.append(f"{rel(pkg, repo)} author")
        if d.get("version") and "version" not in out:
            out["version"] = d["version"]
    # <title> in an html entry or layout
    if "productName" not in out:
        for f in iter_repo_files(repo, ("index.html", "layout.tsx", "_Layout.cshtml", "App.razor", "MainWindow.xaml")):
            m = re.search(r"<title>([^<{]+)</title>|Title=\"([^\"{]+)\"", f.read_text(encoding="utf-8", errors="ignore"))
            if m:
                out["productName"] = (m.group(1) or m.group(2)).strip()
                ev.append(f"{rel(f, repo)} title")
                break
    return out, ev


def _norm_hex(h: str) -> str:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.upper()


def find_colors(repo: Path) -> tuple[dict[str, str], list[str]]:
    out: dict[str, str] = {}
    ev: list[str] = []
    files = list(iter_repo_files(repo, ("*.css", "*.scss", "tailwind.config.*", "App.xaml", "*.xaml", "theme.*", "globals.css", "*.cs")))
    files.sort(key=lambda p: (0 if "tailwind" in p.name or p.name in ("globals.css", "App.xaml") else 1, len(p.parts)))
    for f in files[:80]:
        text = f.read_text(encoding="utf-8", errors="ignore")
        pairs: list[tuple[str, str]] = []
        pairs += re.findall(r"--([\w-]+)\s*:\s*(" + HEX + ")", text)  # CSS custom properties
        pairs += re.findall(r"\$([\w-]+)\s*:\s*(" + HEX + ")", text)  # SCSS variables
        pairs += re.findall(r"['\"]?([\w-]+)['\"]?\s*:\s*['\"](" + HEX + ")['\"]", text)  # tailwind/js theme objects
        pairs += re.findall(r"x:Key=\"([\w.]+)\"[^>]*Color=\"(" + HEX + ")\"", text)  # WPF SolidColorBrush
        pairs += re.findall(r"(\w+)\s*=\s*ColorTranslator\.FromHtml\(\"(" + HEX + r")\"\)", text)  # WinForms
        pairs += re.findall(r"x:Key=\"([\w.]+)\"[^>]*>\s*(" + HEX + r")\s*<", text)  # <Color x:Key>#..</Color>
        for key, val in pairs:
            # BrandPrimaryBrush -> brand-primary ; --color-primary stays as is
            key = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", key).lower()
            key = re.sub(r"[-_.]?(brush|colou?r|resource)$", "", key)
            if "primaryColor" not in out and PRIMARY_KEYS.search(key):
                out["primaryColor"] = _norm_hex(val)
                ev.append(f"{rel(f, repo)} {key}")
            elif "accentColor" not in out and ACCENT_KEYS.search(key):
                out["accentColor"] = _norm_hex(val)
                ev.append(f"{rel(f, repo)} {key}")
        if len(out) == 2:
            break
    return out, ev


def detect_brand(repo: Path) -> dict[str, Any]:
    brand: dict[str, Any] = {}
    evidence: list[str] = []
    logo, ev = find_logo(repo)
    evidence += ev
    if logo:
        brand["logo"] = logo
    names, ev = find_names(repo)
    brand.update(names)
    evidence += ev
    colors, ev = find_colors(repo)
    brand.update(colors)
    evidence += ev
    return {"ok": True, "brand": brand, "evidence": evidence}


# ---------- logo conversion ----------
def logo_png(repo: Path, logo: str | None, dest: Path) -> Path | None:
    """Convert the configured logo to PNG at dest. SVG is rendered with headless Chromium (no Cairo)."""
    if not logo:
        return None
    src = contained(logo, repo, "brand.logo")
    if not src.exists():
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Reuse the last conversion when the source logo is unchanged (an SVG costs a Chromium launch per render).
    stamp = dest.with_name(dest.name + ".source")
    digest = f"{src}|{hashlib.sha256(src.read_bytes()).hexdigest()}"
    if dest.exists() and stamp.exists() and stamp.read_text(encoding="utf-8") == digest:
        return dest
    stamp.unlink(missing_ok=True)
    _convert_logo(src, dest)
    stamp.write_text(digest, encoding="utf-8")
    return dest


def _convert_logo(src: Path, dest: Path) -> None:
    suffix = src.suffix.lower()
    if suffix == ".svg":
        from playwright.sync_api import sync_playwright

        data = base64.b64encode(src.read_bytes()).decode()
        html = (
            "<html><body style='margin:0;background:transparent'>"
            f"<img id='l' src='data:image/svg+xml;base64,{data}' style='height:256px;width:auto;display:block'>"
            "</body></html>"
        )
        from guidegen_engine.drivers.web import launch_chromium

        with sync_playwright() as p:
            b = launch_chromium(p)
            page = b.new_page(device_scale_factor=2)
            page.set_content(html)
            page.wait_for_function("document.getElementById('l').complete")
            page.locator("#l").screenshot(path=str(dest), omit_background=True)
            b.close()
        return
    with Image.open(src) as img:  # closed promptly: an open handle locks the file on Windows
        frame = img
        if suffix == ".ico":
            try:
                frame = img.ico.getimage(max(img.ico.sizes()))  # largest frame
            except Exception:
                pass
        frame.convert("RGBA").save(dest, "PNG")


# ---------- contrast ----------
def _lum(hexc: str) -> float:
    r, g, b = (int(hexc[i : i + 2], 16) / 255 for i in (1, 3, 5))

    def ch(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str = "#FFFFFF") -> float:
    la, lb = _lum(_norm_hex(a)), _lum(_norm_hex(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def text_safe(color: str, minimum: float = 4.5) -> tuple[str, bool]:
    """Darken color until it reaches `minimum` contrast on white. Returns (color, changed)."""
    color = _norm_hex(color)
    if contrast(color) >= minimum:
        return color, False
    r, g, b = (int(color[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    while l > 0 and contrast(color) < minimum:
        l = max(0.0, l - 0.02)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        color = f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"
    return color, True

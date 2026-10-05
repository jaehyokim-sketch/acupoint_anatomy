# -*- coding: utf-8 -*-
"""
render_diagrams.py — Render report diagrams to PNG (used by build_report_html.py)
1) Fixed-grid PNG rendering for Unicode box-drawing diagrams & ASCII art.
2) High-res Mermaid PNG rendering via local Playwright/Chromium engine.
"""
import base64
import hashlib
import io
import os
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    from fontTools.ttLib import TTFont, TTCollection
except Exception:
    TTFont = TTCollection = None

FONT_DIRS = [
    Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
    Path("/usr/share/fonts"),
    Path("/System/Library/Fonts"),
    Path("/Library/Fonts"),
]
FONT_CHAIN = [
    "consola.ttf", "malgun.ttf", "NanumGothic.ttf", "NotoSansKR-VF.ttf", "msyh.ttc", "simsun.ttc",
    "HANBatang.ttf", "HANBatangExt.ttf", "HANBatangExtB.ttf", "SimsunExtG.ttf", "seguisym.ttf", "segoeui.ttf",
    "arialuni.ttf", "NotoSansCJK-Regular.ttc", "AppleSDGothicNeo.ttc"
]
SCALE = 2
FONT_PX = 15
PAD = 14
BG = (255, 255, 255)
FG = (29, 36, 51)
LINE = (55, 65, 85)

BOX_RE = re.compile(r"[\u2500-\u257F]")
ARROW_RE = re.compile(r"[←↑→↓↔↕⇒⇐⇑⇓➔➜➝➞▶◀▲▼►◄]")


def is_text_diagram(lang: str, code: str) -> bool:
    if (lang or "").lower() not in ("", "text", "txt", "plain", "plaintext", "diagram", "ascii"):
        return False
    if (lang or "").lower() in ("diagram", "ascii"):
        return True
    lines = code.splitlines()
    box_lines = sum(1 for l in lines if BOX_RE.search(l))
    arrow_lines = sum(1 for l in lines if ARROW_RE.search(l))
    return box_lines >= 1 or (box_lines >= 1 and arrow_lines >= 1) or arrow_lines >= 2


def _find_font(name):
    for d in FONT_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


@lru_cache(maxsize=None)
def _font_table():
    out = []
    for name in FONT_CHAIN:
        p = _find_font(name)
        if not p:
            continue
        try:
            if TTFont is None:
                out.append((str(p), 0, None))
                continue
            if p.suffix.lower() == ".ttc":
                col = TTCollection(str(p), lazy=True)
                for i, f in enumerate(col.fonts[:1]):
                    out.append((str(p), i, set(f.getBestCmap().keys())))
            else:
                f = TTFont(str(p), lazy=True)
                out.append((str(p), 0, set(f.getBestCmap().keys())))
        except Exception:
            continue
    return out


@lru_cache(maxsize=None)
def _pil_font(path, index, size):
    return ImageFont.truetype(path, size=size, index=index)


@lru_cache(maxsize=4096)
def _font_for(ch, size):
    cp = ord(ch)
    for path, idx, cmap in _font_table():
        if cmap is None or cp in cmap:
            return _pil_font(path, idx, size)
    t = _font_table()
    return _pil_font(t[0][0], t[0][1], size) if t else ImageFont.load_default()


def _width(ch):
    if ch == "\t":
        return 4
    if unicodedata.combining(ch):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def _box_spec():
    S = {}
    def add(chars, u, d, l, r):
        for c in chars:
            S[c] = (u, d, l, r)
    add("─", 0, 0, 1, 1); add("━", 0, 0, 2, 2); add("═", 0, 0, 3, 3)
    add("│", 1, 1, 0, 0); add("┃", 2, 2, 0, 0); add("║", 3, 3, 0, 0)
    add("┌╭", 0, 1, 0, 1); add("┐╮", 0, 1, 1, 0); add("└╰", 1, 0, 0, 1); add("┘╯", 1, 0, 1, 0)
    add("┏", 0, 2, 0, 2); add("┓", 0, 2, 2, 0); add("┗", 2, 0, 0, 2); add("┛", 2, 0, 2, 0)
    add("╔", 0, 3, 0, 3); add("╗", 0, 3, 3, 0); add("╚", 3, 0, 0, 3); add("╝", 3, 0, 3, 0)
    add("├", 1, 1, 0, 1); add("┤", 1, 1, 1, 0); add("┬", 0, 1, 1, 1); add("┴", 1, 0, 1, 1); add("┼", 1, 1, 1, 1)
    add("┣", 2, 2, 0, 2); add("┫", 2, 2, 2, 0); add("┳", 0, 2, 2, 2); add("┻", 2, 0, 2, 2); add("╋", 2, 2, 2, 2)
    add("╠", 3, 3, 0, 3); add("╣", 3, 3, 3, 0); add("╦", 0, 3, 3, 3); add("╩", 3, 0, 3, 3); add("╬", 3, 3, 3, 3)
    add("╞", 1, 1, 0, 3); add("╡", 1, 1, 3, 0); add("╪", 1, 1, 3, 3); add("╟", 3, 3, 0, 1); add("╢", 3, 3, 1, 0); add("╫", 3, 3, 1, 1)
    add("╤", 0, 1, 3, 3); add("╧", 1, 0, 3, 3); add("╥", 0, 3, 1, 1); add("╨", 3, 0, 1, 1)
    add("╒", 0, 1, 0, 3); add("╕", 0, 1, 3, 0); add("╘", 1, 0, 0, 3); add("╛", 1, 0, 3, 0)
    add("╓", 0, 3, 0, 1); add("╖", 0, 3, 1, 0); add("╙", 3, 0, 0, 1); add("╜", 3, 0, 1, 0)
    add("╌┄┈", 0, 0, 1, 1); add("╎┆┊", 1, 1, 0, 0)
    add("╴", 0, 0, 1, 0); add("╶", 0, 0, 0, 1); add("╵", 1, 0, 0, 0); add("╷", 0, 1, 0, 0)
    return S


BOX = _box_spec()


def _draw_box(dr, ch, x0, y0, cw, lh):
    u, d, l, r = BOX[ch]
    cx, cy = x0 + cw / 2, y0 + lh / 2
    thin = max(1, round(1.1 * SCALE)); thick = max(2, round(2.4 * SCALE)); gap = max(2, round(1.6 * SCALE))
    def seg(a, b, weight, vertical):
        if not weight:
            return
        if weight == 3:
            for off in (-gap, gap):
                if vertical:
                    dr.line([(cx + off, a), (cx + off, b)], fill=LINE, width=thin)
                else:
                    dr.line([(a, cy + off), (b, cy + off)], fill=LINE, width=thin)
        else:
            w = thick if weight == 2 else thin
            if vertical:
                dr.line([(cx, a), (cx, b)], fill=LINE, width=w)
            else:
                dr.line([(a, cy), (b, cy)], fill=LINE, width=w)
    ext = thick / 2
    seg(y0, cy + (ext if u else 0), u, True)
    seg(cy - (ext if d else 0), y0 + lh, d, True)
    seg(x0, cx + (ext if l else 0), l, False)
    seg(cx - (ext if r else 0), x0 + cw, r, False)
    if ch in "╌┄┈╎┆┊":
        n = 3 if ch in "┄┆" else 4 if ch in "┈┊" else 2
        if ch in "╌┄┈":
            step = cw / n
            for k in range(n):
                dr.line([(x0 + k * step + step * 0.6, cy), (x0 + (k + 1) * step, cy)], fill=BG, width=thick)
        else:
            step = lh / n
            for k in range(n):
                dr.line([(cx, y0 + k * step + step * 0.6), (cx, y0 + (k + 1) * step)], fill=BG, width=thick)


def render_text_diagram(code: str) -> bytes:
    lines = code.expandtabs(4).rstrip("\n").split("\n")
    size = FONT_PX * SCALE
    base = _font_for("M", size)
    cw = max(1, round(base.getlength("M")))
    lh = round(size * 1.45)
    cols = max((sum(_width(c) for c in l) for l in lines), default=1)
    W, H = cols * cw + 2 * PAD * SCALE, len(lines) * lh + 2 * PAD * SCALE
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    for row, line in enumerate(lines):
        col = 0
        y0 = PAD * SCALE + row * lh
        for ch in line:
            w = _width(ch)
            x0 = PAD * SCALE + col * cw
            if ch in BOX:
                _draw_box(dr, ch, x0, y0, cw, lh)
            elif ch.strip():
                f = _font_for(ch, size)
                gw = f.getlength(ch)
                box_w = cw * max(w, 1)
                if gw > box_w * 1.02:
                    f = _font_for(ch, max(8, int(size * box_w / gw)))
                    gw = f.getlength(ch)
                asc, desc = f.getmetrics()
                dr.text((x0 + (box_w - gw) / 2, y0 + (lh - (asc + desc)) / 2), ch, font=f, fill=FG)
            col += w
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


MERMAID_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>body{margin:0;background:#fff;font-family:'Malgun Gothic','Noto Sans KR',sans-serif}#out{display:inline-block;padding:12px}</style>
</head><body><div id="out"></div>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
mermaid.initialize({startOnLoad:false, theme:"default", securityLevel:"loose", flowchart:{htmlLabels:true}, fontFamily:"Malgun Gothic, Noto Sans KR, sans-serif"});
window.renderOne = async (id, code) => { const {svg} = await mermaid.render(id, code); document.getElementById("out").innerHTML = svg; return true; };
window.ready = true;
</script></body></html>"""


def render_mermaid_batch(codes):
    out = [None] * len(codes)
    if not codes:
        return out
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return out
    try:
        with sync_playwright() as pw:
            browser = None
            launch_args = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
            for ch in ("chrome", "msedge", None):
                try:
                    browser = pw.chromium.launch(channel=ch, args=launch_args) if ch else pw.chromium.launch(args=launch_args)
                    break
                except Exception:
                    continue

            if browser is None:
                return out
            page = browser.new_page(device_scale_factor=SCALE, viewport={"width": 1400, "height": 900})
            page.set_content(MERMAID_PAGE, wait_until="networkidle")
            page.wait_for_function("window.ready === true", timeout=20000)
            for i, code in enumerate(codes):
                try:
                    page.evaluate("([id, c]) => window.renderOne(id, c)", [f"m{i}", code])
                    out[i] = page.locator("#out").screenshot(type="png")
                except Exception:
                    out[i] = None
            browser.close()
    except Exception:
        pass
    return out


def data_uri(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")


def digest(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]

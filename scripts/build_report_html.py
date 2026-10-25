# -*- coding: utf-8 -*-
"""
build_report_html.py — [경혈해부] 보고서 .md → .html 변환 (Claude Code · Antigravity 공용)

- 수식($...$, $$...$$)은 보존 후 KaTeX auto-render로 렌더링, ```mermaid 블록은 Mermaid로 렌더링
- 표·코드·목차 지원(python-markdown), 라이트/다크 테마 자동 대응
- 기존 .html이 있으면 같은 폴더의 `_구판_html/` 에 날짜 붙여 보관한 뒤 새로 쓴다(--no-archive로 끔)
- 도식은 이미지로 삽입(render_diagrams.py): 상자 그림·화살표가 든 코드 블록은 고정 격자 PNG,
  Mermaid는 로컬 Chrome/Edge(Playwright)로 렌더링한 PNG. 이미지는 data URI로 내장해 html 한 파일로 열린다.
  렌더링에 실패하면 기존 방식(코드 블록 / 브라우저 Mermaid)으로 대체한다. --no-images로 끔.

사용: python build_report_html.py <report.md> [<report2.md> ...] [--no-archive] [--no-images]
"""
import html
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import render_diagrams  # 도식 → PNG (상자 그림, Mermaid)
except Exception:  # Pillow·fontTools·Playwright가 없으면 기존 방식으로 동작
    render_diagrams = None

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TEMPLATE = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<style>
:root {{
  --bg: #f7f8fa; --card: #ffffff; --text: #1d2433; --muted: #5b6577; --border: #dfe3ea;
  --accent: #0b6e8a; --accent-soft: #e3f2f7; --warn: #a15c00; --warn-soft: #fff4e0;
  --th: #eef2f6; --code: #f1f3f6;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg: #12151b; --card: #1a1f27; --text: #e4e8ee; --muted: #9aa5b5; --border: #2d3440;
    --accent: #5cc3df; --accent-soft: #15303a; --warn: #f0b45a; --warn-soft: #33270f;
    --th: #222935; --code: #222935;
  }}
}}
:root[data-theme="dark"] {{
  --bg: #12151b; --card: #1a1f27; --text: #e4e8ee; --muted: #9aa5b5; --border: #2d3440;
  --accent: #5cc3df; --accent-soft: #15303a; --warn: #f0b45a; --warn-soft: #33270f;
  --th: #222935; --code: #222935;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--text); font-family: "Noto Sans KR", system-ui, sans-serif; line-height: 1.7; font-size: 16px; }}
main {{ max-width: 1080px; margin: 0 auto; padding: 32px 16px 80px; }}
article {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 32px clamp(16px, 4vw, 48px); }}
h1, h2, h3 {{ font-family: "Noto Serif KR", serif; line-height: 1.35; }}
h1 {{ font-size: 1.75rem; margin-top: 0; }}
h2 {{ font-size: 1.35rem; margin-top: 2.2em; padding-bottom: .3em; border-bottom: 2px solid var(--accent-soft); }}
h3 {{ font-size: 1.12rem; margin-top: 1.6em; color: var(--accent); }}
h4 {{ font-size: 1rem; margin-top: 1.4em; }}
a {{ color: var(--accent); }}
blockquote {{ margin: 1em 0; padding: .6em 1em; background: var(--accent-soft); border-left: 4px solid var(--accent); border-radius: 0 8px 8px 0; color: var(--text); }}
.table-wrap {{ overflow-x: auto; margin: 1em 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: .92rem; }}
th, td {{ border: 1px solid var(--border); padding: 6px 10px; vertical-align: top; }}
th {{ background: var(--th); text-align: left; }}
code {{ font-family: "JetBrains Mono", monospace; background: var(--code); padding: .1em .35em; border-radius: 4px; font-size: .88em; }}
pre {{ background: var(--code); padding: 12px 14px; border-radius: 8px; overflow-x: auto; }}
pre code {{ background: none; padding: 0; }}
pre.mermaid {{ background: var(--card); text-align: center; }}
figure.diagram {{ margin: 1.5em 0; text-align: center; overflow-x: auto; }}
figure.diagram img {{ max-width: 100%; height: auto; background: #ffffff; border: 1px solid var(--border); border-radius: 8px; padding: 10px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05); }}
figure.diagram-text img {{ image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges; }}
/* 반응형 이미지 및 뷰포트 최적화 */
article img {{ max-width: 100%; height: auto; display: block; margin: 1.8em auto; border-radius: 8px; border: 1px solid var(--border); box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06); background: #ffffff; box-sizing: border-box; cursor: zoom-in; transition: transform 0.2s ease, box-shadow 0.2s ease; }}
article img:hover {{ box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12); }}
p:has(> img) {{ text-align: center; margin: 1.5em 0; }}
.meta {{ color: var(--muted); font-size: .85rem; margin-top: 24px; }}
.katex-display {{ overflow-x: auto; overflow-y: hidden; }}
/* 라이트박스 확대 모달 */
.lightbox-modal {{ display: none; position: fixed; z-index: 99999; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.88); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); justify-content: center; align-items: center; cursor: zoom-out; padding: 24px; box-sizing: border-box; }}
.lightbox-modal.active {{ display: flex; }}
.lightbox-modal img {{ max-width: 95vw; max-height: 92vh; object-fit: contain; margin: 0; border: none; border-radius: 6px; box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6); cursor: default; }}
.lightbox-close {{ position: absolute; top: 18px; right: 26px; color: #ffffff; font-size: 34px; font-weight: 300; cursor: pointer; user-select: none; line-height: 1; transition: color 0.2s; }}
.lightbox-close:hover {{ color: var(--accent); }}
</style>
</head>
<body>
<main>
<article>
{body}
<p class="meta">생성: {stamp} · 원본: {src} · build_report_html.py (Framework v2.7)</p>
</article>
</main>
<div class="lightbox-modal" id="lightboxModal">
  <span class="lightbox-close" id="lightboxClose">&times;</span>
  <img id="lightboxImg" src="" alt="Enlarged view">
</div>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],throwOnError:false}});"></script>
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
const dark = matchMedia("(prefers-color-scheme: dark)").matches;
mermaid.initialize({{ startOnLoad: true, theme: dark ? "dark" : "default" }});
</script>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  const modal = document.getElementById('lightboxModal');
  const modalImg = document.getElementById('lightboxImg');
  const closeBtn = document.getElementById('lightboxClose');
  if (modal && modalImg) {{
    document.querySelectorAll('article img').forEach(img => {{
      img.addEventListener('click', () => {{
        modalImg.src = img.src;
        modalImg.alt = img.alt || 'Enlarged diagram';
        modal.classList.add('active');
      }});
    }});
    modal.addEventListener('click', (e) => {{
      if (e.target !== modalImg) {{
        modal.classList.remove('active');
      }}
    }});
    if (closeBtn) {{
      closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    }}
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape' && modal.classList.contains('active')) {{
        modal.classList.remove('active');
      }}
    }});
  }}
}});
</script>
</body>
</html>
"""

MATH_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.S)
MATH_INLINE = re.compile(r"(?<![\\$])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)")
MERMAID = re.compile(r"```mermaid\s*\n(.*?)```", re.S)


FENCE = re.compile(r"^([ \t]*)```([A-Za-z0-9_+-]*)[ \t]*\n(.*?)\n[ \t]*```[ \t]*$", re.S | re.M)


def _img_tag(png: bytes, alt: str, kind: str) -> str:
    return (f'<figure class="diagram diagram-{kind}"><img src="{render_diagrams.data_uri(png)}" alt="{html.escape(alt)}" loading="lazy"></figure>')


def convert(md_text: str, images: bool = True):
    md_text = md_text.replace("\r\n", "\n")
    store = []


    def keep(s):
        store.append(s)
        return f"\u0000MATH{len(store) - 1}\u0000"

    mermaids = []

    def keep_mermaid(m):
        mermaids.append(m.group(1))
        return f"\n\n\u0000MERMAID{len(mermaids) - 1}\u0000\n\n"

    # 문자 도식(상자 그림·화살표 코드 블록)은 PNG로 미리 렌더링해 자리표시자로 바꾼다
    diagrams = []

    def keep_diagram(m):
        lang, code = m.group(2), m.group(3)
        if not images or render_diagrams is None or not render_diagrams.is_text_diagram(lang, code):
            return m.group(0)
        try:
            png = render_diagrams.render_text_diagram(code)
        except Exception:
            return m.group(0)
        diagrams.append((png, code))
        return f"\n\n\u0000DIAGRAM{len(diagrams) - 1}\u0000\n\n"

    t = MERMAID.sub(keep_mermaid, md_text)
    t = FENCE.sub(keep_diagram, t)
    # 코드 블록 안의 $는 수식이 아니므로 펜스 코드 구간을 먼저 분리한다
    parts = re.split(r"(```.*?```)", t, flags=re.S)
    for i, part in enumerate(parts):
        if part.startswith("```"):
            continue
        part = MATH_BLOCK.sub(lambda m: keep("$$" + m.group(1) + "$$"), part)
        part = MATH_INLINE.sub(lambda m: keep("$" + m.group(1) + "$"), part)
        parts[i] = part
    t = "".join(parts)
    body = markdown.markdown(t, extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"], output_format="html5")
    body = re.sub(r"\u0000MATH(\d+)\u0000", lambda m: html.escape(store[int(m.group(1))], quote=False), body)
    mpng = render_diagrams.render_mermaid_batch(mermaids) if (images and render_diagrams is not None and mermaids) else [None] * len(mermaids)

    def put_mermaid(m):
        i = int(m.group(2))
        if mpng[i]:
            return _img_tag(mpng[i], "Mermaid 다이어그램", "mermaid")
        return '<pre class="mermaid">' + html.escape(mermaids[i]) + "</pre>"  # 렌더링 실패 시 브라우저 렌더링으로 대체

    body = re.sub(r"(<p>)?\u0000MERMAID(\d+)\u0000(</p>)?", put_mermaid, body)
    body = re.sub(r"(<p>)?\u0000DIAGRAM(\d+)\u0000(</p>)?", lambda m: _img_tag(diagrams[int(m.group(2))][0], "도식", "text"), body)
    convert.stats = {"text_diagrams": len(diagrams), "mermaid": len(mermaids), "mermaid_images": sum(1 for x in mpng if x)}
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    body = re.sub(r"</table>", "</table></div>", body)
    m = re.search(r"^#\s+(.+)$", md_text, re.M)
    title = re.sub(r"[*`_]", "", m.group(1)).strip() if m else "경혈해부 보고서"
    return title, body


def build(md_path: Path, archive: bool = True, images: bool = True) -> Path:
    md_text = md_path.read_text(encoding="utf-8")
    title, body = convert(md_text, images)
    out = md_path.with_suffix(".html")
    if archive and out.exists():
        adir = out.parent / "_구판_html"
        adir.mkdir(exist_ok=True)
        dst = adir / f"{out.stem}_{datetime.now():%Y%m%d}.html"
        if not dst.exists():
            shutil.copy2(out, dst)
    lang = "en" if (md_path.stem.endswith("_en") or "_en_" in md_path.stem) else "ko"
    out.write_text(TEMPLATE.format(title=html.escape(title), body=body, stamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
                                   src=html.escape(md_path.name), lang=lang), encoding="utf-8", newline="\n")
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    archive = "--no-archive" not in sys.argv
    images = "--no-images" not in sys.argv
    if not args:
        print(__doc__)
        return 1
    for a in args:
        p = Path(a)
        o = build(p, archive, images)
        st = getattr(convert, "stats", {})
        print(f"[html] {o}  (문자 도식 이미지 {st.get('text_diagrams', 0)} · Mermaid 이미지 {st.get('mermaid_images', 0)}/{st.get('mermaid', 0)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

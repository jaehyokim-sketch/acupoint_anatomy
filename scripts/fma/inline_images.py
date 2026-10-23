# -*- coding: utf-8 -*-
"""
inline_images.py — 보고서 HTML 안의 로컬 이미지(<img src="그림.png">)를 data URI로 내장해 단일 파일로 만든다 (Claude Code 전용)

공용 빌더 build_report_html.py는 문자 도식·Mermaid만 PNG로 내장하고, 마크다운의 ![](그림.png)는 상대 링크로 둔다.
빌더 실행 직후 이 스크립트를 돌리면 HTML 하나만 옮겨도 그림이 보인다.

사용 (프로젝트 루트에서):
  python .agents/skills/acupoint-anatomy/scripts/build_report_html.py <보고서.md>
  python .claude/skills/acupoint-anatomy/scripts/fma/inline_images.py <보고서.html>
"""
import base64
import mimetypes
import re
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def inline(html_path: Path) -> int:
    text = html_path.read_text(encoding="utf-8")
    count = 0

    def repl(m):
        nonlocal count
        src = m.group(2)
        if src.startswith(("data:", "http:", "https:")):
            return m.group(0)
        img = (html_path.parent / src).resolve()
        if not img.exists():
            print(f"[inline] ⚠ 파일 없음: {src}")
            return m.group(0)
        mime = mimetypes.guess_type(img.name)[0] or "image/png"
        count += 1
        return f'{m.group(1)}"data:{mime};base64,{base64.b64encode(img.read_bytes()).decode()}" style="max-width:100%;height:auto"'

    text = re.sub(r'(<img[^>]*?\bsrc=)"([^"]+)"', repl, text)
    html_path.write_text(text, encoding="utf-8")
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        p = Path(arg)
        print(f"[inline] {p.name}: 이미지 {inline(p)}개 내장 ({p.stat().st_size // 1024} KB)")

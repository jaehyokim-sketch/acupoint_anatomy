# -*- coding: utf-8 -*-
"""
build_remote_server.py — mcp_server/acupoint_core.py + mcp_server/remote_backend.py → mcp_server/remote_server.py

원격 서버는 외부 사용자가 파일 하나만 내려받아 쓰도록 단일 파일로 배포한다. 로직은 acupoint_core.py 하나에서만 고치고,
이 스크립트로 remote_server.py를 다시 만든다.

  python scripts/build_remote_server.py          # 생성
  python scripts/build_remote_server.py --check  # 생성물이 원본과 다르면 종료코드 1
"""
import argparse
import re
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MCP = Path(__file__).resolve().parents[1] / "mcp_server"
CORE, BACKEND, OUT = MCP / "acupoint_core.py", MCP / "remote_backend.py", MCP / "remote_server.py"


def build():
    core = CORE.read_text(encoding="utf-8")
    backend = BACKEND.read_text(encoding="utf-8")
    m = re.match(r'(# -\*- coding: utf-8 -\*-\n)("""[\s\S]*?"""\n)', backend)
    if not m:
        sys.exit("[중단] remote_backend.py 머리말(docstring)을 찾지 못했습니다.")
    doc = m.group(2)
    body = backend[m.end():]
    body, n = re.subn(r"# <core-import>[\s\S]*?# </core-import>\n", "", body)
    if n != 1:
        sys.exit("[중단] remote_backend.py의 <core-import> 블록을 찾지 못했습니다.")
    core = re.sub(r"^# -\*- coding: utf-8 -\*-\n", "", core)
    banner = ("# " + "=" * 96 + "\n"
              "# 자동 생성 파일 — 직접 고치지 마세요.\n"
              "#   원본: mcp_server/acupoint_core.py(도구 로직) + mcp_server/remote_backend.py(GitHub 백엔드)\n"
              "#   생성: python scripts/build_remote_server.py\n"
              "# " + "=" * 96 + "\n")
    return ("#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n" + doc + banner +
            "\n# ----- acupoint_core.py -----\n" + core.rstrip() + "\n\n\n# ----- remote_backend.py -----\n" + body.lstrip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = build()
    cur = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if cur == text:
        print("[OK] remote_server.py가 최신입니다.")
        return
    if args.check:
        print("[STALE] remote_server.py가 원본과 다릅니다. python scripts/build_remote_server.py 를 실행하세요.")
        sys.exit(1)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"[WRITE] {OUT.relative_to(OUT.parents[1]).as_posix()} ({len(text):,}자)")


if __name__ == "__main__":
    main()

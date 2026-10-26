# -*- coding: utf-8 -*-
"""
register_mcp.py — acupoint-anatomy MCP 서버를 이 PC의 Claude Code에 등록한다 (PC마다 1회, Python·저장소 경로가 바뀌면 다시 실행)

경로를 이 스크립트 위치와 현재 Python(sys.executable)에서 계산하므로, 저장소를 어디에 두든 같은 명령으로 등록된다.

  python scripts/register_mcp.py                  # 로컬 서버(server.py), 사용자 범위(모든 프로젝트)
  python scripts/register_mcp.py --remote         # 원격 서버(remote_server.py, GitHub 스트리밍)
  python scripts/register_mcp.py --scope project  # 현재 폴더의 .mcp.json에 등록
  python scripts/register_mcp.py --print-json     # Claude Desktop·Cursor·Antigravity용 JSON 설정만 출력
  python scripts/register_mcp.py --dry-run        # 실행할 명령만 출력

보조 문헌(로컬 서버 전용): --extra "東醫寶鑑=<폴더>;<이름>=<폴더>"
  지정하지 않으면 Drive 프로젝트(환경변수 ACUPOINT_DRIVE_ROOT, 기본 G:/내 드라이브/도서 번역)의
  01_도서_번역_및_원전/동의보감 폴더가 있을 때 자동으로 넣는다.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

NAME = "acupoint-anatomy"
ROOT = Path(__file__).resolve().parents[1]


def default_extra():
    drive = Path(os.environ.get("ACUPOINT_DRIVE_ROOT", r"G:\내 드라이브\도서 번역"))
    dongui = drive / "01_도서_번역_및_원전" / "동의보감"
    return f"東醫寶鑑={dongui.as_posix()}" if dongui.is_dir() else ""


def main():
    ap = argparse.ArgumentParser(description="acupoint-anatomy MCP 서버 등록")
    ap.add_argument("--remote", action="store_true", help="원격 서버(remote_server.py)를 등록")
    ap.add_argument("--scope", choices=["user", "project", "local"], default="user")
    ap.add_argument("--extra", default=None, help='보조 문헌 "이름=폴더;…" (빈 문자열이면 사용 안 함)')
    ap.add_argument("--print-json", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    python = Path(sys.executable).as_posix()
    server = (ROOT / "mcp_server" / ("remote_server.py" if args.remote else "server.py")).as_posix()
    env = {"PYTHONIOENCODING": "utf-8"}
    extra = default_extra() if args.extra is None else args.extra
    if extra and not args.remote:
        env["ACUPOINT_EXTRA_CLASSICS"] = extra

    if args.print_json:
        print(json.dumps({"mcpServers": {NAME: {"command": python, "args": [server], "env": env}}}, ensure_ascii=False, indent=2))
        return

    claude = shutil.which("claude")
    if not claude:
        sys.exit("[중단] claude CLI를 찾지 못했습니다. Claude Code를 설치했는지 확인하거나 --print-json으로 JSON을 받아 직접 등록하세요.")
    add = [claude, "mcp", "add", "--scope", args.scope, NAME]
    for k, v in env.items():
        add += ["-e", f"{k}={v}"]
    add += ["--", python, server]
    remove = [claude, "mcp", "remove", NAME, "-s", args.scope]
    print("실행:", " ".join(f'"{a}"' if " " in a else a for a in add))
    if args.dry_run:
        return
    subprocess.run(remove, capture_output=True, text=True, encoding="utf-8", errors="replace")  # 기존 등록이 없으면 실패해도 무시
    r = subprocess.run(add, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or "") + (r.stderr or ""))
    if r.returncode:
        sys.exit(r.returncode)
    g = subprocess.run([claude, "mcp", "get", NAME], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(g.stdout or g.stderr)
    print("새 Claude Code 세션부터 mcp__acupoint-anatomy__* 도구를 쓸 수 있습니다.")


if __name__ == "__main__":
    main()

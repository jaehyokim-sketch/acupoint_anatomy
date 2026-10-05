# -*- coding: utf-8 -*-
"""
check_environment.py — Acupoint Anatomy MCP & Skill Environment Checker
Validates Python runtime, dependencies, core dataset files, environment variables, and MCP config.

Usage:
  python check_environment.py [--json]
"""
import importlib
import json
import os
import platform
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

PACKAGES = [
    ("requests", True),
    ("openpyxl", True),
    ("pymupdf", True),
    ("olefile", True),
    ("markdown", True),
    ("PIL", True),
    ("fontTools", True),
    ("pandas", False),
    ("playwright", False),
]

KEY_PATHS = [
    "framework/acupoint_anatomical_logic_framework.md",
    "framework/layer_b_reference_registry.md",
    "framework/biomedical_master_db_sync_design.md",
    "data/361_Acupoints_Refined_Master_DB_v2.csv",
    "data/layer_b_reference_registry.json",
    "data/경혈_생의학_신경반사_마스터DB.json",
    "skill/SKILL.md",
    "mcp_server/server.py",
    "mcp_server/remote_server.py",
]


def resolve_papers_dir():
    env = os.environ.get("ACUPOINT_PAPERS_DIR")
    if env:
        return Path(env), "환경변수 ACUPOINT_PAPERS_DIR"
    cand = ROOT.parent / "02_Master_Datasets"
    if cand.exists():
        return cand, "상위 워크스페이스 02_Master_Datasets"
    return ROOT / "data", "기본 data 폴더"


def main() -> int:
    as_json = "--json" in sys.argv
    rows = []

    def add(level, item, detail):
        rows.append({"level": level, "item": item, "detail": detail})

    v = sys.version_info
    add("OK" if v >= (3, 10) else "FAIL", "Python", f"{platform.python_version()} ({sys.executable})")

    for name, required in PACKAGES:
        try:
            importlib.import_module(name)
            add("OK", f"패키지 {name}", "설치됨")
        except Exception:
            add("FAIL" if required else "WARN", f"패키지 {name}", "미설치 → pip install -r requirements.txt")

    add("OK" if ROOT.exists() else "FAIL", "프로젝트 루트", str(ROOT))

    for rel in KEY_PATHS:
        p = ROOT / rel
        add("OK" if p.exists() else "FAIL", "핵심 파일", rel + ("" if p.exists() else " (없음)"))

    mail = os.environ.get("OPENALEX_MAILTO", "")
    add("OK" if mail else "WARN", "환경변수 OPENALEX_MAILTO", mail or "미설정 (API 정중 요청용 이메일 권장)")

    key = os.environ.get("NCBI_API_KEY", "")
    add("OK" if key else "WARN", "환경변수 NCBI_API_KEY", ("설정됨" if key else "미설정 (무키 시 초당 3회 요청 제한)"))

    pat = os.environ.get("GITHUB_TOKEN", "")
    add("OK" if pat else "WARN", "환경변수 GITHUB_TOKEN", ("설정됨" if pat else "미설정 (비공개 저장소 원격 MCP 스트리밍 시 필요)"))

    fails = [r for r in rows if r["level"] == "FAIL"]
    if as_json:
        print(json.dumps({"ok": not fails, "rows": rows}, ensure_ascii=False, indent=2))
    else:
        print(f"[check-environment] {ROOT}")
        for r in rows:
            print(f"  [{r['level']:4}] {r['item']:24} {r['detail']}")
        print("  결과:", "FAIL %d건" % len(fails) if fails else "OK (WARN %d건)" % sum(1 for r in rows if r["level"] == "WARN"))

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

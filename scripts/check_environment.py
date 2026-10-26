# -*- coding: utf-8 -*-
"""
check_environment.py — [경혈해부] 스킬 실행 환경 점검 (다른 PC에서 처음 사용할 때)

점검: Python 버전 · 필수 패키지 · 프로젝트 루트/핵심 파일 · 로컬 논문 폴더 해석 · 환경변수 · 주간 배치 등록(Windows)
사용: python check_environment.py [--json]
종료코드: 0 = 모두 OK 또는 WARN, 1 = FAIL 존재
"""
import importlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPT_DIR = Path(__file__).resolve().parent


def find_project_root() -> Path:
    for env in ("ACUPOINT_PROJECT_ROOT", "ACUPOINT_DRIVE_ROOT"):
        val = os.environ.get(env)
        if val and (Path(val) / "01_Framework").exists():
            return Path(val)
    curr = SCRIPT_DIR
    for _ in range(8):
        if (curr / "01_Framework").exists() and (curr / "02_Master_Datasets").exists():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
    default = Path(r"G:\내 드라이브\도서 번역")
    if (default / "01_Framework").exists():
        return default
    return SCRIPT_DIR.parents[min(len(SCRIPT_DIR.parents) - 1, 3)]


ROOT = find_project_root()
TASK_NAME = "AcupointMasterDB_WeeklySync"
PACKAGES = [
    ("requests", True),
    ("openpyxl", True),
    ("pymupdf", True),
    ("olefile", True),
    ("markdown", True),
    ("PIL", True),
    ("fontTools", True),
    ("playwright", False),  # 선택: Mermaid 고해상도 PNG 캡처
    ("pandas", False),
    ("owlready2", False),  # FMA OWL 온톨로지 로컬 파싱
    ("rdflib", False),     # FMA SPARQL 질의
    ("neo4j", False),      # FMA 그래프 Cypher 질의
]
KEY_PATHS = [
    "01_Framework/acupoint_anatomical_logic_framework.md",
    "01_Framework/layer_b_reference_registry.md",
    "01_Framework/biomedical_master_db_sync_design.md",
    "02_Master_Datasets/경혈_생의학_신경반사_마스터DB.json",
    "02_Master_Datasets/경혈_생의학_신경반사_마스터DB.xlsx",
    "02_Master_Datasets/361_Acupoints_Refined_Master_DB_v2.csv",
    "02_Master_Datasets/layer_b_reference_registry.json",
    "02_Master_Datasets/中国针灸穴位通鉴 분석데이터셋",
    "02_Master_Datasets/FMA/acupoint_fma_mapping.json",
    ".agents/skills/acupoint-anatomy/SKILL.md",
    ".agents/rules/acupoint-anatomy-routing.md",
    ".claude/skills/acupoint-anatomy/SKILL.md",
    ".claude/CLAUDE.md",
    "01_도서_번역_및_원전/중국침구혈위통감(中国针灸穴位通鉴)",
    "01_도서_번역_및_원전/중국침구증치통감(中国针灸证治通鉴)",
    "01_도서_번역_및_원전/침구수혈통고(针灸腧穴通考)",
    "01_도서_번역_및_원전/중국침구경락통감(中国针灸经络通鉴)",
]


def resolve_papers_dir():
    env = os.environ.get("ACUPOINT_PAPERS_DIR")
    if env:
        return Path(env), "환경변수 ACUPOINT_PAPERS_DIR"
    cand = ROOT.parent / "학습자료" / "실험 및 연구 논문"
    if cand.exists():
        return cand, "프로젝트 루트 상위(내 드라이브)/학습자료"
    try:
        md = json.loads(io_read(ROOT / "02_Master_Datasets" / "경혈_생의학_신경반사_마스터DB.json"))["_metadata"]
        if md.get("source_local_dir"):
            return Path(md["source_local_dir"]), "DB _metadata.source_local_dir"
    except Exception:
        pass
    return cand, "기본 추정(없음)"


def io_read(p: Path) -> str:
    with open(p, encoding="utf-8") as f:
        return f.read()


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
            add("FAIL" if required else "WARN", f"패키지 {name}", "미설치 → pip install -r .agents/skills/acupoint-anatomy/scripts/requirements.txt")
    add("OK" if ROOT.exists() else "FAIL", "프로젝트 루트", str(ROOT))
    for rel in KEY_PATHS:
        p = ROOT / rel
        add("OK" if p.exists() else "FAIL", "핵심 경로", rel + ("" if p.exists() else " (없음)"))
    pdir, how = resolve_papers_dir()
    if pdir.exists():
        n = sum(1 for r, _, fs in os.walk(pdir) for f in fs if f.lower().endswith((".pdf", ".hwp", ".hwpx")))
        add("OK", "로컬 논문 폴더", f"{pdir} ({how}, PDF/HWP {n:,}편)")
    else:
        add("WARN", "로컬 논문 폴더", f"{pdir} 없음 ({how}) → ACUPOINT_PAPERS_DIR 설정 또는 Drive 동기화 확인")
    mail = os.environ.get("OPENALEX_MAILTO", "")
    add("OK" if mail else "WARN", "환경변수 OPENALEX_MAILTO", mail or "미설정 → setx OPENALEX_MAILTO <이메일>")
    key = os.environ.get("NCBI_API_KEY", "")
    add("OK" if key else "WARN", "환경변수 NCBI_API_KEY", ("설정됨 (길이 %d)" % len(key)) if key else "미설정 → NCBI 계정에서 발급 후 setx NCBI_API_KEY <키> (무키 시 초당 3회)")
    if platform.system() == "Windows":
        try:
            # 출력은 콘솔 코드페이지(cp949 등)로 나오므로 바이트로 받고 반환 코드만 사용한다
            r = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            add("OK" if r.returncode == 0 else "WARN", "주간 배치 작업", f"{TASK_NAME} " + ("등록됨" if r.returncode == 0 else "미등록 → register_weekly_task.cmd 실행"))
        except Exception as e:
            add("WARN", "주간 배치 작업", f"조회 실패 ({type(e).__name__})")
    else:
        add("WARN", "주간 배치 작업", "Windows 작업 스케줄러 전용 (현재 OS: %s)" % platform.system())
    add("OK", "호스트", f"{platform.node()} / {platform.system()} {platform.release()}")

    fails = [r for r in rows if r["level"] == "FAIL"]
    if as_json:
        print(json.dumps({"ok": not fails, "rows": rows}, ensure_ascii=False, indent=2))
    else:
        print(f"[check-environment] {ROOT}")
        for r in rows:
            print(f"  [{r['level']:4}] {r['item']:22} {r['detail']}")
        print("  결과:", "FAIL %d건" % len(fails) if fails else "OK (WARN %d건)" % sum(1 for r in rows if r["level"] == "WARN"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
run_ari_analyzer_local.py — Drive 정본 ari_analyzer.py(Antigravity 공용 스크립트)를 '호출만' 하고 출력은 로컬 저장소에 쓴다

ari_analyzer.py는 자기 위치에서 프로젝트 루트를 찾으므로, Drive 사본(.agents/…)을 그대로 실행하면 원전·KJH·FMA 데이터는
모두 찾지만 초안이 Drive 배포 폴더(G:/…/도서 번역/acupoint_anatomy/01_…)에 생긴다. 저장소 사본(scripts/ari_analyzer.py)을
실행하면 저장소에 쓰지만 원전·KJH·FMA 경로를 찾지 못한다. 이 실행기는 Drive 사본을 불러 데이터는 Drive에서 읽고,
출력 위치(OUTPUT_ROOT)만 로컬 저장소 01_경혈별_해부생리_분석보고서로 바꾼 뒤 그 main()을 실행한다. 스크립트 자체는 고치지 않는다.

  python scripts/run_ari_analyzer_local.py <코드> --s-orig 75 --s-clarity 75 --s-reflex 75 --s-safety 75
  옵션: --output-root <폴더>  (기본: 이 저장소의 01_경혈별_해부생리_분석보고서)
  나머지 인자는 ari_analyzer.py에 그대로 넘긴다. Drive 위치: 환경변수 ACUPOINT_DRIVE_ROOT (기본 G:/내 드라이브/도서 번역)
"""
import importlib.util
import os
import re
import subprocess
import sys
import time
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
DRIVE = Path(os.environ.get("ACUPOINT_DRIVE_ROOT", r"G:\내 드라이브\도서 번역"))
SRC = DRIVE / ".agents" / "skills" / "acupoint-anatomy" / "scripts" / "ari_analyzer.py"
BUILDER = REPO / "scripts" / "build_report_html.py"
INLINER = REPO / "scripts" / "fma" / "inline_images.py"

# 스킬 7절 '대체 표기': 원본 데이터 파일 링크 → 기술명
TECH_NAMES = {
    "경혈_생의학_신경반사_마스터DB": "통합 생의학 마스터 DB v3.0",
    "layer_b_reference_registry": "Layer B 4계층 참조 등록부",
    "361_Acupoints_Refined_Master_DB_v2": "361 표준 경혈 마스터 DB",
    "경혈명_비교_정리_KJH": "KJH 경혈 이명 대조 DB",
    "acupoint_anatomical_logic_framework": "로직 정본(Framework v2.7)",
    "acupoint_fma_mapping": "경혈↔FMA 대응표",
}
LEAK = re.compile(r"file:///|\b[A-Za-z]:[\\/]|내 드라이브|02_Master_Datasets|01_도서_번역_및_원전|chunks_refined|01_Framework/"
                  r"|\.agents/|\.claude/|%LOCALAPPDATA%|_DATA_DIR|\.(xlsx|json|csv|db|owl|obj|vtk)\b")


def _tech_name(label):
    plain = label.strip("` ")
    stem = re.sub(r"\.(md|json|xlsx|csv)$", "", plain)
    return TECH_NAMES.get(stem, stem)


def sanitize(md_path: Path) -> int:
    """`[라벨](file:///…)` 로컬 링크를 기술명 텍스트로 바꾼다. 바꾼 개수를 돌려준다"""
    text = md_path.read_text(encoding="utf-8")
    new, n = re.subn(r"\[([^\]]+)\]\(file:///[^)]*\)", lambda m: _tech_name(m.group(1)), text)
    if n:
        md_path.write_text(new, encoding="utf-8")
    return n


def leak_lines(path: Path):
    body = re.sub(r"data:[a-z/+.-]+;base64,[A-Za-z0-9+/=]+", "", path.read_text(encoding="utf-8", errors="replace"))
    out = []
    for i, line in enumerate(body.splitlines(), 1):
        urls = [m.span() for m in re.finditer(r"https?://[^\s\"'<>)]+", line)]
        if any(not any(a <= m.start() < b for a, b in urls) for m in LEAK.finditer(line)):
            out.append(i)
    return out


def postprocess(out_root: Path, started: float):
    """이번 실행에서 생긴 보고서 .md만 비노출 규정에 맞게 고치고 HTML을 다시 빌드한다"""
    for md in out_root.rglob("*_보고서.md"):
        if md.stat().st_mtime < started:
            continue
        n = sanitize(md)
        html = md.with_suffix(".html")
        if n and BUILDER.exists():
            subprocess.run([sys.executable, str(BUILDER), str(md), "--no-archive"], check=False)
            if INLINER.exists() and html.exists():
                subprocess.run([sys.executable, str(INLINER), str(html)], check=False)
        left = {p.name: leak_lines(p) for p in (md, html) if p.exists()}
        print(f"[run_ari_analyzer_local] 비노출 정리: {md.name} 로컬 링크 {n}건 → 기술명"
              + "".join(f" · {k} 남은 적중 {len(v)}건{(' (행 ' + ','.join(map(str, v[:8])) + ')') if v else ''}" for k, v in left.items()))


def main():
    argv = sys.argv[1:]
    out_root = REPO / "01_경혈별_해부생리_분석보고서"
    if "--output-root" in argv:
        i = argv.index("--output-root")
        out_root = Path(argv[i + 1])
        del argv[i:i + 2]
    if not SRC.exists():
        sys.exit(f"[중단] Drive 정본 ari_analyzer.py가 없습니다: {SRC}")
    spec = importlib.util.spec_from_file_location("ari_analyzer", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out_root.mkdir(parents=True, exist_ok=True)
    mod.OUTPUT_ROOT = str(out_root)
    print(f"[run_ari_analyzer_local] 데이터: {mod.BASE_DIR} · 출력: {out_root}")
    sys.argv = [str(SRC)] + argv
    started = time.time() - 1
    mod.main()
    postprocess(out_root, started)


if __name__ == "__main__":
    main()

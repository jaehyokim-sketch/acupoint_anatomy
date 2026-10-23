# -*- coding: utf-8 -*-
"""
fma_common.py — FMA(Foundational Model of Anatomy) 연동 공통 모듈 (Claude Code ↔ Antigravity 공용)

경로 해석 (PC 독립):
  FMA 원본·파생 DB  : FMA_DATA_DIR 환경변수 → %LOCALAPPDATA%\\acupoint_fma (Windows) → ~/.cache/acupoint_fma
                      (208 MB OWL + 수백 MB SQLite이므로 Google Drive 동기화 폴더 밖에 둔다. PC마다 fma_build.py로 재생성)
  경혈↔FMA 대응표   : <프로젝트 루트>/02_Master_Datasets/FMA/  (작은 결과물, Drive로 공유)
"""
import os
import re
import sys
import sqlite3
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

FMA_URL = "http://purl.obolibrary.org/obo/fma.owl"
FMA_NS = "http://purl.org/sig/ont/fma/"
SCRIPT_DIR = Path(__file__).resolve().parent


def find_project_root() -> Path:
    cur = SCRIPT_DIR
    for _ in range(8):
        if (cur / "01_Framework").exists() and (cur / "02_Master_Datasets").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return Path.cwd().resolve()


ROOT = find_project_root()


def data_dir() -> Path:
    env = os.environ.get("FMA_DATA_DIR")
    if env:
        d = Path(env)
    elif os.environ.get("LOCALAPPDATA"):
        d = Path(os.environ["LOCALAPPDATA"]) / "acupoint_fma"
    else:
        d = Path.home() / ".cache" / "acupoint_fma"
    d.mkdir(parents=True, exist_ok=True)
    return d


OWL_PATH = data_dir() / "fma.owl"
QUADSTORE_PATH = data_dir() / "fma_quadstore.sqlite3"   # owlready2 영속 저장소 (SPARQL·rdflib 질의용)
INDEX_PATH = data_dir() / "fma_index.sqlite3"           # 압축 색인: entity / term / edge
NEO4J_DIR = data_dir() / "neo4j_import"                 # neo4j-admin import용 CSV
MAPPING_DIR = ROOT / "02_Master_Datasets" / "FMA"
MAPPING_JSON = MAPPING_DIR / "acupoint_fma_mapping.json"
MAPPING_XLSX = MAPPING_DIR / "acupoint_fma_mapping.xlsx"

TEXTBOOKS = {
    # 출처 약칭: (파일, 시트, 영문용어 열 이름)
    "공통교재": ("경혈학공통교재 경혈_해부구조_데이터셋_refine.xlsx", "해부구조_개별항목_상세", "영문용어"),
    "김재효": ("김재효 수업_경혈_해부구조_데이터셋.xlsx", "해부구조_개별항목_상세", "영문용어"),
}

# 분석에서 자주 쓰는 FMA 관계 (fma_query.py profile 출력 순서)
KEY_RELATIONS = [
    "nerve_supply", "segmental_supply", "arterial_supply", "venous_drainage", "drains_into", "lymphatic_drainage",
    "branch_of", "tributary_of", "regional_part_of", "constitutional_part_of", "member_of",
    "has_origin", "has_insertion", "attaches_to", "bounded_by", "continuous_with",
    "continuous_proximally_with", "continuous_distally_with", "contained_in",
]

# norm()/squash() 규칙을 바꾸면 올린다 — 색인의 term_norm이 이 규칙으로 저장되므로 불일치 시 index 재생성을 요구한다
NORM_VERSION = "2"

ORDINALS = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
            "eleventh", "twelfth"]
_ORD_RE = re.compile(r"\b(1[0-2]|[1-9])(?:st|nd|rd|th)\b")

_SPELLING = [
    (r"\bn\.", "nerve "), (r"\ba\.", "artery "), (r"\bv\.", "vein "), (r"\bm\.", "muscle "),
    (r"\bbrs?\.", "branch "), (r"\bbrs\b", "branch"), (r"\bbranches\b", "branch"), (r"\barteries\b", "artery"),
    (r"\bveins\b", "vein"), (r"\bnerves\b", "nerve"), (r"\bmuscles\b", "muscle"),
    (r"\bperoneal\b", "fibular"), (r"\bperoneus\b", "fibularis"),
    (r"\bmultifidi\b", "multifidus"), (r"\bintercostalis\b", "intercostal"),
    (r"\bsupraspinal\b", "supraspinous"), (r"\binterspinal\b", "interspinous"),
    (r"\binferios\b", "inferior"), (r"\bthracic\b", "thoracic"), (r"\blumbal\b", "lumbar"),
    (r"\bperctoral\b", "pectoral"), (r"\bsupraorbial\b", "supraorbital"),
    (r"\bgreat occipital\b", "greater occipital"), (r"\banorectal\b", "rectal"),
]


def norm(s: str) -> str:
    """대조용 정규화: 소문자, 관사·기호 제거, 약어(n./a./v./brs.) 전개, 서수(4th→fourth), 철자 변이 통일."""
    s = (s or "").lower().replace("ㆍ", " ").replace("’", "'").replace("ﾠ", " ").replace("\xa0", " ")
    for pat, rep in _SPELLING:
        s = re.sub(pat, rep, s)
    s = _ORD_RE.sub(lambda m: ORDINALS[int(m.group(1)) - 1], s)
    s = re.sub(r"[-_/,;.]", " ", s)
    s = re.sub(r"\bthe\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def squash(s: str) -> str:
    """공백까지 없앤 키 (supraorbital = supra-orbital)."""
    return norm(s).replace(" ", "")


def fma_id_from_iri(iri: str):
    m = re.search(r"fma(\d+)$", iri or "")
    return int(m.group(1)) if m else None


def open_index() -> sqlite3.Connection:
    if not INDEX_PATH.exists():
        sys.exit(f"[fma] 색인이 없습니다: {INDEX_PATH}\n      먼저 실행: python .claude/skills/acupoint-anatomy/scripts/fma/fma_build.py all")
    con = sqlite3.connect(str(INDEX_PATH))
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT value FROM meta WHERE key='norm_version'").fetchone()
    if not row or row[0] != NORM_VERSION:
        sys.exit("[fma] 색인의 정규화 규칙이 현재 스크립트와 다릅니다(norm 변경). 다시 실행: "
                 "python .claude/skills/acupoint-anatomy/scripts/fma/fma_build.py index")
    return con

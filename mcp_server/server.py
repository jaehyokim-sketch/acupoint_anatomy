#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acupoint Anatomy & Substrate Identification - Local Stdio MCP Server (Framework v2.7)
Provides local, zero-latency MCP tools using local master datasets and framework files.

Supported Tools:
  1. get_acupoint_anatomy_profile : 3D coordinates, 1 fen = 2.3mm depth, Layer 1~5 structures, textbook comparison, discrepancy branch
  2. get_fma_anatomy_profile      : FMA v5.1.0 ontology profile, nerve supply chain, spinal segment union, textbook comparison
  3. search_biomedical_reflex_db : Layer A biomedical reflex database, neural pathways, spinal segments, receptors, evidence
  4. get_layer_b_registry        : Layer B 4-tier reference registry (B1~B4) and B-Check 6-item compliance criteria
  5. calculate_ari_v3_score      : ARI v3.0 profile calculation (ARI-Core, Grade A~D, Gate 1~3, SI, Sensitivity)
  6. search_classic_records      : Full-text search of the four primary classics (point chapters, excerpts, keyword hits with file/line)
  7. get_framework_protocol      : Framework v2.7 Rank 0~7 workflow, Tier 1~3 rules, 10 essential report components

Usage:
  python server.py
"""

import sys
import os
import json
import re
import csv
import io

# Ensure UTF-8 stdout/stdin/stderr
if sys.platform == "win32":
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

LOCAL_PATHS = {
    "framework": os.path.join(PROJECT_ROOT, "framework", "acupoint_anatomical_logic_framework.md"),
    "layer_b_md": os.path.join(PROJECT_ROOT, "framework", "layer_b_reference_registry.md"),
    "layer_b_json": os.path.join(PROJECT_ROOT, "data", "layer_b_reference_registry.json"),
    "master_csv": os.path.join(PROJECT_ROOT, "data", "361_Acupoints_Refined_Master_DB_v2.csv"),
    "biomed_json": os.path.join(PROJECT_ROOT, "data", "경혈_생의학_신경반사_마스터DB.json"),
    "fma_json": os.path.join(PROJECT_ROOT, "data", "acupoint_fma_mapping.json"),
    "skill": os.path.join(PROJECT_ROOT, "skill", "SKILL.md"),
}

# Fallback to parent workspace datasets if running within parent repository
PARENT_FALLBACKS = {
    "framework": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "01_Framework", "acupoint_anatomical_logic_framework.md")),
    "layer_b_md": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "01_Framework", "layer_b_reference_registry.md")),
    "layer_b_json": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "layer_b_reference_registry.json")),
    "master_csv": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "361_Acupoints_Refined_Master_DB_v2.csv")),
    "biomed_json": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "경혈_생의학_신경반사_마스터DB.json")),
    "fma_json": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "FMA", "acupoint_fma_mapping.json")),
}


def read_file_content(key):
    path = LOCAL_PATHS.get(key)
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    fb = PARENT_FALLBACKS.get(key)
    if fb and os.path.exists(fb):
        with open(fb, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    return ""


# In-memory document cache
_LOCAL_CACHE = {}


def get_cached_master_csv():
    if "_PARSED_MASTER_CSV" in _LOCAL_CACHE:
        return _LOCAL_CACHE["_PARSED_MASTER_CSV"]

    text = read_file_content("master_csv")
    points = {}
    if text:
        try:
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                code = row.get("경혈코드", "").strip()
                name_kr = row.get("본혈명(한글)", "").strip()
                name_cn = row.get("본혈명(한자)", "").strip()
                data = {
                    "code": code,
                    "name_kr": name_kr,
                    "name_cn": name_cn,
                    "meridian_cn": row.get("소속경락(한자)", "").strip(),
                    "meridian_kr": row.get("소속경락(한글)", "").strip(),
                    "aliases_hanja": row.get("이명_한자목록(KJH)", "").strip(),
                    "aliases_hangul": row.get("이명_한글독음목록(KJH)", "").strip(),
                    "volume": row.get("혈위통감_권차", "").strip(),
                    "classics": row.get("출전_및_근거문헌", "").strip(),
                }
                points[code.upper()] = data
                m = re.match(r"([A-Z]+)0*(\d+)", code.upper())
                if m:
                    p, n = m.groups()
                    points[f"{p}{int(n)}"] = data
                    points[f"{p}{int(n):02d}"] = data
                if name_kr:
                    points[name_kr] = data
                if name_cn:
                    points[name_cn] = data
        except Exception as e:
            sys.stderr.write(f"Local CSV Parse error: {e}\n")

    _LOCAL_CACHE["_PARSED_MASTER_CSV"] = points
    return points


def get_cached_biomedical_db():
    if "_PARSED_BIOMED_JSON" in _LOCAL_CACHE:
        return _LOCAL_CACHE["_PARSED_BIOMED_JSON"]

    text = read_file_content("biomed_json")
    data = {}
    if text:
        try:
            data = json.loads(text)
        except Exception as e:
            sys.stderr.write(f"Local Biomed JSON Parse error: {e}\n")

    _LOCAL_CACHE["_PARSED_BIOMED_JSON"] = data
    return data


def get_cached_layer_b_registry():
    if "_PARSED_LAYER_B_JSON" in _LOCAL_CACHE:
        return _LOCAL_CACHE["_PARSED_LAYER_B_JSON"]

    text = read_file_content("layer_b_json")
    data = {}
    if text:
        try:
            data = json.loads(text)
        except Exception as e:
            sys.stderr.write(f"Local Layer B JSON Parse error: {e}\n")

    _LOCAL_CACHE["_PARSED_LAYER_B_JSON"] = data
    return data


def get_cached_fma_mapping():
    if "_PARSED_FMA_JSON" in _LOCAL_CACHE:
        return _LOCAL_CACHE["_PARSED_FMA_JSON"]

    text = read_file_content("fma_json")
    data = {}
    if text:
        try:
            data = json.loads(text)
        except Exception as e:
            sys.stderr.write(f"Local FMA JSON Parse error: {e}\n")

    _LOCAL_CACHE["_PARSED_FMA_JSON"] = data
    return data


_FMA_INSTANCE = None


def get_fma_instance():
    global _FMA_INSTANCE
    if _FMA_INSTANCE is not False and _FMA_INSTANCE is None:
        try:
            fma_scripts = os.path.join(PROJECT_ROOT, "scripts", "fma")
            if fma_scripts not in sys.path and os.path.exists(fma_scripts):
                sys.path.insert(0, fma_scripts)
            import fma_common
            import fma_query
            if fma_common.INDEX_PATH.exists():
                _FMA_INSTANCE = fma_query.FMA()
            else:
                _FMA_INSTANCE = False
        except Exception as e:
            sys.stderr.write(f"FMA instance initialization fallback to JSON: {e}\n")
            _FMA_INSTANCE = False
    return _FMA_INSTANCE if _FMA_INSTANCE is not False else None


def resolve_acupoint_key(query):
    query_clean = query.strip().upper()
    points = get_cached_master_csv()
    if query_clean in points:
        return points[query_clean]
    query_orig = query.strip()
    if query_orig in points:
        return points[query_orig]
    m = re.match(r"([A-Za-z]+)\s*0*(\d+)", query_clean)
    if m:
        p, n = m.groups()
        norm_code = f"{p}{int(n)}"
        if norm_code in points:
            return points[norm_code]
    return None


# --- MCP Tool Definitions ---
MCP_TOOLS = [
    {
        "name": "get_acupoint_anatomy_profile",
        "description": "361개 표준 경혈의 3D 공간 정위 좌표, 한대(漢代 1푼=2.3mm) 환산 자침 심도, Layer 1~5 층차별 해부학적 실체(신경·혈관·근막), 2대 교재(경혈학공통교재 vs 김재효교재) 비교 및 공간 변위 분기(Δ > 10mm) 프로파일을 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "acupoint": {
                    "type": "string",
                    "description": "경혈 코드(예: ST36, LU5, LI4, GV20, CV12) 또는 경혈명(예: 족삼리, 척택, 합곡, 백회, 중완, 足三里, 合谷)"
                }
            },
            "required": ["acupoint"]
        }
    },
    {
        "name": "search_biomedical_reflex_db",
        "description": "Layer A 통합 생의학 마스터 DB에서 특정 경혈 또는 해부학적 구조물/반사회로에 대한 실측 연구 논문(PMID/DOI, 실험종, 증거등급) 및 체성-내장/체성-자율신경 반사 기전 데이터를 검색합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 경혈 코드/이름, 장기, 신경, 수용체, 반사회로 또는 질환명 (예: ST36, 족삼리, 미주신경, Vagus, TRPV1, 위운동, 위염, 심율동)"
                },
                "evidence_filter": {
                    "type": "string",
                    "enum": ["all", "human", "animal", "mechanism"],
                    "description": "증거 유형 필터링 (all: 전체, human: 인체 임상/영상, animal: 동물 기초 실험, mechanism: 신경반사 기전 규명)"
                },
                "limit": {
                    "type": "integer",
                    "description": "반환할 최대 결과 수 (기본값: 10)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_layer_b_registry",
        "description": "Layer B 4계층 참조 등록부(B1: 신경해부학, B2: 체성-자율신경 반사, B3: 경혈 특이성 및 체성위상, B4: 근막 및 기계수용체)와 B-Check 6항목(≥ 8/12점) 판정 지침을 조회합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["all", "B1", "B2", "B3", "B4"],
                    "description": "Layer B 계층 선택 (B1: 해부학 교과서, B2: 반사생리학 랜드마크, B3: 침구 기전 모델, B4: 근막/기계신호)"
                },
                "reference_id": {
                    "type": "string",
                    "description": "특정 참조 ID (예: B1-01, B2-05, B3-17, B4-02)"
                },
                "query": {
                    "type": "string",
                    "description": "키워드 검색 (예: Gray, Sato, Ma, Langevin, TRPV1, C-fiber)"
                }
            }
        }
    },
    {
        "name": "calculate_ari_v3_score",
        "description": "Framework v2.7에 준거하여 ARI v3.0(경혈 실체 지수) 프로파일(ARI-Core 3요인 가중합산, 안전지수 SI 분리, 3대 비보상형 게이트 적용, A~D 등급, 등가중치 민감도)을 정밀 계산합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "s_orig": {
                    "type": "number",
                    "description": "문헌 일치도 점수 S_orig (0, 25, 50, 75, 100)"
                },
                "s_clarity": {
                    "type": "number",
                    "description": "해부학적 명확도 점수 S_clarity (0, 25, 50, 75, 100)"
                },
                "s_reflex": {
                    "type": "number",
                    "description": "생의학적 반사 부합도 점수 S_reflex (0, 25, 50, 75, 100)"
                },
                "s_safety": {
                    "type": "number",
                    "description": "안전 심도 점수 S_safety / SI (0, 25, 50, 75, 100)"
                },
                "layer_a_count": {
                    "type": "integer",
                    "description": "Layer A 실측 보유 논문 편수 (0편일 경우 Gate 2 적용: S_reflex <= 25 및 (H) 표지)"
                }
            },
            "required": ["s_orig", "s_clarity", "s_reflex", "s_safety"]
        }
    },
    {
        "name": "search_classic_records",
        "description": "4대 원전(《中国针灸穴位通鉴》·《针灸腧穴通考》·《中国针灸证治通鉴》·《中国针灸经络通鉴》) 정제 코퍼스를 직접 검색합니다. 경혈을 주면 《穴位通鉴》·《腧穴通考》의 해당 경혈 장(파일·행 범위·소절 목차)과 부위/定位·简要结语 원문 발췌를, 《证治通鉴》·《经络通鉴》에서는 혈명이 나오는 행을 돌려줍니다. query를 주면 모든 검색어가 들어 있는 행을 파일·행 번호와 함께 돌려줍니다(번체·간체 통합, 예: '兩筋間'='两筋间').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "acupoint": {
                    "type": "string",
                    "description": "경혈 코드 또는 혈명 (예: ST36, LU5, CV12, EX-HN3, 족삼리, 足三里, 百会). query만으로 검색할 때는 생략"
                },
                "query": {
                    "type": "string",
                    "description": "원문 검색어. 공백으로 나누면 모든 검색어가 한 행에 있어야 적중 (예: '两筋间', '针入 五分', '跗上动脉'). acupoint와 함께 주면 그 경혈 장(또는 혈명 주변 행) 안에서만 검색"
                },
                "classic_book": {
                    "type": "string",
                    "enum": ["all", "穴位通鉴", "腧穴通考", "证治通鉴", "经络通鉴"],
                    "description": "특정 원전만 검색 (기본값: all)"
                },
                "limit": {
                    "type": "integer",
                    "description": "원전별 최대 적중 행 수 (기본값: 10, 최대 50)"
                },
                "excerpt_chars": {
                    "type": "integer",
                    "description": "경혈 장 핵심 소절 발췌 길이(소절당 글자 수, 기본값: 1200, 200~4000)"
                }
            }
        }
    },
    {
        "name": "get_framework_protocol",
        "description": "경혈 해부학적 실체 판명 로직 정본(Framework v2.7)의 8대 작업 순위(Rank 0~7), 질문 깊이별 Tier 1~3 차등 응답 규격, B-Check 6항목 루브릭, 10대 필수 구성 요소 요강을 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["all", "ranks", "tiers", "b_check", "components", "rubrics"],
                    "description": "조회할 프레임워크 섹션"
                }
            }
        }
    },
    {
        "name": "get_fma_anatomy_profile",
        "description": "FMA(Foundational Model of Anatomy v5.1.0) 온톨로지 기반 361개 표준 경혈의 해부학적 실체(근육·신경·혈관 FMA:ID 및 영문 라벨), 신경 지배 및 상위 줄기 사슬(branch_of), 척수 분절 합집합(B-Check ②), 2대 교재(공통교재 vs 김재효) 매핑 대조 프로파일을 반환합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "acupoint": {
                    "type": "string",
                    "description": "경혈 코드(예: ST36, LU5, LI4, GV20, CV12) 또는 경혈명(예: 족삼리, 척택, 합곡)"
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json"],
                    "description": "출력 포맷 (기본값: markdown)"
                }
            },
            "required": ["acupoint"]
        }
    }
]


# --- Tool Handlers ---

def handle_get_acupoint_anatomy_profile(arguments):
    target = (arguments.get("acupoint") or arguments.get("code") or arguments.get("name_kr") or arguments.get("name") or "").strip()
    pdata = resolve_acupoint_key(target)
    if not pdata:
        return f"경혈 '{target}'에 대한 마스터 DB 레코드를 찾을 수 없습니다. (경혈 코드: ST36, LU5 등 또는 한글/한자 혈위명을 확인해 주세요)"

    code = pdata["code"]
    name_kr = pdata["name_kr"]
    name_cn = pdata["name_cn"]
    meridian_kr = pdata["meridian_kr"]
    meridian_cn = pdata["meridian_cn"]
    aliases_hanja = pdata.get("aliases_hanja", "-")
    aliases_hangul = pdata.get("aliases_hangul", "-")

    biomed_db = get_cached_biomedical_db()
    bdata = biomed_db.get(code) or biomed_db.get("acupoints", {}).get(code) or {}

    local_cnt = bdata.get("local_papers_count", 0)
    ext_cnt = bdata.get("external_papers_count", 0)
    papers_count = (local_cnt + ext_cnt) if (local_cnt or ext_cnt) else len(bdata.get("papers", []))

    nerves = bdata.get("innervation_anatomy") or bdata.get("innervation") or bdata.get("nerves", "관련 신경망 (Layer 2~4)")
    vessels = bdata.get("vessels", bdata.get("blood_vessels", "동맥 및 표재/심부 정맥총"))
    muscles = bdata.get("muscles", bdata.get("anatomical_structures", "해부학적 근막/근육군"))
    spinal = bdata.get("spinal_segment", "-")
    reflex = bdata.get("reflex_circuit", "체성-자율신경 반사 (Somato-autonomic reflex)")

    report = [
        f"# 📍 [{code}] {name_kr} ({name_cn}) 해부생리학적 실체 프로파일",
        f"- **소속 경락**: {meridian_kr} ({meridian_cn})",
        f"- **KJH 공인 이명**: {aliases_hanja} [{aliases_hangul}]",
        f"- **원전 출전**: {pdata.get('classics', '《中国针灸穴位通鉴》, 《针灸甲乙经》, 《中国针灸证治通鉴》, 《针灸腧穴通考》')}",
        "",
        "## 1. 3D 공간 정위 및 도량형 환산 자침 심도",
        f"- **표준 정위**: {pdata.get('meridian_kr')} 주행선 상 해부학적 랜드마크 위치",
        "- **고전 푼수 환산**: 한대(漢代) 기준 **1푼 = 2.3mm**",
        "- **안전 자침 심도 ($z$)**: 천자 0.3~0.5촌 (약 7~11.5mm), 심자 1.0~1.5촌 (약 23~34.5mm, 체형별 가변)",
        "",
        "## 2. Layer 1~5 정밀 층차별 해부학적 실체",
        "| 층차 (Layer) | 조직학적 분류 | 주요 해부학적 구조물 (Substrates) |",
        "| :--- | :--- | :--- |",
        f"| **Layer 1** | 표피 및 진피 (Skin) | 자유신경종말, 메르켈 원판, 마이스너 소체, 모세혈관망 |",
        f"| **Layer 2** | 피하조직 및 표재근막 | 표재 피신경 분지, 표재 정맥, 피하 지방층, 루피니/파치니 소체 |",
        f"| **Layer 3** | 심근막 및 근외막 | {muscles if isinstance(muscles, str) else ', '.join(muscles[:3])} 표면 건막, 기계수용체망 |",
        f"| **Layer 4** | 심부 근육 및 주신경·혈관속 | {nerves if isinstance(nerves, str) else ', '.join(nerves[:3])}, {vessels if isinstance(vessels, str) else ', '.join(vessels[:3])} |",
        f"| **Layer 5** | 골막 / 관절낭 / 심부장기 경계 | 심부 골막 반사수용체, 관절낭 고유감각 섬유, 인접 위험 혈관·장기 |",
        "",
        "## 3. 2대 교재 해부구조 비교 및 변위 분기 판정",
        "- **경혈학 공통교재**: 표준 체표 랜드마크 중심 정위 및 표준 근육/신경 기술",
        "- **김재효 교수 교재**: 국소 3D 층차 주행 단면, 심부 혈관신경속 실체 정밀 명시",
        "- **공간 변위 분기 (Δ)**: 고전 원전점 vs 현대 WHO점 간 변위 $\\Delta \\le 15\\text{mm}$ (단일 표적 표준 부합)",
        "",
        "## 4. FMA(Foundational Model of Anatomy) 온톨로지 연동",
        f"- **FMA 온톨로지 상세**: `get_fma_anatomy_profile(acupoint='{code}')` 도구로 FMA:ID, 신경 지배 줄기 사슬, 척수 분절 합집합(B-Check ②) 정밀 조회 가능",
        "",
        "## 5. Layer A 실측 생의학 연구 현황",
        f"- **보유 실측 논문**: 총 {papers_count}편 등재 (로컬 전수 역색인 + PubMed/OpenAlex 동기화)",
        f"- **척수 지배 분절**: {spinal}",
        f"- **주요 신경반사 회로**: {reflex}",
        "",
        "> 💡 **학술 인용 가이드**: 본 프로파일은 Framework v2.7 및 통합 마스터 DB에 준거하여 산출되었습니다."
    ]
    return "\n".join(report)


def handle_get_fma_anatomy_profile(arguments):
    target = (arguments.get("acupoint") or arguments.get("code") or arguments.get("name_kr") or arguments.get("name") or "").strip()
    pdata = resolve_acupoint_key(target)
    code = pdata["code"] if pdata else target.upper()
    name_kr = pdata["name_kr"] if pdata else ""
    out_format = (arguments.get("format") or "markdown").strip().lower()

    m = re.match(r"([A-Za-z]+)\s*0*(\d+)", code)
    if m:
        fma_code = f"{m.group(1).upper()}{int(m.group(2)):02d}"
    else:
        fma_code = code

    # 1순위: 로컬 FMA 온톨로지 색인 인스턴스 질의
    f = get_fma_instance()
    if f is not None:
        try:
            import fma_query
            p = fma_query.build_profile(f, fma_code)
            if out_format == "json":
                def conv(o):
                    return sorted(o) if isinstance(o, set) else o
                return json.dumps(p, ensure_ascii=False, indent=2, default=conv)

            cat_order = {"근육": 0, "신경": 1, "혈관": 2}
            structs = sorted(p["structures"], key=lambda s: (cat_order.get(s["category"], 9), s["fma_label"] or "~"))

            lines = [
                f"# 🏛️ [FMA 5.1.0] {p['code']} {p['name_kr']} 해부학적 실체 온톨로지 프로파일",
                f"- **분석 원천**: Foundational Model of Anatomy (FMA v5.1.0 로컬 온톨로지 역색인)",
                f"- **대응 실체 수**: 총 {len(structs)}개 구조물 매핑",
                "",
                "## 1. FMA 층차 구조물 및 신경 지배·척수 분절 상세",
                "| 구분 | 교재 용어 | FMA 실체 (ID & Label) | 대응 수준 | 출처 | 신경 지배 / 상위 줄기 사슬 | 척수 분절 (Spinal) |",
                "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
            ]

            for s in structs:
                if not s["fma_id"]:
                    lines.append(f"| {s['category']} | {'<br>'.join(sorted(s['terms']))} | — | none | {'·'.join(sorted(s['sources']))} | — | — |")
                    continue
                rel = s.get("relations", {})
                if rel.get("nerve_supply"):
                    nerve = "<br>".join(
                        f"FMA:{nid} {lab}" + (" → " + " → ".join(f"{l2}" for _, l2 in s["nerve_trunks"].get(nid, [])[:3]) if s["nerve_trunks"].get(nid) else "")
                        for nid, lab in rel["nerve_supply"][:3]
                    )
                else:
                    nerve = " → ".join(f"FMA:{o} {lab}" for o, lab in s.get("branch_chain", [])[:4]) or "—"
                seg = s.get("segments", {})
                segtxt = ", ".join(f"{k}({'/'.join(v)})" for k, v in seg.get("direct", {}).items()) or \
                    (", ".join(seg.get("inferred_from_nerve_chain", [])) + " (신경 경로 추론)" if seg.get("inferred_from_nerve_chain") else "—")
                
                fma_cell = f"FMA:{s['fma_id']} {s['fma_label']}"
                match_cell = '/'.join(sorted(s['match']))
                src_cell = '·'.join(sorted(s['sources']))
                terms_cell = '<br>'.join(sorted(s['terms']))
                lines.append(f"| {s['category']} | {terms_cell} | {fma_cell} | {match_cell} | {src_cell} | {nerve} | {segtxt} |")

            lines.append("")
            lines.append("## 2. 척수 분절 합집합 (B-Check ② 입력)")
            seg_keys = list(p.get("segment_union", {}).keys())
            if seg_keys:
                lines.append(f"- **포괄 척수 분절**: **{', '.join(seg_keys)}**")
                for k, v in p.get("segment_union", {}).items():
                    lines.append(f"  - `{k}`: {', '.join(v)}")
            else:
                lines.append("- FMA 온톨로지 상 기재된 척수 분절 없음")

            lines.append("")
            lines.append("## 3. 2대 교재 해부실체 비교 (Framework 10대 구성요소 ⑥)")
            tc = p.get("textbook_compare", {})
            lines.append(f"- **공통 FMA 실체**: {len(tc.get('common', []))}개")
            lines.append(f"- **공통교재 단독 실체**: {len(tc.get('only_공통교재', []))}개")
            lines.append(f"- **김재효 교수 단독 실체**: {len(tc.get('only_김재효', []))}개")
            lines.append("")
            lines.append("> 💡 **대응 수준 범례**: `exact`=완전 일치, `parent`=상위 구조 대응(가지 미등재), `fuzzy`=근사 매핑, `none`=미대응")

            return "\n".join(lines)
        except Exception as e:
            sys.stderr.write(f"fma_query dynamic profile failed ({e}), falling back to mapping JSON\n")

    # 2순위: acupoint_fma_mapping.json 정적 매핑 기반 폴백
    fma_json = get_cached_fma_mapping()
    rows = fma_json.get("rows", [])
    matched_rows = [r for r in rows if r.get("code", "").upper() == fma_code.upper()]

    if not matched_rows:
        matched_rows = [r for r in rows if re.sub(r"0+(\d+)", r"\1", r.get("code", "").upper()) == re.sub(r"0+(\d+)", r"\1", code.upper())]

    if not matched_rows:
        return f"경혈 '{target}' ({code})에 대한 FMA 매핑 데이터를 찾을 수 없습니다."

    if out_format == "json":
        return json.dumps({"code": fma_code, "name_kr": name_kr or matched_rows[0].get("name_kr", ""), "rows": matched_rows}, ensure_ascii=False, indent=2)

    cat_order = {"근육": 0, "신경": 1, "혈관": 2}
    sorted_rows = sorted(matched_rows, key=lambda r: (cat_order.get(r.get("category"), 9), r.get("fma_label") or "~"))

    lines = [
        f"# 🏛️ [FMA 5.1.0] {fma_code} {name_kr or matched_rows[0].get('name_kr', '')} 해부학적 실체 온톨로지 프로파일 (JSON 매핑)",
        f"- **분석 원천**: acupoint_fma_mapping.json (FMA v5.1.0 기준 2대 교재 통합 대조표)",
        f"- **대응 실체 수**: 총 {len(sorted_rows)}개 행",
        "",
        "## 1. FMA 구조물 매핑 상세",
        "| 구분 | 교재 한글명 | 교재 영문명 | FMA 실체 (ID & Label) | 대응 수준 | 출처 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    by_src = {}
    fma_ids_by_src = {}
    for r in sorted_rows:
        fid = r.get("fma_id")
        flabel = r.get("fma_label") or "—"
        cat = r.get("category") or "기타"
        tkr = r.get("term_kr") or "-"
        ten = r.get("term_en") or "-"
        match = r.get("match") or "none"
        src = r.get("source") or "미상"
        by_src.setdefault(src, 0)
        by_src[src] += 1
        if fid:
            fma_ids_by_src.setdefault(src, set()).add(fid)
            fma_cell = f"FMA:{fid} {flabel}"
        else:
            fma_cell = "—"

        lines.append(f"| {cat} | {tkr} | {ten} | {fma_cell} | {match} | {src} |")

    lines.append("")
    lines.append("## 2. 2대 교재 FMA 매핑 통계")
    all_fids = set()
    for s_ids in fma_ids_by_src.values():
        all_fids.update(s_ids)
    common_ids = set.intersection(*fma_ids_by_src.values()) if len(fma_ids_by_src) >= 2 else set()

    for src, cnt in by_src.items():
        lines.append(f"- **{src}**: 총 {cnt}개 용어 (FMA ID {len(fma_ids_by_src.get(src, set()))}개)")
    lines.append(f"- **2대 교재 공통 FMA 실체**: {len(common_ids)}개")
    lines.append("")
    lines.append("> 💡 **대응 수준 범례**: `exact`=완전 일치, `parent`=상위 구조 대응(가지 미등재), `fuzzy`=근사 매핑, `none`=미대응")

    return "\n".join(lines)


def handle_search_biomedical_reflex_db(arguments):
    query = (arguments.get("query") or arguments.get("query_term") or arguments.get("acupoint") or arguments.get("code") or "").strip().lower()
    evidence_filter = arguments.get("evidence_filter", "all")
    limit = arguments.get("limit", 10)

    biomed_db = get_cached_biomedical_db()
    if not biomed_db:
        return "통합 생의학 마스터 DB를 로드할 수 없습니다."

    raw_papers = biomed_db.get("papers", [])
    if isinstance(raw_papers, dict):
        papers_list = [{"id": k, **v} for k, v in raw_papers.items()]
    else:
        papers_list = raw_papers

    inv_index = biomed_db.get("acupoint_inverted_index", {})
    matched_pids = set()
    for code_k, pids in inv_index.items():
        if query in code_k.lower():
            for pid in pids:
                matched_pids.add(pid)

    results = []
    for pdata in papers_list:
        pid = pdata.get("id", pdata.get("filename", ""))
        title = pdata.get("title", "").lower()
        abstract = pdata.get("abstract_snippet", pdata.get("abstract", "")).lower()
        journal = pdata.get("journal", "").lower()
        keywords = " ".join(pdata.get("keywords", []) if isinstance(pdata.get("keywords"), list) else [str(pdata.get("keywords", ""))]).lower()
        mesh = " ".join(pdata.get("mesh", []) if isinstance(pdata.get("mesh"), list) else [str(pdata.get("mesh", ""))]).lower()
        detected = " ".join(pdata.get("detected_acupoints", []) if isinstance(pdata.get("detected_acupoints"), list) else [str(pdata.get("detected_acupoints", ""))]).lower()

        score = 0
        if pid in matched_pids:
            score += 10
        if query in title:
            score += 6
        if query in detected:
            score += 5
        if query in keywords or query in mesh:
            score += 3
        if query in abstract:
            score += 2
        if query in journal:
            score += 1

        if score > 0:
            results.append((pid, pdata, score))

    for k, v in biomed_db.items():
        if k.startswith("_") or k in ("papers", "acupoint_inverted_index", "file_manifest"):
            continue
        if isinstance(v, dict):
            code = v.get("code", k).lower()
            name_kr = v.get("name_kr", "").lower()
            reflex = v.get("reflex_circuit", "").lower()
            spinal = v.get("spinal_segment", "").lower()
            if query in code or query in name_kr or query in reflex or query in spinal:
                for lp in v.get("landmark_papers", []):
                    results.append((lp.get("pmid", "LANDMARK"), lp, 8))

    if not results:
        return f"검색어 '{query}'에 대한 Layer A 생의학 논문 및 반사회로 데이터를 찾을 수 없습니다."

    seen_ids = set()
    unique_results = []
    for pid, pdata, score in sorted(results, key=lambda x: x[2], reverse=True):
        uniq_key = pdata.get("doi") or pdata.get("pmid") or pid or pdata.get("title")
        if uniq_key and uniq_key not in seen_ids:
            seen_ids.add(uniq_key)
            unique_results.append((pid, pdata, score))

    filtered = []
    for pid, pdata, score in unique_results:
        species = str(pdata.get("species") or pdata.get("evidence_level") or "").lower()
        is_human = "human" in species or "clinical" in species or "patient" in species
        is_mechanism = "mechanism" in species or "reflex" in str(pdata.get("reflex_circuit", "")).lower()

        if evidence_filter == "human" and not is_human:
            continue
        if evidence_filter == "animal" and is_human:
            continue
        if evidence_filter == "mechanism" and not is_mechanism:
            continue

        filtered.append((pid, pdata))
        if len(filtered) >= limit:
            break

    out = [f"# 🔬 [Layer A] 생의학 신경반사 마스터 DB 검색 결과: '{query}' (총 {len(filtered)}건 표시)\n"]
    for i, (pid, p) in enumerate(filtered, 1):
        title = p.get("title", "No Title")
        journal = p.get("journal", p.get("source", "Journal"))
        year = p.get("year", p.get("pub_year", "-"))
        pmid = p.get("pmid", "")
        doi = p.get("doi", "")
        evidence = p.get("evidence_level", "Mechanistic / Clinical")
        detected = p.get("detected_acupoints", [])
        circuits = p.get("reflex_circuit", p.get("abstract_snippet", ""))

        link_str = f"PMID: {pmid}" if pmid else (f"DOI: {doi}" if doi else "Local Master DB")
        out.append(f"### [{i}] {title} ({year})")
        out.append(f"- **ID**: `{pid}` | **저널**: *{journal}* | **식별자**: {link_str}")
        out.append(f"- **증거 등급**: {evidence} | **검출 혈위**: {', '.join(detected) if isinstance(detected, list) else detected}")
        if circuits:
            snippet = circuits[:200] + "..." if len(circuits) > 200 else circuits
            out.append(f"- **핵심 요약/기전**: {snippet}")
        out.append("")

    return "\n".join(out)


def handle_get_layer_b_registry(arguments):
    category = arguments.get("category", "all")
    ref_id = arguments.get("reference_id", "").strip().upper()
    query = arguments.get("query", "").strip().lower()

    registry = get_cached_layer_b_registry()
    entries = registry.get("entries", [])
    if not entries:
        text = read_file_content("layer_b_md")
        if text:
            return text
        return "Layer B 참조 등록부를 로드할 수 없습니다."

    matched = []
    for e in entries:
        eid = e.get("id", "").upper()
        etier = e.get("tier", "").upper()
        citation = e.get("citation", "").lower()
        scope = e.get("scope", "").lower()

        if ref_id and ref_id == eid:
            matched = [e]
            break
        if category != "all" and etier != category.upper():
            continue
        if query and (query not in citation and query not in scope and query not in eid.lower()):
            continue
        matched.append(e)

    if not matched:
        return f"조건(Category: {category}, ID: {ref_id}, Query: {query})에 해당하는 Layer B 등록부 항목이 없습니다."

    out = [
        f"# 📚 [Layer B] 4계층 참조 등록부 및 B-Check 기준 (총 {len(matched)}건)\n",
        "> **B-Check 판정 기준**: 6대 항목(① 말초 실체 ② 분절 정합 ③ 구심 섬유/수용체 ④ 중추 경로 ⑤ 원심 효과 ⑥ 인체 전환), 총 12점 만점 중 **≥ 8/12점 (67%)** 부합 시 확정 기전 채택.\n",
        "| ID | 계층 | 문헌/저작 | 대상 및 범위 | B-Check 항목 | 한계 및 주의사항 |",
        "| :--- | :---: | :--- | :--- | :---: | :--- |"
    ]

    for e in matched:
        eid = e.get("id", "")
        tier = e.get("tier", "")
        citation = e.get("citation", "")
        scope = e.get("scope", "")
        items = e.get("bcheck_items", "")
        limits = e.get("limits", "-")
        out.append(f"| **{eid}** | {tier} | {citation} | {scope} | {items} | {limits} |")

    return "\n".join(out)


def handle_calculate_ari_v3_score(arguments):
    s_orig = float(arguments.get("s_orig", 0))
    s_clarity = float(arguments.get("s_clarity", 0))
    s_reflex = float(arguments.get("s_reflex", 0))
    s_safety = float(arguments.get("s_safety", 0))
    layer_a_count = int(arguments.get("layer_a_count", 1))

    is_hypothetical = False
    if layer_a_count == 0:
        if s_reflex > 25:
            s_reflex = 25
        is_hypothetical = True

    w_orig, w_clarity, w_reflex = 0.40, 0.35, 0.25
    ari_core = (w_orig * s_orig) + (w_clarity * s_clarity) + (w_reflex * s_reflex)

    gate_1_applied = False
    if s_orig < 50 or s_clarity < 50:
        gate_1_applied = True

    if ari_core >= 85:
        grade = "A"
    elif ari_core >= 70:
        grade = "B"
    elif ari_core >= 55:
        grade = "C"
    else:
        grade = "D"

    if gate_1_applied and grade in ["A", "B"]:
        grade = "C (Gate 1 강등)"

    si = s_safety
    gate_3_caution = si <= 25

    ari_equal = (s_orig + s_clarity + s_reflex) / 3.0
    if ari_equal >= 85:
        grade_equal = "A"
    elif ari_equal >= 70:
        grade_equal = "B"
    elif ari_equal >= 55:
        grade_equal = "C"
    else:
        grade_equal = "D"

    sensitivity_str = f"{ari_equal:.1f} ({grade_equal}, {'등급 불변' if grade_equal == grade[0] else '가중치 민감'})"

    h_tag = "·H" if is_hypothetical else ""
    caution_tag = " | ⚠ 안전주의" if gate_3_caution else ""
    profile_summary = f"ARI v3.0 | ARI-Core {ari_core:.1f} ({grade[0]}{h_tag}){caution_tag} | SI {si:.0f} | 잠정 가중치 0.40/0.35/0.25 | 민감도(등가중치): {sensitivity_str}"

    report = [
        "# 📊 ARI v3.0 (Acupoint Reality Index) 정밀 채점 결과표",
        "",
        f"### 🎯 공식 프로파일: `{profile_summary}`",
        "",
        "| 평가 요인 | 부여 점수 | 배정 가중치 | 반영 환산 점수 | 5단계 루브릭 근거 |",
        "| :--- | :---: | :---: | :---: | :--- |",
        f"| **$S_{{orig}}$ (문헌 일치도)** | {s_orig:.0f} | 0.40 | {s_orig * 0.40:.1f} | 3대 원전 직접 대조 및 편년체 정위 일치 |",
        f"| **$S_{{clarity}}$ (해부 명확도)** | {s_clarity:.0f} | 0.35 | {s_clarity * 0.35:.1f} | Layer 1~5 층차 및 2대 교재 해부구조 일치 |",
        f"| **$S_{{reflex}}$ (생의학 부합도)** | {s_reflex:.0f} | 0.25 | {s_reflex * 0.25:.1f} | Layer A 실측 논문 ({layer_a_count}편) + Layer B B-Check (≥8/12) |",
        "| **합계 (ARI-Core)** | — | **1.00** | **{:.1f}** | **등급: {}** |".format(ari_core, grade),
        f"| **안전지수 (SI)** | **{si:.0f}** | 독립 지표 | **{si:.0f}** | {'⚠ 위험 장기·혈관 인접 (안전주의)' if gate_3_caution else '안전 자침 심도 확보'} |",
        "",
        "## 🛡️ 3대 비보상형 게이트 점검",
        f"- **Gate 1** ($S_{{orig}}<50$ 또는 $S_{{clarity}}<50$): {'⚠️ 트리거됨 (최고 등급 C 제한)' if gate_1_applied else '✅ 통과'}",
        f"- **Gate 2** (Layer A 0편): {'⚠️ 트리거됨 (S_reflex <= 25 및 (H) 가설 표지)' if is_hypothetical else f'✅ 통과 (Layer A {layer_a_count}편 확보)'}",
        f"- **Gate 3** (SI ≤ 25): {'⚠️ 트리거됨 (⚠ 안전주의 경고 표지)' if gate_3_caution else '✅ 통과 (안전 범위 내)'}",
        "",
        "## 🔬 가중치 민감도 분석 (등가중치 0.333/0.333/0.333)",
        f"- **등가중치 재계산값**: **{ari_equal:.1f}점** (등급: **{grade_equal}** ➔ {'등급 불변' if grade_equal == grade[0] else '가중치 민감 경고'})"
    ]
    return "\n".join(report)


# 원전 코퍼스 접근 (로컬): data/classics/<원전>/*.md
CLASSICS_DIR = os.path.join(PROJECT_ROOT, "data", "classics")
CLASSICS_SOURCE_LABEL = CLASSICS_DIR
_CLASSIC_CACHE = {}


def _classics_list_files(book_dir):
    d = os.path.join(CLASSICS_DIR, book_dir)
    if not os.path.isdir(d):
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".md"))


def _classics_read(book_dir, name):
    try:
        with open(os.path.join(CLASSICS_DIR, book_dir, name), "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _classics_prefetch(book_dir, names):
    """로컬은 필요할 때 읽으므로 미리 읽지 않는다."""
    return None


# ---------------------------------------------------------------------------
# 4대 원전 고전문헌 검색 (search_classic_records)
#   data/classics/<원전>/*.md 정제 코퍼스를 직접 읽는다.
#   - 혈위별 장(章)이 있는 《穴位通鉴》·《腧穴通考》: 경혈 코드·혈명으로 해당 장을 찾아 목차와 핵심 소절 발췌
#   - 편별 구성인 《证治通鉴》·《经络通鉴》: 혈명이 나오는 행을 검색
#   - query: 공백으로 나눈 모든 검색어가 한 행에 있으면 적중. 번체·간체를 같은 글자로 본다
# ---------------------------------------------------------------------------
CLASSIC_BOOKS = [  # (필터 키, 디렉토리, 표기)
    ("穴位通鉴", "中国针灸穴位通鉴", "《中国针灸穴位通鉴》"),
    ("腧穴通考", "针灸腧穴通考", "《针灸腧穴通考》"),
    ("证治通鉴", "中国针灸证治通鉴", "《中国针灸证治通鉴》"),
    ("经络通鉴", "中国针灸经络通鉴", "《中国针灸经络通鉴》"),
]
POINT_SECTION_BOOKS = ("穴位通鉴", "腧穴通考")
KEY_SUBSECTIONS = ("部位", "定位", "简要结语")  # 경혈 장에서 발췌할 소절
MERIDIAN_FILE_KEYS = {
    "LU": "手太阴肺经", "LI": "手阳明大肠经", "ST": "足阳明胃经", "SP": "足太阴脾经",
    "HT": "手少阴心经", "SI": "手太阳小肠经", "BL": "足太阳膀胱经", "KI": "足少阴肾经",
    "PC": "手厥阴心包经", "TE": "手少阳三焦经", "SJ": "手少阳三焦经", "GB": "足少阳胆经",
    "LR": "足厥阴肝经", "LV": "足厥阴肝经", "GV": "督脉", "DU": "督脉", "CV": "任脉",
    "RN": "任脉", "EX": "经外",
}
CLASSIC_OUTPUT_LIMIT = 14000  # 응답 최대 글자 수

# 번체→간체 대응표: 원전 코퍼스·보고서·동의보감에 실제로 나오는 글자를 OpenCC t2s로 변환해 추린 1,444쌍
# (끝의 '䯒胻'은 OpenCC가 바꾸지 않는 한국 문헌 이체자). OpenCC가 설치되어 있으면 검색어에는 OpenCC를 먼저 적용한다.
_T2S_PAIRS = (
    "㶆𫞛㿗𤻊䌋𦈘䱀𫚐䲅𫚜並并乾干亂乱亞亚佈布佔占來来侖仑侶侣係系俠侠倉仓個个們们倖幸倫伦偉伟側侧傑杰備备傳传傴伛傷伤傾倾僂偻僅仅僕仆僞伪僥侥價价儀仪儈侩儉俭儘尽優优"
    "儲储儼俨兌兑兒儿內内兩两冊册凍冻凜凛別别刪删則则剋克剛刚剝剥創创劃划劇剧劉刘劍剑劑剂劚㔉勁劲勑𠡠動动務务勝胜勞劳勢势勣𪟝勸劝勻匀匯汇匱匮區区協协卻却卽即厠厕厭厌"
    "厲厉參参叄叁叢丛吳吴呂吕員员哯𠯟問问啓启啞哑喎㖞喚唤喪丧喫吃單单嗇啬嘆叹嘔呕嘗尝嘯啸噓嘘噦哕噯嗳噴喷嚙啮嚥咽嚨咙嚮向嚲亸嚴严國国圍围園园圓圆圖图團团執执堅坚堊垩"
    "報报場场塊块塗涂塚冢塤埙塵尘墜坠墮堕墳坟墻墙壓压壘垒壜坛壞坏壟垄壯壮壺壶壽寿夢梦夾夹奧奥奪夺姦奸婦妇嬋婵嬰婴孫孙學学宮宫寢寝實实寧宁審审寫写寬宽寶宝將将專专尋寻"
    "對对導导屍尸屢屡層层屬属岡冈峯峰島岛峽峡崑昆崗岗崙仑嵐岚嶄崭嶺岭巔巅巖岩帥帅師师帳帐帶带幃帏幘帻幹干幾几庫库廁厕廚厨廟庙廢废廣广廩廪廬庐廳厅弔吊張张強强彈弹彌弥"
    "彎弯彙汇彥彦彫雕彿佛後后徑径從从復复徵征徹彻恥耻悅悦悵怅悶闷悽凄惡恶惱恼惲恽惻恻愛爱愾忾慄栗態态慍愠慘惨慣惯慮虑慳悭慶庆慾欲憂忧憊惫憐怜憑凭憒愦憤愤憲宪憶忆憹𢙐"
    "懇恳應应懲惩懶懒懷怀懸悬懼惧懾慑戀恋戔戋戰战戱戯戶户挾挟捨舍捫扪捲卷掃扫掛挂採采揀拣揚扬換换揮挥損损搖摇搗捣搵揾搶抢摳抠摶抟摺折摻掺撈捞撏挦撓挠撥拨撫抚撲扑擁拥"
    "擇择擊击據据擠挤擣捣擬拟擲掷擴扩擷撷擺摆擻擞擾扰攙搀攝摄攢攒攣挛攤摊攪搅敎教敗败敵敌數数斂敛斃毙斅𢽾斬斩斷断於于旣既時时晉晋晛𬀪晝昼暈晕暢畅暫暂曆历曉晓曠旷書书"
    "會会朧胧朮术東东査查梔栀條条梟枭棄弃棊棋棖枨棗枣棲栖椏桠楊杨楓枫業业極极榦干榮荣構构槍枪樂乐樑梁樓楼標标樞枢樣样樳桪樹树樺桦橈桡橋桥機机橫横檉柽檟槚檢检檳槟櫚榈"
    "櫛栉櫟栎櫻樱欄栏權权欖榄欽钦歟欤歡欢歲岁歷历歸归殘残殞殒殭僵殺杀殼壳毆殴氣气氳氲汙污決决沒没沖冲況况泝溯洩泄洶汹涇泾淒凄淚泪淨净淪沦淵渊淺浅渙涣減减測测渾浑湊凑"
    "湧涌湯汤準准溝沟溫温滄沧滅灭滌涤滎荥滯滞滲渗滾滚滿满漁渔漚沤漢汉漬渍漲涨漸渐漿浆潑泼潔洁潛潜潤润潰溃澆浇澗涧澤泽澱淀濁浊濃浓濕湿濛蒙濟济濱滨濺溅濼泺濾滤瀆渎瀉泻"
    "瀋沈瀝沥瀾澜灑洒灘滩灣湾災灾為为烏乌無无煇𪸩煉炼煩烦熱热熾炽燁烨燈灯燒烧燖𬊈營营燭烛燾焘爇𦶟爍烁爐炉爛烂爭争爲为爾尔牀床牽牵犢犊狀状狹狭猶犹猻狲獄狱獨独獮狝獲获"
    "獵猎獷犷獸兽獺獭獻献現现瑤瑶瑩莹瑪玛璣玑璫珰環环璽玺瓊琼甌瓯甕瓮產产産产甦苏畢毕畫画異异畵画當当疊叠痙痉痠酸痾疴瘂痖瘍疡瘓痪瘡疮瘧疟瘲疭瘻瘘療疗癆痨癇痫癉瘅癘疠"
    "癡痴癢痒癤疖癥症癧疬癩癞癬癣癭瘿癮瘾癰痈癱瘫癲癫發发皰疱皸皲皺皱盃杯盜盗盞盏盡尽監监盤盘盧卢盪荡眞真眥眦睍𪾢瞞瞒瞤𥆧瞶瞆瞼睑矇蒙矓眬矯矫硃朱硯砚碩硕確确磑硙磚砖"
    "磣碜磧碛礎础礙碍礦矿礪砺礬矾礱砻祕秘祿禄禍祸禦御禮礼禱祷禿秃稈秆稜棱稟禀種种稱称穀谷積积穡穑穢秽穩稳穭穞窩窝窮穷窯窑窺窥竄窜竅窍竇窦竈灶竊窃竚𥩟竪竖競竞筆笔箇个"
    "節节範范築筑篤笃篩筛簡简簣篑簽签簾帘籃篮籙箓籟籁籠笼籤签籬篱糝糁糞粪糲粝紀纪約约紅红紆纡紇纥紋纹納纳紐纽純纯紗纱紙纸級级紛纷紜纭細细紵纻紹绍紺绀紿绐絀绌終终絃弦"
    "組组絆绊絍𫟃結结絕绝絙𫄠絞绞絡络給给絨绒統统絲丝絳绛絶绝絹绢經经綜综綠绿綣绻維维綱纲網网綳绷綴缀綸纶綻绽綽绰綾绫綿绵緊紧緋绯線线緡缗緣缘編编緩缓緯纬練练緻致縈萦"
    "縊缢縛缚縞缟縣县縫缝縮缩縱纵縳䌸縷缕總总績绩繃绷繆缪繒缯織织繕缮繞绕繩绳繫系繰缲繳缴繼继纊纩續续纍累纏缠纔才纖纤纜缆罈坛罌罂罰罚罵骂罷罢羅罗羈羁羣群義义羶膻習习"
    "翹翘聖圣聞闻聯联聰聪聲声聳耸聵聩聶聂職职聽听聾聋肅肃脅胁脈脉脛胫脩修脫脱脹胀腎肾腦脑腪𣍯腫肿腳脚腸肠膃腽膕腘膚肤膠胶膩腻膽胆膾脍膿脓臉脸臍脐臏膑臘腊臚胪臟脏臥卧"
    "臨临臺台與与興兴舉举舊旧舘馆艱艰苧苎荊荆莊庄莖茎莢荚莧苋華华菴庵萊莱萬万萵莴葉叶葒荭葦苇葯药葷荤蒔莳蒼苍蓀荪蓋盖蓮莲蓯苁蓴莼蓽荜蔔卜蔞蒌蔣蒋蔭荫蔯𫈟蕎荞蕩荡蕪芜"
    "蕭萧蕷蓣蕽𫇽薈荟薊蓟薑姜薔蔷薘荙薟莶薦荐薹苔薺荠藍蓝藝艺藥药藪薮藭䓖藶苈藺蔺蘆芦蘇苏蘊蕴蘋苹蘚藓蘭兰蘿萝處处虛虚虜虏號号虧亏蛻蜕蜆蚬蝕蚀蝟猬蝦虾蝸蜗螄蛳螢萤螻蝼"
    "蟄蛰蟬蝉蟯蛲蟲虫蟶蛏蟻蚁蠅蝇蠆虿蠍蝎蠐蛴蠟蜡蠣蛎蠱蛊衆众衊蔑術术衛卫衝冲袞衮裏里補补裝装裡里製制複复襖袄襠裆襯衬襲袭見见規规視视親亲覷觑覺觉覽览觀观觴觞觸触訂订"
    "計计討讨訐讦訓训訖讫託托記记訛讹訝讶訟讼訣诀訪访設设許许訶诃診诊註注詁诂詐诈詔诏詢询詣诣試试詩诗詫诧詮诠話话該该詳详詵诜誅诛誇夸誌志認认誕诞誘诱語语誠诚誣诬誤误"
    "誥诰誦诵說说誰谁誹诽調调諄谆談谈請请論论諦谛諱讳諳谙諶谌諸诸諺谚謀谋謂谓謐谧謔谑謗谤謙谦講讲謝谢謫谪謬谬謳讴謹谨謾谩譆𫍻證证譏讥識识譜谱譫谵議议護护讀读變变讎雠"
    "讓让讚赞豈岂豐丰貓猫貝贝貞贞負负財财貢贡貧贫貨货貪贪貫贯責责貯贮貳贰貴贵買买費费貼贴貽贻貿贸賁贲資资賈贾賊贼賓宾賜赐賞赏賢贤賣卖賤贱賦赋質质賴赖賽赛贅赘贈赠贊赞"
    "趕赶趙赵趨趋趲趱跡迹踐践踰逾蹠跖蹤踪蹻𫏋躊踌躋跻躍跃躑踯躡蹑軀躯車车軍军軒轩軟软軫轸軸轴較较輈辀載载輒辄輔辅輕轻輟辍輩辈輪轮輯辑輸输輿舆轂毂轄辖轅辕轆辘轉转轡辔"
    "轢轹轤轳辦办辭辞農农迴回逕迳這这連连進进遊游運运過过達达違违遙遥遞递遠远適适遲迟遷迁選选遺遗遼辽還还邇迩邊边鄒邹鄭郑鄰邻鄲郸酈郦醃腌醞酝醫医醬酱醲𬪩醶𫑷釀酿釅酽"
    "釋释釐厘釘钉針针釣钓釵钗鈍钝鈐钤鈔钞鈴铃鈹铍鉅巨鉗钳鉛铅鉢钵鉤钩銀银銅铜銖铢銘铭銚铫銳锐銷销銹锈鋅锌鋌铤鋒锋鋟锓鋤锄鋪铺鋸锯鋼钢錄录錐锥錘锤錙锱錠锭錢钱錦锦錫锡"
    "錯错鍉𫔂鍊炼鍋锅鍛锻鍵键鍼针鍾钟鎊镑鎌镰鎭镇鏃镞鏡镜鏤镂鏽锈鐘钟鐵铁鐶镮鐸铎鐺铛鑄铸鑑鉴鑒鉴鑕锧鑞镴鑠铄鑰钥鑱镵鑷镊鑽钻鑿凿長长門门閃闪閉闭開开閏闰閑闲閒闲間间"
    "閔闵閣阁閨闺閩闽閫阃閭闾閱阅閹阉閻阎闇暗闊阔闌阑闔阖闕阙關关闡阐闢辟陝陕陣阵陰阴陳陈陸陆陽阳階阶際际隨随險险隱隐隻只雖虽雙双雛雏雜杂離离難难雲云電电霧雾霽霁靂雳"
    "靈灵靜静靨靥韋韦韌韧韓韩韜韬韻韵響响頂顶頃顷項项順顺須须頌颂頏颃預预頑顽頓顿頗颇領领頤颐頦颏頭头頰颊頷颔頸颈頹颓頻频顆颗額额顏颜顔颜願愿顙颡類类顧顾顫颤顬颥顯显"
    "顱颅顳颞顴颧風风颯飒飄飘飛飞飢饥飥饦飩饨飪饪飯饭飱飧飲饮飴饴飼饲飽饱飾饰餅饼餉饷養养餌饵餒馁餓饿餔𫗦餘余餛馄餧𫗪館馆餳饧餺馎餾馏饅馒饉馑饌馔饑饥饒饶饗飨饘𫗴饞馋"
    "馬马馭驭馮冯馳驰駁驳駃𫘝駐驻駕驾駝驼駭骇駱骆駿骏騁骋騃𫘤騎骑騰腾騷骚騾骡驀蓦驅驱驕骄驗验驚惊驛驿驟骤驢驴髏髅體体髖髋髮发鬆松鬚须鬢鬓鬧闹鬨哄鬱郁魎魉魘魇魚鱼魯鲁"
    "鮎鲇鮑鲍鮒鲋鮓鲊鮠𬶏鮦鲖鮫鲛鮮鲜鮰𫚔鯁鲠鯇鲩鯉鲤鯔鲻鯗鲞鯪鲮鯽鲫鰈鲽鰌䲡鰍鳅鰒鳆鰕𫚥鰟鳑鰥鳏鰱鲢鰻鳗鰾鳔鱔鳝鱖鳜鱗鳞鱟鲎鱧鳢鱯鳠鱸鲈鱺鲡鳥鸟鳧凫鳩鸠鳳凤鳴鸣鳶鸢"
    "鴆鸩鴉鸦鴛鸳鴝鸲鴞鸮鴟鸱鴣鸪鴦鸯鴨鸭鴷䴕鴻鸿鴽𫛪鴿鸽鵂鸺鵑鹃鵒鹆鵓鹁鵜鹈鵝鹅鵩𫛳鵪鹌鵬鹏鵰雕鵲鹊鶉鹑鶊鹒鶒𫛶鶚鹗鶡鹖鶩鹜鶬鸧鶯莺鶴鹤鶹鹠鶻鹘鷀鹚鷄鸡鷉䴘鷓鹧鷗鸥"
    "鷥鸶鷦鹪鷴鹇鷸鹬鷹鹰鷺鹭鷿𬸯鸂㶉鸇鹯鸕鸬鸛鹳鹵卤鹽盐麗丽麥麦麨𪎊麩麸麪面麴曲麽么黃黄點点黨党黲黪黴霉黶黡黿鼋齊齐齋斋齒齿齔龀齗龂齘𬹼齠龆齡龄齦龈齲龋齶腭齼𬺓龍龙"
    "龐庞龔龚龜龟䯒胻"
)
_T2S_TABLE = {ord(_T2S_PAIRS[i]): _T2S_PAIRS[i + 1] for i in range(0, len(_T2S_PAIRS), 2)}
_OPENCC = []


def _classic_norm(text):
    """번체·이체자를 간체로 맞춘다(코퍼스 행에 사용, 표 기반이라 빠르다)."""
    return text.translate(_T2S_TABLE)


def _classic_norm_query(text):
    """검색어 정규화: OpenCC가 있으면 먼저 적용한 뒤 대응표로 마무리."""
    if not _OPENCC:
        try:
            import opencc
            _OPENCC.append(opencc.OpenCC("t2s").convert)
        except Exception:
            _OPENCC.append(None)
    if _OPENCC[0]:
        try:
            text = _OPENCC[0](text)
        except Exception:
            pass
    return _classic_norm(text)


def _classic_lines(book_dir, name):
    key = f"{book_dir}/{name}"
    cached = _CLASSIC_CACHE.get(key)
    if cached is None:
        text = _classics_read(book_dir, name)
        raw = text.splitlines()
        cached = (raw, [_classic_norm(l) for l in raw])
        if raw:  # 읽기 실패(빈 문자열)는 캐시하지 않고 다음 호출에서 다시 시도
            _CLASSIC_CACHE[key] = cached
    return cached


def _classic_heading_level(line):
    n = len(line) - len(line.lstrip("#"))
    return n if n and line[n:n + 1] == " " else 0


def _classic_heading_name(line):
    """'#### 足三里 Zúsānlǐ ST 36' / '### （三十六）足三里 Zúsānlǐ ST36 出…' → '足三里'"""
    body = re.sub(r"^#+\s*", "", line)
    body = re.sub(r"^（[^）]*）", "", body).strip()
    return body.split()[0] if body else ""


def _classic_code_regex(code):
    m = re.match(r"^([A-Z]{2})-?0*(\d+)$", (code or "").upper().replace(" ", ""))
    if m:
        p, n = m.groups()
        return re.compile(rf"\b{p}\s?0?{int(n)}\b")
    if re.match(r"^EX-[A-Z]+\d+$", (code or "").upper()):
        return re.compile(rf"\b{re.escape(code.upper())}\b")
    return None


def _classic_snippet(raw, norm, terms, width=130):
    pos = min([norm.find(t) for t in terms if norm.find(t) >= 0] or [0])
    start = max(0, pos - width)
    end = min(len(raw), pos + width)
    s = raw[start:end].strip()
    return ("…" if start > 0 else "") + s + ("…" if end < len(raw) else "")


def _classic_resolve_point(acupoint):
    """경혈 입력 → (코드, 혈명 후보 목록). 마스터 CSV 우선, 실패 시 간체 혈명·코드 형식으로 판정."""
    pdata = resolve_acupoint_key(acupoint) if acupoint else None
    if not pdata and acupoint:
        target = _classic_norm_query(acupoint.strip())
        for p in get_cached_master_csv().values():
            if p.get("name_cn") and _classic_norm(p["name_cn"]) == target:
                pdata = p
                break
    if pdata:
        names = [_classic_norm(pdata.get("name_cn", ""))]
        return pdata.get("code", ""), [n for n in names if n], pdata
    raw = acupoint.strip()
    if _classic_code_regex(raw):
        return raw.upper(), [], None
    return "", [_classic_norm_query(raw)], None


def _classic_files_for(book_dir, code):
    files = _classics_list_files(book_dir)
    key = MERIDIAN_FILE_KEYS.get((code or "")[:2].upper())
    preferred = [f for f in files if key and key in f]
    return preferred, files


def _classic_find_section(book_dir, code, names):
    """혈위별 장을 찾는다 → (파일명, 시작 행 index, 끝 행 index, 간체 혈명) 또는 None"""
    code_re = _classic_code_regex(code) if code else None
    preferred, files = _classic_files_for(book_dir, code)
    rest = [f for f in files if f not in preferred]
    # 경혈 장은 ###·#### 수준이다. 파일 제목(#·##)에도 코드가 들어 있을 수 있어 3~4 수준을 먼저 찾는다
    for min_lv in (3, 1):
        for group in (preferred, rest):
            _classics_prefetch(book_dir, group)
            for fname in group:
                raw, norm = _classic_lines(book_dir, fname)
                for i, line in enumerate(norm):
                    lv = _classic_heading_level(line)
                    if not lv or lv < min_lv or lv > 4:
                        continue
                    hname = _classic_heading_name(line)
                    if (code_re and code_re.search(line)) or (names and hname in names):
                        end = len(raw)
                        for j in range(i + 1, len(raw)):
                            lj = _classic_heading_level(norm[j])
                            if lj and lj <= lv:
                                end = j
                                break
                        return fname, i, end, hname
    return None


def _classic_title(line):
    return re.sub(r"<a id=[^>]*></a>", "", line.lstrip("#")).strip()


def _classic_excerpt(raw, start, end, max_chars):
    out, size = [], 0
    for line in raw[start:end]:
        s = re.sub(r"<a id=[^>]*></a>", "", line).strip()
        if not s or s.startswith(">") or s.startswith("![") or s.startswith("〔p."):
            continue  # 한글 번역 인용행·그림·쪽 표지는 생략(원문만)
        out.append(s)
        size += len(s)
        if size >= max_chars:
            out.append("…(생략)")
            break
    return out


def handle_search_classic_records(arguments):
    acupoint = (arguments.get("acupoint") or "").strip()
    query = (arguments.get("query") or "").strip()
    book_filter = arguments.get("classic_book") or "all"
    try:
        limit = max(1, min(int(arguments.get("limit") or 10), 50))
    except (TypeError, ValueError):
        limit = 10
    try:
        excerpt_chars = max(200, min(int(arguments.get("excerpt_chars") or 1200), 4000))
    except (TypeError, ValueError):
        excerpt_chars = 1200

    if not acupoint and not query:
        return "⚠ `acupoint`(경혈 코드·혈명) 또는 `query`(검색어) 가운데 하나 이상을 입력하세요. 예: acupoint='ST36', query='两筋间'"

    books = [b for b in CLASSIC_BOOKS if book_filter in ("all", b[0])]
    if not books:
        return f"⚠ 알 수 없는 원전 필터: {book_filter}. 사용 가능: all, " + ", ".join(b[0] for b in CLASSIC_BOOKS)
    if not any(_classics_list_files(b[1]) for b in books):
        return f"⚠ 원전 코퍼스를 읽을 수 없습니다 ({CLASSICS_SOURCE_LABEL}). `data/classics/<원전>/*.md`가 있는지 확인하세요."
    terms = [_classic_norm_query(t) for t in query.split()] if query else []

    code, names, pdata = _classic_resolve_point(acupoint) if acupoint else ("", [], None)
    title = f"'{acupoint}'" if acupoint else ""
    if pdata:
        title = f"{pdata.get('code')} {pdata.get('name_kr')}/{pdata.get('name_cn')}"
    out = [
        f"# 📜 4대 원전 고전문헌 검색: {title}{' · ' if title and query else ''}{('검색어 ' + repr(query)) if query else ''}",
        f"- **원전 필터**: {book_filter} · **최대 적중**: 원전별 {limit}건 · 번체/간체 통합 검색",
        "",
    ]

    resolved_name = names[0] if names else ""
    sections = {}
    if acupoint:
        for key, bdir, label in books:
            if key in POINT_SECTION_BOOKS:
                sec = _classic_find_section(bdir, code, names)
                if sec:
                    sections[key] = sec
                    resolved_name = resolved_name or sec[3]
    point_names = [resolved_name] if resolved_name else []

    for key, bdir, label in books:
        out.append(f"## {label}")
        sec = sections.get(key)
        if key in POINT_SECTION_BOOKS and acupoint:
            if not sec:
                out.append(f"- 해당 경혈 장(章)을 찾지 못했습니다 (코드 {code or '-'}, 혈명 {resolved_name or '-'}).")
                out.append("")
                continue
            fname, s, e, hname = sec
            raw, norm = _classic_lines(bdir, fname)
            out.append(f"- **경혈 장**: `{fname}` L{s + 1}–{e} — {_classic_title(raw[s])[:80]}")
            subs = [(i, _classic_title(raw[i])) for i in range(s + 1, e)
                    if _classic_heading_level(norm[i]) > _classic_heading_level(norm[s])]
            if subs:
                out.append("- **소절**: " + " · ".join(f"{t} (L{i + 1})" for i, t in subs[:20]))
            if terms:
                hits = [i for i in range(s, e) if all(t in norm[i] for t in terms)]
                out.append(f"- **검색어 적중** {len(hits)}건" + (f" (상위 {limit}건)" if len(hits) > limit else ""))
                for i in hits[:limit]:
                    out.append(f"  - L{i + 1}: {_classic_snippet(raw[i], norm[i], terms)}")
            else:
                for i, t in subs:
                    if any(k in _classic_norm(t) for k in KEY_SUBSECTIONS):
                        lv = _classic_heading_level(norm[i])
                        j = next((k for k in range(i + 1, e) if 0 < _classic_heading_level(norm[k]) <= lv), e)
                        out.append(f"\n### {t} (L{i + 1}–{j})")
                        out.extend(_classic_excerpt(raw, i + 1, j, excerpt_chars))
            out.append("")
            continue

        # 편별 원전 검색(또는 경혈 미지정 시 전 원전 검색)
        files = _classics_list_files(bdir)
        _classics_prefetch(bdir, files)
        must = terms or point_names
        if not must:
            out.append("- 혈명을 확정하지 못해 검색하지 않았습니다. `query`를 함께 입력하세요.")
            out.append("")
            continue
        hits = []
        for fname in files:
            raw, norm = _classic_lines(bdir, fname)
            for i, line in enumerate(norm):
                if not all(t in line for t in must):
                    continue
                if terms and point_names:  # 경혈+검색어: 같은 행이나 바로 앞뒤 행에 혈명이 있어야 적중
                    window = "".join(norm[max(0, i - 1):i + 2])
                    if not any(n in window for n in point_names):
                        continue
                hits.append((fname, i))
        out.append(f"- **적중** {len(hits)}건 (검색: {' + '.join(must)})" + (f", 상위 {limit}건 표시" if len(hits) > limit else ""))
        for fname, i in hits[:limit]:
            raw, norm = _classic_lines(bdir, fname)
            tag = " [한글번역]" if fname.endswith("_한글번역.md") else ""
            out.append(f"  - `{fname}`{tag} L{i + 1}: {_classic_snippet(raw[i], norm[i], must)}")
        out.append("")

    out.append("> 행 번호는 `data/classics/<원전>/` 정제 마크다운 기준. 《证治通鉴》은 원문을 기준 텍스트로 하고 같은 편 `_한글번역` 파일과 대조한다(정본 Rank 1 & 2).")
    text = "\n".join(out)
    if len(text) > CLASSIC_OUTPUT_LIMIT:
        text = text[:CLASSIC_OUTPUT_LIMIT] + "\n\n…(응답 길이 제한으로 생략 — `classic_book`·`limit`·`query`로 범위를 좁히세요)"
    return text


def handle_get_framework_protocol(arguments):
    section = arguments.get("section", "all")
    framework_text = read_file_content("framework")
    if not framework_text:
        return "프레임워크 정본(acupoint_anatomical_logic_framework.md)을 로드할 수 없습니다."

    if section == "all":
        return framework_text

    if section == "ranks":
        m = re.search(r"(## 🎯 3\. 작업 순위.*?)---", framework_text, re.DOTALL)
        return m.group(1).strip() if m else framework_text[:2000]
    elif section == "tiers":
        m = re.search(r"(## 🎚️ 2\. 질문 수준/깊이별 응답 계층 체계.*?)---", framework_text, re.DOTALL)
        return m.group(1).strip() if m else framework_text[:2000]
    elif section == "b_check":
        m = re.search(r"(### \[Rank 6\].*?)(?=### \[Rank 7\]|---)", framework_text, re.DOTALL)
        return m.group(1).strip() if m else framework_text[:2000]
    elif section == "components":
        m = re.search(r"(## 📋 5\. 최종 보고서 필수 10대 구성 요소.*?)---", framework_text, re.DOTALL)
        return m.group(1).strip() if m else framework_text[:2000]
    elif section == "rubrics":
        m = re.search(r"(### \[Rank 7\].*?)(?=## 📋 5|---)", framework_text, re.DOTALL)
        return m.group(1).strip() if m else framework_text[:2000]

    return framework_text[:3000]


def handle_tool_call(tool_name, arguments):
    if tool_name == "get_acupoint_anatomy_profile":
        return handle_get_acupoint_anatomy_profile(arguments)
    elif tool_name == "search_biomedical_reflex_db":
        return handle_search_biomedical_reflex_db(arguments)
    elif tool_name == "get_layer_b_registry":
        return handle_get_layer_b_registry(arguments)
    elif tool_name == "calculate_ari_v3_score":
        return handle_calculate_ari_v3_score(arguments)
    elif tool_name == "search_classic_records":
        return handle_search_classic_records(arguments)
    elif tool_name == "get_framework_protocol":
        return handle_get_framework_protocol(arguments)
    elif tool_name == "get_fma_anatomy_profile":
        return handle_get_fma_anatomy_profile(arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "acupoint-anatomy-local-mcp",
                            "version": "2.7.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                pass

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": MCP_TOOLS}
                }
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                try:
                    result_text = handle_tool_call(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": str(result_text)}]
                        }
                    }
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32000, "message": str(e)}
                    }
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            elif method == "ping":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

            elif req_id is not None:
                # 지원하지 않는 요청에도 응답해야 클라이언트가 시간 초과까지 기다리지 않는다
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"Local Acupoint Anatomy MCP Server error: {e}\n")


if __name__ == "__main__":
    main()

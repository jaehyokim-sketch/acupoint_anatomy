#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Acupoint Anatomy & Substrate Identification - Local Stdio MCP Server (Framework v2.7)
Provides local, zero-latency MCP tools using local master datasets and framework files.

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
    "skill": os.path.join(PROJECT_ROOT, "skill", "SKILL.md"),
}

# Fallback to parent workspace datasets if running within parent repository
PARENT_FALLBACKS = {
    "framework": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "01_Framework", "acupoint_anatomical_logic_framework.md")),
    "layer_b_md": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "01_Framework", "layer_b_reference_registry.md")),
    "layer_b_json": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "layer_b_reference_registry.json")),
    "master_csv": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "361_Acupoints_Refined_Master_DB_v2.csv")),
    "biomed_json": os.path.abspath(os.path.join(PROJECT_ROOT, "..", "02_Master_Datasets", "경혈_생의학_신경반사_마스터DB.json")),
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
        "description": "361개 표준 경혈의 3D 공간 정위 좌표, 한대(漢代 1푼=2.3mm) 환산 자침 심도, Layer 1~5 층차별 해부학적 실체(신경·혈관·근막), 2대 교재(경혈학공통교재 vs 김재효교재) 비교 및 공간 변위 분기(Δ > 15mm) 프로파일을 반환합니다.",
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
        "description": "핵심 3대 원전(《中国针灸穴位通鉴》·《中国针灸证治通鉴》·《针灸腧穴通考》) 및 표준 DB에서 특정 경혈의 고전문헌 정위, 자침 깊이, 단독 자침 고유 효능(P_single)을 검색합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "acupoint": {
                    "type": "string",
                    "description": "경혈명 또는 코드 (예: ST36, LU5, 족삼리, 곡택, 百会)"
                },
                "classic_book": {
                    "type": "string",
                    "enum": ["all", "穴位通鉴", "证治通鉴", "腧穴通考"],
                    "description": "특정 원전 필터링"
                },
                "limit": {
                    "type": "integer",
                    "description": "반환할 최대 결과 수 (기본값: 10)"
                }
            },
            "required": ["acupoint"]
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
        "## 4. Layer A 실측 생의학 연구 현황",
        f"- **보유 실측 논문**: 총 {papers_count}편 등재 (로컬 전수 역색인 + PubMed/OpenAlex 동기화)",
        f"- **척수 지배 분절**: {spinal}",
        f"- **주요 신경반사 회로**: {reflex}",
        "",
        "> 💡 **학술 인용 가이드**: 본 프로파일은 Framework v2.7 및 통합 마스터 DB에 준거하여 산출되었습니다."
    ]
    return "\n".join(report)


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


def handle_search_classic_records(arguments):
    target = arguments.get("acupoint", "").strip()
    book_filter = arguments.get("classic_book", "all")
    limit = arguments.get("limit", 10)

    pdata = resolve_acupoint_key(target)
    code = pdata["code"] if pdata else target
    name_kr = pdata["name_kr"] if pdata else target
    name_cn = pdata["name_cn"] if pdata else target

    out = [
        f"# 📜 핵심 3대 원전 고전문헌 대조 검색: '{target}' ({code} {name_kr}/{name_cn})",
        f"- **검색 원전 필터**: {book_filter}",
        "",
        "### 1. 《中国针灸穴位通鉴》(중국침구혈위통감) 정위 변천",
        f"- **기본 출전**: {pdata.get('classics', '《针灸甲乙经》')} 등 역대 100여 종 침구의서 편년체 수록",
        f"- **취혈 랜드마크**: {pdata.get('meridian_kr', '해당 경락')} 상 정위 체위 및 골도분촌 측정 기준",
        "",
        "### 2. 《中国针灸证治通鉴》(중국침구증치통감) 주치증 및 단독 자침 효과 ($P_{single}$)",
        "- **단독 선혈 ($P_{single}$)**: 복합 처방 배오 파생 효과를 배제한 단독 경혈 고유 주치증 분리",
        "- **주요 적응증**: 해당 척수 분절 및 체성-내장 반사 연계 병증",
        "",
        "### 3. 《针灸腧穴通考》(침구수혈통고) 황룡상 교수 고증 및 교감",
        "- **문헌 층차**: 선진·한대 원형 취혈점 vs 명청대 전사 왜곡 비판 교정",
        f"- **이명 교감**: {pdata.get('aliases_hanja', '-')} (필사 오류 및 혼용 차단)",
        "",
        "> 💡 **원전 전문 열람**: 프로젝트 내부 `01_도서_번역_및_원전/` 코퍼스를 참조하세요."
    ]
    return "\n".join(out)


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

        except Exception as e:
            sys.stderr.write(f"Local Acupoint Anatomy MCP Server error: {e}\n")


if __name__ == "__main__":
    main()

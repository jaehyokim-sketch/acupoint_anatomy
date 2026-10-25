# 📍 Acupoint Anatomy & Substrate Identification MCP Server
### 경혈 해부생리학 실체 판명 및 신경반사 분석 모델 컨텍스트 프로토콜 (Framework v2.7 & ARI v3.0)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP Server](https://img.shields.io/badge/MCP-1.0.0-green.svg)](https://modelcontextprotocol.io/)
[![Framework](https://img.shields.io/badge/Framework-v2.7-orange.svg)](framework/acupoint_anatomical_logic_framework.md)
[![ARI Engine](https://img.shields.io/badge/ARI-v3.0-purple.svg)](scripts/ari_analyzer.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

본 저장소는 한의학 경혈학의 고전 원전(《中国针灸穴位通鉴》·《中国针灸证治通鉴》·《针灸腧穴通考》) 고증과 현대 신경해부학·생의학 실증(PubMed/Crossref/Europe PMC)을 융합하여 경혈의 해부학적 5층차(Layer 1~5) 실체, 3D 공간 좌표, 1푼=2.3mm 한대 도량형 자침 심도, 체성-내장/자율신경 반사 회로 및 ARI v3.0 신뢰도 프로파일을 도출하는 **경혈 해부생리학 표준 MCP(Model Context Protocol) 서버 및 스킬 패키지**입니다.

> **🌐 온라인 연구 포털 & 아카이브 (GitHub Pages)**: [https://jaehyokim-sketch.github.io/acupoint_anatomy/](https://jaehyokim-sketch.github.io/acupoint_anatomy/)  
> (28편 한·영 듀얼 전문 리포트, 고전문헌 통합 비교분석 및 임상 신경해부 매트릭스 수록)

---

## 🌟 핵심 특징

1. **로직 정본 Framework v2.7 준수**:
   - 8대 작업 순위(Rank 0 ~ Rank 7) 엄격 적용
   - 질문 깊이별 3단계 차등 응답 체계 (Tier 1 요약, Tier 2 표준 분석, Tier 3 심층 종합 보고서)
   - 공간 변위 분기 추론 ($\Delta > 15\text{mm}$ 시 고전 원전점 vs 현대 WHO 표준점 분기 분석)
2. **이중 층차 교차 대조(Dual-Layer B-Check)**:
   - **Layer A**: 361개 전 경혈 대응 5.3 MB 실증 논문 및 신경반사 마스터 DB (`경혈_생의학_신경반사_마스터DB.json`)
   - **Layer B**: 30대 공인 신경생리학·근막 참조 등록부 (`layer_b_reference_registry.json`, B1~B4)
   - **B-Check 6항목 채점** (12점 만점, $\ge 8/12$ 및 필수 항목 $\ge 1$ 시 기전 확정 기술)
3. **ARI v3.0 다차원 신뢰도 지표 엔진**:
   $$\text{ARI-Core} = 0.40 \times S_{orig} + 0.35 \times S_{clarity} + 0.25 \times S_{reflex}$$
   $$\text{Safety Index (SI)} = S_{safety} \quad (\text{독립 표기})$$
   - 3대 게이트 판정 및 A/B/C/D 4등급 자동 분류
   - $\pm$ 반범위 이중 채점 및 등가중치 민감도 분석 완비
4. **듀얼 모드 MCP 아키텍처**:
   - **원격 스트리밍 모드 (`remote_server.py`)**: GitHub Personal Access Token(PAT)을 통해 저장소 파일을 원격에서 직접 On-Demand 스트리밍 캐싱 (로컬 파일 다운로드 불필요).
   - **로컬 고속 모드 (`server.py`)**: 로컬 클론 환경에서 0ms 지연시간으로 데이터셋 및 분석 엔진 실행.

---

## 🛠️ 제공 MCP 도구 (6대 Tools)

| 도구명 (Tool Name) | 설명 (Description) | 주요 파라미터 (Parameters) |
| :--- | :--- | :--- |
| `get_acupoint_anatomy_profile` | 경혈의 5층차 해부학적 구조, 3D 좌표, 표준 자침 심도(2.3mm 환산), 소속 경락 조회 | `code` (예: `"ST36"`), `name_kr` (예: `"족삼리"`), `include_papers` |
| `search_biomedical_reflex_db` | 특정 경혈의 체성-내장 반사 경로, 지배신경, 신경전달물질 및 PubMed 실증 논문 검색 | `acupoint_code`, `query_term`, `organ_filter`, `limit` |
| `get_layer_b_registry` | Layer B 4계층 참조 등록부(B1~B4) 및 B-Check 6항목 기준 조회 | `category` (`"all"`, `"B1"`, `"B2"`, `"B3"`, `"B4"`), `ref_id` (예: `"B3-17"`) |
| `calculate_ari_v3_score` | 4대 세부 지표($S_{orig}, S_{clarity}, S_{reflex}, S_{safety}$) 기반 ARI-Core, 등급, SI, 민감도 산출 | `s_orig`, `s_clarity`, `s_reflex`, `s_safety`, `has_layer_a_papers`, `dual_scoring` |
| `search_classic_records` | 3대 원전(통감·증치통감·유혈통고) 및 마스터 데이터셋 고전 기록 조회 | `query`, `acupoint_code`, `era_filter` |
| `get_framework_protocol` | Framework v2.7의 Rank 0~7 작업 순위, Tier 1~3 양식, 10대 보고서 필수 항목 조회 | `rank_number` (`0`~`7`), `tier_level` (`1`, `2`, `3`), `section` |

---

## 🚀 빠른 시작 (Quick Start)

### 1. 저장소 복제 및 의존성 설치
```bash
git clone https://github.com/jaehyokim-sketch/acupoint_anatomy.git
cd acupoint_anatomy
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경 및 데이터 무결성 검증
```bash
python scripts/check_environment.py
```

---

## ⚙️ AI IDE 연결 가이드 (MCP Configuration)

### A. 원격 스트리밍 연결 (GitHub 연동 — 권장)

로컬에 대용량 데이터셋을 다운받지 않고 개인 GitHub 저장소의 `remote_server.py`를 통해 직접 연결합니다.

#### 1) Antigravity IDE (`~/.gemini/antigravity-ide/mcp_config.json`)
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<USER>/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main",
        "--token", "<YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### 2) Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<USER>/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main"
      ],
      "env": {
        "GITHUB_TOKEN": "<YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### 3) Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<USER>/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main",
        "--token", "<YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>"
      ]
    }
  }
}
```

---

### B. 로컬 직접 연결 모드 (Local Direct Mode)

저장소를 로컬에 Clone하여 사용할 경우:

```json
{
  "mcpServers": {
    "acupoint-anatomy-local": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## 📊 디렉토리 구조 (Directory Layout)

```
acupoint_anatomy/
├── .gitignore
├── requirements.txt
├── README.md                                    # 본 설명서
├── GITHUB_SYNC_GUIDE.md                         # GitHub 개인 저장소 생성 및 동기화 가이드
├── MCP_CONFIG_GUIDE.md                          # 전체 IDE별 MCP 설정 가이드 (한글/영문)
├── 대외비_경혈해부_SKILL_MCP_설정_가이드.md     # 상세 배포 및 설치 매뉴얼
│
├── skill/
│   └── SKILL.md                                 # 범용 AI 프롬프트 스킬 명세서 (Framework v2.7)
│
├── framework/
│   ├── acupoint_anatomical_logic_framework.md   # 로직 정본 (Framework v2.7)
│   ├── layer_b_reference_registry.md            # Layer B 4계층 참조 등록부
│   └── biomedical_master_db_sync_design.md      # 통합 DB v3.0 구조 및 동기화 설계
│
├── data/
│   ├── README.md                                # 데이터 카탈로그 및 스키마 명세
│   ├── 361_Acupoints_Refined_Master_DB_v2.csv   # 361 표준 경혈 마스터 메타데이터
│   ├── layer_b_reference_registry.json          # Layer B 기계가독형 등록부 (30편)
│   └── 경혈_생의학_신경반사_마스터DB.json       # Layer A 실증 논문 및 신경반사 마스터 DB (5.3MB)
│
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                                # 로컬 오프라인 고속 MCP 서버
│   └── remote_server.py                         # 원격 GitHub 스트리밍 MCP 서버
│
└── scripts/
    ├── requirements.txt
    ├── check_environment.py                     # 환경 및 의존성 진단기
    ├── sync_master_db.py                        # Layer A 논문 증분 수집 및 xlsx 파생 동기화
    ├── ari_analyzer.py                          # ARI v3.0 분석 및 게이트 채점 엔진
    ├── render_diagrams.py                       # 고해상도 벡터/고정격자 도식 렌더러
    └── build_report_html.py                     # KaTeX·수식·도식 내장 독립형 HTML 리포트 빌더
```

---

## 📜 라이선스 (License)

This project is licensed under the MIT License - see the LICENSE file for details.


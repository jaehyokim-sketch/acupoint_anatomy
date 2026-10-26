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
   - 공간 변위 분기 추론 ($\Delta > 10\text{mm}$ 시 Tri-Target: 고전 문헌점 · 촉진 실체점 · WHO점 분기 분석)
2. **이중 층차 교차 대조(Dual-Layer B-Check)**:
   - **Layer A**: 361개 경혈 역색인 실증 논문·신경반사 마스터 DB (`경혈_생의학_신경반사_마스터DB.json`, 인용 제외 상태 자동 필터)
   - **Layer B**: 4계층 참조 등록부 43편 (`layer_b_reference_registry.json`, B1~B4)
   - **B-Check 6항목 채점** (각 0~2점, 합계 $\ge 8/12$ 그리고 ①·② $\ge 1$일 때만 기전 확정 기술)
3. **ARI v3.0 다차원 신뢰도 지표 엔진**:
   $$\text{ARI-Core} = 0.40 \times S_{orig} + 0.35 \times S_{clarity} + 0.25 \times S_{reflex}$$
   $$\text{Safety Index (SI)} = S_{safety} \quad (\text{독립 표기})$$
   - 3대 게이트 판정 및 A/B/C/D 4등급 자동 분류, 5단계 루브릭 값 검증
   - 이중 채점(평균 $\pm$ 반범위, 15점 이상 차이 조정 표시)·등가중치 민감도·Tri-Target 우위 판정
4. **듀얼 모드 MCP 아키텍처 (공통 로직 1벌)**:
   - 도구 로직은 `mcp_server/acupoint_core.py` 하나에 있고, 데이터 접근만 백엔드로 나뉜다.
   - **로컬 모드 (`server.py`)**: 로컬 저장소에서 바로 읽음. 보조 문헌(《東醫寶鑑》 등)·FMA 로컬 색인 사용 가능.
   - **원격 모드 (`remote_server.py`)**: 파일 하나로 GitHub 저장소를 스트리밍. 원전 목록은 `data/classics/index.json`(SHA-1)으로 확인해 GitHub API 호출 제한과 무관하고, 원전은 디스크에 캐시되며, `--ttl`(기본 1시간)마다 저장소 변경을 다시 확인한다. 이 파일은 `scripts/build_remote_server.py`가 공통 로직과 원격 백엔드를 합쳐 생성한다(직접 고치지 않음).

---

## 🛠️ 제공 MCP 도구 (7종)

| 도구명 (Tool Name) | 설명 (Description) | 주요 파라미터 (Parameters) |
| :--- | :--- | :--- |
| `get_acupoint_anatomy_profile` | 경혈 데이터 프로파일 — 마스터 CSV(경락·KJH 이명·출전), 2대 교재 근육·신경·혈관 비교, 문헌별 자침 깊이(푼→2.3mm, 0=금침), 통합 DB 요약, 기존 Tier 3 보고서·ARI 표기 | `acupoint` (예: `"ST36"`, `"족삼리"`, `"足三里"`) |
| `get_fma_anatomy_profile` | FMA 5.1.0 실체 대응(FMA:ID·대응 수준), 로컬 FMA 색인이 있으면 신경 지배 줄기·척수 분절 합집합(B-Check ②) | `acupoint`, `format` (`markdown`/`json`) |
| `search_biomedical_reflex_db` | Layer A 검색 — 경혈은 랜드마크·역색인·검출 혈위로 정확히 대조, 키워드는 모든 단어 포함. duplicate·missing·superseded 기본 제외, 설계(인체·동물·리뷰)는 키워드 추정 | `query`, `evidence_filter` (`all`/`human`/`animal`/`review`/`mechanism`), `include_inactive`, `limit` |
| `get_layer_b_registry` | Layer B 4계층 등록부와 B-Check 판정 규칙 | `category` (`all`/`B1`~`B4`), `reference_id` (예: `"B3-17"`), `query` |
| `calculate_ari_v3_score` | ARI v3.0 — 게이트·등급·SI·민감도, 채점자 B 입력 시 이중 채점, `targets` 입력 시 Tri-Target 우위 판정 | `s_orig`(또는 `s_orig_items`), `s_clarity`, `s_reflex`, `s_safety`, `*_b`, `layer_a_count`, `targets` |
| `search_classic_records` | 4대 원전(+보조 문헌) 정제 코퍼스 전문 검색 — 경혈 장(파일·행·소절)·부위/定位·简要结语 발췌, 혈명·별명 행(관련도순, 원문·번역 중복 제거), 검색어 행(행 경계·문장부호 무시, 번체/간체·이체자 통합) | `acupoint`, `query`, `classic_book`, `include_aliases`, `limit`, `excerpt_chars`, `max_chars` |
| `get_framework_protocol` | 정본의 해당 절을 제목 기준으로 잘라 반환(목차·Tier·Rank 0~7·B-Check·루브릭·10대 구성 요소·문서 이력) | `section` (`summary`, `tiers`, `ranks`, `rank0`~`rank7`, `b_check`, `rubrics`, `components`, `history`, `all`) |

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
MCP 서버 자체는 Python 표준 라이브러리만 쓴다(OpenCC가 있으면 검색어 번체→간체 변환에 함께 쓴다).

### 2. 환경 및 데이터 무결성 검증
```bash
python scripts/check_environment.py
```

### 3. 데이터를 고친 뒤 (관리자)
```bash
python scripts/build_mcp_reference_data.py   # 교재·자침깊이 xlsx·보고서 머리말 → data/mcp_reference_data.json, 원전 목록 → data/classics/index.json
python scripts/build_remote_server.py        # acupoint_core.py·remote_backend.py → remote_server.py
python scripts/build_mcp_reference_data.py --check && python scripts/build_remote_server.py --check   # 커밋 전 확인(옛것이면 종료코드 1)
```

---

## ⚙️ AI IDE 연결 가이드 (MCP Configuration)

### A. Claude Code (권장: 등록 스크립트)

저장소 경로와 현재 Python 경로를 자동으로 넣어 사용자 범위(모든 프로젝트)에 등록한다. PC마다 1회, 경로가 바뀌면 다시 실행한다.
```bash
python scripts/register_mcp.py              # 로컬 서버
python scripts/register_mcp.py --remote     # 원격 서버
python scripts/register_mcp.py --dry-run    # 실행할 명령만 확인
```
보조 문헌은 `--extra "東醫寶鑑=<폴더>"`로 지정하며, 지정하지 않으면 Drive 프로젝트의 `01_도서_번역_및_원전/동의보감` 폴더가 있을 때 자동으로 넣는다.

### B. 그 밖의 IDE (Claude Desktop · Cursor · Antigravity)

`python scripts/register_mcp.py --print-json`(로컬) 또는 `--remote --print-json`(원격)이 이 PC에 맞는 JSON을 출력한다. 아래는 원격 모드 예시다.
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<USER>/.acupoint_anatomy/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main"
      ],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```
- 공개 저장소이므로 토큰은 필요 없다. 비공개 포크를 쓰면 `--token <PAT>` 또는 환경변수 `GITHUB_TOKEN`을 넣는다.
- 설정 파일 위치: Claude Desktop `%APPDATA%\Claude\claude_desktop_config.json`, Cursor `.cursor/mcp.json`, Antigravity `~/.gemini/antigravity-ide/mcp_config.json`.

---

## 📊 디렉토리 구조 (Directory Layout)

```
acupoint_anatomy/
├── README.md · requirements.txt · MCP_CONFIG_GUIDE.md · 경혈해부_MCP_사용자_연결_매뉴얼.md
├── skill/SKILL.md                               # 범용 AI 스킬 명세서 (Framework v2.7)
├── framework/                                   # 로직 정본 사본 · Layer B 등록부 · DB 설계
├── data/
│   ├── 361_Acupoints_Refined_Master_DB_v2.csv   # 361 표준 경혈 마스터
│   ├── 경혈_생의학_신경반사_마스터DB.json       # Layer A 통합 DB
│   ├── layer_b_reference_registry.json          # Layer B 등록부
│   ├── acupoint_fma_mapping.json                # 경혈↔FMA 대응표
│   ├── mcp_reference_data.json                  # (생성) 교재·자침깊이·보고서 색인
│   └── classics/<4대 원전>/*.md · index.json    # 원전 정제 마크다운 · (생성) 파일 목록·SHA-1
├── mcp_server/
│   ├── acupoint_core.py                         # 도구 7종 공통 로직
│   ├── server.py                                # 로컬 백엔드
│   ├── remote_backend.py                        # 원격(GitHub) 백엔드
│   └── remote_server.py                         # (생성) 원격 단일 파일 배포본
└── scripts/
    ├── register_mcp.py                          # Claude Code 등록 / IDE용 JSON 출력
    ├── build_mcp_reference_data.py              # 참조 JSON·원전 색인 생성
    ├── build_remote_server.py                   # remote_server.py 생성
    ├── sync_claude_skill.py                     # Claude Code 스킬 Drive ↔ 로컬 워크스페이스 동기화
    ├── run_ari_analyzer_local.py                # Drive ari_analyzer.py 호출 → 초안을 로컬 저장소에 생성(비노출 정리·HTML 재빌드)
    ├── check_environment.py · sync_master_db.py · ari_analyzer.py
    └── build_report_html.py · render_diagrams.py
```

---

## 📜 라이선스 (License)

This project is licensed under the MIT License - see the LICENSE file for details.


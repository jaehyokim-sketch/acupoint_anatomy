# 📍 [경혈해부] MCP 서버 사용자 연결 매뉴얼
### Acupoint Anatomy & Substrate Identification MCP Server User Guide

> **프레임워크 버전**: Framework v2.7 & ARI v3.0  
> **공식 GitHub 저장소**: [`https://github.com/jaehyokim-sketch/acupoint_anatomy`](https://github.com/jaehyokim-sketch/acupoint_anatomy)  
> **지원 연결 방식**: **[옵션 A] 로컬 직접 연결 모드** (권장: 로컬 저장소 보유자) / **[옵션 B] 원격 클라우드 스트리밍 모드** (외부 사용자·타 PC용)  
> **인증 방식**: 공개(Public) 저장소 — **GitHub 토큰(PAT) 및 별도 API 키 불필요**

---

## 📖 1. 개요 (Introduction)

본 매뉴얼은 한의학 361개 표준 경혈의 **원전 정위 변천, 2대 교재 해부구조, 한대(漢代 1푼=2.3mm) 환산 자침 깊이, FMA 해부 실체, 체성-내장/자율신경 반사 근거(Layer A·B), ARI v3.0 계산**을 AI 어시스턴트(Claude Code, Claude Desktop, Google Antigravity, Cursor 등)에서 직접 조회하도록 **MCP(Model Context Protocol)** 서버를 연결하는 방법을 안내합니다.

* ✅ **데이터 단일 진실원천**: 361 표준 경혈 마스터 CSV, 통합 생의학 마스터 DB, Layer B 참조 등록부(B1~B4, 43편), 경혈↔FMA 대응표, 4대 원전 정제 마크다운 167편
* ✅ **공통 로직 1벌**: 도구 로직은 `mcp_server/acupoint_core.py` 하나에 있고, 로컬(`server.py`)과 원격(`remote_server.py`)은 데이터를 읽는 방식만 다르다
* ✅ **무료·무인증**: 공개 저장소이므로 GitHub 토큰이나 API 키가 필요 없다
* ✅ **표준 라이브러리만 사용**: 추가 패키지 없이 Python 3.10 이상에서 실행된다(OpenCC가 있으면 검색어 번체→간체 변환에 함께 쓴다)

---

## 🔀 2. 연결 모드 선택 (Connection Modes)

| 구분 | [옵션 A] 로컬 직접 연결 (권장) | [옵션 B] 원격 스트리밍 |
| :--- | :--- | :--- |
| **적용 대상** | 저장소를 내려받은(clone) PC | 저장소 없이 파일 하나로 쓰는 외부 사용자·다른 PC |
| **실행 파일** | `<저장소>/mcp_server/server.py` | `remote_server.py` (사용자 홈에 내려받음) |
| **데이터 원천** | 로컬 `data/`, `framework/`, `data/classics/` + 보조 문헌(《東醫寶鑑》 등, 선택) + FMA 로컬 색인(선택) | GitHub 저장소 `jaehyokim-sketch/acupoint_anatomy` |
| **갱신·캐시** | 파일을 바로 읽으므로 항상 최신 | 원전은 SHA-1 기준 디스크 캐시(`~/.acupoint_anatomy/cache`), 그 밖의 데이터는 `--ttl`(기본 3600초)마다 다시 확인 |
| **API 호출 제한** | 해당 없음 | 원전 목록을 `data/classics/index.json`으로 확인하므로 GitHub API 제한(시간당 60회)과 무관 |

---

## ⚙️ 3. 사전 준비 (Prerequisites)

* **Python 3.10 이상**이 설치되어 있어야 합니다.
  * Windows: [python.org](https://www.python.org/downloads/)에서 설치 시 **`Add python.exe to PATH`** 반드시 체크 ✅
  * macOS: `brew install python`
  * Linux: `sudo apt install python3`

---

## 🚀 4. 모드별 설치 및 설정 가이드

### 🅰️ [옵션 A] 로컬 직접 연결 모드

#### 1) Claude Code — 등록 스크립트 (권장)
저장소 위치와 현재 Python 경로를 자동으로 넣어 **사용자 범위(모든 프로젝트)**에 등록합니다. PC마다 한 번, Python이나 저장소 위치가 바뀌면 다시 실행합니다.
```bash
cd <저장소 폴더>              # 예: C:/workspace/acupoint_anatomy (Git 로컬 분리 구성)
python scripts/register_mcp.py
python scripts/register_mcp.py --dry-run   # 실행할 명령만 확인
```
* Drive 프로젝트(`G:/내 드라이브/도서 번역`)의 `01_도서_번역_및_원전/동의보감` 폴더가 있으면 《東醫寶鑑》을 보조 문헌으로 자동 등록합니다. 다른 위치는 `--extra "東醫寶鑑=<폴더>"`로 지정합니다.
* 등록 확인: `claude mcp get acupoint-anatomy` → `✔ Connected`. **새 Claude Code 세션부터** `mcp__acupoint-anatomy__*` 도구가 보입니다.
* Drive 사본(`G:/내 드라이브/도서 번역/acupoint_anatomy`)에서 실행해도 같은 명령으로 등록됩니다. 다만 Drive는 배포·열람용이므로 로컬 저장소 등록을 권장합니다.

#### 2) Claude Desktop · Antigravity · Cursor — JSON 설정
```bash
python scripts/register_mcp.py --print-json
```
출력된 JSON을 각 설정 파일에 넣습니다.
* Claude Desktop: Windows `%APPDATA%\Claude\claude_desktop_config.json`, macOS `~/Library/Application Support/Claude/claude_desktop_config.json`
* Antigravity: `C:\Users\<사용자명>\.gemini\config\mcp_config.json`
* Cursor: `.cursor/mcp.json` 또는 Cursor Settings ➔ Features ➔ MCP

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "C:/Python314/python.exe",
      "args": ["C:/workspace/acupoint_anatomy/mcp_server/server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "ACUPOINT_EXTRA_CLASSICS": "東醫寶鑑=G:/내 드라이브/도서 번역/01_도서_번역_및_원전/동의보감"
      }
    }
  }
}
```
*(경로는 예시. `--print-json` 출력값을 그대로 쓰세요. 보조 문헌을 쓰지 않으면 `ACUPOINT_EXTRA_CLASSICS` 줄을 지웁니다)*

---

### 🅱️ [옵션 B] 원격 스트리밍 모드 (외부 사용자 / 다른 PC)

로컬에 저장소가 없는 환경에서는 실행 파일 하나(`remote_server.py`)만 내려받아 GitHub 저장소 데이터를 씁니다.

#### 1) 원클릭 다운로드 (30초)
* **Windows (PowerShell)**:
  ```powershell
  $targetDir = "$HOME\.acupoint_anatomy"
  if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force }
  Invoke-WebRequest -Uri "https://raw.githubusercontent.com/jaehyokim-sketch/acupoint_anatomy/main/mcp_server/remote_server.py" -OutFile "$targetDir\remote_server.py"
  Write-Host "✅ 설치 완료! 위치: $targetDir\remote_server.py" -ForegroundColor Green
  ```
* **macOS / Linux (Bash)**:
  ```bash
  mkdir -p ~/.acupoint_anatomy
  curl -fsSL -o ~/.acupoint_anatomy/remote_server.py https://raw.githubusercontent.com/jaehyokim-sketch/acupoint_anatomy/main/mcp_server/remote_server.py
  echo "✅ 설치 완료! 위치: ~/.acupoint_anatomy/remote_server.py"
  ```

#### 2) 등록
* **Claude Code**: `claude mcp add --scope user acupoint-anatomy -e PYTHONIOENCODING=utf-8 -- python "<홈>/.acupoint_anatomy/remote_server.py"`
* **그 밖의 IDE**: 설정 파일에 아래 JSON을 넣습니다.
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<사용자명>/.acupoint_anatomy/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main"
      ],
      "env": { "PYTHONIOENCODING": "utf-8" }
    }
  }
}
```
* 선택 인자: `--ttl <초>`(데이터 재확인 주기, 기본 3600), `--cache-dir <폴더>`(원전 디스크 캐시 위치), `--token <PAT>`(비공개 포크일 때만)
*(macOS/Linux는 `command`를 `python3`, 경로를 `/Users/<사용자명>/.acupoint_anatomy/remote_server.py`로)*
* 원격 모드에서는 보조 문헌(《東醫寶鑑》)과 FMA 로컬 색인을 쓰지 않습니다. FMA 도구는 경혈↔FMA 대응표로 응답합니다.

---

## 🛠️ 5. 제공되는 7대 MCP 도구 (Tools)

| 도구명 | 기능 | 주요 인자 |
| :--- | :--- | :--- |
| **`get_acupoint_anatomy_profile`** | 경혈 데이터 프로파일 — 마스터 CSV(경락·KJH 이명·출전), 2대 교재(공통교재·김재효) 근육·신경·혈관 비교, 문헌별 자침 깊이(푼→2.3mm, 0=금침, 빈칸=미기술), 통합 DB 요약(역색인 편수·DB 기재 반사 회로), 기존 Tier 3 보고서와 ARI 표기. 층차 배치·Tri-Target·ARI 값은 만들지 않는다 | `acupoint` |
| **`get_fma_anatomy_profile`** | FMA 5.1.0 실체 대응(FMA:ID·대응 수준). 로컬 FMA 색인이 있으면 신경 지배 줄기·척수 분절 합집합(B-Check ②)까지 | `acupoint`, `format` |
| **`search_biomedical_reflex_db`** | Layer A 검색. 경혈은 랜드마크·역색인·검출 혈위로 정확히 대조, 키워드는 모든 단어 포함. duplicate·missing·superseded는 기본 제외. 설계(인체·동물·리뷰)는 제목·초록 키워드 추정 | `query`, `evidence_filter`, `include_inactive`, `limit` |
| **`get_layer_b_registry`** | Layer B 4계층 등록부(43편)와 B-Check 판정 규칙(6항목 각 0~2점, 합계 ≥ 8/12 그리고 ①·② ≥ 1) | `category`, `reference_id`, `query` |
| **`calculate_ari_v3_score`** | ARI-Core·SI·게이트 1~3·등급·등가중치 민감도. 채점자 B 점수(`*_b`)를 주면 이중 채점(평균 ± 반범위, 15점 이상 차이 표시), `targets`를 주면 Tri-Target 우위 판정. 5단계 루브릭 값이 아니면 경고 | `s_orig`/`s_orig_items`, `s_clarity`, `s_reflex`, `s_safety`, `*_b`, `layer_a_count`, `targets` |
| **`search_classic_records`** | 4대 원전(혈위통감 41편·수혈통고 25편·증치통감 원문·한글번역 62편·경락통감 39편)과 보조 문헌 전문 검색. `acupoint`: 경혈 장(파일·행·소절)과 부위/定位·简要结语 발췌, 편별 원전에서는 혈명·별명 행(관련도순, 원문·번역 중복 제거, 別名은 [별명] 표시, 手三里/足三里처럼 같은 글자의 다른 혈은 경맥으로 구별). `query`: 모든 검색어가 든 행(행 경계·문장부호 무시, 번체/간체·이체자 통합: 兩筋間=两筋间, 臁=廉, 䯒=胻) | `acupoint`, `query`, `classic_book`, `include_aliases`, `limit`, `excerpt_chars`, `max_chars` |
| **`get_framework_protocol`** | 정본의 해당 절을 제목 기준으로 잘라 반환 | `section`: `summary`(목차), `tiers`, `ranks`, `rank0`~`rank7`, `b_check`, `rubrics`, `components`, `history`, `all` |

---

## 💬 6. 바로 사용해보는 프롬프트 예시

AI 채팅창에서 **`[경혈해부]`** 또는 **`@경혈해부`** 키워드를 넣고 질문하세요.

### 1) 경혈 데이터 프로파일
> "[경혈해부] ST36 족삼리의 2대 교재 해부구조와 문헌별 자침 깊이를 1푼=2.3mm로 환산해줘."

### 2) FMA 해부 실체와 척수 분절
> "[경혈해부] ST36 족삼리의 FMA:ID 매핑, 상위 신경 줄기, 척수 분절 합집합과 2대 교재 차이를 보여줘."

### 3) Layer A 논문 검색
> "[경혈해부] PC6 내관혈 관련 인체 연구 논문을 찾아줘." (`evidence_filter`=human, 키워드 추정)

### 4) Layer B와 B-Check
> "[경혈해부] B3-17(Nature 2021) 등록부 항목과 B-Check 판정 규칙을 보여주고 ST36에 적용해줘."

### 5) ARI v3.0 이중 채점
> "[경혈해부] 채점자 A (S_orig 하위 50/50/75/75, S_clarity 75, S_reflex 25, SI 50), 채점자 B (50/50/75/50, 75, 25, 50), Layer A 0편으로 ARI v3.0을 계산해줘."

### 6) 원전 대조
> "[경혈해부] 족삼리의 '兩筋間' 조문을 4대 원전과 《東醫寶鑑》에서 모두 찾아 정위 계통을 비교해줘."

---

## ❓ 7. 자주 묻는 질문 및 트러블슈팅 (FAQ)

**Q1. `python: command not found` 오류가 납니다.**
➔ Python이 없거나 PATH에 없습니다. 설치 시 `Add Python to PATH`를 체크했는지 확인하거나, macOS/Linux에서는 `command`를 `python3`으로 바꾸세요. 등록 스크립트(`register_mcp.py`)는 Python 절대경로를 넣으므로 이 문제가 없습니다.

**Q2. 한글이나 한자가 깨집니다.**
➔ MCP 설정의 `env`에 `"PYTHONIOENCODING": "utf-8"`이 있는지 확인하세요.

**Q3. 옵션 A와 옵션 B 중 무엇을 써야 하나요?**
➔ 저장소를 내려받은 PC에서는 **옵션 A**(보조 문헌·FMA 색인까지 사용)를, 외부 연구자나 저장소 없는 PC에서는 **옵션 B**를 쓰세요.

**Q4. 원격 모드에서 데이터가 최신이 아닌 것 같습니다.**
➔ 원격 서버는 `--ttl`(기본 1시간)마다 저장소를 다시 확인하고, 원전은 파일별 SHA-1이 바뀌면 새로 받습니다. 바로 반영하려면 IDE를 다시 시작하거나 `--ttl 300`처럼 줄이세요.

**Q5. Claude Code에서 도구가 보이지 않습니다.**
➔ `claude mcp get acupoint-anatomy`로 `✔ Connected`를 확인하고 **새 세션**을 여세요. Python·저장소 경로가 바뀌었으면 `python scripts/register_mcp.py`를 다시 실행합니다.

**Q6. 관리자: 데이터나 도구 로직을 고친 뒤에는?**
➔ 교재·자침깊이 xlsx나 보고서·원전이 바뀌면 `python scripts/build_mcp_reference_data.py`, 도구 로직(`acupoint_core.py`·`remote_backend.py`)을 고치면 `python scripts/build_remote_server.py`를 실행한 뒤 커밋합니다. 커밋 전 두 스크립트를 `--check`로 실행하면 갱신 누락을 잡을 수 있습니다.

---

## 📜 라이선스 및 저작권
- **Framework & Database**: Acupoint Anatomical Logic Framework v2.7 & ARI v3.0
- **GitHub Repository**: [https://github.com/jaehyokim-sketch/acupoint_anatomy](https://github.com/jaehyokim-sketch/acupoint_anatomy)

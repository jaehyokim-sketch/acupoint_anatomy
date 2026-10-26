# 📍 [경혈해부] MCP 서버 사용자 연결 매뉴얼
### Acupoint Anatomy & Substrate Identification MCP Server User Guide

> **프레임워크 버전**: Framework v2.7 & ARI v3.0  
> **공식 GitHub 저장소**: [`https://github.com/jaehyokim-sketch/acupoint_anatomy`](https://github.com/jaehyokim-sketch/acupoint_anatomy)  
> **지원 연결 방식**: **[옵션 A] 로컬 직접 연결 모드** (권장: 로컬 저장소 보유자) / **[옵션 B] 원격 클라우드 스트리밍 모드** (외부 사용자·타 PC용)  
> **인증 방식**: 공개(Public) 저장소 — **GitHub 토큰(PAT) 및 별도 API 키 불필요**

---

## 📖 1. 개요 (Introduction)

본 매뉴얼은 한의학 361개 표준 경혈의 **5층차(Layer 1~5) 해부학적 실체, 3D 공간 정위, 한대(漢代 1푼=2.3mm) 환산 자침 심도, 체성-내장/자율신경 반사 회로 및 ARI v3.0 신뢰도 프로파일**을 다양한 AI 어시스턴트(Google Antigravity, Claude Desktop, Cursor, Roo Code 등)에서 실시간으로 직접 질의하고 분석할 수 있도록 **MCP(Model Context Protocol)**를 구성하는 방법을 안내합니다.

* ✅ **완벽한 데이터 단일 진실원천(SSOT)**: 361 표준 마스터 DB, Layer B 참조 등록부(B1~B4), 핵심 3대 원전 128개 세분화 챕터 DB 완비
* ✅ **듀얼 연결 아키텍처**: 로컬 파일 직접 고속 서빙(옵션 A) 및 GitHub On-Demand 원격 스트리밍(옵션 B) 동시 지원
* ✅ **100% 무료 & 무인증**: GitHub 토큰이나 유료 API 키 없이 즉시 연동
* ✅ **표준 JSON-RPC 2.0 지원**: Python 표준 라이브러리 기반으로 추가 패키지 없이 완벽 호환

---

## 🔀 2. 연결 모드 선택 (Connection Modes)

| 구분 | [옵션 A] 로컬 직접 연결 모드 (권장) | [옵션 B] 원격 클라우드 스트리밍 모드 |
| :--- | :--- | :--- |
| **적용 대상** | **현재 PC 및 로컬 저장소 보유 개발자/연구자** | **외부 사용자, 지인, 로컬 폴더 없는 원격 PC** |
| **실행 스크립트** | `acupoint_anatomy/mcp_server/server.py` | `remote_server.py` (사용자 홈에 다운로드) |
| **데이터 원천** | 로컬 `data/`, `framework/`, `01_도서_번역_및_원전/` | GitHub Raw API (`jaehyokim-sketch/acupoint_anatomy`) |
| **속도/지연시간** | **초고속 무지연 (0ms, 네트워크 무관)** | 네트워크 의존 (메모리 10분 캐시) |
| **사전 다운로드** | 불필요 (이미 로컬에 작업 디렉토리 존재) | 스크립트 1개(단일 .py)만 다운로드 |

---

## ⚙️ 3. 사전 준비 (Prerequisites)

* **Python 3.10 이상**이 설치되어 있어야 합니다.
  * Windows: [python.org](https://www.python.org/downloads/)에서 설치 시 **`Add python.exe to PATH`** 반드시 체크 ✅
  * macOS: `brew install python`
  * Linux: `sudo apt install python3`

---

## 🚀 4. 모드별 설치 및 설정 가이드

### 🅰️ [옵션 A] 로컬 직접 연결 모드 설정 (권장: 현재 작업 PC)

로컬에 `G:\내 드라이브\도서 번역\acupoint_anatomy` 저장소가 이미 존재하므로 별도 다운로드 없이 설정 파일에 아래 JSON만 등록하면 즉시 연결됩니다.

#### 1) Google Antigravity IDE (현재 IDE)
* **글로벌 설정 경로**: `C:\Users\<사용자명>\.gemini\config\mcp_config.json`
* **워크스페이스 설정 경로**: `G:\내 드라이브\도서 번역\.vscode\mcp.json`

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "G:/내 드라이브/도서 번역/acupoint_anatomy/mcp_server/server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### 2) Claude Desktop
* **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
* **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "G:/내 드라이브/도서 번역/acupoint_anatomy/mcp_server/server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

#### 3) Cursor
* **프로젝트 루트 설정**: `.cursor/mcp.json` 또는 Cursor Settings ➔ Features ➔ MCP

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "G:/내 드라이브/도서 번역/acupoint_anatomy/mcp_server/server.py"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

### 🅱️ [옵션 B] 원격 클라우드 스트리밍 모드 설정 (외부 사용자 / 타 PC용)

로컬에 프로젝트 폴더가 없는 환경에서는 실행용 단일 파일(`remote_server.py`)만 다운로드하여 GitHub 저장소 데이터를 스트리밍으로 사용합니다.

#### 1) 원클릭 스크립트 다운로드 (30초)
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
  chmod +x ~/.acupoint_anatomy/remote_server.py
  echo "✅ 설치 완료! 위치: ~/.acupoint_anatomy/remote_server.py"
  ```

#### 2) IDE 설정 등록 (옵션 B 원격용)
각 AI 환경 설정 파일의 `args`에 다운로드한 `remote_server.py` 경로와 GitHub 리포지토리 매개변수를 등록합니다:

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
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```
*(macOS/Linux의 경우 `command`를 `python3`, 경로를 `/Users/<사용자명>/.acupoint_anatomy/remote_server.py`로 설정)*

---

## 🛠️ 5. 제공되는 7대 핵심 MCP 도구 (Tools)

연결이 완료되면 AI 어시스턴트가 대화 중 사용자의 질문 의도에 맞춰 아래 도구들을 자율적으로 호출합니다:

| 도구명 (Tool Name) | 주요 기능 및 연동 데이터 |
| :--- | :--- |
| **`get_acupoint_anatomy_profile`** | 361 경혈의 5층차 해부학적 구조(신경·혈관·근막), 3D 좌표, 표준 자침 심도(2.3mm 환산), 2대 교재(공통교재 vs 김재효) 비교 및 $\Delta > 15\text{mm}$ 분기 분석 |
| **`get_fma_anatomy_profile`** | **FMA(Foundational Model of Anatomy v5.1.0)** 온톨로지 기반 361개 표준 경혈의 해부학적 실체(근육·신경·혈관 FMA:ID 및 영문 라벨), 신경 지배 상위 줄기 사슬(`trunk_chain`), 척수 분절 합집합(B-Check ②), 2대 교재 매핑 대조 프로파일 |
| **`search_biomedical_reflex_db`** | Layer A 통합 마스터 DB에서 체성-내장/자율신경 반사 회로, 척수 분절, 지배신경 및 PubMed/OpenAlex 실측 논문 검색 |
| **`get_layer_b_registry`** | Layer B 4계층 참조 등록부(B1 해부기반, B2 신경반사, B3 전침매개변수, B4 근막기계수용체) 및 B-Check 6항목(12점 만점, $\ge 8/12$ 통과 기준) 조회 |
| **`calculate_ari_v3_score`** | 4대 지표($S_{orig}, S_{clarity}, S_{reflex}, S_{safety}$) 기반 ARI-Core, 등급(A~D), SI, 3대 비보상형 게이트, 가중치 민감도 자동 계산 |
| **`search_classic_records`** | 4대 원전(**혈위통감 41편, 수혈통고 25편, 증치통감 원문·한글번역 62편, 경락통감 39편**) 정제 코퍼스 전문 검색. `acupoint`를 주면 혈위통감·수혈통고의 해당 경혈 장(파일·행 범위·소절 목차)과 부위/定位·简要结语 원문을, 증치통감·경락통감에서는 혈명이 나오는 행을 돌려준다. `query`를 주면 모든 검색어가 든 행을 파일·행 번호와 함께 돌려준다(번체·간체 통합, 예: `兩筋間`=`两筋间`). `classic_book`·`limit`·`excerpt_chars`로 범위 조절 |
| **`get_framework_protocol`** | Framework v2.7의 8대 작업 순위(Rank 0~7), Tier 1~3 차등 응답 규격, 10대 보고서 필수 구성 요소 요강 반환 |

---

## 💬 6. 바로 사용해보는 프롬프트 예시

AI 채팅창에서 **`[경혈해부]`** 또는 **`@경혈해부`** 키워드를 넣고 다음과 같이 질문하세요:

### 1) 경혈 5층차 해부 실체 및 안전 심도 분석
> "[경혈해부] ST36 족삼리의 5층차 해부학적 실체와 1푼=2.3mm 기준 자침 심도를 알려줘."

### 2) FMA 온톨로지 해부 실체 및 척수 분절 합집합 정밀 조회
> "[경혈해부] ST36 족삼리의 FMA:ID 온톨로지 매핑, 상위 신경 줄기 사슬, 척수 분절 합집합과 2대 교재 차이를 보여줘."

### 3) 체성-내장 반사 및 PubMed 실증 논문 검색
> "[경혈해부] PC6 내관혈의 미주신경-심장 자율신경 반사 회로와 관련 논문 목록을 검색해줘."

### 4) Layer B 참조 등록부 및 B-Check 검증
> "[경혈해부] ST36과 B3-17(Nature 2021) 항염증 반사 회로에 대해 B-Check 6항목 채점을 수행해줘."

### 5) ARI v3.0 신뢰도 지표 정밀 산출
> "[경혈해부] ST36의 S_orig=100, S_clarity=100, S_reflex=75, S_safety=100 점수로 ARI v3.0 코어 점수와 등급, 게이트 판정표를 작성해줘."

### 6) 3대 원전 고전문헌 대조
> "[경혈해부] LU09 태연혈의 《中国针灸穴位通鉴》 정위 변천과 《中国针灸证治通鉴》의 단독 자침 효능을 대조해줘."

---

## ❓ 7. 자주 묻는 질문 및 트러블슈팅 (FAQ)

**Q1. `python: command not found` 오류가 납니다.**  
➔ 파이썬이 설치되어 있지 않거나 환경변수 PATH에 등록되지 않은 경우입니다. 파이썬 설치 시 `Add Python to PATH`를 체크했는지 확인하거나, macOS/Linux에서는 `command`를 `python3`으로 변경하세요.

**Q2. 한글이나 한자 특수문자가 깨집니다.**  
➔ MCP 설정의 `env` 블록에 `"PYTHONIOENCODING": "utf-8"` 이 포함되어 있는지 확인하세요.

**Q3. 옵션 A(로컬)와 옵션 B(원격) 중 무엇을 써야 하나요?**  
➔ 본 PC에서 도서 번역 및 보고서 작업을 진행하시는 사용자 본인은 **초고속 무지연 옵션 A**를 사용하시는 것이 최선입니다. 외부 동료 연구자나 다른 PC에서 접속할 때만 **옵션 B**를 안내하시면 됩니다.

**Q4. 데이터가 최신으로 갱신되지 않는 것 같습니다.**  
➔ 옵션 B(원격)는 메모리에 10분간 캐시를 유지합니다. IDE를 재시작하시면 GitHub의 최신 데이터가 즉시 다시 동기화됩니다. 옵션 A(로컬)는 로컬 파일을 즉시 읽으므로 항상 실시간 반영됩니다.

---

## 📜 라이선스 및 저작권
- **Framework & Database**: Acupoint Anatomical Logic Framework v2.7 & ARI v3.0
- **GitHub Repository**: [https://github.com/jaehyokim-sketch/acupoint_anatomy](https://github.com/jaehyokim-sketch/acupoint_anatomy)

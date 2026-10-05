# 📍 [경혈해부] MCP 서버 사용자 연결 매뉴얼
### Acupoint Anatomy & Substrate Identification MCP Server User Guide
**프레임워크 버전**: Framework v2.7 & ARI v3.0  
**저장소 URL**: `https://github.com/jaehyokim-sketch/acupoint_anatomy`  
**인증 방식**: 공개(Public) 저장소 — **GitHub 계정 로그인 및 토큰(PAT) 불필요**

---

## 📖 1. 개요 (Introduction)

본 매뉴얼은 한의학 경혈의 **5층차(Layer 1~5) 해부학적 실체, 3D 공간 정위, 한대(漢代 1푼=2.3mm) 환산 자침 심도, 체성-내장/자율신경 반사 회로 및 ARI v3.0 신뢰도 프로파일**을 AI 어시스턴트(Claude Desktop, Cursor, Antigravity, Roo Code 등)에서 실시간으로 조회하고 분석할 수 있도록 **원격 MCP(Model Context Protocol)**를 연결하는 방법을 안내합니다.

* ✅ **대용량 파일 다운로드 불필요**: GitHub 클라우드에서 On-Demand로 필요한 데이터만 실시간 스트리밍
* ✅ **100% 무료 & 무인증**: GitHub 토큰이나 별도 API 키 없이 누구나 즉시 사용 가능
* ✅ **표준 JSON-RPC 2.0 지원**: 파이썬 표준 라이브러리 기반으로 추가 패키지 설치 없이 완벽 호환

---

## ⚙️ 2. 사전 준비 (Prerequisites)

* **Python 3.10 이상**이 설치되어 있어야 합니다.
  * Windows: [python.org](https://www.python.org/downloads/)에서 설치 시 **`Add python.exe to PATH`** 반드시 체크 ✅
  * macOS: `brew install python`
  * Linux: `sudo apt install python3`

---

## 🚀 3. 원클릭 30초 간편 설치 (Quick Setup)

터미널을 열고 본인의 운영체제에 맞는 명령어를 복사하여 실행하십시오. (실행용 중계 스크립트 `remote_server.py`를 사용자 홈 디렉토리에 자동으로 다운로드합니다.)

### 🪟 Windows (PowerShell)
```powershell
$targetDir = "$HOME\.acupoint_anatomy"
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force }
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/jaehyokim-sketch/acupoint_anatomy/main/mcp_server/remote_server.py" -OutFile "$targetDir\remote_server.py"
Write-Host "✅ 설치 완료! 위치: $targetDir\remote_server.py" -ForegroundColor Green
```

### 🍎 macOS / 🐧 Linux (Bash)
```bash
mkdir -p ~/.acupoint_anatomy
curl -fsSL -o ~/.acupoint_anatomy/remote_server.py https://raw.githubusercontent.com/jaehyokim-sketch/acupoint_anatomy/main/mcp_server/remote_server.py
chmod +x ~/.acupoint_anatomy/remote_server.py
echo "✅ 설치 완료! 위치: ~/.acupoint_anatomy/remote_server.py"
```

---

## 💻 4. AI IDE별 MCP 등록 설정 가이드

본인이 사용하는 AI 애플리케이션의 설정 파일에 아래 JSON 설정을 추가하십시오.

---

### 🟣 1) Claude Desktop
* **설정 파일 경로**:
  * **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
  * **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<본인사용자명>/.acupoint_anatomy/remote_server.py",
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
> *(macOS의 경우 `args`의 경로를 `/Users/<본인사용자명>/.acupoint_anatomy/remote_server.py` 로 변경하고 `command`를 `python3`으로 설정)*

---

### 💻 2) Cursor
* **설정 방법**: 프로젝트 루트에 `.cursor/mcp.json` 생성 또는 `Cursor Settings` ➔ `Features` ➔ `MCP` 에서 등록

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<본인사용자명>/.acupoint_anatomy/remote_server.py",
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

---

### 🌐 3) Google Antigravity IDE
* **설정 파일 경로**: `C:\Users\<본인사용자명>\.gemini\antigravity-ide\mcp_config.json`

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<본인사용자명>/.acupoint_anatomy/remote_server.py",
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

---

### 🤖 4) Roo Code / Cline (VS Code 확장)
* **설정 방법**: VS Code 전역 `settings.json` 또는 Roo Code MCP 탭에서 JSON 붙여넣기

```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "C:/Users/<본인사용자명>/.acupoint_anatomy/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      },
      "autoApprove": [
        "get_acupoint_anatomy_profile",
        "search_biomedical_reflex_db",
        "get_layer_b_registry",
        "calculate_ari_v3_score",
        "search_classic_records",
        "get_framework_protocol"
      ]
    }
  }
}
```

---

## 🛠️ 5. 제공되는 6대 핵심 MCP 도구 (Tools)

연결이 완료되면 AI 어시스턴트가 대화 중 자동으로 아래 도구들을 호출하여 답변합니다:

| 도구명 (Tool Name) | 주요 기능 |
| :--- | :--- |
| **`get_acupoint_anatomy_profile`** | 361 경혈의 5층차 해부학적 구조(신경·혈관·근막), 3D 좌표, 표준 자침 심도(2.3mm 환산), 2대 교재 비교 및 $\Delta > 15\text{mm}$ 분기 분석 |
| **`search_biomedical_reflex_db`** | Layer A 통합 마스터 DB에서 체성-내장/자율신경 반사 회로, 척수 분절, 지배신경 및 PubMed 실측 논문 검색 |
| **`get_layer_b_registry`** | Layer B 4계층 참조 등록부(B1~B4) 및 B-Check 6항목(12점 만점, $\ge 8/12$ 통과 기준) 조회 |
| **`calculate_ari_v3_score`** | 4대 지표($S_{orig}, S_{clarity}, S_{reflex}, S_{safety}$) 기반 ARI-Core, 등급(A~D), SI, 3대 게이트, 민감도 자동 계산 |
| **`search_classic_records`** | 3대 원전(혈위통감·증치통감·수혈통고) 고전 취혈 정위, 자침 심도, 단독 효능($P_{single}$) 원문 대조 |
| **`get_framework_protocol`** | Framework v2.7의 8대 작업 순위(Rank 0~7), Tier 1~3 양식, 10대 보고서 필수 구성 요소 요강 반환 |

---

## 💬 6. 바로 사용해보는 프롬프트 예시

AI 채팅창에서 **`[경혈해부]`** 또는 **`@경혈해부`** 키워드를 넣고 다음과 같이 질문하세요:

### 1) 경혈 5층차 해부 실체 및 안전 심도 분석
> "[경혈해부] ST36 족삼리의 5층차 해부학적 실체와 1푼=2.3mm 기준 자침 심도를 알려줘."

### 2) 체성-내장 반사 및 PubMed 실증 논문 검색
> "[경혈해부] PC6 내관혈의 미주신경-심장 자율신경 반사 회로와 관련 논문 목록을 검색해줘."

### 3) Layer B 참조 등록부 및 B-Check 검증
> "[경혈해부] ST36과 B3-17(Nature 2021) 항염증 반사 회로에 대해 B-Check 6항목 채점을 수행해줘."

### 4) ARI v3.0 신뢰도 지표 정밀 산출
> "[경혈해부] ST36의 S_orig=100, S_clarity=100, S_reflex=75, S_safety=100 점수로 ARI v3.0 코어 점수와 등급, 게이트 판정표를 작성해줘."

---

## ❓ 7. 자주 묻는 질문 및 트러블슈팅 (FAQ)

**Q1. `python: command not found` 오류가 납니다.**  
➔ 파이썬이 설치되어 있지 않거나 환경변수 PATH에 등록되지 않은 경우입니다. 파이썬 설치 시 `Add Python to PATH`를 체크했는지 확인하거나, macOS/Linux에서는 `command`를 `python3`으로 변경하세요.

**Q2. 한글이나 한자 특수문자가 깨집니다.**  
➔ MCP 설정의 `env` 블록에 `"PYTHONIOENCODING": "utf-8"` 이 포함되어 있는지 확인하세요.

**Q3. 데이터가 최신으로 갱신되지 않는 것 같습니다.**  
➔ `remote_server.py`는 메모리에 10분간 캐시를 유지합니다. AI IDE(Claude Desktop, Cursor 등)를 재시작하시면 GitHub의 최신 데이터가 즉시 다시 동기화됩니다.

---

## 📜 라이선스 및 저작권
- **Framework & Database**: Acupoint Anatomical Logic Framework v2.7 & ARI v3.0
- **GitHub Repository**: [https://github.com/jaehyokim-sketch/acupoint_anatomy](https://github.com/jaehyokim-sketch/acupoint_anatomy)

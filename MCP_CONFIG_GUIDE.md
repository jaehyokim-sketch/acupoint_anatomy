# 🛠️ 경혈해부 (Acupoint Anatomy) MCP 설정 및 IDE 연동 가이드

본 문서는 `acupoint_anatomy` MCP 서버를 다양한 AI IDE(Antigravity, Claude Desktop, Cursor, Roo Code/Cline 등)에 등록하여 고성능 경혈 해부생리학 분석 도구를 활성화하는 완벽 가이드입니다.

---

## 🎯 핵심 연동 방식 요약

| 방식 | 설명 | 장점 | 권장 대상 |
| :--- | :--- | :--- | :--- |
| **A. 원격 GitHub 스트리밍 (`remote_server.py`)** | GitHub API를 통해 On-Demand로 최신 데이터 스트리밍 | 로컬 디스크 공간 절약, 여러 PC에서 동일한 설정 유지 | **모든 사용자 권장** |
| **B. 로컬 직접 연결 (`server.py`)** | 로컬에 Clone된 저장소의 파이썬 서버 직접 실행 | 0ms 무지연, 완전 오프라인 동작 가능 | 로컬 분석 및 개발자 |

---

## 1. AI IDE별 원격 MCP 설정 (Remote Streaming Mode)

> ⚠️ `<YOUR_GITHUB_ID>`를 본인의 GitHub 사용자명(예: `jaehyokim-sketch`)으로 변경하고, Private 저장소인 경우 `<YOUR_GITHUB_TOKEN>`에 발급받은 Personal Access Token (`ghp_...`)을 입력하십시오.

### 🌐 1) Antigravity IDE
- **설정 파일 위치**: `C:\Users\<사용자명>\.gemini\antigravity-ide\mcp_config.json`
- **설정 내용**:
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "<YOUR_GITHUB_ID>/acupoint_anatomy",
        "--branch", "main",
        "--token", "<YOUR_GITHUB_TOKEN>"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

### 🟣 2) Claude Desktop
- **설정 파일 위치**:
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **설정 내용**:
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "<YOUR_GITHUB_ID>/acupoint_anatomy",
        "--branch", "main"
      ],
      "env": {
        "GITHUB_TOKEN": "<YOUR_GITHUB_TOKEN>",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

### 💻 3) Cursor
- **설정 파일 위치**: 프로젝트 루트의 `.cursor/mcp.json` 또는 글로벌 Cursor MCP Settings
- **설정 내용**:
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "<YOUR_GITHUB_ID>/acupoint_anatomy",
        "--branch", "main",
        "--token", "<YOUR_GITHUB_TOKEN>"
      ]
    }
  }
}
```

---

### 🤖 4) Roo Code / Cline (VS Code 확장)
- **설정 파일 위치**: VS Code 전역 설정 `settings.json` 또는 Roo Code MCP 탭
- **설정 내용**:
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "<YOUR_GITHUB_ID>/acupoint_anatomy",
        "--branch", "main",
        "--token", "<YOUR_GITHUB_TOKEN>"
      ],
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

## 2. 로컬 직접 연결 설정 (Local Direct Mode)

오프라인 상태이거나 로컬 저장소에서 개발 및 테스트를 진행할 때 사용합니다.

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

## 3. 원클릭 자동 설치 스크립트 (PowerShell)

원클릭으로 `remote_server.py`를 사용자 홈 디렉토리에 복사하고 Antigravity 또는 Claude Desktop MCP 설정을 자동으로 업데이트하는 스크립트입니다:

```powershell
# PowerShell 관리자/일반 터미널에서 실행
$repo = "jaehyokim-sketch/acupoint_anatomy"
$token = "ghp_xxxxxxxxxxxxxxxxxxxx" # 개인 토큰 입력

$targetDir = "$HOME\.acupoint_anatomy_mcp"
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir -Force }

Copy-Item "d:\도서 번역\acupoint_anatomy\mcp_server\remote_server.py" "$targetDir\remote_server.py" -Force

Write-Host "✅ remote_server.py 가 $targetDir 로 복사되었습니다." -ForegroundColor Green
Write-Host "💡 상단의 JSON 설정을 복사하여 각 IDE 설정 파일에 등록하십시오." -ForegroundColor Cyan
```

---

## 4. MCP 도구(Tools) 활용 예시 프롬프트

AI 어시스턴트에게 다음과 같이 요청하면 자동으로 경혈해부 MCP 도구가 호출됩니다:

1. **경혈 해부학적 5층차 및 3D 정위 조회**:
   > "[경혈해부] ST36 족삼리의 5층차 해부학적 실체와 1푼=2.3mm 기준 자침 심도를 알려줘."
2. **체성-내장 반사 및 PubMed 실증 논문 검색**:
   > "[경혈해부] PC6 내관혈의 미주신경-심장 자율신경 반사 회로와 관련 논문을 찾아줘."
3. **Layer B 참조 등록부 및 B-Check 검증**:
   > "[경혈해부] ST36과 B3-17(Nature 2021) 항염증 반사 경로에 대해 B-Check 6항목 채점을 수행해줘."
4. **ARI v3.0 신뢰도 지표 산출**:
   > "[경혈해부] ST36의 S_orig=100, S_clarity=100, S_reflex=75, S_safety=100 점수로 ARI v3.0 코어 점수와 게이트 판정을 계산해줘."

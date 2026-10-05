# [대외비] 경혈해부 SKILL MCP 서버 설정 및 원격 스트리밍 가이드
**문서 버전**: v2.7  
**보안 등급**: 대외비 (Confidential)  
**적용 프레임워크**: Acupoint Anatomical Logic Framework v2.7 & ARI v3.0

---

## 1. 개요 및 목적

본 문서는 **경혈 해부생리학 실체 판명 분석 스킬([경혈해부])**의 데이터와 로직을 GitHub 개인 저장소(`acupoint_anatomy`)를 통해 안전하게 원격 스트리밍 방식으로 연동하기 위한 표준 운영 절차서(SOP)입니다.

로컬 PC의 물리적 저장 용량을 차지하지 않으면서도, GitHub Personal Access Token(PAT) 인증을 통해 보안을 유지하고, 언제 어디서나 최신 프레임워크와 마스터 데이터베이스를 동기화하여 고성능 AI IDE(Antigravity, Claude Desktop, Cursor 등)에서 활용할 수 있습니다.

---

## 2. 시스템 아키텍처

```mermaid
graph TD
    subgraph GitHub Remote Repo ["GitHub 개인 저장소 (jaehyokim-sketch/acupoint_anatomy)"]
        F1["framework/ (로직 정본 v2.7, Layer B 등록부)"]
        D1["data/ (361 경혈 DB, 마스터 JSON 5.3MB)"]
        S1["skill/SKILL.md (시스템 프롬프트 명세)"]
    end

    subgraph Client IDE ["로컬 AI IDE (Antigravity / Claude / Cursor)"]
        MCP_Client["MCP Client Engine"]
        Subagent["Acupoint Anatomy Skill"]
    end

    subgraph Streaming Server ["mcp_server/remote_server.py"]
        Cache["In-Memory LRU Cache (10분 TTL)"]
        Streamer["GitHub Raw Content API Streamer"]
        Tools["6대 MCP 도구 엔진"]
    end

    MCP_Client <-->|stdio JSON-RPC 2.0| Streaming Server
    Streaming Server <-->|HTTPS + PAT Header| GitHub Remote Repo
```

---

## 3. GitHub 개인 저장소 생성 및 초기화

### 1) 저장소 생성
1. GitHub(`https://github.com`)에 로그인합니다.
2. 새 저장소(`New repository`)를 생성합니다.
   - **Repository Name**: `acupoint_anatomy`
   - **Visibility**: `Private` (대외비 연구자료 권장)
   - **Initialize repository with**: 모든 항목 체크 해제 (빈 저장소)

### 2) 로컬 코드 푸시 (PowerShell)
```powershell
cd "d:\도서 번역\acupoint_anatomy"
git init -b main
git add .
git commit -m "feat: Release Acupoint Anatomy MCP Server v2.7 & ARI v3.0"
git remote add origin https://github.com/jaehyokim-sketch/acupoint_anatomy.git
git push -u origin main
```

### 3) GitHub Token(PAT) 생성
- GitHub ➔ `Settings` ➔ `Developer settings` ➔ `Personal access tokens (classic)`
- `Generate new token (classic)` 선택
- Note: `Acupoint-Anatomy-MCP`
- Scopes: `repo` (Full control of private repositories) 체크 ✅
- 발급된 토큰(`ghp_...`) 보관

---

## 4. AI IDE별 MCP 등록 설정

### 1) Antigravity IDE
파일: `C:\Users\<사용자명>\.gemini\antigravity-ide\mcp_config.json`
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main",
        "--token", "<YOUR_GITHUB_PAT_TOKEN>"
      ],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

### 2) Claude Desktop
파일: `%APPDATA%\Claude\claude_desktop_config.json`
```json
{
  "mcpServers": {
    "acupoint-anatomy": {
      "command": "python",
      "args": [
        "d:/도서 번역/acupoint_anatomy/mcp_server/remote_server.py",
        "--repo", "jaehyokim-sketch/acupoint_anatomy",
        "--branch", "main"
      ],
      "env": {
        "GITHUB_TOKEN": "<YOUR_GITHUB_PAT_TOKEN>",
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

---

## 5. 제공되는 6대 핵심 MCP 도구

1. **`get_acupoint_anatomy_profile`**: 361 경혈의 5층차 해부 구조, 3D 좌표, 표준 심도, 신경/혈관 지배 구조 조회
2. **`search_biomedical_reflex_db`**: 체성-내장 반사 회로, 척수 분절, 지배신경 및 PubMed 실증 논문 검색
3. **`get_layer_b_registry`**: Layer B 4계층 참조 등록부(B1~B4) 및 B-Check 6항목 기준 조회
4. **`calculate_ari_v3_score`**: 4대 지표 기반 ARI-Core, 등급, SI, 민감도 자동 계산 엔진
5. **`search_classic_records`**: 3대 원전(통감·증치통감·유혈통고) 고전 기록 검색
6. **`get_framework_protocol`**: Framework v2.7의 Rank 0~7 순위, Tier 1~3 양식, 10대 보고서 구성 요소 조회

---

## 6. 유지보수 및 데이터 동기화 절차

새로운 논문이 추가되거나 프레임워크가 갱신되었을 때:
```powershell
# 1. 로컬에서 데이터 갱신 실행
python scripts/sync_master_db.py --trigger rank6 all --code ST36

# 2. 변경사항 Git 커밋 & 푸시
git add .
git commit -m "update: Sync ST36 biomedical literature and refresh master DB"
git push origin main
```
원격 MCP 서버는 10분 이내 또는 IDE 재시작 시 갱신된 데이터를 자동으로 동기화합니다.

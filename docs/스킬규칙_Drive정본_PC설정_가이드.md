# [경혈해부] 스킬 규칙 — Google Drive 정본 기준 PC 설정 가이드

> 2026-10-26 결정: GOYANGSOON PC와 김재효연구실 PC는 모두 **Google Drive `도서 번역` 폴더의 정본**을 스킬 규칙으로 쓴다. 각 PC의 로컬 사본은 Drive를 그대로 따르는 읽기 전용 미러다.

## 1. 무엇이 정본이고 무엇이 미러인가

| 정본 (Google Drive `도서 번역`) | 로컬 미러 | 비고 |
| :--- | :--- | :--- |
| `.claude/skills/acupoint-anatomy/**` | `C:\workspace\.claude\skills\acupoint-anatomy\` | Claude Code 스킬 본문·FMA/초음파 스크립트·WORKLOG |
| `.claude/workspace_CLAUDE.md` | `C:\workspace\CLAUDE.md` | 로컬 워크스페이스 지침 |
| `01_Framework/` 정본·Layer B 등록부·DB 설계 | `acupoint_anatomy/framework/` | 저장소 사본(바뀌면 커밋) |
| `.agents/skills/acupoint-anatomy/SKILL.md` | `acupoint_anatomy/skill/SKILL.md` | 〃 |
| `02_Master_Datasets/layer_b_reference_registry.json` | `acupoint_anatomy/data/` | 〃 |

- 미러는 `acupoint_anatomy/scripts/sync_claude_skill.py`가 **Drive → 로컬 단방향**으로 맞춘다.
- 로컬 미러를 직접 고치면 다음 동기화 때 `C:\workspace\.claude\skill_sync_backup\<시각>\`에 보관된 뒤 Drive본으로 덮어써진다. **규칙은 Drive 정본에서 고친다.**
- Drive에 연결되지 않은 상태에서는 아무것도 바꾸지 않는다.

## 2. PC별 1회 설정

1. **Google Drive 확인**: Google Drive 데스크톱이 실행 중이고 `도서 번역` 폴더가 최신으로 동기화되는지 확인한다.
   - Drive 경로가 `G:\내 드라이브\도서 번역`이 아니면 사용자 환경변수를 설정한다: `setx ACUPOINT_DRIVE_ROOT "<Drive의 도서 번역 경로>"` (새 터미널부터 적용).
   - 동기화되지 않는 로컬 복사본(예: 예전에 복사해 둔 `D:\도서 번역`)을 정본으로 쓰지 않는다.
2. **저장소**: `C:\workspace\acupoint_anatomy`에 GitHub 저장소를 clone(이미 있으면 `git pull`).
3. **미러 생성**: `cd C:\workspace` → `python acupoint_anatomy\scripts\sync_claude_skill.py`
   - `C:\workspace\.claude\skills\acupoint-anatomy\`와 `C:\workspace\CLAUDE.md`가 Drive 정본으로 만들어진다. `--check`로 차이만 볼 수 있다.
4. **세션 시작 자동 동기화(hook)**: `C:\workspace\.claude\settings.json`에 다음을 넣는다(파일이 있으면 `hooks` 항목만 합친다). Claude Code에서 `/hooks`로 확인할 수 있다.
   ```json
   {
     "hooks": {
       "SessionStart": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python \"C:/workspace/acupoint_anatomy/scripts/sync_claude_skill.py\" --quiet || true",
               "timeout": 120,
               "statusMessage": "[경혈해부] 스킬 규칙을 Google Drive 정본에 맞추는 중"
             }
           ]
         }
       ]
     }
   }
   ```
5. **MCP 서버 등록**: `python acupoint_anatomy\scripts\register_mcp.py`

## 3. 주간 DB 배치 주의

- 통합 생의학 마스터 DB 주간 배치(`AcupointMasterDB_WeeklySync`)는 **한 PC에만** 등록한다.
- 배치를 돌리는 PC의 프로젝트 경로는 반드시 Google Drive와 동기화되는 `도서 번역`이어야 한다. 2026-10-25에는 김재효연구실 PC의 동기화되지 않은 `D:\도서 번역`(10/12 상태)에서 배치가 돌아 Drive의 DB를 덮어썼다(2026-10-26 복구).

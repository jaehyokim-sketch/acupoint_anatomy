# [경혈해부] 스킬 규칙 — Google Drive 정본 기준 PC 설정 가이드

> 2026-10-26 결정: GOYANGSOON PC와 김재효연구실 PC는 모두 **Google Drive `도서 번역` 폴더의 정본**을 스킬 규칙으로 쓴다. 각 PC의 로컬 사본은 Drive를 그대로 따르는 읽기 전용 미러다.
>
> **같은 날 추가 결정 — `C:\workspace`의 모든 작업: 김재효연구실 PC ⇄ Google Drive 정본 → GOYANGSOON PC 로컬 미러.** 정책 파일은 Drive `도서 번역\.claude\drive_canonical_policy.json`(`editor_host` = 김재효연구실)이다.

## 0. PC 역할

| | 김재효연구실 PC (편집 PC) | GOYANGSOON PC (미러 PC) |
| :--- | :--- | :--- |
| Drive 정본(스킬 규칙·지침·`01_Framework`·`02_Master_Datasets`·`01_도서_번역_및_원전`, 각 저장소 Drive 폴더의 지침 파일) | 고친다 | **고치지 않는다** (PreToolUse hook이 막음) |
| 로컬 미러 | 세션 시작 hook으로 Drive와 맞춤 | 세션 시작 hook으로 Drive와 맞춤(읽기 전용) |
| 산출물(보고서·코드) | 커밋·푸시 → `deploy_to_gdrive.py` | 같음 |
| `sync_master_db.py` (Drive DB 갱신) | 실제 실행 | `--dry-run`만 (병합은 편집 PC) |
| `sync_skill_settings.py` | `--apply` 가능 | `--check`만 |
| 주간 DB 배치 | 실행 PC(`weekly_sync_host.txt`) | 건너뜀 |

- 미러 PC에서 규칙·정본 변경이 필요하면 바꿀 내용을 정리해 사용자에게 알리고, 편집 PC에서 반영한다.
- 배포 스크립트는 지침 파일(`CLAUDE.md`·`AGENTS.md`·`GEMINI.md`·`.claude/`·`.agents/`)을 Drive로 올리거나 지우지 않는다(Drive 쪽이 정본).

## 1. 무엇이 정본이고 무엇이 미러인가

| 정본 (Google Drive) | 로컬 미러 | 비고 |
| :--- | :--- | :--- |
| `도서 번역/.claude/skills/acupoint-anatomy/**` | `C:\workspace\.claude\skills\acupoint-anatomy\` | Claude Code 스킬 본문·FMA/초음파 스크립트·WORKLOG |
| `도서 번역/.claude/workspace_CLAUDE.md` | `C:\workspace\CLAUDE.md` | 로컬 워크스페이스 지침 |
| `도서 번역/01_Framework/` 정본·Layer B 등록부·DB 설계 | `acupoint_anatomy/framework/` | 저장소 사본(바뀌면 커밋) |
| `도서 번역/.agents/skills/acupoint-anatomy/SKILL.md` | `acupoint_anatomy/skill/SKILL.md` | 〃 |
| `도서 번역/02_Master_Datasets/` 마스터 DB(JSON·xlsx)·KJH xlsx·마스터 CSV·교재 2종·자침깊이·로직 원칙·ARI 데이터셋·`layer_b_reference_registry.json`·`FMA/acupoint_fma_mapping.json` | `acupoint_anatomy/data/` | 바이트 단위 미러. 교재·자침깊이 xlsx가 바뀌면 `mcp_reference_data.json` 자동 재생성. 바뀌면 커밋 |
| 다른 저장소의 Drive 배포 폴더에 있는 `CLAUDE.md`·`AGENTS.md`·`GEMINI.md`·`.claude/settings.json`·`.claude/skills|commands/`·`.agents/rules|skills/` | `C:\workspace\<저장소>\` 같은 경로 | 저장소↔Drive 폴더는 각 `deploy_to_gdrive.py`의 배포 경로로 찾는다(현재 `amari-gl-dmn` ↔ `논문작업\비평형열역학`) |
| `도서 번역/.agents/skills/huanglongxiang-scholar/` | `huanglongxiang-scholar/skill/` 등 | [황룡상] — `huanglongxiang-scholar/scripts/sync_skill_copies.py` |

- 미러는 `acupoint_anatomy/scripts/sync_claude_skill.py`가 **Drive → 로컬 단방향**으로 맞춘다.
- 로컬 미러를 직접 고치면 다음 동기화 때 `C:\workspace\.claude\skill_sync_backup\<시각>\`에 보관된 뒤 Drive본으로 덮어써진다. **규칙은 편집 PC에서 Drive 정본을 고친다.**
- Drive에 연결되지 않은 상태에서는 아무것도 바꾸지 않는다.

## 2. PC별 1회 설정

1. **Google Drive 확인**: Google Drive 데스크톱이 실행 중이고 `도서 번역` 폴더가 최신으로 동기화되는지 확인한다.
   - Drive 경로가 `G:\내 드라이브\도서 번역`이 아니면 사용자 환경변수를 설정한다: `setx ACUPOINT_DRIVE_ROOT "<Drive의 도서 번역 경로>"` (새 터미널부터 적용).
   - 동기화되지 않는 로컬 복사본(예: 예전에 복사해 둔 `D:\도서 번역`)을 정본으로 쓰지 않는다.
2. **저장소**: `C:\workspace\acupoint_anatomy`에 GitHub 저장소를 clone(이미 있으면 `git pull`).
3. **미러 생성**: `cd C:\workspace` → `python acupoint_anatomy\scripts\sync_claude_skill.py`
   - `C:\workspace\.claude\skills\acupoint-anatomy\`와 `C:\workspace\CLAUDE.md`가 Drive 정본으로 만들어진다. `--check`로 차이만 볼 수 있다.
4. **hook**: `C:\workspace\.claude\settings.json`(PC별 파일)에 다음을 넣는다(파일이 있으면 `hooks` 항목만 합친다). Claude Code에서 `/hooks`로 확인할 수 있다.
   - SessionStart 두 개: Drive → 로컬 미러([경혈해부]·지침·데이터, [황룡상]).
   - PreToolUse 하나: 정본·미러 편집 차단. 두 PC에 똑같이 넣는다. 편집 PC에서는 스크립트가 정책 파일을 보고 아무것도 막지 않는다.
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
             },
             {
               "type": "command",
               "command": "python \"C:/workspace/huanglongxiang-scholar/scripts/sync_skill_copies.py\" --apply --quiet || true",
               "timeout": 120,
               "statusMessage": "[황룡상] 스킬 규칙을 Google Drive 정본에 맞추는 중"
             }
           ]
         }
       ],
       "PreToolUse": [
         {
           "matcher": "Edit|Write|MultiEdit|NotebookEdit",
           "hooks": [
             {
               "type": "command",
               "command": "python \"C:/workspace/acupoint_anatomy/scripts/drive_canonical_guard.py\"",
               "timeout": 15
             }
           ]
         }
       ]
     }
   }
   ```
5. **MCP 서버 등록**: `python acupoint_anatomy\scripts\register_mcp.py`

## 3. 주간 DB 배치 (Google Drive `도서 번역` 기준)

- 통합 생의학 마스터 DB 주간 배치(`AcupointMasterDB_WeeklySync`, 일요일 03:00)는 **Google Drive `도서 번역` 안의 스크립트로만** 등록·실행한다. 2026-10-25에는 김재효연구실 PC의 동기화되지 않은 `D:\도서 번역`(10/12 상태)에서 배치가 돌아 Drive의 DB를 덮어썼다(2026-10-26 복구).
- **등록**(PC마다 1회, 기존 등록은 덮어씀): Google Drive의 `도서 번역\.agents\skills\acupoint-anatomy\scripts\register_weekly_task.cmd`를 실행한다.
  - Drive 밖 사본(예: `D:\도서 번역\…`)의 등록 스크립트는 등록을 거부한다.
  - 작업은 `cmd.exe /c "<Drive 경로>\weekly_sync.cmd"`로 등록된다. 예전 방식은 경로의 공백에서 실행 파일이 잘려(`G:\내`) 0x80070002로 실패했다.
- **실제 실행 PC**: Drive의 `02_Master_Datasets\weekly_sync_host.txt` 첫 줄에 적힌 컴퓨터 이름(현재 **김재효연구실**)만 배치를 실행한다. 다른 PC에 등록된 작업은 실행 시점에 건너뛰고 배치 로그에 그 사실만 남긴다. 담당 PC를 바꾸려면 이 파일의 이름만 고친다.
- **안전 점검**(`weekly_guard.py`): 프로젝트 경로에 "내 드라이브"/"My Drive"가 없으면 실행하지 않는다(Drive 경로 이름이 다른 PC는 `ACUPOINT_ALLOW_NON_DRIVE_ROOT=1`). `ACUPOINT_WEEKLY_DRYRUN=1`로 판정만 확인할 수 있다.
- 배치를 실행하려면 그 시각에 Google Drive 데스크톱이 실행 중이고 사용자가 로그온해 있어야 한다. 놓친 실행은 다음 로그온 때 실행된다(StartWhenAvailable).

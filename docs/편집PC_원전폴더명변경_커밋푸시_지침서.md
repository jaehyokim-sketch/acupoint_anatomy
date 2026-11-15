# 편집 PC(김재효연구실) 실행 지침서 — 11-09 원전 폴더명 변경 커밋·푸시

**작성 일자**: 2026-11-15 (GOYANGSOON PC에서 점검 후 작성)
**실행할 PC**: 김재효연구실(편집 PC) — PowerShell
**대상 저장소**: `C:\workspace\acupoint_anatomy` (GitHub `origin/main`)
**Drive 배포 폴더**: `D:\도서 번역\acupoint_anatomy`

---

## 1. 무엇을, 왜 하는가

2026-11-09 편집 PC에서 Antigravity로 다음 작업을 했지만 **Git에 커밋되지 않아** GitHub와 다른 PC(GOYANGSOON 등)에 전달되지 않았습니다. Drive 배포 폴더에만 반영되어 있습니다.

- `data/classics` 4대 원전 폴더명을 `한글명(한자명)` 형식으로 변경 (내용은 그대로)
- 『중국침구자구법통감(中國鍼灸刺灸法通鑑)』 7편 추가 (약 3.5 MB)
- 새 폴더명에 맞춰 코드·문서 9개 파일 수정

| 옛 폴더명 | 새 폴더명 | 파일 수 |
| :--- | :--- | ---: |
| `中国针灸穴位通鉴` | `중국침구혈위통감(中国针灸穴位通鉴)` | 41 |
| `针灸腧穴通考` | `침구수혈통고(针灸腧穴通考)` | 26 |
| `中国针灸证治通鉴` | `중국침구증치통감(中国针灸证治通鉴)` | 62 |
| `中国针灸经络通鉴` | `중국침구경락통감(中国针灸经络通鉴)` | 39 |
| (신규) | `중국침구자구법통감(中國鍼灸刺灸法通鑑)` | 7 |

**수정된 9개 파일**: `README.md`, `WORKLOG.md`, `data/README.md`, `data/mcp_reference_data.json`, `data/classics/index.json`, `mcp_server/server.py`, `mcp_server/acupoint_core.py`, `mcp_server/remote_backend.py`, `mcp_server/remote_server.py`

**GOYANGSOON에서 확인한 사실 (2026-11-15)**
- Drive의 새 폴더 4개는 로컬 옛 폴더와 파일 내용이 바이트 단위로 같습니다(이름만 바뀜).
- 2026-11-05 이후 GitHub에 올라간 커밋 중 위 9개 파일이나 `data/classics`를 건드린 것은 없습니다. 따라서 커밋 후 `git pull`에서 충돌이 나지 않습니다.
- 지금 Drive `data/classics`에는 옛 이름 폴더 4개와 새 폴더 5개가 함께 있습니다(정리 필요, 5단계).

**이 작업이 끝나지 않으면**: 다른 PC의 MCP 원전 검색에서 『자구법통감』이 빠지고, `CLAUDE.md`(새 폴더명 기준)와 실제 로컬 폴더가 맞지 않습니다.

---

## 2. 1단계 — 변경 확인

```powershell
cd C:\workspace\acupoint_anatomy
git fetch origin
git status --short -- README.md WORKLOG.md data/README.md data/mcp_reference_data.json data/classics mcp_server
```

**정상 결과**
- 옛 원전 폴더 4개의 파일이 삭제(` D`)로 표시
- 새 폴더 5개가 새 파일(`??`)로 표시
- 9개 파일이 수정(` M`)으로 표시

결과가 이와 다르면 진행하지 말고 7절(문제 해결)을 보세요.

---

## 3. 2단계 — MCP 서버가 새 폴더를 찾는지 확인

```powershell
Get-ChildItem data\classics -Directory | Select-Object Name
Select-String -Path mcp_server\server.py -Pattern '\("\S+", "[^"]+\(' | Select-Object -ExpandProperty Line
```

`server.py`의 `CORE_BOOKS`에 적힌 폴더 5개가 `data\classics`에 모두 있어야 합니다.

> 주의: MCP 서버는 없는 폴더를 **오류 없이 건너뜁니다**. 이 확인을 하지 않으면 원전 하나가 검색에서 빠져도 알아채기 어렵습니다.

---

## 4. 3단계 — 이 변경만 커밋하고 푸시

```powershell
git add -A -- README.md WORKLOG.md data/README.md data/mcp_reference_data.json data/classics mcp_server/acupoint_core.py mcp_server/remote_backend.py mcp_server/remote_server.py mcp_server/server.py
git status --short
```

원전 파일 대부분이 이름 변경(`R`), 자구법통감 7편이 추가(`A`), 9개 파일이 수정(`M`)으로 보이면 정상입니다. 이어서:

```powershell
git commit -F - @'
refactor(classics): 원전 폴더명을 한글명(한자명) 형식으로 통일, 《中国针灸刺灸法通鉴》 추가 (2026-11-09)

- data/classics 4대 원전 폴더명 변경(내용 동일), 중국침구자구법통감 7편 추가
- MCP 서버(server.py CORE_BOOKS, remote_backend.py REMOTE_BOOKS, acupoint_core.py, remote_server.py) 갱신
- data/classics/index.json, data/mcp_reference_data.json, README·data/README·WORKLOG 갱신
'@
git pull --rebase --autostash origin main
git push origin main
```

- `'@`는 반드시 **줄 맨 앞(0열)** 에 있어야 합니다. 들여쓰면 PowerShell 구문 오류가 납니다.
- `--autostash`는 커밋하지 않은 다른 수정 파일이 있어도 pull이 멈추지 않게 합니다.
- `git pull`로 GOYANGSOON에서 올린 2026-11-15 커밋들(핸드북 포털 영문판, 주치증 KCD 정정, 포털 생성기 이관, 조회수 배지 등)이 함께 내려옵니다.

---

## 5. 4단계 — Drive의 옛 원전 폴더 정리

먼저 무엇이 지워질지 확인합니다(실제로 지우지 않음).

```powershell
python -u deploy_to_gdrive.py --prune --dry-run
```

- **삭제 예정 목록이 옛 원전 폴더 4개와 그 안의 파일뿐이면** 실제로 정리합니다.
  ```powershell
  python -u deploy_to_gdrive.py --prune
  ```
- **목록에 다른 파일이 섞여 있으면** `--prune`을 쓰지 말고, 탐색기에서 `D:\도서 번역\acupoint_anatomy\data\classics\` 아래 옛 이름 폴더 4개(`中国针灸穴位通鉴`, `针灸腧穴通考`, `中国针灸证治通鉴`, `中国针灸经络通鉴`)만 직접 삭제한 뒤 `python -u deploy_to_gdrive.py`를 실행합니다.

---

## 6. 5단계 — 다른 PC(GOYANGSOON 등)에서

```powershell
cd C:\workspace\acupoint_anatomy
git pull --ff-only
```

확인:

```powershell
Get-ChildItem data\classics -Directory | Select-Object Name
```

새 폴더 5개만 보이면 완료입니다. 이후 MCP `search_classic_records`로 『자구법통감』(`classic_book`에 `刺灸法通鉴`)을 검색할 수 있습니다.

---

## 7. 문제 해결

### 1단계에서 변경이 보이지 않는 경우
11-09 작업이 로컬 저장소가 아니라 Drive 배포 폴더에만 들어갔을 수 있습니다. 이때는 Drive본을 로컬로 가져온 뒤 1단계부터 다시 합니다.

```powershell
$D = 'D:\도서 번역\acupoint_anatomy'
$L = 'C:\workspace\acupoint_anatomy'
# 새 원전 폴더 5개 가져오기
Get-ChildItem "$D\data\classics" -Directory | Where-Object { $_.Name -match '\(' } | ForEach-Object {
  robocopy $_.FullName "$L\data\classics\$($_.Name)" /E /NJH /NJS /NP
}
# 9개 파일 가져오기
'README.md','WORKLOG.md','data\README.md','data\mcp_reference_data.json','data\classics\index.json',
'mcp_server\server.py','mcp_server\acupoint_core.py','mcp_server\remote_backend.py','mcp_server\remote_server.py' |
  ForEach-Object { Copy-Item "$D\$_" "$L\$_" -Force }
# 옛 원전 폴더 4개는 Git에서 제거
cd $L
git rm -r -q -- "data/classics/中国针灸穴位通鉴" "data/classics/针灸腧穴通考" "data/classics/中国针灸证治通鉴" "data/classics/中国针灸经络通鉴"
```

### `git pull --rebase`에서 충돌이 난 경우
이 지침서 작성 시점에는 충돌할 커밋이 없었습니다. 그래도 충돌이 나면 `git rebase --abort`로 되돌리고, `git status` 결과를 Claude에게 보여 주세요.

### 푸시가 거부된 경우 (`rejected`, `fetch first`)
그사이 다른 PC가 푸시한 것입니다. `git pull --rebase --autostash origin main` 후 다시 `git push origin main`.

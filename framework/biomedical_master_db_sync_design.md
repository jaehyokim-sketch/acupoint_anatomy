# 경혈 생의학 통합 마스터 DB 동기화 설계 (Master DB Sync Design v3.0)

> **문서 성격**: 설계 및 구현 기록. **구현 완료 (2026-10-04)** — 공용 스크립트 `.agents/skills/acupoint-anatomy/scripts/sync_master_db.py` (Claude Code·Antigravity 공용), `migrate-v3`·초기 `scan-local` 실행 완료. [`acupoint_anatomical_logic_framework.md`](acupoint_anatomical_logic_framework.md) Rank 6 Layer A의 데이터 갱신 규칙을 구체화한다.
> **작성일**: 2026-10-04
> **대상 데이터**: `02_Master_Datasets/경혈_생의학_신경반사_마스터DB.json` (단일 진실원천) 및 `.xlsx` (파생물)
> **대상 폴더**: `G:\내 드라이브\학습자료\실험 및 연구 논문` (하위 폴더 포함)

---

## 0. 현황 진단 (2026-10-04 실측)

| 항목 | 실측값 | 문제 |
| :--- | :--- | :--- |
| 로컬 폴더 파일 | PDF 1,717 + HWP 40 (하위 폴더 6개 포함) | 색인은 PDF만 대상 |
| JSON `papers` 색인 | 1,673편 (ID 1~1673) | **미색인 97편** (예: 공최 LU6 치질 관련 논문 4편), 삭제 0편 |
| DOI / PMID 보유 | 526편 / 1편 | PMID 거의 없음, 외부 메타 보강 없음 |
| 경혈 감지 | 609편 | 나머지 1,064편은 역색인에서 제외 |
| 스키마 드리프트 | 일부 레코드의 `id`·`detected_acupoints`·`parsed_filename`이 문자열로 저장 | 코드에서 타입 분기 필요, 검증 없음 |
| API 수집 논문 | 경혈 항목 `landmark_papers`에만 32편 (출처 미표기 9편) | `papers`·역색인·시트 2·3에 **미반영** |
| xlsx 저장 로직 | 시트 1의 대상 경혈 1행, 8~10열(첫 논문)만 갱신 | 13·14열(소장논문수·ID) 미갱신, 시트 2·3 미갱신 |
| 전체 재색인 스크립트 | `build_local_papers_index.py` → 별도 파일 `local_papers_index.json` 출력, ID를 처리 완료 순서로 부여 | 재실행 시 **ID가 바뀌어** 역색인·참조가 깨짐, 통합 DB 재병합 절차 없음 |
| 하드코딩 | `_metadata.total_local_papers=1673`, 시트명 `..._1673편` | 갱신 시 불일치 |

결론: 현재 구조는 "한 번 만든 스냅샷"이며, 로컬 추가 파일과 API 수집 결과를 **지속적으로** 반영하는 경로가 없다.

---

## 1. 설계 목표

| ID | 요구사항 |
| :--- | :--- |
| R1 | 로컬 폴더의 추가·수정·이동·삭제가 증분 스캔으로 JSON·xlsx에 반영된다. |
| R2 | PubMed·OpenAlex·Crossref·Europe PMC로 수집한 메타데이터가 `papers` 레지스트리·역색인·3개 시트 모두에 반영된다. |
| R3 | 논문 ID는 영구적이다. 기존 1~1673은 보존하고 신규는 순차 증가한다. |
| R4 | 재실행해도 결과가 같다(멱등). 중복 제거는 DOI → PMID → 제목 해시 3단계에 콘텐츠 해시(로컬)를 더한다. |
| R5 | JSON이 단일 진실원천이고 xlsx는 JSON에서 전면 재생성한다. 수기 편집은 JSON에만 한다. |
| R6 | 모든 갱신은 `_metadata.sync_log`에 기록되며, 보고서의 "외부 검색 로그 표"(프레임워크 5절 8항)는 이 로그에서 생성한다. |
| R7 | 트리거는 Rank 6 진입 자동 실행, 수동 CLI, 주기 배치의 3중으로 둔다. |
| R8 | 기존 소비자(`sync_biomedical_papers.py`의 `search_local_papers`)가 읽는 키(`papers`, `acupoint_inverted_index`, `id`, `filename`, `snippet`, `doi`, `pmid`, `parsed_filename`)는 유지한다. |

---

## 2. 데이터 모델 (JSON v3.0)

### 2.1 `_metadata`
```json
{
  "version": "3.0_unified",
  "schema_version": 3,
  "source_local_dir": "G:\\내 드라이브\\학습자료\\실험 및 연구 논문",
  "counts": {"papers_total": 0, "local_active": 0, "local_missing": 0, "external": 0, "acupoints_indexed": 0},
  "last_local_scan": {"at": "", "files_seen": 0, "added": 0, "updated": 0, "moved": 0, "missing": 0, "duration_ms": 0},
  "last_api_sync": {"at": "", "acupoint": "", "sources": {"pubmed": "ok", "openalex": "ok", "crossref": "ok"}},
  "sync_log": []
}
```
- `sync_log` 항목: `{ts, trigger(rank6|cli|batch), action(scan-local|sync-api|export|validate), source, acupoint, query, http_status, fetched, deduped, added, duration_ms, note}`. JSON에는 최근 500건만 롤링 보관하고 전체는 `02_Master_Datasets/sync_logs/YYYY-MM.jsonl`에 추가 기록한다.

### 2.2 `papers[]` — 로컬·외부 통합 레지스트리
| 필드 | 타입 | 설명 |
| :--- | :--- | :--- |
| `id` | int | 영구 ID. 기존 1~1673 유지, 신규는 `max(id)+1` |
| `origin` | enum | `local` / `pubmed` / `openalex` / `crossref` / `europepmc` / `manual` |
| `status` | enum | `active` / `missing`(로컬 파일 유실) / `superseded`(병합으로 대체) |
| `title`, `authors`, `journal`, `year`, `volume_issue` | str/int | 공통 서지 |
| `doi` | str | `normalize_doi` 적용값(소문자, 접두 URL 제거) |
| `pmid` | str | 숫자 문자열 |
| `abstract_snippet` | str | ≤300자 (기존 `snippet` 키도 동일 값으로 유지, R8) |
| `detected_acupoints` | list[str] | 표준 코드(`ST36` 형식). 외부 논문은 대상 경혈 + 제목·초록에서 감지된 경혈 |
| `keywords`, `mesh` | list[str] | 외부 메타에서 보강 |
| `language` | str | `en` / `chi` / `kor` 등 |
| `evidence_level` | str\|null | Oxford CEBM 단계(수기 또는 규칙 분류), ARI v3.0 $S_{reflex}$ 루브릭 입력 |
| `added_at`, `updated_at` | ISO | |
| **로컬 전용** `file_path`(루트 기준 상대경로), `filename`, `ext`, `file_size`, `mtime`, `content_hash`(SHA-1, 첫 4MB), `parsed_filename{}`, `text_extracted`(bool) | | 기존 절대경로 `file_path`는 마이그레이션 시 상대경로로 변환 |
| **외부 전용** `source_db`, `source_query`, `fetched_at`, `url`, `cn_title`, `cn_abstract` | | 중국어 보강은 ChinaDOI 핸들러·공식 사이트 DOI 페이지에서 선택 수집 |
| `also_found_in` | list[str] | 동일 DOI가 여러 소스에서 확인된 경우 소스 목록 |

### 2.3 `acupoint_inverted_index`
- `표준코드 → [paper_id, ...]`. 로컬·외부 논문을 모두 포함한다. 소비자는 `papers[id].origin`으로 구분한다.

### 2.4 `file_manifest`
- `{relpath: {"id": int, "size": int, "mtime": float, "hash": str}}`. 증분 스캔의 비교 기준이다.

### 2.5 경혈 항목(기존 키 유지 + 추가)
- 파생값(재계산): `local_paper_ids`, `local_papers_count`, `local_papers_sample`
- 추가: `landmark_paper_ids`(레지스트리 ID 참조), `external_paper_ids`, `external_papers_count`, `last_api_sync_at`
- 기존 `landmark_papers`(객체 배열)는 마이그레이션에서 레지스트리로 이관하고, 1개 버전 동안 읽기 호환용으로 ID 기반으로 재생성해 둔다.

---

## 3. 처리 파이프라인

### 3.1 `scan-local` — 로컬 증분 스캔
1. `os.walk`로 하위 폴더까지 PDF·HWP·HWPX를 수집하고 현재 manifest(상대경로, size, mtime)를 만든다.
2. 이전 `file_manifest`와 비교한다.
   - **신규**: manifest에 없는 경로 → 파싱 후 새 ID.
   - **변경**: size 또는 mtime 변화 → 해시 재계산, 다르면 재파싱(ID 유지).
   - **이동/개명**: 경로는 없지만 동일 해시가 존재 → `file_path`·`filename`만 갱신(ID 유지).
   - **삭제**: 경로·해시 모두 없음 → `status=missing`. ID와 역색인은 유지하되 검색 결과에 "소장 파일 유실"을 표시한다.
3. 신규·변경 파일만 파싱한다. PDF는 PyMuPDF로 첫 2쪽, HWP는 `olefile`로 PrvText 스트림(미리보기 텍스트), 실패 시 파일명 메타만 쓴다.
4. DOI/PMID를 추출한다. `--enrich` 옵션이 있으면 DOI 보유 레코드를 PubMed(esummary/efetch)·OpenAlex(`works/doi:`)로 보강한다(제목·저자·저널·초록·MeSH·PMID). 요청 제한(NCBI 3 req/s, 키 설정 시 10 req/s)을 지킨다.
5. 경혈 감지는 기존 사전(361 CSV의 코드·한글·한자)에 병음을 추가해 수행하고 표준 코드로 저장한다.
6. ID는 신규 파일을 상대경로 기준으로 정렬한 뒤 순차 부여한다(스레드 완료 순서에 의존하지 않는다).
7. 역색인과 경혈 항목 파생값을 전량 재계산한다(수천 건 규모라 1초 미만).
8. 저장은 원자적으로 한다. 임시 파일에 쓴 뒤 교체하고, 직전본은 `02_Master_Datasets/backup/`에 1세대 보관한다. 이어서 `export-xlsx`와 `validate`를 실행한다.

### 3.2 `sync-api` — 외부 API 수집 적재 (Rank 6 필수 단계)
1. 검색은 기존 `sync_biomedical_papers.py`의 함수를 재사용하되 쿼리를 보강한다. PubMed는 `[Journal]` 필터 쿼리(《中国针灸》·《针刺研究》)를 추가하고, OpenAlex는 `doi_starts_with:10.13703` / `10.13702`를 저널별로 호출하며, Crossref는 보완, Europe PMC는 PubMed 장애 시 폴백으로 둔다.
2. 후보를 정규화(DOI 소문자·접두 제거, PMID 문자열, 제목 슬러그)한 뒤 **레지스트리 전체**를 대상으로 3단계 중복 제거를 수행한다(현재는 `landmark_papers`만 대상이라 로컬 소장본과 중복 적재된다).
3. 신규 후보는 `papers`에 `origin=<소스>`로 추가하고 ID를 부여한다. `detected_acupoints`에는 대상 경혈과 제목·초록에서 감지된 경혈을 넣고 역색인을 갱신한다.
4. 기존 로컬 레코드와 DOI가 일치하면 **병합**한다. 로컬 레코드에 `pmid`·`abstract_snippet`·`mesh`·`keywords`를 보강하고 `also_found_in`에 소스를 추가한다. 이렇게 소장 PDF와 외부 메타가 하나의 레코드로 연결된다.
5. 경혈 항목의 `landmark_paper_ids`·`external_paper_ids`·`external_papers_count`·`last_api_sync_at`을 갱신한다. 보고서에는 CEBM 상위 N편만 표시하되 레지스트리에는 상한을 두지 않는다.
6. 소스별 HTTP 상태·쿼리·건수를 `sync_log`에 기록한다. 소스 실패는 `http_status`와 `note`에 남기고 조용히 건너뛰지 않는다(프레임워크 Rank 6 "성공 판정과 실패 처리" 규칙).

### 3.3 `export-xlsx` — 파생 워크북 전면 재생성
- JSON에서 모든 시트를 다시 만든다(덮어쓰기). 시트명의 건수 접미사는 제거를 권고한다: `생의학_신경반사_마스터DB`, `로컬_논문_역색인`, `논문_전수_색인`. 신설: `외부_수집_논문`, `동기화_로그`.
- 기존 3개 시트의 열 순서는 유지하고 열을 **추가만** 한다.
  - 시트 1: `외부수집논문수`, `최종API동기화` 추가. 모든 경혈 행의 소장논문수·ID·대표 논문을 갱신한다(현재는 대상 1행만).
  - 시트 2: 변경 없음(전 행 재계산).
  - 시트 3: `출처(origin)`, `상태`, `콘텐츠해시`, `추가일`, `PMID`(보강값) 추가.
- `_metadata.total_local_papers` 같은 고정 건수는 `counts`의 계산값으로 대체한다.

### 3.4 `validate` — 저장 후 정합성 검증
| 검사 | 기준 |
| :--- | :--- |
| ID | 정수, 유일, 결번 허용 |
| 역색인 | 모든 ID가 `papers`에 존재, 코드가 표준 형식 |
| manifest ↔ papers | `status=active`인 로컬 레코드와 manifest 1:1 |
| 시트 3 행수 | `papers` 중 `superseded` 제외 건수와 일치 |
| 시트 2 소장논문수 | 역색인 길이(로컬 active만)와 일치 |
| 중복 | 정규화 DOI·PMID 중복 0건 |
| 타입 | 문자열화된 `id`·`detected_acupoints`·`parsed_filename` 0건 |
- 하나라도 실패하면 백업본으로 롤백하고 종료 코드 1을 반환한다. Rank 6에서는 이 경우 "DB 갱신 실패"를 외부 검색 로그 표에 기록하고 $S_{reflex}$ 채점을 보류한다.

---

## 4. 트리거 설계

| 트리거 | 시점 | 실행 범위 | 비고 |
| :--- | :--- | :--- | :--- |
| **Rank 6 진입(자동)** | Tier 2·3 분석마다 | `scan-local`(증분, 수 초) → `sync-api --code <대상>` → `export-xlsx` → `validate` | 프레임워크 필수 단계. `--dry-run`으로 미리 확인 후 실행 |
| **수동 CLI** | 사용자 요청 | 개별 서브커맨드 또는 `--full-rescan` | 폴더 대량 추가 후 |
| **주기 배치** | 주 1회(Windows 작업 스케줄러) | `scan-local --enrich` → `export-xlsx` → `validate` | Google Drive 동기화가 끝나는 시간대로 설정 |

- 파일 감시(watchdog)는 Google Drive 가상 파일시스템에서 이벤트 누락과 중복이 잦아 채택하지 않는다. manifest 비교 방식이 신뢰할 수 있다.

---

## 5. CLI 설계 — 단일 진입점 `sync_master_db.py`

```bash
python sync_master_db.py scan-local [--full-rescan] [--enrich] [--dry-run]
python sync_master_db.py sync-api --code ST36 --name-kr 족삼리 --name-cn 足三里 --pinyin Zusanli [--dry-run]
python sync_master_db.py export-xlsx
python sync_master_db.py validate
python sync_master_db.py all --code ST36 --name-kr 족삼리 --name-cn 足三里 --pinyin Zusanli [--dry-run]   # Rank 6 표준 호출
python sync_master_db.py migrate-v3 [--dry-run]   # 1회 실행
```

- 배치 위치: Claude Code 측은 `.claude/skills/acupoint-anatomy/scripts/sync_master_db.py`, Antigravity 측은 `.agents/skills/acupoint-anatomy/scripts/`에 통합. 어느 쪽이든 `normalize_doi`, `search_pubmed`, `search_openalex_chinese_proxy`, `search_crossref_chinese_proxy`, `load_acupoint_dictionary`, `process_single_pdf`는 기존 두 스크립트에서 import하여 재사용한다.
- 종료 코드: 0 성공, 1 검증 실패(롤백됨), 2 외부 소스 전부 실패.

---

## 6. 마이그레이션 (1회, `migrate-v3`)

1. JSON·xlsx 백업.
2. 문자열화 레코드 교정(`id`→int, `detected_acupoints`→list, `parsed_filename`→dict).
3. 모든 `papers`에 `origin="local"`, `status="active"`, `ext`, `file_size`, `mtime`, `content_hash` 채움(1,673편 해시 계산, 수 분 소요). `file_path`를 상대경로로 변환.
4. 경혈 항목의 `landmark_papers` 32편을 레지스트리로 이관(ID 1674~). `source_db`가 없는 9편은 `origin="manual"`. DOI가 로컬 레코드와 일치하면 병합.
5. `file_manifest` 생성.
6. `scan-local` 실행으로 미색인 97편·HWP 40편 처리.
7. `export-xlsx` → `validate`.
8. `_metadata.version = "3.0_unified"`.

---

## 7. 프레임워크·스킬 연계

- Rank 6 Layer A: "통합 DB는 본 파이프라인으로만 갱신한다"를 명시하고, 외부 검색 로그 표는 `sync_log`에서 생성한다.
- 보고서의 Layer A 인용은 `papers.id`를 근거 포인터로 쓴다. ARI v3.0 루브릭의 "근거 포인터 기록" 요구와 직접 연결된다.
- `evidence_level` 필드는 $S_{reflex}$ 5단계 판정(인체 연구·동물 연구·종설 구분)의 입력이 된다.

---

## 8. 결정 필요 사항과 리스크

| 항목 | 내용 | 권고 |
| :--- | :--- | :--- |
| 시트명 변경 | 건수 접미사 제거 시 외부 참조가 깨질 수 있음 | **결정·적용 완료**: `로컬_논문_역색인`, `논문_전수_색인`으로 변경, `외부_수집_논문`·`동기화_로그` 신설. 프레임워크 Rank 6 서술 동기화 |
| HWP 추출 | `olefile` 설치 필요, 미리보기 텍스트만 추출 가능 | 설치 확인. 소장 HWP 40편은 구형 HWP 3.0 포맷(OLE 아님)이라 본문 추출 불가 → 파일명 메타만 색인(`text_extracted=false`) |
| `--enrich` 비용 | DOI 526편 보강 시 NCBI 무키 기준 약 3~4분 | 주기 배치에서만 실행, `NCBI_API_KEY` 설정 권장 |
| 스크립트 배치 | `.agents`는 읽기 전용 | **결정·적용 완료**: 사용자 승인으로 `.agents/skills/acupoint-anatomy/scripts/sync_master_db.py`에 공용 배치(기존 두 스크립트는 수정하지 않음). `.claude` 래퍼는 이 경로를 호출 |
| 경혈 감지 정밀도 | 한글 2자 이름(예: 합곡) 오탐 가능 | 코드·한자 일치를 우선하고 한글 단독 일치는 가중치 낮게 처리, 추후 검수 열 추가 |

---

## 9. 구현 메모 (2026-10-04)

| 항목 | 내용 |
| :--- | :--- |
| 실행 결과 | `migrate-v3`: 경혈 키 병합 106건, papers 1,673편 정규화, landmark 32편 이관(신규 27·병합 5), 동일 DOI 중복 PDF 4편 duplicate. `scan-local`: 파일 1,770편 확인, 신규 101편(PDF 97·HWP 4) 추가, 중복 5편 추가 표시, 8.8초 소요 |
| 현재 규모 | 레지스트리 1,806편(로컬 active 1,765 · duplicate 5 · superseded 12 · 외부 36), 경혈 291개 색인, 시트1 291행 |
| 긴 경로 | 전체 경로 260자 초과 파일 3편이 `exists()` 실패로 유실 판정되던 문제를 확장 경로 접두(`\\?\`)로 해결(`lp()` 헬퍼) |
| 중복 상태 | 같은 DOI의 로컬 PDF가 여럿이면 최소 ID만 active, 나머지 `status=duplicate`·`duplicate_of`. 역색인·검증에서는 제외, 시트 3에는 상태 열로 표시 |
| DOI 검증 | `normalize_doi`가 `10.xxxx/...` 형식이 아니면 빈 값 처리(출판사명이 DOI 칸에 들어간 구 레코드 교정) |
| 셀 정화 | PDF 추출 텍스트의 제어 문자를 스니펫 생성 시와 xlsx 기록 시 제거(openpyxl IllegalCharacterError 방지) |
| 로그 | `_metadata.sync_log`(최근 500건) + `02_Master_Datasets/sync_logs/YYYY-MM.jsonl` 영구 기록. 백업은 `02_Master_Datasets/backup/`에 1세대 보관 |
| manifest 규칙 | manifest는 디스크 파일 단위로 추적하며 duplicate 레코드도 포함한다(초기 구현은 active만 포함해 같은 파일 4편이 스캔 시 재등록됨 → superseded 처리 후 규칙 수정). 스캔 시 상태 복귀는 `missing`→`active`만 허용하고 `duplicate`는 유지 |
| 배치 옵션 | `scan-local --enrich --enrich-limit N`으로 보강 건수를 제한해 시험 실행 가능. 주간 배치 `weekly_sync.cmd`(작업 스케줄러 `AcupointMasterDB_WeeklySync`, 일요일 03:00)는 `--trigger batch scan-local --enrich` 전량 실행, 로그는 `sync_logs/batch_YYYYMMDD.log` |
| Crossref 필터 | `query.bibliographic`의 느슨한 매칭 때문에 제목·초록에 경혈 코드·병음이 없는 결과는 제외(LU6 시험 적재에서 무관 8편 superseded) |
| 미구현·후속 | ChinaDOI/공식 사이트 중국어 원제 보강(`cn_title`) 자동 수집, `evidence_level` 자동 분류, Windows 작업 스케줄러 배치 등록, 기존 보고서 7건의 Layer A 재인용(`papers.id` 포인터) |

## 10. 경혈 연결 정확도 개정 (2026-10-23)

경혈 병음이 지명·기관명과 같거나(太原 Taiyuan → LU9, 商丘 Shangqiu → SP5, 天府 Tianfu → LU3), 코드가 다른 약어와 같아(Sp5 = 삼차신경 척수핵) 무관 논문이 경혈에 연결되던 문제를 고쳤다. 계기: LU9 역색인 41편 중 실제 LU9 자극 연구 15편(LU09 보고서), SP5 33편 중 6편(SP05 보고서).

| 항목 | 변경 |
| :--- | :--- |
| 경혈 언급 판정 `acupoint_mentioned()` | `sync-api`의 모든 후보(PubMed·OpenAlex·Crossref·Europe PMC)는 제목+초록 **전문**에 경혈이 경혈로서 나올 때만 연결한다. 인정: ① 대문자 코드(`LU9`·`LU 9`·`LU-9`·`LU09`) ② 혼합 대소문자 코드(`Gb21`, 침구 맥락 있을 때만, `Sp`는 제외) ③ 한자명(뒤에 市·县·区·省·大学·医院 등이 오면 제외) ④ 병음(침구 맥락이 있고, 뒤에 City·Province·University·Hospital·First·People's 등이 오지 않을 때). 기존 레코드에 병합될 때도 같은 검사를 거친다. 제외 후보는 `_metadata.relevance_rejections[<코드>]`(최근 200건)에 사유와 함께 남는다 |
| PubMed 쿼리 | 경혈 용어를 `[tiab]`(제목·초록)으로 한정 — 저자 소속(예: 太原 소재 병원) 적중 차단 |
| 로컬 PDF 감지 | 코드 패턴을 대소문자 구분으로, 한자명 패턴에 지명·기관명 후행 제외를 적용. 반영하려면 `scan-local --full-rescan` |
| 로컬 사본 중복 | DOI 없는 로컬 PDF가 정규화 제목+연도로 같으면 최소 ID만 active, 나머지 `status=duplicate`·`duplicate_reason`(`mark_local_title_duplicates`). `scan-local`·`relink`에서 실행 |
| `relink` 명령(신규) | 외부 레코드(manual 제외)의 제목+초록을 PMID(efetch)·DOI(OpenAlex)로 다시 받아 경혈 연결을 재검사하고, 실패한 연결을 제거한다. 제거 내역은 레코드의 `relink_removed[]`(코드·사유·초록 전문 여부·시각)에 남아 되돌릴 수 있다. 초록을 못 받은 레코드는 확실한 경우만 제거 |
| 병음 저장 | `sync-api`가 경혈 항목에 `pinyin`을 저장한다(`relink`는 과거 레코드의 병음을 `sync_log` PubMed 쿼리에서 복원) |
| 실행 결과 | `relink`: 외부 341편 재검사(초록 재수집 341편) → 연결 38건 제거(LU9 15, LU6 12, LU3 5, SP5 3, GB21·CV4·GB39 각 1), 로컬 사본 134편 duplicate 표시. validate OK. 제거된 연결은 모두 각 보고서가 이미 '오적중'으로 판정해 인용하지 않은 논문이었다 |
| 로컬 감지 보완 | 1차 전면 재스캔에서 대문자 전용 규칙 때문에 "Li 4"·"St36"·"St-36" 표기 논문(Hsieh 2001, Zhu 2004 등)이 빠졌다. 침구 맥락이 있을 때 혼합 대소문자 코드(`Sp` 제외)와 병음(`KNOWN_PINYIN` + 항목 `pinyin`)도 인정하도록 보완 |
| 연결 보존 필드 | `api_linked_acupoints`: sync-api가 초록으로 확인해 기존 레코드에 붙인 경혈. `manual_linked_acupoints`: 보고서 Layer A 표에서 사람이 확인한 경혈(2026-10-23, 11개 보고서의 경혈-논문 연결 126건 등록(LU03-LU04 통합 보고서의 8편은 LU3·LU4 양쪽) — 예: papers.id 294 Liu 2020 Neuron은 초록에 'ST36' 표기가 없어 자동 규칙으로는 확인 불가). 두 필드는 `scan-local`(전면 재스캔 포함)에서 본문 감지와 합집합으로 유지되고, `relink`에서도 제거하지 않는다 |
| 전면 재스캔 결과 | 1차(대문자 전용): KI8 138→2, BL41 121→0, LI20 153→27, BL49 135→54 등 대소문자 무시 오적중(예: 'Li 20', 'ki8') 대량 제거. 2차(혼합 대소문자·병음 보완 후, 272 s): 오적중 제거는 유지(KI8 2, BL41 0, LI20 27, BL49 54)하면서 진짜 연결 회복·증가 — ST36 109→111, LI4 74→78, PC6 33→34, LU9 9→10. 로컬 사본 duplicate 164편. validate OK |
| 백업 | `02_Master_Datasets/backup/sync_master_db.py.20261023_before_relink.bak`, `…마스터DB_20261023_before_relink.json`·`.xlsx` |

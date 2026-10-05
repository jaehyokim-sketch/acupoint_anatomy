# 경혈 생의학 통합 마스터 DB 동기화 설계 (Master DB Sync Design v3.0)

> **문서 성격**: 설계 및 구현 기록. **구현 완료 (2026-10-04)** — 공용 스크립트 `scripts/sync_master_db.py`, `migrate-v3`·초기 `scan-local` 실행 완료. [`acupoint_anatomical_logic_framework.md`](acupoint_anatomical_logic_framework.md) Rank 6 Layer A의 데이터 갱신 규칙을 구체화한다.
> **작성일**: 2026-10-04
> **대상 데이터**: `data/경혈_생의학_신경반사_마스터DB.json` (단일 진실원천) 및 `.xlsx` (파생물)
> **대상 폴더**: 로컬 소장 논문 디렉토리 (환경변수 `ACUPOINT_PAPERS_DIR` 또는 상위 학습자료 폴더)

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
- `sync_log` 항목: `{ts, trigger(rank6|cli|batch), action(scan-local|sync-api|export|validate), source, acupoint, query, http_status, fetched, deduped, added, duration_ms, note}`. JSON에는 최근 500건만 롤링 보관하고 전체는 `data/sync_logs/YYYY-MM.jsonl`에 추가 기록한다.

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
8. 저장은 원자적으로 한다. 임시 파일에 쓴 뒤 교체하고, 직전본은 `data/backup/`에 1세대 보관한다. 이어서 `export-xlsx`와 `validate`를 실행한다.

### 3.2 `sync-api` — 외부 API 수집 적재 (Rank 6 필수 단계)
1. 검색은 기존 `sync_biomedical_papers.py`의 함수를 재사용하되 쿼리를 보강한다. PubMed는 `[Journal]` 필터 쿼리(《中国针灸》·《针刺研究》)를 추가하고, OpenAlex는 `doi_starts_with:10.13703` / `10.13702`를 저널별로 호출하며, Crossref는 보완, Europe PMC는 PubMed 장애 시 폴백으로 둔다.
2. 후보를 정규화(DOI 소문자·접두 제거, PMID 문자열, 제목 슬러그)한 뒤 **레지스트리 전체**를 대상으로 3단계 중복 제거를 수행한다.
3. 신규 후보는 `papers`에 `origin=<소스>`로 추가하고 ID를 부여한다. `detected_acupoints`에는 대상 경혈과 제목·초록에서 감지된 경혈을 넣고 역색인을 갱신한다.
4. 기존 로컬 레코드와 DOI가 일치하면 **병합**한다. 로컬 레코드에 `pmid`·`abstract_snippet`·`mesh`·`keywords`를 보강하고 `also_found_in`에 소스를 추가한다.
5. 경혈 항목의 `landmark_paper_ids`·`external_paper_ids`·`external_papers_count`·`last_api_sync_at`을 갱신한다.
6. 소스별 HTTP 상태·쿼리·건수를 `sync_log`에 기록한다.

### 3.3 `export-xlsx` — 파생 워크북 전면 재생성
- JSON에서 모든 시트를 다시 만든다(덮어쓰기): `생의학_신경반사_마스터DB`, `로컬_논문_역색인`, `논문_전수_색인`, `외부_수집_논문`, `동기화_로그`.
- 기존 3개 시트의 열 순서는 유지하고 열을 **추가만** 한다.
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

---

## 4. 트리거 설계

| 트리거 | 시점 | 실행 범위 | 비고 |
| :--- | :--- | :--- | :--- |
| **Rank 6 진입(자동)** | Tier 2·3 분석마다 | `scan-local`(증분, 수 초) → `sync-api --code <대상>` → `export-xlsx` → `validate` | 프레임워크 필수 단계. `--dry-run`으로 미리 확인 후 실행 |
| **수동 CLI** | 사용자 요청 | 개별 서브커맨드 또는 `--full-rescan` | 폴더 대량 추가 후 |
| **주기 배치** | 주 1회(Windows 작업 스케줄러) | `scan-local --enrich` → `export-xlsx` → `validate` | Google Drive 동기화 시간대 연계 |

---

## 5. CLI 설계 — 단일 진입점 `sync_master_db.py`

```bash
python scripts/sync_master_db.py scan-local [--full-rescan] [--enrich] [--dry-run]
python scripts/sync_master_db.py sync-api --code ST36 --name-kr 족삼리 --name-cn 足三里 --pinyin Zusanli [--dry-run]
python scripts/sync_master_db.py export-xlsx
python scripts/sync_master_db.py validate
python scripts/sync_master_db.py all --code ST36 --name-kr 족삼리 --name-cn 足三里 --pinyin Zusanli [--dry-run]   # Rank 6 표준 호출
python scripts/sync_master_db.py migrate-v3 [--dry-run]   # 1회 실행
```

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
| 로그 | `_metadata.sync_log`(최근 500건) + `data/sync_logs/YYYY-MM.jsonl` 영구 기록. 백업은 `data/backup/`에 1세대 보관 |
| manifest 규칙 | manifest는 디스크 파일 단위로 추적하며 duplicate 레코드도 포함한다. |
| 배치 옵션 | `scan-local --enrich --enrich-limit N`으로 보강 건수를 제한해 시험 실행 가능. |
| Crossref 필터 | `query.bibliographic`의 느슨한 매칭 때문에 제목·초록에 경혈 코드·병음이 없는 결과는 제외 |

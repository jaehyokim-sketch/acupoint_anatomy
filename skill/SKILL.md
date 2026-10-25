---
name: acupoint-anatomy
description: >-
  오직 [경혈해부] 또는 @경혈해부 키워드가 프롬프트에 명시적으로 포함된 경우에만 활성화.
  질문 깊이별 차등 응답(Tier 1: 200단어 이내 요약, Tier 2: 200~1,000단어 표준 분석, Tier 3: 1,000단어 이상 심층 종합 보고서).
  핵심 4대 원전(《中国针灸穴位通鉴》·《中国针灸证治通鉴》·《针灸腧穴通考》·《中国针灸经络通鉴》) 전수 직접 대조와
  로직 정본 01_Framework/acupoint_anatomical_logic_framework.md (Framework v2.7)의 8대 작업 순위(Rank 0~7) 통합 프로토콜에 기반하여
  통합 생의학 마스터 DB v3.0(JSON 단일 진실원천 + 5시트 xlsx, sync_master_db.py 동기화) 및 Layer B 4계층 참조 등록부와의
  이중 층차 B-Check 교차 대조(6항목 12점, ≥ 8/12 부합)를 거쳐,
  경혈의 3D 공간 좌표, 1푼=2.3mm 한대 도량형 자침 심도, 공간 변위 분기 추론(Δ > 10mm 시 고전 문헌점·촉진 실체점·현대 WHO점 Tri-Target 분기),
  Layer 1~5 층차별 신경·혈관·근막 실체, 체성-내장/자율신경 반사 기전 및 ARI v3.0 프로파일(ARI-Core + 안전지수 SI)을 산출하는
  경혈 해부생리학 전용 학술 분석 스킬.
---

# 경혈 해부생리학 실체 판명 분석 스킬 — Antigravity 본문 (Framework v2.7)

이 파일은 **Antigravity IDE용 스킬 본문**이다. 분석 규칙의 **정본은 `01_Framework/acupoint_anatomical_logic_framework.md`(Version 2.7)** 이며, 이 파일은 정본을 Antigravity 환경에서 실행하는 방법과 정본에 없는 IDE 전용 규칙만 담는다. Claude Code는 `.claude/skills/acupoint-anatomy/SKILL.md`로 같은 정본을 따른다. 종전 본문(4요인 가중 합산 ARI, 분모 미정의 67% 부합 기준, 구 동기화 스크립트)은 `references/SKILL_v2.6_archive.md`에 보존했으며 더 이상 적용하지 않는다.

> 경로 표기: 모든 경로는 프로젝트 루트(`도서 번역` 폴더) 기준 상대경로다. 드라이브 문자(G: 등)는 PC마다 다를 수 있으므로 절대경로 링크는 쓰지 않는다.

---

## 0. 시작 시 로드 순서 (Rank 0)

| 순서 | 파일 | 역할 | Tier 1 | Tier 2·3 |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `01_Framework/acupoint_anatomical_logic_framework.md` | 로직 **정본**: Tier 1~3, Rank 0~7, ARI v3.0 루브릭·게이트, 10대 구성 요소 | 1·2절 | 전체 |
| 2 | `.agents/rules/acupoint-anatomy-routing.md` | 트리거 규칙, 산출물 5대 디렉토리 분류·저장 규칙 | — | 읽음 |
| 3 | `01_Framework/layer_b_reference_registry.md` | Layer B 4계층 참조 등록부(B1~B4), B-Check 6항목 기준 | — | 읽음 |
| 4 | `01_Framework/biomedical_master_db_sync_design.md` | 통합 DB v3.0 구조·동기화 설계(필요 시) | — | 참조 |
| 5 | `references/acupoint_anatomical_logic_framework.md` | 정본의 오프라인 사본(`sync_skill_settings.py --apply`가 갱신). 정본을 읽을 수 없을 때만 사용 | — | 대체 |

- 정본과 이 파일·라우팅 규칙이 다르면 **정본을 우선**한다. 이 파일의 IDE 전용 규칙은 정본과 충돌하지 않는 한 적용한다.
- **두 IDE 간 동기화 점검**(Tier 2·3 필수):
  ```bash
  python .agents/skills/acupoint-anatomy/scripts/sync_skill_settings.py --check
  python .agents/skills/acupoint-anatomy/scripts/sync_skill_settings.py --apply   # 드리프트 시
  ```
  `[CHG]`로 표시된 `claude_skill`·`claude_md`는 Claude Code 쪽 변경이다. 정본에 반영된 규칙은 자동으로 따르게 되며, 래퍼 전용 변경은 참고만 한다.
- 마스터 원칙 xlsx(`02_Master_Datasets/경혈의 해부학적 실체를 판명하기 위한 로직(logic) 원칙.xlsx`)는 확인하되 정본과 다르면 정본을 우선한다(Framework v2.7 및 ARI v3.0 기준 정합).

## 1. 데이터 소스 (정본 1절·머리말)

- **4대 원전**: `01_도서_번역_및_원전/중국침구혈위통감(中国针灸穴位通鉴)`(41개편) · `중국침구증치통감(中国针灸证治通鉴)`(원문 31 + 한글번역 31, 62개편) · `침구수혈통고(针灸腧穴通考)`(25개편) · `중국침구경락통감(中国针灸经络通鉴)`(39개편) 정제 마크다운 디렉토리에서 해당 경맥/편별 파일을 직접 대조하고 전수 검색한다. 역할 분담은 정본 Rank 1 & 2를 따른다.
  - 《证治通鉴》: 중국어 원문을 기준 텍스트로 하되 같은 편 `*_한글번역.md`와 대조하고, 분석·기술(description)은 한글 번역본 문장으로 한다(인용은 원문·번역 병기, 불일치 시 원문 우선·감사 기록).
  - 《经络通鉴》: 역대 경락(경맥·락맥) 문헌 오류를 황룡상 교수의 출토문헌 실증주의로 교감하는 준거. 12경맥 소속 혈은 第叁编(17~29), 임·독맥·기경은 第肆编(30~36), 경맥명·이명은 第伍编 脉名索引(37)을 검색한다.
- **8대 마스터 데이터셋**(`02_Master_Datasets/`): 361 경혈 마스터 CSV, KJH 이명 대조 xlsx, 자침깊이 xlsx(`'0'`=금침, `'blank'`=미기술, 정수=푼), 공통교재·김재효 해부구조 데이터셋 2종, 통합 생의학 마스터 DB(`경혈_생의학_신경반사_마스터DB.json` 정본 + 파생 `.xlsx` 5시트), 《中国针灸穴位通鉴》 파생 분석데이터셋 12종(`02_Master_Datasets/中国针灸穴位通鉴 분석데이터셋/`), 및 FMA 해부 온톨로지 매핑 데이터셋(`02_Master_Datasets/FMA/acupoint_fma_mapping.json` · `.xlsx`, 361개 경혈 6,122행).
- 마스터 DB `.xlsx`는 파생물이므로 직접 편집하지 않는다. 레코드 `status`가 `duplicate`·`missing`·`superseded`이면 인용하지 않는다.

## 2. Tier 1~3 응답 체계 (정본 2절)

- Tier 1(200단어 이내): 핵심 실체·표준 정위·지배신경·안전 심도 1~2문단.
- Tier 2(200~1,000단어): Layer 1~5 층차표, 1푼=2.3mm 심도, 교재 비교, 반사 회로, **ARI v3.0 프로파일(예비 단일 채점)**. Rank 6-3 필수 외부 실증 검색을 수행한다.
- Tier 3(1,000단어 이상): Rank 0~7 완전 전개, 10대 구성 요소, B-Check 채점표·외부 검색 로그 표, **ARI v3.0 이중 채점**, 5대 디렉토리에 한국어(.md, .html), 영어(_en.md, _en.html), 엑셀(.xlsx) 5종 완결 세트(영어 버전 한의학 용어 번체자(繁體字) 병기 필수).

## 3. Rank 0~7 요약과 정본 참조 위치 (정본 3절)

| Rank | 핵심 | 정본 위치 |
| :--- | :--- | :--- |
| 0 | 원칙 xlsx 확인, 정본 우선, 두 IDE 동기화 점검, 편집기 옛 버퍼 저장 금지 | Rank 0 |
| 1 & 2 | 4대 원전(`중국침구혈위통감`, `중국침구증치통감`, `침구수혈통고`, `중국침구경락통감`) 편별 파일 직접 대조 및 전수 검색, 《证治通鉴》 원문 기준·한글 번역본 기술 | Rank 1 & 2 |
| 3 | 이명·별칭 분리(KJH DB + 4대 원전), 5시기 편년체 정렬, 원문/재인용 구분, $P_{single}$ 분리 | Rank 3 |
| 4 | 인과성 우선, 필사 오류 감별(《腧穴通考》·《经络通鉴》), 배오 전이 배제, 병증 통합 편향 차단, 노이즈 제거, 키네시올로지 | Rank 4 |
| 5 | 자침깊이 해석, 1푼=2.3mm, 촉진 표현 실체화, 分肉·兩筋間·緣 간극의 X·Y 자입 기준점, X·Y·Z 좌표, Layer 1~5, Tri-Target 분기(Δ>10mm), 2대 교재 비교 | Rank 5 |
| 6 | Layer A 통합 DB v3.0 + 필수 외부 검색 ↔ Layer B 4계층 등록부 → B-Check 6항목(≥ 8/12) | Rank 6 (6-1~6-6) |
| 7 | ARI v3.0: ARI-Core(0.40/0.35/0.25 잠정) + SI 분리, 5단계 루브릭, 게이트 3종, 등급 A~D, 이중 채점·민감도, 5대 디렉토리 저장, 50% 중복 시 통합 | Rank 7, 4절 |

## 4. Rank 6 실행 — 통합 DB 동기화와 필수 외부 실증 검색

통합 DB 보유 편수와 무관하게 Tier 2·3마다 공용 스크립트를 실행한다. `--dry-run`으로 먼저 확인한 뒤 실제 반영한다.
```bash
python .agents/skills/acupoint-anatomy/scripts/sync_master_db.py --dry-run --trigger rank6 all --code <경혈코드> --name-kr <한글명> --name-cn <한자명> --pinyin <병음>
python .agents/skills/acupoint-anatomy/scripts/sync_master_db.py --trigger rank6 all --code <경혈코드> --name-kr <한글명> --name-cn <한자명> --pinyin <병음>
```
- `all` = scan-local(로컬 폴더 증분 스캔) → sync-api(PubMed 1차·OpenAlex/Crossref 2차·Europe PMC 폴백) → export-xlsx → validate(실패 시 자동 롤백, 종료코드 1; 외부 소스 전부 실패 시 2).
- 실패 처리: PubMed 실패 → $S_{reflex}$ 채점 보류·"외부 검색 미완". OpenAlex·Crossref 실패 → "보완 검색 미완" 표지. 전 소스 0건 → Layer A 0편, 게이트 2(H).
- 외부 검색 로그 표(정본 5절 8항)는 `_metadata.sync_log` 또는 xlsx `동기화_로그` 시트의 해당 경혈 행으로 작성한다. Layer A 인용은 `papers.id`와 PMID/DOI로 한다.
- 중국 핵심 저널(《中国针灸》·《针刺研究》) 경로와 중국어 보강 방법은 정본 6-3을 따른다. 구 스크립트 `sync_biomedical_papers.py`·`build_local_papers_index.py`는 호출하지 않는다.

## 5. Layer B 인용과 B-Check (정본 6-4·6-5)

- 등록부 참조 ID(예: B3-17)로만 인용하고 연구자명("Sato 모델"·"Ma 모델")으로 지칭하지 않는다. 종·마취·검증 경혈 범위 밖이면 B-Check 1점(유추) 상한.
- B-Check 6항목(① 말초 실체 ② 분절 정합 ③ 구심 섬유·수용체 ④ 중추 경로 ⑤ 원심 효과 방향 ⑥ 인체 전환)을 각 0/1/2로 채점한다. 합계 ≥ 8/12이고 ①·② ≥ 1일 때만 기전을 확정 기술한다. ③~⑤가 동물 근거뿐이고 ⑥ = 0이면 "(동물 한정)", 상충 근거가 있으면 "가설"로 제한한다.

## 6. FMA 온톨로지 연동과 해부 실체·분절 추적 (Claude Code ↔ Antigravity 공용 도구)

워싱턴 대학교 FMA(Foundational Model of Anatomy, v5.1.0: 실체 104,720 · 관계 259,140) 및 `02_Master_Datasets/FMA/acupoint_fma_mapping.json` (361개 전 경혈 매핑 6,122행)을 연동하여, 교재 해부 용어를 국제 표준 실체 ID(FMA:ID)로 고정하고 지배신경·척수 분절·신경 줄기 경로를 정량적으로 추적한다.

**실행 명령어** (`.agents/skills/acupoint-anatomy/scripts/fma/`, 프로젝트 루트에서 실행):
```bash
python .agents/skills/acupoint-anatomy/scripts/fma/fma_query.py profile <경혈코드> --md   # 보고서용 표준 마크다운 표 생성
python .agents/skills/acupoint-anatomy/scripts/fma/fma_query.py entity "<구조명 또는 FMA ID>" # 특정 해부구조 상세 조회
python .agents/skills/acupoint-anatomy/scripts/fma/fma_query.py path "<말초신경>" "<줄기신경>"  # 신경 주행 최단 경로 추적
python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py graph <경혈코드>         # Neo4j 기반 FMA 신경해부 지식 그래프 이미지(.png) 생성
python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py cross-section <경혈코드> # 혈위별 횡단면 해부 모식도(.png) 생성
python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py all <경혈코드>           # 지식 그래프 및 횡단면 모식도 일괄 생성
```

**Rank 0~7 단계별 FMA 근거 보강 체계**:
1. **Rank 5 (10대 요소 ④)**: Layer 1~5 층차표의 각 구조물에 표준 `FMA:ID` 병기 및 `contained_in`(구획) 확인.
2. **Rank 5 (10대 요소 ⑥)**: `fma_query.py profile`의 2대 교재 해부구조 비교(공통 / 공통교재 단독 / 김재효 단독 실체 수)를 통해 동일 구조의 이명 표기를 FMA ID로 통합 판별.
3. **Rank 6 (B-Check ① 말초 실체)**: 교재 해부구조가 FMA 표준 실체로 일치(`exact`, `exact+muscle/nerve`)하는지 판정.
4. **Rank 6 (B-Check ② 분절 정합)**: FMA의 `segmental_supply` 및 신경 줄기 사슬(`spinal nerve`) 상향 순회에서 추출한 **분절 합집합(segment_union)**을 $P_{single}$ 표적 장기의 척수 분절과 대조.
5. **Rank 6 (반사 기전도 ⑧)**: 말초 가지 → 본줄기 → 신경총 경로(`path`, `ancestors`)를 구심 경로 앞단 회로로 직접 활용.

**인용 및 기술 원칙**:
- 표기 형식: `FMA:44771 Deep fibular nerve (FMA 5.1.0)`. Layer B 등록부 미등재 항목은 "B1 보조(등록부 미등재)"로 표기.
- 대응 수준: `exact`·`exact+…`만 확정 근거로 사용하고, `parent(branch_of)`는 "상위 구조 대응(가지 미등재)", `none`은 "FMA 미등재"로 기재.

## 7. Rank 7 — ARI v3.0 채점 요약 (정본 Rank 7·4절)

1. $S_{orig}$(4개 하위 항목 평균)·$S_{clarity}$·$S_{reflex}$·$S_{safety}$를 **0/25/50/75/100** 중 하나로만 부여하고 근거 포인터(chunk ID, `papers.id`, 참조 ID, 교재 행)를 `.xlsx`에 기록한다.
2. 게이트: $S_{orig}<50$ 또는 $S_{clarity}<50$ → 최고 등급 C / Layer A 0편 → $S_{reflex}\le 25$ + (H) / SI ≤ 25 → ⚠ 안전주의.
3. ARI-Core = $0.40\,S_{orig} + 0.35\,S_{clarity} + 0.25\,S_{reflex}$(잠정 가중치). SI = $S_{safety}$ 는 합산하지 않고 병기.
4. 등급 A ≥ 85 / B 70~84 / C 55~69 / D < 55. Tier 3는 이중 채점(평균 ± 반범위)과 등가중치 민감도, Tier 2는 "예비" 표지.
5. 분기 판정(Tri-Target: 1 고전 문헌 / 2 촉진 실체화 / 3 WHO): 최고 Target이 나머지 각 Target보다 ΔARI-Core ≥ 10이고 ± 구간 비중첩일 때만 단독 우위 선언. 일부만 충족하면 충족한 Target만 열위로 두고 나머지는 병기(예: `Target 2 ≈ Target 3 > Target 1`). 고전 문헌·촉진 표현·WHO 중 어디에도 해당하지 않는 위치(후대 이설·근현대 신설·개인 제안 정위 등)는 Δ > 10mm여도 Target에서 제외하고 정위 주석·참고 이설로만 기록한다.
6. 표기: `ARI v3.0 | ARI-Core 78 ± 4 (B·H) | SI 75 | 잠정 가중치 0.40/0.35/0.25 | 민감도(등가중치): 76 (B, 등급 불변)`. 구판 점수는 비교하지 않고 재채점한다.

## 8. 산출물 저장 (라우팅 규칙 제3조, 정본 Rank 7)

`acupoint_anatomy/` 하위 5대 디렉토리(01 경혈별 보고서 / 02 고전문헌 통합 비교 / 03 주제별 고증 / 04 번역원고·매트릭스 / 05 의료행정·정책보고서)에 자동 분류하여 저장하고, Tier 3는 한국어(.md, .html)와 영어(_en.md, _en.html) 및 엑셀(.xlsx) 총 5종 세트를 함께 만든다. 기존 문서와 중복도 50% 이상이면 통합 갱신하며 구판 ARI는 v3.0으로 재채점한다.

- **영어 버전 보고서 및 한의학 용어 번체자(繁體字) 병기 규정**:
  - Tier 3 보고서 생성 시 영문본(`*_en.md` 및 `*_en.html`)을 동시 구축한다.
  - 영어 버전 작성 시 모든 한의학 고유명사, 경혈명, 경락명, 원전서명, 이론 개념 및 고전 주치증은 반드시 **한자 번체자(繁體字)**를 괄호 내에 병기한다. (예: `Zusanli (足三里, ST36)`, `Stomach Meridian (足陽明胃經)`, `Zhen Jiu Jia Yi Jing (《針灸甲乙經》)`, `Zhongguo Zhenjiu Jingluo Tongjian (《中國針灸經絡通鑑》)`, `Qi (氣)`, `Stomach pain (胃痛)`). 서양 해부구조는 영문(FMA label)과 `FMA:ID`를 기본으로 표기한다.

- **HTML 웹리포트 빌드 필수**: Tier 3 보고서 작성 시 `.html`은 수동 변환하지 않고 반드시 공용 빌더 스크립트를 실행하여 생성한다:
  ```bash
  python .agents/skills/acupoint-anatomy/scripts/build_report_html.py <보고서경로.md>
  ```
  - **도식 PNG 렌더링**: 한글·한자가 섞인 문자 도식(┌─│ 등 상자 그림, 화살표, 층차도 등)은 브라우저 글꼴 폭 불일치로 인한 줄바꿈·선 어긋남 왜곡을 원천 방지하기 위해 고정 격자 PNG로 렌더링되며, Mermaid 다이어그램은 Playwright로 사전 렌더링된 고해상도 PNG로 자동 삽입(Data URI 내장)된다.

- **HTML 공개본 원본 자료 비노출 규정** (정본 Rank 7): `.html`(한국어·영어)은 외부 공유용이므로 원본·중간 데이터 파일의 저장 위치·파일명·링크를 노출하지 않는다. HTML은 `.md`에서 빌드되므로 `.md` 본문부터 지킨다.
  - 금지: 드라이브 문자·`file:///` 링크·`내 드라이브`, 저장소 경로(`02_Master_Datasets/…`, `01_도서_번역_및_원전/…`·`chunks_refined`, `01_Framework/…`, `.agents/…`, `.claude/…`), `.xlsx`·`.json`·`.csv` 등 데이터 파일명과 그 링크(보고서 자신의 분석데이터 `.xlsx`, `final_*.json` 등 중간 산출물 포함), 실행 명령·파일 크기·PC 이름·계정·API 키.
  - 대체: 정본 대체 표기표의 기술명(예: "통합 생의학 마스터 DB v3.0", 영어본 "Integrated Biomedical Master DB v3.0"). 원전은 서명·편명으로 인용하고, 파일 경로·chunk ID 등 근거 포인터는 내부용 `.xlsx`에만 기록한다.
  - 허용: PMID, DOI, FMA:ID, Layer B 참조 ID, `papers.id`, 공개 외부 URL.
  - 빌드 직후 `.md`·`.html`을 정본의 금지 패턴 정규식으로 검색해 0건(공개 URL 내 적중 제외)을 확인하고, 적중 시 `.md`를 고쳐 다시 빌드한다.


### Tier 3 종합 보고서 필수 10대 구성 요소 (정본 5절)
1. **문헌 스크리닝 표**: 4대 원전 원문 발췌 및 한중 대조 (4대 원전 편별 파일 직접 대조, 《证治通鉴》은 원문 기준·한글 번역본 기술)
2. **원천/재인용 구분 표**: 선진·한대 최초 기술과 후대 주석·재인용의 분리 분석
3. **이명·별칭 검증 표**: KJH DB 대조를 통한 혼용·필사 오류 차단 기록
4. **3D 공간 좌표 및 Layer 1~5 층차 구조도**: X·Y·Z 좌표 및 단면 모식도 (分肉·兩筋間·緣 간극이 명확하면 X·Y 자입 기준점과 경계 구조물 표기)
5. **자침 깊이 계산표**: 고전 푼수 ➔ 한대 2.3mm 환산 심도 및 Layer 도달 안전 범위 ('0'=금침, 'blank'=미기술 명시)
6. **해부학 구조 교재 비교표**: 경혈학 공통교재 vs 김재효 교재 해부구조 공통점/차이점 및 도식 표기
7. **공간 변위 분기 추론도 (필요 시)**: Target 1(고전 문헌)·Target 2(촉진 실체화)·Target 3(WHO) 좌표·쌍별 편차, $\Delta_{discrepancy} > 10\text{mm}$ 쌍의 독립 분기 비교 및 ΔARI-Core 판정
8. **생의학적 반사 기전도 및 외부 검색 로그**: Layer A 논문(`papers.id`) 및 Layer B 신경회로 매핑 + B-Check 6항목 채점표(≥ 8/12 부합, 동물 한정/가설 표지) + 외부 API 검색 로그 표(`sync_log` 행)
9. **주치증 분리 표**: 단독 자침($P_{single}$) 효능 vs 복합 배오 처방 파생 효과
10. **ARI v3.0 프로파일 평가표 및 최종 결론**: 하위 점수별 루브릭 단계·근거 포인터, 게이트 적용 내역, ARI-Core(평균 ± 반범위)·등급·표지(H/⚠), SI, 등가중치 민감도, 버전 명기 및 감사 기록


## 9. PC 독립성과 운영

- 첫 사용 PC: `python .agents/skills/acupoint-anatomy/scripts/check_environment.py` → `pip install -r .agents/skills/acupoint-anatomy/scripts/requirements.txt` (FMA 추가 패키지: `pip install -r .agents/skills/acupoint-anatomy/scripts/fma/requirements-fma.txt`).
- 로컬 논문 폴더: `ACUPOINT_PAPERS_DIR` 환경변수 → 프로젝트 루트 상위 폴더의 `학습자료/실험 및 연구 논문` → DB 기록값 순으로 해석.
- 환경변수(사용자 계정): `OPENALEX_MAILTO`(연구자 이메일), `NCBI_API_KEY`(선택), `NEO4J_URI`/`USER`/`PASSWORD`(선택, FMA Neo4j 분석).
- 주간 배치: `register_weekly_task.cmd`로 **한 PC에만** 등록(일요일 03:00, `weekly_sync.cmd`).

## 10. 변경 관리

- 규칙 변경은 정본 → `sync_skill_settings.py --apply`(references 사본·버전 표기 정렬) → 정본 6절 문서 이력 기록 순으로 한다. IDE 전용 실행 방법만 바뀌면 해당 래퍼만 고친다.
- 공용 통합 파일(`scripts/`의 `sync_master_db.py`·`sync_skill_settings.py`·`check_environment.py`·`weekly_sync.cmd`·`register_weekly_task.cmd`·`requirements.txt`·`fma/`, `references/` 사본, `sync_state.json`)은 두 IDE가 함께 쓴다.
- 편집기에 정본이 열려 있는 상태에서 도구가 파일을 갱신했으면 저장 전에 디스크 버전을 다시 불러온다.

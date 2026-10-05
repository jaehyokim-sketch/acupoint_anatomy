---
name: acupoint-anatomy
description: >-
  오직 [경혈해부] 또는 @경혈해부 키워드가 프롬프트에 명시적으로 포함된 경우에만 활성화.
  질문 깊이별 차등 응답(Tier 1: 200단어 이내 요약, Tier 2: 200~1,000단어 표준 분석, Tier 3: 1,000단어 이상 심층 종합 보고서).
  핵심 3대 원전(《中国针灸穴位通鉴》·《中国针灸证治通鉴》·《针灸腧穴通考》) 전수 직접 대조와
  로직 정본 acupoint_anatomical_logic_framework.md (Framework v2.7)의 8대 작업 순위(Rank 0~7) 통합 프로토콜에 기반하여
  통합 생의학 마스터 DB v3.0(JSON 단일 진실원천 + 5시트 xlsx) 및 Layer B 4계층 참조 등록부와의
  이중 층차 B-Check 교차 대조(6항목 12점, ≥ 8/12 부합)를 거쳐,
  경혈의 3D 공간 좌표, 1푼=2.3mm 한대 도량형 자침 심도, 공간 변위 분기 추론(Δ > 15mm 시 고전 원전점 vs 현대 WHO점 이원 분기),
  Layer 1~5 층차별 신경·혈관·근막 실체, 체성-내장/자율신경 반사 기전 및 ARI v3.0 프로파일(ARI-Core + 안전지수 SI)을 산출하는
  경혈 해부생리학 전용 학술 분석 스킬.
---

# 경혈 해부생리학 실체 판명 분석 스킬 (Framework v2.7 / ARI v3.0)

본 스킬은 **361개 표준 경혈의 3D 공간 정위, 한대(漢代) 1푼=2.3mm 도량형 환산 자침 심도, Layer 1~5 층차별 신경·혈관·근막 실체, 2대 교재(공통교재 vs 김재효교재) 비교, 공간 변위 분기 추론(Δ > 15mm), Layer A 실측 생의학 논문 및 신경반사회로, Layer B 4계층 참조 등록부와의 B-Check 6항목 채점(≥ 8/12점), 및 ARI v3.0 정밀 채점**을 수행하는 경혈 해부생리학 표준 분석 프레임워크입니다.

---

## 🏛️ 1. 스킬 활성화 및 호출 규칙

- **트리거 키워드**: 프롬프트에 **`@경혈해부`** 또는 **`[경혈해부]`** 가 명시적으로 포함된 경우에만 활성화됩니다.
- **키워드가 없는 일반 질의**: 본 스킬의 엄격한 프로토콜을 강제 적용하지 않고 일반 지식으로 간결히 응답합니다.

---

## 🎯 2. 질문 깊이별 3단계 차등 응답 체계 (Tiered Inquiry Architecture)

| 구분 | 분량 규격 | 응답 내용 및 필수 수록 항목 | MCP 도구 활용 |
| :--- | :--- | :--- | :--- |
| **Tier 1<br>(간이 질의)** | **200단어 이내** | • 핵심 해부학적 실체, 표준 정위, 지배신경, 안전 자침 심도 ($z = \text{푼} \times 2.3\text{mm}$)<br>• 1~2문단 직관적 요약 | `get_acupoint_anatomy_profile` |
| **Tier 2<br>(표준 분석)** | **200 ~ 1,000단어** | • **Layer 1~5 정밀 층차 분석표**<br>• 한대 1푼=2.3mm 심도 환산 및 안전 범위<br>• **경혈학 공통교재 vs 김재효 교재 해부구조 비교 요약**<br>• 체성-자율신경 반사 회로(Somato-autonomic reflex)<br>• **Layer A 실측 논문 및 Rank 6-3 외부 실증 검색**<br>• **ARI v3.0 프로파일(예비 단일 채점)** | `get_acupoint_anatomy_profile`<br>`search_biomedical_reflex_db`<br>`calculate_ari_v3_score` |
| **Tier 3<br>(심층 모노그래프)** | **1,000단어 이상** | • **Rank 0 ~ 7 통합 표준 분석 프로토콜 100% 완전 전개**<br>• 3대 원전 편년체 사료 대조표 및 이명 검증 (KJH DB)<br>• **공간 변위 분기 추론 ($\Delta > 15\text{mm}$)** Target 1 vs Target 2<br>• **2대 교재 해부구조 전수 비교·대조표 및 도식**<br>• **Layer A(`papers.id`) + Layer B(B1~B4) 대조 및 B-Check 6항목 채점표 (≥ 8/12점)**<br>• **ARI v3.0 이중 채점(평균 ± 반범위, 민감도, 3대 게이트)**<br>• **최종 보고서 필수 10대 구성 요소 전수 수록**<br>• 산출물 3종 동시 구축 (`.md`, `.html`, `.xlsx`) | 전체 MCP 도구 총동원<br>+ 리포트 빌더 스크립트 |

---

## ⚡ 3. 8대 작업 순위(Rank 0~7) 통합 표준 분석 프로토콜

1. **[Rank 0] 사전 검증 및 로직 동기화**:
   - 로직 정본 `framework/acupoint_anatomical_logic_framework.md` (Framework v2.7) 준수.
   - `get_framework_protocol` 도구를 통해 최신 룰셋 로드.
2. **[Rank 1 & 2] 3대 원전 전수 직접 대조 스크리닝**:
   - 《中国针灸穴位通鉴》(정위 변천), 《中国针灸证治通鉴》(주치증 분리), 《针灸腧穴通考》(고증·교감) 직접 대조.
   - `search_classic_records` 도구 호출.
3. **[Rank 3] 이명·별칭 섞임 방지 & 문헌 층차주의 정렬**:
   - KJH 공인 이명 DB 대조로 필사 오류 및 혼용 차단, 5시기 편년체 정렬.
   - 처방 전체 효과와 단독 자침 고유 효능($P_{single}$) 엄격 분리.
4. **[Rank 4] 원천 인과성 추론 & 키네시올로지·노이즈 필터링**:
   - 인과성 우선 평가, 배오 전이 배제, 체위성 근막 역학 분석.
5. **[Rank 5] 3D 공간 좌표·도량형 환산 & 2대 교재 해부구조 비교 & 분기 추론**:
   - 한대 기준 $1\text{푼} = 2.3\text{mm}$ ($z = \text{푼} \times 2.3\text{mm}$) 안전 심도 환산.
   - **Layer 1~5 정밀 층차 규명**:
     - Layer 1: 표피 및 진피 (자유신경종말, 메르켈 원판)
     - Layer 2: 피하조직 및 표재근막 (표재 피신경, 표재 정맥)
     - Layer 3: 심근막 및 근외막 (기계수용체, 건막)
     - Layer 4: 심부 근육 및 주신경·혈관속 (운동신경 종판, 고유수용체)
     - Layer 5: 골막 / 관절낭 / 심부 장기 경계 (골막 반사 수용체, 위험 장기)
   - **2대 교재 비교**: 경혈학 공통교재 vs 김재효 교수 교재 해부구조 공통점/차이점 명시.
   - **공간 변위 분기 추론**: $\Delta > 15\text{mm}$ 시 Target 1(고전 원전점) vs Target 2(현대 WHO점) 이원 분기 비교.
6. **[Rank 6] 이중 층차 생의학 검증 & B-Check Refinement (≥ 8/12)**:
   - **Layer A (실측 학술 DB)**: `search_biomedical_reflex_db`로 논문(`papers.id`, PMID/DOI), 실험종, 반사회로 확인.
   - **Layer B (4계층 참조 등록부 B1~B4)**: `get_layer_b_registry`로 B1(신경해부), B2(반사생리), B3(경혈특이성), B4(근막기계신호) 매핑.
   - **B-Check 6항목 채점**: ① 말초 실체 ② 분절 정합 ③ 구심 섬유/수용체 ④ 중추 경로 ⑤ 원심 효과 ⑥ 인체 전환 (각 0/1/2점, 총 12점).
   - **판정 기준**: **합계 ≥ 8/12점 (67%)** 및 ①·② ≥ 1점일 때만 기전 확정 기술. ⑥=0이면 "(동물 한정)", 상충 근거 시 "가설" 표지.
7. **[Rank 7] ARI v3.0 프로파일 정밀 채점**:
   - `calculate_ari_v3_score` 도구 활용.
   - 4개 하위 요인 점수 ($S_{orig}, S_{clarity}, S_{reflex}, S_{safety}$)는 **0, 25, 50, 75, 100 5단계 루브릭** 적용.
   - **ARI-Core** = $0.40 S_{orig} + 0.35 S_{clarity} + 0.25 S_{reflex}$ (잠정 가중치).
   - **안전지수 SI** = $S_{safety}$ (독립 지표로 병기).
   - **고정 등급**: A ($\ge 85$), B (70~84), C (55~69), D ($< 55$).
   - **3대 비보상형 게이트**:
     - Gate 1: $S_{orig}<50$ 또는 $S_{clarity}<50 \rightarrow$ 최고 등급 C.
     - Gate 2: Layer A 0편 $\rightarrow S_{reflex} \le 25$ 및 `(H)` 가설 표지.
     - Gate 3: SI $\le 25 \rightarrow$ `⚠ 안전주의` 경고 표지.
   - **이중 채점 & 민감도**: Tier 3는 평균 ± 반범위 표기 및 등가중치(0.333/0.333/0.333) 민감도 분석 수록.
   - **공식 표기 형식**: `ARI v3.0 | ARI-Core 78 ± 4 (B·H) | SI 75 | 잠정 가중치 0.40/0.35/0.25 | 민감도(등가중치): 76 (B, 등급 불변)`

---

## 📋 4. Tier 3 종합 보고서 필수 10대 구성 요소

1. **문헌 스크리닝 표**: 3대 원전 원문 발췌 및 한중 대조
2. **원천/재인용 구분 표**: 선진·한대 최초 기술과 후대 주석·재인용의 분리 분석
3. **이명·별칭 검증 표**: KJH DB 대조를 통한 혼용·필사 오류 차단 기록
4. **3D 공간 좌표 및 Layer 1~5 층차 구조도**: X·Y·Z 좌표 및 단면 모식도
5. **자침 깊이 계산표**: 고전 푼수 ➔ 한대 2.3mm 환산 심도 및 Layer 도달 안전 범위
6. **해부학 구조 교재 비교표**: 경혈학 공통교재 vs 김재효 교재 해부구조 비교 및 도식
7. **공간 변위 분기 추론도 (필요 시)**: $\Delta > 15\text{mm}$ 시 Target 1 vs Target 2 분기 비교 및 ΔARI-Core 판정
8. **생의학적 반사 기전도 및 외부 검색 로그**: Layer A 논문(`papers.id`) + Layer B 매핑 + B-Check 6항목 채점표(≥ 8/12점) + 검색 로그 표
9. **주치증 분리 표**: 단독 자침($P_{single}$) 효능 vs 복합 배오 처방 파생 효과
10. **ARI v3.0 프로파일 평가표 및 최종 결론**: 하위 점수별 루브릭 단계, 게이트 적용 내역, ARI-Core(평균 ± 반범위)·등급·표지, SI, 등가중치 민감도, 버전 명기 및 감사 기록

---

## 🛠️ 5. 제공되는 6대 MCP 도구 요약

| MCP 도구명 | 주요 기능 | 입력 매개변수 |
| :--- | :--- | :--- |
| **`get_acupoint_anatomy_profile`** | 361개 경혈 3D 좌표, 1푼=2.3mm 심도, Layer 1~5 구조, 2대 교재 비교, 변위 분기 반환 | `acupoint` (코드/이름) |
| **`search_biomedical_reflex_db`** | Layer A 실측 논문(PMID/DOI, 실험종) 및 신경반사 회로 검색 | `query`, `evidence_filter`, `limit` |
| **`get_layer_b_registry`** | Layer B 4계층 참조 등록부(B1~B4) 및 B-Check 6항목 기준 조회 | `category`, `reference_id`, `query` |
| **`calculate_ari_v3_score`** | ARI v3.0 프로파일(ARI-Core, Grade, Gate 1~3, SI, 민감도) 정밀 계산 | `s_orig`, `s_clarity`, `s_reflex`, `s_safety`, `layer_a_count` |
| **`search_classic_records`** | 3대 원전 정위 변천, 자침 깊이, 단독 효능($P_{single}$) 검색 | `acupoint`, `classic_book`, `limit` |
| **`get_framework_protocol`** | Framework v2.7 Rank 0~7, Tier 1~3 규격, 10대 요소 요강 반환 | `section` |

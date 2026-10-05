# Acupoint Anatomy Data Repository (`data/`)

이 디렉토리는 **경혈 해부생리학 실체 판명 프레임워크(Framework v2.7 & ARI v3.0)**의 단일 진실원천(Single Source of Truth) 데이터셋을 담고 있습니다. 로컬 MCP 서버(`server.py`) 및 원격 GitHub 스트리밍 MCP 서버(`remote_server.py`)는 이 데이터셋을 인덱싱하여 AI 어시스턴트에게 고속·정밀 해부생리학 컨텍스트를 제공합니다.

---

## 📂 데이터셋 목록 및 명세

### 1. `361_Acupoints_Refined_Master_DB_v2.csv` (표준 361 경혈 마스터 메타데이터)
- **크기/용량**: 361개 표준 경혈 전수 레코드 (약 92 KB)
- **주요 필드**:
  - `code`: WHO 표준 경혈 코드 (예: `ST36`, `PC6`, `BL23`)
  - `name_kr`: 표준 한글 명칭 (예: `족삼리`, `내관`, `신수`)
  - `name_cn`: 한자 정체자 표기 (예: `足三里`, `內關`, `腎兪`)
  - `pinyin`: 로마자 병음 표기 (예: `Zusanli`, `Neiguan`, `Shenshu`)
  - `meridian`: 소속 경락 (예: `족양명위경`, `수궐음심포경`)
  - `region`: 해부학적 대분류 (예: `하퇴 전외측`, `전완 전면`, `요배부`)
  - `depth_cun`: 고전 및 표준 자침 심도 (촌/푼 단위)
  - `who_location`: WHO 표준 취혈 정위 가이드

### 2. `layer_b_reference_registry.json` (Layer B 4계층 표준 참조 등록부)
- **크기/용량**: 30대 핵심 생의학·신경해부학 공인 참조 문헌 레코드 (약 25 KB)
- **계층 구조**:
  - `B1` (계통적 문헌고찰·신경해부학 기반 — 5편): WHO 표준 해부, Gray's Anatomy, 편측/양측 투사
  - `B2` (신경반사 회로 — 8편): 체성-내장 반사(Sato 1997 등), 미주신경-부신 축, 척수 반사궁
  - `B3` (전침·체성감각 반사 매개변수 — 9편): Ma et al. (Nature 2021, Neuron 2014, Nature 2020), PROKR2-Cre+ 후근신경절 신경세포 특이적 항염증 경로
  - `B4` (근막·기계수용체·혈관신경초 — 8편): Langevin 근막 모델, Piezo1/2 기계채널, TRP 채널
- **주요 활용**: `B-Check` (6개 항목 12점 만점, ≥ 8점 통과 기준) 채점 시 공인 Reference ID로만 인용.

### 3. `경혈_생의학_신경반사_마스터DB.json` (Layer A 실증 논문 및 신경반사 마스터 DB)
- **크기/용량**: 361개 전 경혈에 대응하는 실증 논문, 임상시험, 신경반사 경로 통합 DB (약 5.3 MB)
- **구조**:
  - `_metadata`: DB 버전(`v3.0`), 최종 동기화 일시, 통계 정보
  - `acupoints`: 경혈 코드별 1:1 매핑 객체
    - `profile`: 경혈 기본 정보, 3D 좌표, 표준 자침 심도, 해부학적 5층차(Layer 1~5)
    - `reflex_circuits`: 체성-내장 반사, 척수 반사분절, 신경전달물질, 자율신경계 연결 회로
    - `papers`: PubMed, Europe PMC, OpenAlex, Crossref 등에서 검증된 논문 목록(PMID, DOI, 저자, 초록 요약, 실증 수준)
    - `ari_profile`: ARI v3.0 4개 구성 점수($S_{orig}, S_{clarity}, S_{reflex}, S_{safety}$), ARI-Core, 안전지수 SI, 게이트 판정값

---

## 🔄 데이터 동기화 및 갱신 방법

데이터셋 갱신 및 외부 논문 동기화는 `scripts/sync_master_db.py` 스크립트를 통해 자동으로 수행됩니다.

```bash
# 특정 경혈(예: ST36 족삼리)에 대한 PubMed/Crossref 실증 논문 증분 동기화
python scripts/sync_master_db.py --trigger rank6 all --code ST36 --name-kr 족삼리 --name-cn 足三里 --pinyin Zusanli

# 엑셀 파생 파일 5시트 내보내기
python scripts/sync_master_db.py --trigger manual export-xlsx
```

---

## 🌐 원격 스트리밍 지원 (Remote Streaming)

`mcp_server/remote_server.py`는 GitHub Raw Content API와 REST API를 통해 이 디렉토리의 파일들을 메모리 내에 On-Demand로 스트리밍 캐싱합니다. 로컬에 5.3 MB의 JSON 파일을 물리적으로 내려받지 않고도 원격에서 안전하게 쿼리할 수 있습니다.

# Layer B 참조 등록부 (Four-Tier Reference Registry) v1.0

> **용도**: [`acupoint_anatomical_logic_framework.md`](acupoint_anatomical_logic_framework.md) Rank 6 Layer B 대조와 B-Check 6항목 채점에 사용할 수 있는 참조 문헌의 **폐쇄 목록**. 보고서는 참조 ID(예: B3-17)로 인용하고 연구자 이름만으로 '모델'을 지칭하지 않는다.
> **생성일**: 2026-10-04 · PubMed 저자·연도·저널 제약 검색으로 PMID 30/30편 확인(제목 토큰 일치 ≥ 0.6) · 기계용 사본: `02_Master_Datasets/layer_b_reference_registry.json`
> **추가 규칙**: 등록부 밖 문헌을 쓰려면 먼저 이 표에 행을 추가하고 PMID/DOI를 확인한다. 책은 판·장·쪽을, 논문은 종·마취 여부·검증 경혈을 함께 적는다.

## B-Check 6항목과 계층의 대응

| B-Check 항목 | 내용 | 주 참조 계층 |
| :---: | :--- | :---: |
| ① | 자침 심도의 말초신경·혈관 실체 | B1·B2 |
| ② | 척수 분절 정합(피절·근절·골절 ↔ 표적 장기 내장절) | B1·B3 |
| ③ | 구심 섬유형·수용체(Aβ/Aδ/C, PROKR2, 기계수용기, 아데노신 등) | B3 |
| ④ | 중추 중계·경로(후각 수렴, NTS, rVLM, PAG, 시상하부 등) | B3 |
| ⑤ | 원심 경로와 표적 장기 효과 방향이 주치와 일치 | B3 |
| ⑥ | 인체 전환 근거(신경영상·자율신경 지표·임상) | B4 |

채점: 각 항목 0(근거 없음·상충) / 1(간접·유추·동물 한정) / 2(명시적 문헌 근거 일치). 합계 ≥ 8/12이고 ①②가 각각 ≥ 1이면 부합. ③~⑤가 모두 동물 근거뿐이고 ⑥ = 0이면 "(동물 한정)" 표지. 상충 근거가 있으면 등급 "가설"로 제한.

## B1 규범 해부 표준 (Normative Anatomy & Standards)

> 항목 ①②의 기준 근거. 단독으로는 '기전'을 입증하지 못함

| ID | 유형 | 서지 | 대상·범위 | B-Check | 한계·주의 | PMID | 검증 |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| B1-01 | 교과서 | Standring S (ed). Gray's Anatomy: The Anatomical Basis of Clinical Practice. 42nd ed. Elsevier; 2020. | 사람, 전신 규범 해부 | ①② | 경혈 특이 심도·변이 빈도 없음. 장·절·판 번호를 함께 인용 | — | 서지(비논문) |
| B1-02 | 교과서 | Splittgerber R. Snell's Clinical Neuroanatomy. 8th ed. Wolters Kluwer; 2019. | 사람, 중추·말초 신경계 | ②④ | 사지 말초 국소해부 상세 부족. 전도로·분절·자율신경 중추 확인용 | — | 서지(비논문) |
| B1-03 | 교과서 | Moore KL, Dalley AF, Agur AMR. Clinically Oriented Anatomy. 8th ed. Wolters Kluwer; 2018. | 사람, 임상·체표 해부, 피절 | ①② | 경혈 언급 없음 | — | 서지(비논문) |
| B1-04 | 참고서 | Tubbs RS, Shoja MM, Loukas M (eds). Bergman's Comprehensive Encyclopedia of Human Anatomic Variation. Wiley; 2016. | 사람, 신경·혈관·근육 변이 빈도 | ① | 변이 빈도는 집단별 차이 큼. SI(안전지수) 채점에 반영 | — | 서지(비논문) |
| B1-05 | 표준 | WHO Regional Office for the Western Pacific. WHO Standard Acupuncture Point Locations in the Western Pacific Region. Manila: WHO; 2008. | 361 경혈 표준 정위 | ① | 정위 기준이지 해부 실체 근거는 아님. 고전 원위와의 Δ 산출 기준(Rank 5) | — | 서지(비논문) |
| B1-06 | 교과서 | Lumley JSP. Surface Anatomy: The Anatomical Basis of Clinical Examination. 4th ed. Churchill Livingstone; 2008. | 사람, 촉진 랜드마크 | ① | 경혈 언급 없음 | — | 서지(비논문) |
## B2 경혈 특이 해부 실증 (Acupoint-Specific Anatomical Evidence)

> 항목 ①의 2점 조건(경혈 특이 실측). 반증 문헌(B2-04)과 병기

| ID | 유형 | 서지 | 대상·범위 | B-Check | 한계·주의 | PMID | 검증 |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| B2-01 | 사체 연구 | Heine H. Anatomical structure of acupoints. J Tradit Chin Med. 1988;8(3):207-212. | 사람 사체, 경혈 전반 | ① | 표본 수·통계 보고 제한. 신경혈관속의 천근막 관통점 대응 가설 | [3216666](https://pubmed.ncbi.nlm.nih.gov/3216666/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B2-02 | 사체 연구 | Langevin HM, Yandow JA. Relationship of acupuncture points and meridians to connective tissue planes. Anat Rec. 2002;269(6):257-265. | 사람 사체 단면, 상지 | ①③ | 상지 표본 한정. 결합조직면 가설 | [12467083](https://pubmed.ncbi.nlm.nih.gov/12467083/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B2-03 | 대응 분석 | Melzack R, Stillwell DM, Fox EJ. Trigger points and acupuncture points for pain: correlations and implications. Pain. 1977;3(1):3-23. | 문헌 대응, 통증 경혈 | ①⑤ | 71% 대응 주장은 Birch(2003)가 방법론 비판 | [69288](https://pubmed.ncbi.nlm.nih.gov/69288/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B2-04 | 비판 분석 | Birch S. Trigger point-acupuncture point correlations revisited. J Altern Complement Med. 2003;9(1):91-103. | 문헌 재분석 | ① | 반증 문헌. B2-03 인용 시 반드시 병기 | [12676038](https://pubmed.ncbi.nlm.nih.gov/12676038/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B2-05 | 대응 분석 | Dorsher PT. Can classical acupuncture points and trigger points be compared in the treatment of pain disorders? Birch's analysis revisited. J Altern Complement Med. 2008;14(4):353-359. | 문헌 재분석 | ①⑤ | 해부 대응은 높으나 임상 적응증 대응은 논쟁 | [18576919](https://pubmed.ncbi.nlm.nih.gov/18576919/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B2-06 | 교과서 | Simons DG, Travell JG, Simons LS. Myofascial Pain and Dysfunction: The Trigger Point Manual. Vol 1, 2nd ed. Williams & Wilkins; 1999. (3rd ed. Donnelly JM, ed. Wolters Kluwer; 2019) | 사람, 근막 발통점·연관통 | ①⑤ | 발통점 ≠ 경혈. Layer 2~3 근막층 해석용 | — | 서지(비논문) |
| B2-07 | 심도 측정 | Lin JG. Studies of needling depth in acupuncture treatment. Chin Med J (Engl). 1997;110(2):154-156. | 사람, 경혈 자침 심도 | ① | 체형 보정 없음. SI 채점 보조 | [9594291](https://pubmed.ncbi.nlm.nih.gov/9594291/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B2-08 | 단면 도해 | 严振国 主编. 经穴断面解剖图解(四肢部·头颈胸部·腹盆部). 上海: 上海科学技术出版社. | 사람 사체 단면, 경혈 전반(중국 표준) | ①② | PubMed 미색인. 판차·쪽 명기 | — | 서지(비논문) |
| B2-09 | 국내 교재 | 경혈학 공통교재 해부구조 데이터셋 · 김재효 교수 경혈 해부구조 데이터셋 (Rank 5, 02_Master_Datasets) | 361 경혈, 국내 표준 | ①② | 교재 간 불일치는 Rank 5 비교표로 처리 | — | 서지(비논문) |
| B2-10 | 유형(수집) | 영상 기반 안전 자침 심도 연구군(초음파·CT·MRI). 경혈별 개별 논문은 Layer A 파이프라인(sync_master_db.py)으로 수집하여 papers.id로 인용 | 사람, 경혈별 | ① | 등록부에는 유형만 두고 개별 PMID는 Layer A에서 관리 | — | 서지(비논문) |
## B3 일반 신경생리 기전 체계 (General Neurophysiological Frameworks)

> 항목 ③④⑤. 종·마취·검증 경혈 범위 밖이면 1점(유추) 상한

| ID | 유형 | 서지 | 대상·범위 | B-Check | 한계·주의 | PMID | 검증 |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| B3-01 | 고전 이론 | Head H. On disturbances of sensation with especial reference to the pain of visceral disease. Brain. 1893;16(1-2):1-133. | 사람 임상 관찰, 내장-체성 연관(Head zone) | ②⑤ | 역사적 관찰. 분절 대응의 출발점 | — | 서지(비논문) |
| B3-02 | 고전 이론 | Ruch TC. Visceral sensation and referred pain. In: Fulton JF, ed. Howell's Textbook of Physiology. 15th ed. Saunders; 1947. | 수렴-투사 이론 | ②④ | 이론 틀. 실험 근거는 B3-03 등으로 보강 | — | 서지(비논문) |
| B3-03 | 종설 | Foreman RD. Mechanisms of cardiac pain. Annu Rev Physiol. 1999;61:143-167. | 동물·사람, 척수 후각 내장-체성 수렴 | ②④ | 심장 중심. 타 장기는 유추 | [10099685](https://pubmed.ncbi.nlm.nih.gov/10099685/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-04 | 종설 | Sato A, Schmidt RF. Somatosympathetic reflexes: afferent fibers, central pathways, discharge characteristics. Physiol Rev. 1973;53(4):916-947. | 마취 동물(고양이·쥐), 체성-교감 반사 | ③④⑤ | 마취 동물. 분절성 vs 상척수성 반사 구분 | [4355517](https://pubmed.ncbi.nlm.nih.gov/4355517/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-05 | 단행 종설 | Sato A, Sato Y, Schmidt RF. The impact of somatosensory input on autonomic functions. Rev Physiol Biochem Pharmacol. 1997;130:1-328. | 마취 쥐 중심, 장기별 체성-자율 반사 | ②③④⑤ | 마취 쥐. 침 자극 강도·부위 의존성. 인체 전환 근거 별도 필요 | [9019119](https://pubmed.ncbi.nlm.nih.gov/9019119/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-06 | 종설 | Kagitani F, Uchida S, Hotta H. Afferent nerve fibers and acupuncture. Auton Neurosci. 2010;157(1-2):2-8. | 동물, 침 자극 구심 섬유형 | ③ | Sato 학파 후속. 섬유형-반사 대응 정리 | [20494626](https://pubmed.ncbi.nlm.nih.gov/20494626/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-07 | 이론 | Melzack R, Wall PD. Pain mechanisms: a new theory. Science. 1965;150(3699):971-979. | 관문조절설 | ④ | 진통 기전 한정 | [5320816](https://pubmed.ncbi.nlm.nih.gov/5320816/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-08 | 실험 | Le Bars D, Dickenson AH, Besson JM. Diffuse noxious inhibitory controls (DNIC). I. Effects on dorsal horn convergent neurones in the rat. Pain. 1979;6(3):283-304. | 마취 쥐, 광범위 억제 조절 | ④ | 비특이적 진통(혈위 특이성 반증 측면) | [460935](https://pubmed.ncbi.nlm.nih.gov/460935/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-09 | 실험 | Pomeranz B, Chiu D. Naloxone blockade of acupuncture analgesia: endorphin implicated. Life Sci. 1976;19(11):1757-1762. | 마우스, 내인성 아편계 | ③④ | 진통 한정 | [187888](https://pubmed.ncbi.nlm.nih.gov/187888/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-10 | 종설 | Han JS. Acupuncture: neuropeptide release produced by electrical stimulation of different frequencies. Trends Neurosci. 2003;26(1):17-22. | 쥐·사람, 주파수별 아편 펩티드 | ③④ | 전침 주파수 조건 명시 필요 | [12495858](https://pubmed.ncbi.nlm.nih.gov/12495858/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-11 | 종설 | Zhao ZQ. Neural mechanism underlying acupuncture analgesia. Prog Neurobiol. 2008;85(4):355-375. | 동물·사람, 진통 기전 종합 | ③④ | 진통 한정. 내장 반사 미포함 | [18582529](https://pubmed.ncbi.nlm.nih.gov/18582529/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-12 | 실험 | Tjen-A-Looi SC, Li P, Longhurst JC. Medullary substrate and differential cardiovascular responses during stimulation of specific acupoints. Am J Physiol Regul Integr Comp Physiol. 2004;287(4):R852-R862. | 마취 고양이·쥐, PC5-6·ST36·LI4 등 심혈관 반사(rVLM) | ②③④⑤ | 마취 동물. 검증 경혈 외 적용은 유추 | [15217791](https://pubmed.ncbi.nlm.nih.gov/15217791/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-13 | 종설 | Li P, Longhurst JC. Neural mechanism of electroacupuncture's hypotensive effects. Auton Neurosci. 2010;157(1-2):24-30. | 동물·사람, 전침 강압 기전 | ④⑤⑥ | 심혈관 한정 | [20444652](https://pubmed.ncbi.nlm.nih.gov/20444652/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-14 | 종설 | Tracey KJ. The inflammatory reflex. Nature. 2002;420(6917):853-859. | 동물, 콜린성 항염증 경로 | ④⑤ | 침 연구 아님. 미주신경 항염증 틀 제공 | [12490958](https://pubmed.ncbi.nlm.nih.gov/12490958/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-15 | 실험 | Torres-Rosas R, Yehia G, Peña G, et al. Dopamine mediates vagal modulation of the immune system by electroacupuncture. Nat Med. 2014;20(3):291-295. | 마우스 패혈증, ST36 좌골신경 전침, 미주-부신 도파민 | ③④⑤ | ST36·패혈증 모델 한정 | [24562381](https://pubmed.ncbi.nlm.nih.gov/24562381/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-16 | 실험 | Liu S, Wang ZF, Su YS, et al. Somatotopic organization and intensity dependence in driving distinct NPY-expressing sympathetic pathways by electroacupuncture. Neuron. 2020;108(3):436-450. | 마우스, ST36(저강도 미주-부신) vs ST25(고강도 교감) | ②③④⑤ | 마우스. 사지 심부 vs 복부 체성 지형 구분 | [32791039](https://pubmed.ncbi.nlm.nih.gov/32791039/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-17 | 실험 | Liu S, Wang Z, Su Y, et al. A neuroanatomical basis for electroacupuncture to drive the vagal-adrenal axis. Nature. 2021;598(7882):641-645. | 마우스, PROKR2 감각신경(사지 심부 근막) → 미주-부신 항염증 | ①③④⑤ | ST36 심부 근막 한정. PROKR2 섬유 분포 없는 부위(복부 등)에는 미적용 | [34646018](https://pubmed.ncbi.nlm.nih.gov/34646018/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-18 | 실험 | Goldman N, Chen M, Fujita T, et al. Adenosine A1 receptors mediate local anti-nociceptive effects of acupuncture. Nat Neurosci. 2010;13(7):883-888. | 마우스, ST36 국소 아데노신 | ③ | 국소 진통 한정 | [20512135](https://pubmed.ncbi.nlm.nih.gov/20512135/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-19 | 가설 | Burnstock G. Acupuncture: a novel hypothesis for the involvement of purinergic signalling. Med Hypotheses. 2009;73(4):470-472. | 가설, 퓨린 신호 | ③ | 가설 수준(1점 상한) | [19628336](https://pubmed.ncbi.nlm.nih.gov/19628336/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B3-20 | 교과서 | Filshie J, White A, Cummings M (eds). Medical Acupuncture: A Western Scientific Approach. 2nd ed. Elsevier; 2016. | 사람 임상, 분절 침술 체계 | ②④⑤ | 서양 의학적 침술 틀. 고전 주치 해석과 분리 | — | 서지(비논문) |
## B4 인체 전환·임상 근거 및 반증 (Human Translation, Clinical Evidence & Counter-Evidence)

> 항목 ⑥. 인체 전환 여부와 혈위 특이성 반증을 반드시 검토

| ID | 유형 | 서지 | 대상·범위 | B-Check | 한계·주의 | PMID | 검증 |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| B4-01 | fMRI | Hui KK, Liu J, Makris N, et al. Acupuncture modulates the limbic system and subcortical gray structures of the human brain: evidence from fMRI studies in normal subjects. Hum Brain Mapp. 2000;9(1):13-25. | 사람, ST36·LI4 fMRI | ⑥ | 건강인. 임상 효과와 직접 연결 아님 | [10643726](https://pubmed.ncbi.nlm.nih.gov/10643726/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B4-02 | fMRI | Dhond RP, Yeh C, Park K, Kettner N, Napadow V. Acupuncture modulates resting state connectivity in default and sensorimotor brain networks. Pain. 2008;136(3):407-418. (papers.id 1674) | 사람, LI4 fMRI | ⑥ | 건강인 | [18337009](https://pubmed.ncbi.nlm.nih.gov/18337009/) | PubMed 확인(2026-10-04 재검증: 종전 'NeuroImage 2012' 표기는 오인용) |
| B4-03 | 메타분석 | Chae Y, Chang DS, Lee SH, et al. Inserting needles into the body: a meta-analysis of brain activity associated with acupuncture needle stimulation. J Pain. 2013;14(3):215-222. | 사람 fMRI 메타분석 | ⑥ | 혈위 특이성 미해결 | [23395475](https://pubmed.ncbi.nlm.nih.gov/23395475/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B4-04 | IPD 메타분석 | Vickers AJ, Vertosick EA, Lewith G, et al. Acupuncture for chronic pain: update of an individual patient data meta-analysis. J Pain. 2018;19(5):455-474. | 사람 RCT 39편, 만성 통증 | ⑥ | 진침 vs 가침 차이는 작음 → 혈위 특이성 반증 측면 병기 | [29198932](https://pubmed.ncbi.nlm.nih.gov/29198932/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B4-05 | 종설(반증) | Choi EM, Jiang F, Longhurst JC. Point specificity in acupuncture. Chin Med. 2012;7:4. | 사람·동물, 혈위 특이성 논쟁 | ⑥ | 특이성 지지·반증 근거 균형 검토용 | [22373514](https://pubmed.ncbi.nlm.nih.gov/22373514/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B4-06 | 보고 표준 | MacPherson H, Altman DG, Hammerschlag R, et al. Revised STandards for Reporting Interventions in Clinical Trials of Acupuncture (STRICTA). PLoS Med. 2010;7(6):e1000261. | 임상시험 보고 표준 | ⑥ | Layer A 인체 RCT의 S_reflex 100점 조건(STRICTA 준수) 판정용 | [20543992](https://pubmed.ncbi.nlm.nih.gov/20543992/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
| B4-07 | 근거 등급 | Guyatt GH, Oxman AD, Vist GE, et al. GRADE: an emerging consensus on rating quality of evidence and strength of recommendations. BMJ. 2008;336(7650):924-926. | 근거 수준 체계 | ⑥ | Rank 7 게이트·루브릭 방법론 준거 | [18436948](https://pubmed.ncbi.nlm.nih.gov/18436948/) | PubMed 확인(저자·연도·저널 제약, 제목 일치 1.0) |
## 적용 예시: 종전 '4대 모델'의 재배치

| 종전 표기 | 등록부 ID | 적용 범위 명시 |
| :--- | :--- | :--- |
| Gray's Anatomy | B1-01 | 전신 규범 해부. 경혈 특이 심도는 B2로 보강 |
| Snell Clinical Neuroanatomy | B1-02 | 분절·전도로·자율신경 중추 |
| Sato Akio 교수 모델 | B3-04, B3-05, B3-06 | 마취 동물 체성-자율 반사. 인체 전환은 B4로 별도 입증 |
| Ma Qiufu 교수 모델 | B3-16, B3-17 (+ 선행 B3-14, B3-15) | 마우스 ST36 심부 근막 PROKR2 → 미주-부신. 타 경혈은 1점(유추) 상한 |

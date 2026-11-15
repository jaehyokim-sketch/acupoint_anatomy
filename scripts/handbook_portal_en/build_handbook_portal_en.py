"""경혈학 핸드북 포털 영문판 생성기.

한국어 포털(tools/acupoint-handbook.html)을 1:1로 영어로 옮긴 영문판
(tools/acupoint-handbook-en.html)을 만든다.

데이터 출처
- 경혈명 로마자 표기·병음, 위치(Location)·취혈(Guide)·주의(Caution):
  영문판 핸드북 PDF → handbook_en_points.json (extract_handbook_en.py로 추출)
- 해부구조: 한국어 포털과 같은 김재효 수업자료·공통교재 데이터셋의 영문 병기
  (영문 병기가 없는 항목은 translations_en.json의 anatomy_fill)
- 주치증·분류·자침깊이 출전·자침법: translations_en.json
- 그 밖의 값(KCD 코드·한자·이명·자침깊이 수치·장수)은 한국어 포털 그대로
- 주의(Caution)는 영문판에만 표기한다(2026-11-15 사용자 결정). 한국어판에는 넣지 않는다.

영문 POINTS_DATA는 한국어판과 같은 키 구조를 유지하고 값만 영어로 바꾼다
(name=한국 한자음 로마자, meridian_ko=영문 경맥명, *_bilingual·*_ko=영문 목록).
추가 키: pinyin, name_ko.

사용: python scripts/handbook_portal_en/build_handbook_portal_en.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC_HTML = os.path.join(REPO, "tools", "acupoint-handbook.html")
OUT_HTML = os.path.join(REPO, "tools", "acupoint-handbook-en.html")
EN_POINTS = os.path.join(HERE, "handbook_en_points.json")
TRANS = os.path.join(HERE, "translations_en.json")

HANGUL = re.compile(r"[가-힣]")


def load_points(html):
    m = re.search(r"^    const POINTS_DATA = (.*);\r?$", html, re.M)
    return json.loads(m.group(1))


def load_meridians(html):
    m = re.search(r"^    const MERIDIANS = (.*);\r?$", html, re.M)
    return json.loads(m.group(1))


def anat_lines(bilingual, fill):
    """'큰가슴근 (pectoralis major)' → 'pectoralis major'. 영문 병기가 없으면 anatomy_fill."""
    out = []
    for line in (bilingual or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        m = re.search(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)\s*$", line)
        if m and not HANGUL.search(m.group(1)):
            out.append(m.group(1).strip())
        elif line in fill:
            out.append(fill[line])
        else:
            raise KeyError(f"anatomy_fill에 없음: {line}")
    return out


def depth_en(v, t):
    if not v:
        return v
    s = v
    for ko, en in t["depth_terms"].items():
        s = s.replace(ko, en)
    if HANGUL.search(s):
        raise KeyError(f"depth_terms에 없음: {v}")
    return s


def lookup(table, key, what):
    if not key:
        return key
    if key not in table:
        raise KeyError(f"{what}에 없음: {key}")
    return table[key]


def translate_point(p, en, t, by_code):
    e = dict(en[p["code"]])
    e.update(t.get("point_override", {}).get(p["code"], {}))
    q = json.loads(json.dumps(p, ensure_ascii=False))
    q["name_ko"] = p["name"]
    q["name"] = e["romanization_ko"]
    q["pinyin"] = e["pinyin"]
    q["meridian_ko"] = p["meridian_en"]

    loc = e["location"]
    if e["location_notes"]:
        loc += " • " + " • ".join(e["location_notes"])
    q["handbook"] = {
        "location": loc,
        "find_method": e["guide"],
        "caution": e["caution"],
        "pdf_source": e["pdf"],
        "page": e["page"],
    }

    fill = t["anatomy_fill"]
    kjh = p["anatomy"]["kjh"]
    for k in ("muscle", "nerve", "vessel"):
        lines = anat_lines(kjh[f"{k}_bilingual"], fill)
        q["anatomy"]["kjh"][f"{k}_bilingual"] = "\n".join(lines)
        q["anatomy"]["kjh"][f"{k}_ko"] = lines
        q["anatomy"]["kjh"][f"{k}_en"] = lines
    com = p["anatomy"]["common"]
    over = t["common_override"].get(p["code"], {})
    for k in ("muscle", "nerve", "vessel"):
        en_list = over.get(k, com[f"{k}_en"])
        if len(en_list) != len(com[f"{k}_ko"]):
            raise ValueError(f"공통교재 {p['code']} {k}: 한·영 항목 수 불일치")
        q["anatomy"]["common"][f"{k}_ko"] = en_list
        q["anatomy"]["common"][f"{k}_en"] = en_list

    ind = q["indications"]
    if HANGUL.search(ind.get("moxa_huanglongxiang") or ""):
        ind["moxa_huanglongxiang"] = lookup(t["moxa_values"], ind["moxa_huanglongxiang"], "moxa_values")
    if HANGUL.search(ind.get("depth_huanglongxiang") or ""):
        ind["depth_huanglongxiang"] = lookup(t["depth_hlx_values"], ind["depth_huanglongxiang"], "depth_hlx_values")
    for cat in q["indications"]["categories"]:
        cat["category"] = lookup(t["categories"], cat["category"], "categories")
        for it in cat["items"]:
            it["ind"] = lookup(t["indications"], it["ind"], "indications")

    dl = q["depth_literature"]
    for k in ("mingtang", "jiayijing", "jingyanfang", "donguibogam",
              "common_range", "acupuncture_range", "tongkao_range"):
        dl[k] = depth_en(dl[k], t)
    for k in ("common_method", "tongkao_method"):
        dl[k] = lookup(t["methods"], dl[k], "methods")
        dl["raw"][k] = dl[k]
    dl["dongui_source"] = lookup(t["dongui_source"], dl["dongui_source"], "dongui_source")
    dl["raw"]["dongui_source"] = dl["dongui_source"]

    for hm in q.get("homonym_matches", []):
        tgt = by_code[hm["target_code"]]
        src = by_code[hm["src_code"]]
        hm["target_name"] = en[tgt["code"]]["romanization_ko"]
        hm["match_pronunciation"] = en[tgt["code"]]["romanization_ko"]
        hm["src_name"] = en[src["code"]]["romanization_ko"]
    return q


def main():
    html = open(SRC_HTML, encoding="utf-8", newline="").read()
    en = json.load(open(EN_POINTS, encoding="utf-8"))
    t = json.load(open(TRANS, encoding="utf-8"))
    for part in t.get("indication_files", []):
        t["indications"].update(json.load(open(os.path.join(HERE, part), encoding="utf-8")))

    points = load_points(html)
    by_code = {p["code"]: p for p in points}
    pts_en = [translate_point(p, en, t, by_code) for p in points]

    mers = load_meridians(html)
    for m in mers:
        m["name"] = re.sub(r"\s*\([A-Z]{2}\)$", "", m["en"])

    out = html
    out = re.sub(r"^    const POINTS_DATA = .*;(\r?)$",
                 lambda m: "    const POINTS_DATA = " + json.dumps(pts_en, ensure_ascii=False) + ";" + m.group(1),
                 out, count=1, flags=re.M)
    out = re.sub(r"^    const MERIDIANS = .*;(\r?)$",
                 lambda m: "    const MERIDIANS = " + json.dumps(mers, ensure_ascii=False) + ";" + m.group(1),
                 out, count=1, flags=re.M)

    nl = "\r\n" if "\r\n" in html else "\n"
    for ko, en_s in UI_REPLACEMENTS:
        ko, en_s = ko.replace("\n", nl), en_s.replace("\n", nl)
        n = out.count(ko)
        if n == 0:
            raise ValueError(f"UI 문구를 찾지 못함: {ko[:80]}")
        out = out.replace(ko, en_s)

    # 데이터 줄을 뺀 나머지에 한글이 남았는지 검사
    rest = "\n".join(l for l in out.split("\n")
                     if not l.startswith("    const POINTS_DATA") and not l.startswith("    const MERIDIANS"))
    allowed_ko = ("lang-switch", "page-view-counter", "경혈학 핸드북 포털 · English Edition", "title=\"한국어판\"")
    left = [l.strip()[:120] for l in rest.split("\n")
            if HANGUL.search(l) and not any(a in l for a in allowed_ko)]
    if left:
        raise ValueError("번역되지 않은 UI 문구:\n" + "\n".join(left))
    data_left = set()
    for p in pts_en:
        blob = json.dumps({k: v for k, v in p.items() if k not in ("name_ko",)}, ensure_ascii=False)
        blob = re.sub(r'"(pdf_source|src_hanja)": "[^"]*"', "", blob)
        data_left.update(HANGUL.findall(blob))
    if data_left:
        raise ValueError(f"영문 데이터에 한글이 남음: {''.join(sorted(data_left))[:80]}")

    open(OUT_HTML, "w", encoding="utf-8", newline="").write(out)
    print(f"{len(pts_en)} points -> {OUT_HTML} ({len(out.encode('utf-8')):,} bytes)")


# (한국어 원문, 영어) — 원본에 없으면 오류
UI_REPLACEMENTS = [
    ('<html lang="ko">', '<html lang="en">'),
    ('          <span class="page-view-counter" style="display:inline-flex;align-items:center;margin:0 4px;vertical-align:middle;" title="Views 열람 횟수"><a href="https://hits.sh/jaehyokim-sketch.github.io/acupoint_anatomy/tools/acupoint-handbook.html/" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-flex;align-items:center;"><img src="https://hits.sh/jaehyokim-sketch.github.io/acupoint_anatomy/tools/acupoint-handbook.html.svg?style=flat-square&label=%EC%A1%B0%ED%9A%8C%EC%88%98&color=2563eb&labelColor=0f172a" alt="Views" style="height:20px;vertical-align:middle;border-radius:3px;" /></a></span>',
     '          <span class="page-view-counter" style="display:inline-flex;align-items:center;margin:0 4px;vertical-align:middle;" title="Views 열람 횟수"><a href="https://hits.sh/jaehyokim-sketch.github.io/acupoint_anatomy/tools/acupoint-handbook-en.html/" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-flex;align-items:center;"><img src="https://hits.sh/jaehyokim-sketch.github.io/acupoint_anatomy/tools/acupoint-handbook-en.html.svg?style=flat-square&label=%EC%A1%B0%ED%9A%8C%EC%88%98&color=2563eb&labelColor=0f172a" alt="Views" style="height:20px;vertical-align:middle;border-radius:3px;" /></a></span>'),
    ("<title>경혈학 핸드북 포털 (Acupoint Handbook Portal) — 14경맥 361경혈 표준 정본</title>",
     "<title>Acupoint Handbook Portal — 361 Standard Acupoints of the 14 Meridians</title>"),
    ('content="14경맥 361종 경혈 핸드북 포털: 김재효 수업자료 및 경혈학 공통교재 해부구조 데이터셋, 문헌별 자침깊이(명당경·갑을경·경험방·동의보감·공통교재·통고), 황룡상 고증 침구법, 표준 KCD 질병코드 연계, KJH 경혈명 비교정리 및 본명-이명 혼동주의 경보"',
     'content="Acupoint handbook portal for the 361 acupoints of the 14 meridians: anatomical structure datasets (Prof. Jae-Hyo Kim\'s lecture data and the Common Textbook of Acupoint Science), needling depth by classical literature (Mingtangjing, Jiayijing, Gyeongheombang, Donguibogam, Common Textbook, Tongkao), acupuncture-moxibustion methods verified by Huang Longxiang, KCD disease code mapping, and KJH acupoint name comparison with standard-name/alias confusion alerts"'),
    ("""            <span>경혈학 핸드북 포털</span>
            <span style="font-size: 1rem; font-weight: 500; opacity: 0.8;">Acupoint Handbook Portal</span>""",
     """            <span>Acupoint Handbook Portal</span>
            <span style="font-size: 1rem; font-weight: 500; opacity: 0.8;">경혈학 핸드북 포털 · English Edition</span>"""),
    ("<p>14경맥 361종 표준 경혈 정본: 원광대 한의과대학 핸드북 · 7대 문헌군 자침깊이 · 황룡상 고증 침구법 · KCD-8 질병코드 · KJH 경혈명 및 이명 대조</p>",
     "<p>Standard reference for the 361 acupoints of the 14 meridians: Wonkwang University College of Korean Medicine Handbook · needling depth in 7 literature groups · acupuncture-moxibustion methods verified by Huang Longxiang · KCD-8 disease codes · KJH acupoint name &amp; alias comparison</p>"),
    ('<span class="badge gold">14경맥 361혈 전수 완비</span>', '<span class="badge gold">All 361 points of the 14 meridians</span>'),
    ('<span class="badge">7대 문헌군 자침깊이</span>', '<span class="badge">Needling depth in 7 literature groups</span>'),
    ('<span class="badge">황룡상 침구법 &amp; KCD-8</span>', '<span class="badge">Huang Longxiang methods &amp; KCD-8</span>'),
    ('<span class="badge rose">⚠️ 본명-이명 혼동주의 35쌍 경보</span>',
     '<span class="badge rose">⚠️ 35 standard-name/alias confusion alerts</span>'),
    ('href="acupoint-handbook-en.html" title="English edition">🌐 English</a>',
     'href="acupoint-handbook.html" title="한국어판">🌐 한국어</a>'),
    ('placeholder="경혈코드, 국문명, 한자, 이명, 위치, 근육, 신경, 혈관, 주치증, KCD 검색..."',
     'placeholder="Search code, name, pinyin, hanja, alias, location, muscle, nerve, vessel, indication, KCD..."'),
    ('<option value="ALL">전체 경맥 (All Meridians)</option>', '<option value="ALL">All Meridians</option>'),
    ('<option value="ALL">전체 자침법 (All Methods)</option>', '<option value="ALL">All Needling Methods</option>'),
    ('<option value="직자">직자 (Perpendicular)</option>', '<option value="Perpendicular">Perpendicular</option>'),
    ('<option value="사자">사자 (Oblique)</option>', '<option value="Oblique">Oblique</option>'),
    ('<option value="횡자">횡자 / 연피자 (Transverse)</option>', '<option value="Transverse">Transverse / Subcutaneous</option>'),
    ('<option value="ALL">전체 혈위 (모든 항목)</option>', '<option value="ALL">All Acupoints</option>'),
    ('<option value="homonym">⚠️ 본명-이명 혼동주의 (34혈)</option>', '<option value="homonym">⚠️ Name/Alias Confusion (34 points)</option>'),
    ('<option value="muscle">근육(Muscles) 포함</option>', '<option value="muscle">With Muscles</option>'),
    ('<option value="nerve">신경(Nerves) 포함</option>', '<option value="nerve">With Nerves</option>'),
    ('<option value="vessel">혈관(Vessels) 포함</option>', '<option value="vessel">With Vessels</option>'),
    ('<span class="label">수록 경맥</span>', '<span class="label">Meridians</span>'),
    ('<span class="label">표준 경혈수</span>', '<span class="label">Standard Acupoints</span>'),
    ('<span class="label">검색된 경혈</span>', '<span class="label">Matching Acupoints</span>'),
    ('<span class="label">본명-이명 혼동주의</span>', '<span class="label">Name/Alias Confusion</span>'),
    ('35 Pairs (34혈)', '35 Pairs (34 pts)'),
    ('data-meridian="ALL">전체 <span', 'data-meridian="ALL">All <span'),
    ('title="맨 위로"', 'title="Back to top"'),
    ("<p><strong>경혈학 핸드북 포털 (Acupoint Handbook Portal) v1.2</strong></p>",
     "<p><strong>Acupoint Handbook Portal v1.2 — English Edition</strong></p>"),
    ("<p>학술 고증 및 데이터 출처: 《핸드북(한 영) 한글판》 (원광대학교 한의과대학 경혈학교실 &amp; 최수빈(KMD)) · 《침구문헌별 자침깊이 정리_AI 분석용》 (황제명당경·침구갑을경·침구경험방·동의보감·경락수혈학·침구의학·침구수혈통고) · 《김재효 수업_경혈_해부구조_데이터셋》 · 《경혈학공통교재 해부구조 데이터셋》 · 《경혈별 주치증 정리 V2》 (황룡상 교수 고증 침구법 &amp; KCD-8 질병코드 연계) · 《경혈명_비교_정리_KJH》 (표준 한자명·이명 및 본명-이명 일치 Case A 경보)</p>",
     "<p>Sources: <i>Acupoint Handbook (Korean/English), English Edition</i> (Department of Acupoint Science, College of Korean Medicine, Wonkwang University &amp; Subin Choi, KMD) · <i>Needling Depth by Acupuncture Literature</i> (Huangdi Mingtangjing, Zhenjiu Jiayijing, Chimgu Gyeongheombang, Donguibogam, Meridian &amp; Acupoint Textbook, Acupuncture Medicine, Zhenjiu Shuxue Tongkao) · <i>Prof. Jae-Hyo Kim's Lecture Dataset of Acupoint Anatomy</i> · <i>Common Textbook Anatomy Dataset</i> · <i>Indications by Acupoint V2</i> (methods verified by Prof. Huang Longxiang &amp; KCD-8 disease codes) · <i>KJH Acupoint Name Comparison</i> (standard hanja names, aliases and Case A standard-name/alias match alerts). Indication terms were translated from the Korean edition.</p>"),
    ("opt.textContent = `${m.name} (${m.code}) - ${m.count}혈`;",
     "opt.textContent = `${m.name} (${m.code}) - ${m.count} points`;"),
    ("        const matchName = p.name.toLowerCase().includes(q);",
     "        const matchName = p.name.toLowerCase().includes(q) || (p.pinyin || '').toLowerCase().includes(q) || (p.name_ko || '').includes(q);"),
    ("검색 조건과 일치하는 경혈이 없습니다.", "No acupoints match the current search and filters."),
    ("주치증 데이터 없음", "No indication data"),
    ("<span>⚠️ 본명-이명 혼동주의 (Case A: 타 경혈 정명과 일치)</span>",
     "<span>⚠️ Name/Alias Confusion (Case A: alias identical to another acupoint's standard name)</span>"),
    ("• 이명 <strong>「${escapeHtml(hm.match_alias)}」</strong>(${escapeHtml(hm.match_pronunciation || '')})은",
     "• Alias <strong>「${escapeHtml(hm.match_alias)}」</strong> (${escapeHtml(hm.match_pronunciation || '')}) is identical to the standard name of"),
    ("""                    의 본명(정명)과 일치함
""", ""),
    ("""<span class="point-hanja">${p.hanja}</span>""",
     """<span class="point-hanja">${p.hanja}</span>
                ${p.pinyin ? `<span class="point-pinyin" style="font-size: 0.85rem; color: #64748b; font-style: italic;">${escapeHtml(p.pinyin)}</span>` : ''}"""),
    ('title="강의슬라이드 표기 한자">교재: ', 'title="Hanja as written in the lecture slides">Textbook: '),
    ("<strong>[이명]</strong>", "<strong>[Aliases]</strong>"),
    ("위치 및 취혈 (Location & Method)", "Location &amp; Guide"),
    ("<strong>[부위]</strong> ${escapeHtml(p.handbook.location || '위치 기술 준비 중')}",
     "<strong>[Location]</strong> ${escapeHtml(p.handbook.location || 'Location description in preparation')}"),
    ("<strong>[취혈]</strong>", "<strong>[Guide]</strong>"),
    ("<strong>황제명당경:</strong>", "<strong>Mingtangjing (明堂經):</strong>"),
    ("<strong>뜸법:</strong>", "<strong>Moxibustion:</strong>"),
    ("p.indications.moxa_huanglongxiang + ' 장'", "p.indications.moxa_huanglongxiang + ' cones'"),
    ("<strong>자침법:</strong>", "<strong>Needling:</strong>"),
    ("<strong>통고 자침법:</strong>", "<strong>Tongkao needling:</strong>"),
    ("<th>침구갑을경</th>", "<th>Jiayijing (甲乙經)</th>"),
    ("<th>침구경험방</th>", "<th>Gyeongheombang (經驗方)</th>"),
    ("<th>동의보감</th>", "<th>Donguibogam (東醫寶鑑)</th>"),
    ("<th>경락수혈학</th>", "<th>Meridian &amp; Acupoint Textbook</th>"),
    ("<th>침구의학</th>", "<th>Acupuncture Medicine</th>"),
    ("<th>침구수혈통고</th>", "<th>Shuxue Tongkao (腧穴通考)</th>"),
    ("<span>해부학적 구조 (Anatomical Structures)</span>", "<span>Anatomical Structures</span>"),
    ('<span style="font-size: 0.75rem; color: var(--primary);">상세보기 ▼</span>',
     '<span style="font-size: 0.75rem; color: var(--primary);">Details ▼</span>'),
    ("근육 (Muscles) - 김재효 수업자료", "Muscles - Prof. Jae-Hyo Kim's lecture data"),
    ("신경 (Nerves) - 김재효 수업자료", "Nerves - Prof. Jae-Hyo Kim's lecture data"),
    ("혈관 (Vessels) - 김재효 수업자료", "Vessels - Prof. Jae-Hyo Kim's lecture data"),
    ("<strong>공통교재 대조:</strong>", "<strong>Common Textbook:</strong>"),
    ("주치증 및 표준 KCD 질병분류 (Indications &amp; KCD-8)", "Indications &amp; KCD-8 Disease Codes"),
    ("arrow.textContent = '상세보기 ▲';", "arrow.textContent = 'Details ▲';"),
    ("arrow.textContent = '상세보기 ▼';", "arrow.textContent = 'Details ▼';"),
]


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError) as ex:
        print(f"[ERROR] {ex}")
        sys.exit(1)

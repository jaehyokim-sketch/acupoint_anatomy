"""영문판 핸드북 PDF(14경맥)에서 경혈별 영문 항목을 추출한다.

입력: Drive `강의/경혈학 교재 편찬/핸드북(한 영)/영문판/0304_영_첨삭반영 NN. <경맥>.pdf`
출력: scripts/handbook_portal_en/handbook_en_points.json
      {code: {name_ko, romanization_ko, pinyin, hanja, location, location_notes[],
              guide, muscle[], nerve[], vessel[], moxibustion, caution,
              specificity, usage, pdf, page}}

사용: python scripts/handbook_portal_en/extract_handbook_en.py [영문판 폴더]
"""
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")
import pymupdf  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SRC = r"G:\내 드라이브\강의\경혈학 교재 편찬\핸드북(한 영)\영문판"
OUT = os.path.join(HERE, "handbook_en_points.json")

CODE_RE = re.compile(r"^(LU|LI|ST|SP|HT|SI|BL|KI|PC|TE|GB|LR|CV|GV)(\d{1,2})$")
SECTION_KEYS = ["Location", "Guide", "Anatomy", "Method", "Specificity", "Usage"]
HANGUL = re.compile(r"[\uac00-\ud7a3]")
CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
LATIN = re.compile(r"^[A-Za-z][A-Za-z'\-]*\)?$")
BULLET = "\uf09f"

# 영문판 오기 보정: (잘못 표기된 코드, 한자) → 올바른 코드
FIX_CODE = {("HT07", "少府"): "HT08"}


def norm_code(prefix, num):
    return f"{prefix}{int(num):02d}"


def fix_ordinals(s):
    return re.sub(r"(\d)\s+(st|nd|rd|th)\b", r"\1\2", s)


def norm(s):
    s = s.replace(BULLET, "•").replace("ﾠ", " ")
    return fix_ordinals(re.sub(r"\s+", " ", s).strip())


def split_points(text):
    """한 페이지에 경혈이 여러 개일 수 있으므로 코드 머리글 줄 기준으로 나눈다."""
    lines = text.split("\n")
    starts = []
    for i, l in enumerate(lines):
        if CODE_RE.match(l.strip()):
            nxt = next((x for x in lines[i + 1:i + 4] if x.strip()), "")
            if HANGUL.search(nxt):
                starts.append(i)
    chunks = []
    for k, st in enumerate(starts):
        en = starts[k + 1] if k + 1 < len(starts) else len(lines)
        chunk = lines[st:en]
        if any(x.strip() == "Location" for x in chunk):
            chunks.append(chunk)
    return chunks


def parse_chunk(lines):
    lines = [l.rstrip() for l in lines]
    m = CODE_RE.match(lines[0].strip())
    code = norm_code(m.group(1), m.group(2))

    idx_loc = next(i for i, l in enumerate(lines) if l.strip() == "Location")
    toks = " ".join(lines[1:idx_loc]).split()
    hangul = "".join(t for t in toks if HANGUL.search(t))
    hanja = "".join("".join(CJK.findall(t)) for t in toks if CJK.search(t))
    latin = [t.rstrip(")") for t in toks if LATIN.match(t)]
    romanization = latin[0] if latin else ""
    pinyin = " ".join(latin[1:]) if len(latin) > 1 else ""

    sec = {}
    cur = None
    for l in lines[idx_loc:]:
        st = l.strip()
        if st == "주치":  # 일부 페이지는 Usage 머리글이 한국어. 앞의 'Usage'는 실제로 Specificity
            if cur == "Usage":
                sec["Specificity"] = sec.pop("Usage")
            cur = "Usage"
            sec[cur] = []
            continue
        if st in SECTION_KEYS:
            cur = st
            sec[cur] = []
            continue
        if cur:
            sec[cur].append(l)

    # Location: 본문 + (글머리표) 보충 문구
    paras, buf = [], []
    for l in sec.get("Location", []):
        st = l.strip()
        if st.startswith(BULLET):
            if buf:
                paras.append(norm(" ".join(buf)))
            rest = st[len(BULLET):].strip()
            buf = [rest] if rest else []
            continue
        if st:
            buf.append(st)
    if buf:
        paras.append(norm(" ".join(buf)))
    location = paras[0] if paras else ""
    location_notes = [p for p in paras[1:] if p]

    guide = norm(" ".join(sec.get("Guide", [])))

    anat = {"muscle": [], "nerve": [], "vessel": []}
    key = None
    pending_blood = False
    for l in sec.get("Anatomy", []):
        st = l.strip()
        if not st:
            continue
        if st == "muscle":
            key = "muscle"
            continue
        if st == "nerve":
            key = "nerve"
            continue
        if st == "blood":
            pending_blood = True
            continue
        if pending_blood and st == "vessel":
            key = "vessel"
            pending_blood = False
            continue
        if st == "blood vessel":
            key = "vessel"
            continue
        if not key:
            continue
        prev = anat[key][-1] if anat[key] else ""
        joins = (
            re.fullmatch(r"(st|nd|rd|th)", st)  # 위첨자 조각
            or (prev and re.search(r"\d$", prev) and re.match(r"(st|nd|rd|th)\b", st))
            or (prev and st[:1].islower() and re.search(r"\b(of|the|and|to|from|branch)$", prev))
        )
        if joins:
            anat[key][-1] = norm(prev + " " + st)
        else:
            anat[key].append(norm(st))

    meth = sec.get("Method", [])
    mm = re.search(r"moxibustion\s*([○◯×✕⨉△])", "\n".join(meth))
    moxa = mm.group(1) if mm else ""
    caution = ""
    ci = next((i for i, l in enumerate(meth) if l.strip() == "Caution"), None)
    if ci is not None:
        caution = norm(" ".join(l.strip() for l in meth[ci + 1:]))

    return code, {
        "code_label": lines[0].strip(),
        "name_ko": hangul,
        "romanization_ko": romanization,
        "pinyin": pinyin,
        "hanja": hanja,
        "location": location,
        "location_notes": location_notes,
        "guide": guide,
        "muscle": anat["muscle"],
        "nerve": anat["nerve"],
        "vessel": anat["vessel"],
        "moxibustion": moxa,
        "caution": caution,
        "specificity": norm(" ".join(sec.get("Specificity", []))),
        "usage": norm(" ".join(sec.get("Usage", []))),
    }


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    pdfs = sorted(f for f in os.listdir(src) if re.match(r"0304_영_첨삭반영 \d\d\. .+\.pdf$", f))
    out = {}
    for f in pdfs:
        doc = pymupdf.open(os.path.join(src, f))
        for i in range(doc.page_count):
            for chunk in split_points(doc[i].get_text()):
                code, rec = parse_chunk(chunk)
                code = FIX_CODE.get((code, rec["hanja"]), code)
                if code in out:
                    print(f"[DUP] {code} {f} p{i + 1}")
                    continue
                rec["pdf"] = f
                rec["page"] = i + 1
                out[code] = rec
    with open(OUT, "w", encoding="utf-8", newline="\n") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=1)
    print(f"{len(out)} points -> {OUT}")


if __name__ == "__main__":
    main()

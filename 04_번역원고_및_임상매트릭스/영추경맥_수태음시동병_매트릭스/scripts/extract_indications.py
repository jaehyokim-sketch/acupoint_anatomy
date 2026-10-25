# -*- coding: utf-8 -*-
"""[경혈해부] Rank 1~4: 《针灸腧穴通考》 361혈 【适应症】 조문 파싱 → 수태음 시동병 증상군 대응 경혈 추출.

출력: indications.json (경혈별 조문·출전·시기·증상군·배오/오록 표지), candidates.csv
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"G:\내 드라이브\도서 번역")
TK = ROOT / "01_도서_번역_및_원전" / "침구수혈통고(针灸腧穴通考)"
OUT = Path(__file__).resolve().parent

HDR = re.compile(r"^### （[一二三四五六七八九十百]+）(\S+) (\S+) ((?:LU|LI|ST|SP|HT|SI|BL|KI|PC|TE|GB|LR|GV|CV)\d+) ")
SEC = re.compile(r"^#{2,4} ")
ITEM = re.compile(r"^[\s　]*(\d+)\.\s*(.*)$")
SUB = re.compile(r"^[\s　]*\((\d+)\)\s*(.*)$")

# 시동병 증상군 — 《灵枢·经脉》 층(A~D)과 《阴阳十一脉灸经》 원형 층(E)
GROUPS = {
    "A_胀满膨膨": r"肺胀|胸[中]?[^，。；]{0,3}[膨彭滂]{2}|心[^，。；]{0,4}[膨彭滂]{2}|胀满[膨彭滂]{2}|胸中?满|胸胀|胸中胀",
    "B_喘咳": r"喘|咳|欬|上气",
    "C_缺盆中痛": r"缺盆[中]?[^，。；、]{0,5}痛",
    "D_交两手而瞀_臂厥": r"交两手|而瞀|而務|如瞀|(?<!肘)臂厥(?!痛)",
    "E_心痛_心膨膨": r"心痛|心[膨彭滂]{2}",
}
SPECIFIC = ("A_胀满膨膨", "C_缺盆中痛", "D_交两手而瞀_臂厥")

ERA = [  # (시기, 출전 정규식) — 앞에서부터 첫 적중
    ("1_先秦两汉", r"黄帝明堂经|黄帝内经明堂|明堂经|灵枢|素问|难经|阴阳十一脉|足臂十一脉"),
    ("2_魏晋隋唐", r"甲乙|千金|外台|医心方|太素|甄权|产经|肘后|小品"),
    ("3_宋金元", r"圣惠|铜人|资生|西方子|窦太师|琼瑶|玉龙|标幽|扁鹊心书|圣济|指南|子午|针经摘英|卫生宝鉴|儒门事亲|普济"),
    ("4_明清", r"聚英|大成|六集|图翼|循经|医统|入门|神应|大全|金鉴|逢源|集成|采艾|医学纲目|类经|奇效|杨敬斋|刺灸心法|勉学堂"),
    ("5_现代", r"针灸学|教材|讲义|中国针灸学|国标|经穴部位|19\d\d|20\d\d|版《"),
]


def era_of(src):
    for name, pat in ERA:
        if re.search(pat, src):
            return name
    return "9_미상"


def split_points():
    pts = {}
    for f in sorted(TK.glob("针灸腧穴通考_*.md")):
        lines = f.read_text(encoding="utf-8").splitlines()
        cur = None
        for i, l in enumerate(lines, 1):
            m = HDR.match(l)
            if m:
                cur = {"code": m.group(3), "name": m.group(1), "pinyin": m.group(2),
                       "file": f.name, "start": i, "lines": []}
                pts[cur["code"]] = cur
                continue
            if cur is not None:
                cur["lines"].append((i, l))
    return pts


def parse_indications(pt, other_names):
    """【适应症】 절의 번호 조문만(附：临床应用举例 제외). 각 조문 뒤 按 문장을 붙인다."""
    items, in_sec = [], False
    for i, l in pt["lines"]:
        if SEC.match(l):
            in_sec = "【适应症】" in l
            continue
        if not in_sec:
            continue
        s = l.strip()
        if s.startswith("**按**") and items:
            items[-1]["note"] += s
            continue
        m = ITEM.match(l) or SUB.match(l)
        if not m or not m.group(2):
            continue
        text = m.group(2)
        src = "".join(re.findall(r"（([^（）]*《[^（）]*)）\s*$", text)) or ""
        body = re.sub(r"（[^（）]*《[^（）]*）\s*$", "", text)
        if not src and re.search(r"遗存|教材|针灸学教材", text):
            continue  # 소제목 행
        items.append({"line": i, "text": body, "source": src, "era": era_of(src), "note": ""})
    for it in items:
        note = it["note"]
        # Rank 4 ① 오록·전사 오류, ② 경맥병후 전재(母子補瀉 등 이론적 귀속) — 《通考》 按語 기준
        err = re.search(r"误|错入|不知.{0,4}所据|欠妥", note)
        trans = re.search(r"经.{0,4}病候.{0,24}(?:归|录|列)|(?:归|录|列|辑).{0,24}经.{0,4}病候|悉为.{0,8}病候|全出于.{0,8}病候|母子补泻", note)
        quoted = re.findall(r"“([^”]{2,40})”", note)
        text = it["text"]
        it["flag"] = "오록" if err else ("경맥병후_전재" if trans else "")
        if it["flag"] and it["era"] != "1_先秦两汉":
            # 按語가 인용한 구절만 제거, 인용이 없으면 조문 전체 무효
            text = ""  # 후대 조문은 按語가 지목하면 통째로 제외(Rank 4 보수 원칙)
        it["text_valid"] = text
        # 구절(clause) 단위 배오 판정: 다른 혈명이 取·刺·灸·及·、 뒤에 오는 구절
        single_cl, combo_cl, combo_with = [], [], set()
        for cl in [c for c in re.split(r"[。；]", text) if c.strip()]:
            hit = [n for n in other_names if n != pt["name"] and re.search(
                rf"(?:取|刺|灸|及|、|并取){n}|{n}(?:、|及|主之)", cl)]
            (combo_cl if hit else single_cl).append(cl)
            combo_with.update(hit)
        it["combo_with"] = sorted(combo_with)
        it["groups"] = [g for g, p in GROUPS.items() if any(re.search(p, c) for c in single_cl)]
        it["groups_combo"] = [g for g, p in GROUPS.items() if any(re.search(p, c) for c in combo_cl)]
        it["misrecorded"] = False
    return items


def main():
    pts = split_points()
    names = sorted({p["name"] for p in pts.values()}, key=len, reverse=True)
    names = [n for n in names if len(n) >= 2 and n not in ("缺盆", "膻中", "气海", "关元")]  # 해부 부위어와 겹치는 혈명은 배오 판정에서 제외
    out = {}
    for code, pt in pts.items():
        items = parse_indications(pt, names)
        han = [it for it in items if it["era"] == "1_先秦两汉"]
        g_all = sorted({g for it in items for g in it["groups"]})
        g_han = sorted({g for it in han for g in it["groups"]})
        g_combo = sorted({g for it in items for g in it["groups_combo"]})
        out[code] = {"code": code, "name": pt["name"], "pinyin": pt["pinyin"], "file": pt["file"],
                     "start": pt["start"], "n_items": len(items), "groups_single_all": g_all,
                     "groups_single_han": g_han, "groups_combo": g_combo, "items": items}
    (OUT / "indications.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = []
    for code, d in out.items():
        spec_all = [g for g in d["groups_single_all"] if g in SPECIFIC]
        spec_han = [g for g in d["groups_single_han"] if g in SPECIFIC]
        core4 = [g for g in d["groups_single_all"] if g != "E_心痛_心膨膨"]
        if spec_all and len(core4) >= 2:
            rows.append({"code": code, "name": d["name"], "pinyin": d["pinyin"],
                         "n_groups_all": len(core4), "groups_all": "|".join(d["groups_single_all"]),
                         "n_groups_han": len([g for g in d["groups_single_han"] if g != "E_心痛_心膨膨"]),
                         "groups_han": "|".join(d["groups_single_han"]),
                         "specific_han": "|".join(spec_han), "file": d["file"]})
    rows.sort(key=lambda r: (-r["n_groups_han"], -r["n_groups_all"], r["code"]))
    with open(OUT / "candidates.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("points parsed:", len(out), "| candidates:", len(rows))
    for r in rows:
        print(r["code"], r["name"], r["n_groups_han"], r["groups_han"], "||", r["n_groups_all"], r["groups_all"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

# -*- coding: utf-8 -*-
"""[경혈해부] 『동의보감』 두통 鍼灸法 20혈의 단독 주치($P_{single}$) 두통 증상군 추출 (Rank 1~4).

입력: ../lu_sd/indications.json(《通考》 361혈 【适应症】 파싱 결과 — 구절 단위 배오 분리, 按語 기준 오록·전재 표지 포함)
      《通考》 经外奇穴 太阳(EX-HN5) 절은 직접 파싱
출력: headache_points.json
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TK = Path(r"G:\내 드라이브\도서 번역\01_도서_번역_및_원전\침구수혈통고(针灸腧穴通考)")
IND = json.loads((HERE.parent / "lu_sd" / "indications.json").read_text(encoding="utf-8"))

# 두통 증상군(간체 원문 대조)
HG = {
    "H1_頭痛·頭風": r"头痛|头疼|头风|首风|脑风|脑痛|头脑痛|巅痛|顶痛|顶上痛|巅上痛|头上痛|头中痛|头[眩项重]痛",
    "H2_偏頭·側頭": r"偏头|头半|头角|额角痛|颞",
    "H3_前頭·眉稜": r"眉棱|眉头|眉间|眉攒|额痛|前头痛",
    "H4_頭重·眩": r"头重|眩|头旋|脑旋",
    "H5_項強·項痛": r"项强|项痛|颈项痛|头项|项急",
}
# 『동의보감』 鍼灸法 두통 처방 20혈 (Tongkao 코드)
POINTS = ["GV20", "GV23", "GV24", "GV22", "GV21", "GV29", "TE23", "GB20", "GB7", "BL2", "ST8", "BL12",
          "LI4", "ST41", "ST36", "ST40", "CV12", "CV17", "CV4"]  # + EX-HN5 太阳(별도 파싱)


def groups(text):
    return [g for g, p in HG.items() if re.search(p, text)]


def from_ind(code):
    d = IND[code]
    items = []
    for it in d["items"]:
        txt = it.get("text_valid", it["text"])
        if not txt:
            continue
        single, combo = [], []
        for cl in [c for c in re.split(r"[。；]", txt) if c.strip()]:
            (combo if any(n in cl for n in it.get("combo_with", [])) else single).append(cl)
        gs = sorted({g for c in single for g in groups(c)})
        gc = sorted({g for c in combo for g in groups(c)})
        if gs or gc:
            hits = list(dict.fromkeys(m.group(0) for p in HG.values() for c in single for m in re.finditer(p, c)))
            items.append({"line": it["line"], "era": it["era"], "source": it["source"], "groups": gs, "groups_combo": gc,
                          "hits": hits, "flag": it.get("flag", ""), "text": txt[:300]})
    return {"code": code, "name": d["name"], "pinyin": d["pinyin"], "file": d["file"], "items": items}


def taiyang():
    """经外奇穴 太阳(EX-HN5) 【定位、主治与操作】 절 번호 조문."""
    f = TK / "针灸腧穴通考_25_下_经外奇穴·附录·后记.md"
    L = f.read_text(encoding="utf-8").split("\n")
    s0 = next(i for i, l in enumerate(L) if l.startswith("### （三）太阳"))
    s = next(i for i in range(s0, len(L)) if "【定位、主治与操作】" in L[i])
    e = next(i for i in range(s + 1, len(L)) if L[i].startswith("### （四）") or "【临床应用举例】" in L[i])
    items = []
    for i in range(s, e):
        m = re.match(r"^[\s　]*\d+\.\s*(.*)$", L[i])
        if not m:
            continue
        text = m.group(1)
        src = "".join(re.findall(r"（([^（）]*《[^（）]*)）\s*$", text))
        body = re.sub(r"（[^（）]*《[^（）]*）\s*$", "", text)
        gs = groups(body)
        if gs:
            era = ("3_宋金元" if re.search(r"圣惠|圣济|窦太师|资生|铜人", src) else "4_明清" if re.search(r"六集|大成|捷径|聚英|入门|银海", src)
                   else "5_现代" if re.search(r"针灸学|教材|讲义", src) else "9_미상")
            items.append({"line": i + 1, "era": era, "source": src, "groups": gs, "groups_combo": [],
                          "hits": list(dict.fromkeys(m.group(0) for p in HG.values() for m in re.finditer(p, body))),
                          "flag": "", "text": body[:300]})
    return {"code": "EX-HN5", "name": "太阳", "pinyin": "Tàiyáng", "file": f.name, "items": items}


def main():
    out = {c: from_ind(c) for c in POINTS}
    out["EX-HN5"] = taiyang()
    for c, d in out.items():
        han = sorted({g for it in d["items"] if it["era"] == "1_先秦两汉" for g in it["groups"]})
        later = sorted({g for it in d["items"] if it["era"] != "1_先秦两汉" for g in it["groups"]})
        combo = sorted({g for it in d["items"] for g in it["groups_combo"]})
        core = {"H1_頭痛·頭風", "H2_偏頭·側頭", "H3_前頭·眉稜"}
        tier = "I" if core & set(han) else ("II" if core & set(later) else "III")
        d.update({"groups_han": han, "groups_later": later, "groups_combo": combo, "tier": tier})
        print(c, d["name"], tier, "| 한대:", "·".join(x[:2] for x in han) or "—", "| 후대:", "·".join(x[:2] for x in later) or "—",
              "| 배오:", "·".join(x[:2] for x in combo) or "—")
    (HERE / "headache_points.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

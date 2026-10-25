# -*- coding: utf-8 -*-
"""보고서용 마크다운 표 조각(ko·en) 생성 → frag_ko.md / frag_en.md"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
from opencc import OpenCC
from scipy.cluster.hierarchy import fcluster

HERE = Path(__file__).resolve().parent
s2t = OpenCC("s2t").convert
IND = json.loads((HERE / "indications.json").read_text(encoding="utf-8"))
CL = json.loads((HERE / "clusters.json").read_text(encoding="utf-8"))
codes, Z, FEAT, INFO = CL["codes"], np.array(CL["linkage"]), CL["features"], CL["info"]
RANK = list(csv.DictReader(open(HERE / "ranking.csv", encoding="utf-8-sig")))
LA = {r["code"]: r for r in csv.DictReader(open(HERE / "layerA_counts.csv", encoding="utf-8-sig"))}
SEG = json.loads((HERE / "seg_table.json").read_text(encoding="utf-8"))
P = {"A_胀满膨膨": r"肺胀|胸[中]?[^，。；]{0,3}[膨彭滂]{2}|心[^，。；]{0,4}[膨彭滂]{2}|胀满[膨彭滂]{2}|胸中?满|胸胀|胸中胀",
     "B_喘咳": r"喘|咳|欬|上气", "C_缺盆中痛": r"缺盆[中]?[^，。；、]{0,5}痛",
     "D_交两手而瞀_臂厥": r"交两手|而瞀|而務|如瞀|(?<!肘)臂厥(?!痛)", "E_心痛_心膨膨": r"心痛|心[膨彭滂]{2}"}
TIERK = {"I": "1층", "II": "2층", "III": "3층"}
PIN = {}
for c in codes:
    PIN[c] = IND[c]["pinyin"]
NAMEKR = {"LU1": "중부", "LU3": "천부", "LU4": "협백", "LU5": "척택", "LU6": "공최", "LU7": "열결", "LU8": "경거", "LU9": "태연",
          "LU11": "소상", "LI1": "상양", "LI3": "삼간", "SI2": "전곡", "HT6": "음극", "HT7": "신문", "PC1": "천지", "SP18": "천계",
          "GB23": "첩근", "ST16": "응창", "ST18": "유근", "LR14": "기문", "KI22": "보랑", "KI23": "신봉", "KI24": "영허", "KI25": "신장",
          "KI27": "수부", "CV15": "구미", "CV18": "옥당", "CV21": "선기", "CV22": "천돌", "ST9": "인영", "ST12": "결분", "BL13": "폐수",
          "BL14": "궐음수", "BL17": "격수", "GV14": "대추", "GB21": "견정", "KI4": "대종", "GB41": "족임읍"}


def han_evidence(c):
    """한대 층(1층·2층) 또는 후대 층(3층) 근거 1~2조 — (행, 출전, 적중어)."""
    t = INFO[c]["tier"]
    out = []
    for it in IND[c]["items"]:
        if t != "III" and it["era"] != "1_先秦两汉":
            continue
        if not it["groups"] and not it.get("groups_combo"):
            continue
        hits = []
        for p in P.values():
            hits += [m.group(0) for m in re.finditer(p, it["text"])]
        hits = list(dict.fromkeys(hits))
        out.append((it["line"], it["source"].split("、")[0], hits, it.get("groups_combo", [])))
    return out[:2]


def tier_table(lang):
    rows = []
    hdr = ("| 층 | 코드 | 혈명 | 한대 단독 증상군 | 전 시기 단독 | 배오 구절 | 대표 근거(《通考》 행·출전·적중어) |\n| :-: | :-- | :-- | :-- | :-- | :-- | :-- |"
           if lang == "ko" else
           "| Tier | Code | Point | Han-era single-point groups | All-era single-point | In combination clause | Key evidence (Tongkao line, source, matched terms) |\n| :-: | :-- | :-- | :-- | :-- | :-- | :-- |")
    for t in ("I", "II", "III"):
        for c in [x for x in codes if INFO[x]["tier"] == t]:
            d = IND[c]
            g = lambda L: "".join(x[0] for x in L) or "—"
            ev = han_evidence(c)
            evs = "; ".join(f"L{l} {(s if lang == 'ko' else s2t(s))} “{'/'.join(h if lang == 'ko' else [s2t(x) for x in h])}”" for l, s, h, _ in ev)
            nm = s2t(d["name"])
            name = f"{NAMEKR[c]} {nm}" if lang == "ko" else f"{PIN[c]} ({nm}, {c})"
            rows.append(f"| {TIERK[t] if lang == 'ko' else t} | {c} | {name} | {g(d['groups_single_han'])} | {g(d['groups_single_all'])} | {g(d.get('groups_combo', []))} | {evs} |")
    return hdr + "\n" + "\n".join(rows)


def rank_table(lang):
    hdr = ("| 순위 | 코드 | 혈명 | 주치 층 | 太淵 유사도 | 등가중치 | 부위 | 척수 분절 | 가장 가까운 3혈 |\n| :-: | :-- | :-- | :-: | :-: | :-: | :-- | :-- | :-- |"
           if lang == "ko" else
           "| Rank | Code | Point | Tier | Similarity to LU9 | Equal weights | Region | Spinal segments | Three nearest points |\n| :-: | :-- | :-- | :-: | :-: | :-: | :-- | :-- | :-- |")
    REG_EN = {"흉벽 전외측": "anterolateral chest wall", "위팔 앞": "anterior arm", "팔오금": "cubital fossa", "아래팔 앞": "anterior forearm",
              "손목 노쪽": "radial wrist", "손가락": "digit", "손": "hand", "손목 자쪽": "ulnar wrist", "흉벽 외측": "lateral chest wall",
              "흉벽 앞": "anterior chest wall", "흉벽 앞(하부)": "anterior chest wall (lower)", "흉벽 앞(흉골 옆)": "parasternal chest wall",
              "앞 정중(명치)": "anterior midline (epigastric)", "앞 정중(흉골)": "anterior midline (sternum)", "목 앞(흉골위패임)": "anterior neck (suprasternal notch)",
              "목 앞": "anterior neck", "빗장위오목": "supraclavicular fossa", "등(흉추 옆)": "back (paravertebral)", "등 정중(C7)": "back midline (C7)",
              "어깨 위": "top of shoulder", "발목 안쪽": "medial ankle", "발등": "dorsum of foot"}
    out = []
    for r in RANK:
        c = r["code"]
        nm = s2t(IND[c]["name"])
        name = f"{NAMEKR[c]} {nm}" if lang == "ko" else f"{PIN[c]} ({nm})"
        reg = r["region"] if lang == "ko" else REG_EN.get(r["region"], r["region"])
        segs = r["segments"].replace(",", ", ") + (f" + {r['cranial']}" if r["cranial"] else "")
        out.append(f"| {r['rank_LU9']} | {c} | {name} | {TIERK[r['tier']] if lang == 'ko' else r['tier']} | {r['sim_LU9']} | {r['sim_LU9_eq']} | {reg} | {segs or '—'} | {r['nearest3']} |")
    return hdr + "\n" + "\n".join(out)


def la_table(lang):
    hdr = ("| 코드 | DB 연결(active) | 심장 관련 | 호흡 관련 |\n| :-- | :-: | :-: | :-: |" if lang == "ko" else
           "| Code | Linked papers (active) | Cardiac | Respiratory |\n| :-- | :-: | :-: | :-: |")
    rows = [f"| {c} | {LA[c]['n_active']} | {LA[c]['n_cardiac']} | {LA[c]['n_resp']} |" for c in codes if int(LA[c]["n_cardiac"]) + int(LA[c]["n_resp"]) > 0]
    zero = [c for c in codes if int(LA[c]["n_cardiac"]) + int(LA[c]["n_resp"]) == 0]
    tail = (f"\n\n심장·호흡 관련 연결 논문이 0편인 혈({len(zero)}혈): {', '.join(zero)}" if lang == "ko" else
            f"\n\nPoints with no linked cardiac or respiratory paper ({len(zero)}): {', '.join(zero)}")
    return hdr + "\n" + "\n".join(rows) + tail


def seg_table(lang):
    hdr = ("| 소분류 | 혈 수 | 구성혈 | T1–T5 포함 | C8–T1 포함 | C3–C4 포함 | 미주신경 | 군집 내 평균 유사도 |\n| :-- | :-: | :-- | :-: | :-: | :-: | :-: | :-: |"
           if lang == "ko" else
           "| Sub-group | n | Members | Includes T1–T5 | Includes C8–T1 | Includes C3–C4 | Vagus | Mean within-group similarity |\n| :-- | :-: | :-- | :-: | :-: | :-: | :-: | :-: |")
    return hdr + "\n" + "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in SEG)


for lang in ("ko", "en"):
    txt = "\n\n<!--TIER-->\n" + tier_table(lang) + "\n\n<!--RANK-->\n" + rank_table(lang) + "\n\n<!--LA-->\n" + la_table(lang) + "\n\n<!--SEG-->\n" + seg_table(lang) + "\n"
    (HERE / f"frag_{lang}.md").write_text(txt, encoding="utf-8")
print("ok")

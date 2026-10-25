# -*- coding: utf-8 -*-
"""[경혈해부] 『동의보감』 두통 鍼灸法 20혈 — FMA 해부 유사도·층위·삼차-경수 복합체(TCC) 수렴 분석 (Rank 3·5·6).

입력: headache_points.json(단독 주치 층), fma/<코드>.json(fma_query.py profile --json; GV29 = B1 수작업, EX-HN5 = GB01 대리)
출력: hd_clusters.json, hd_similarity.csv, hd_points.csv
"""
import csv
import json
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import cophenet, fcluster, linkage
from scipy.spatial.distance import squareform

HERE = Path(__file__).resolve().parent
OK_MATCH = ("exact", "exact+muscle", "exact+nerve", "exact-muscle", "exact(set)", "exact+region", "parent(branch_of)")
GENERIC = {"Thoracic nerve", "Cervical nerve", "Lumbar nerve", "Sacral nerve", "Intercostal nerve", "None", ""}

# ---- 『동의보감』 外形篇 頭 1.33 鍼灸法 (동의보감_030_外形篇一_頭.md L557·L563) ----
RX = [
    {"id": "R1", "type": "偏正頭痛", "method": "取(鍼)", "points": ["TE23", "GB20", "LI4", "CV12", "ST41", "ST36"], "tag": "綱目",
     "trace": "《针灸集成》 偏正头风：中脘、风池、三里、合谷、丝竹空、解溪 — 证治通鉴_16 L746"},
    {"id": "R2", "type": "正頭痛", "method": "取(鍼)", "points": ["GV20", "GV23", "GV24", "EX-HN5", "LI4"], "tag": "綱目",
     "trace": "《针灸集成》 正头风大痛及脑痛：神庭、合谷、太阳、上星、百会 — 证治通鉴_16 L734"},
    {"id": "R3", "type": "腎厥頭痛", "method": "灸 百壯", "points": ["CV4"], "tag": "資生",
     "trace": "《普济本事方》 肾厥…更灸关元穴百壮 — 证治通鉴_16 L618"},
    {"id": "R4", "type": "厥逆頭痛 齒亦痛", "method": "灸 七壯", "points": ["GB7"], "tag": "資生",
     "trace": "3대 원전 미검출(《资生经》 원서 미대조)"},
    {"id": "R5", "type": "痰厥頭痛", "method": "取(鍼)", "points": ["ST40"], "tag": "綱目",
     "trace": "《针经摘英集》 治风痰头痛，刺足阳明经丰隆 — 证治通鉴_16 L658"},
    {"id": "R6", "type": "頭風頭痛", "method": "鍼 百會 / 灸 顖會·前頂·上星·百會", "points": ["GV20", "GV22", "GV21", "GV23"], "tag": "丹心",
     "trace": "《丹溪心法·头风》 宜灸囟会、百会、前顶、上星 — 证治通鉴_16 L718"},
    {"id": "R7", "type": "腦痛·腦旋·腦瀉·腦熱·腦冷", "method": "灸", "points": ["GV22"], "tag": "資生",
     "trace": "《针灸资生经·脑痛·脑风》 凡脑痛、脑旋、脑泻先宜灸囟会 — 证治通鉴_16 L632"},
    {"id": "R8", "type": "眉稜骨痛", "method": "取(鍼)", "points": ["BL2", "LI4", "GV24", "ST8", "ST41"], "tag": "綱目",
     "trace": "《医学纲目·头风痛》 眉攒内痛：解溪 / 眉间痛：攒竹·头维 / 眉棱骨痛：攒竹·合谷·神庭 — 证治通鉴_16 L794–796"},
    {"id": "R9", "type": "醉後頭痛", "method": "取(鍼)", "points": ["GV29", "BL2", "ST36", "BL12", "CV17"], "tag": "綱目",
     "trace": "《针灸集成》 醉头风痛：中脘、风门、三里、印堂、攒竹、胆中 — 证治通鉴_14 L1265 (동의보감은 中脘 누락, 胆中→膻中)"},
]
NAMES = {"GV20": ("百會", "백회", "Baihui"), "GV23": ("上星", "상성", "Shangxing"), "GV24": ("神庭", "신정", "Shenting"),
         "GV22": ("顖會", "신회", "Xinhui"), "GV21": ("前頂", "전정", "Qianding"), "GV29": ("印堂", "인당", "Yintang"),
         "EX-HN5": ("太陽", "태양", "Taiyang"), "TE23": ("絲竹空", "사죽공", "Sizhukong"), "GB20": ("風池", "풍지", "Fengchi"),
         "GB7": ("曲鬢", "곡빈", "Qubin"), "BL2": ("攢竹", "찬죽", "Cuanzhu"), "ST8": ("頭維", "두유", "Touwei"),
         "BL12": ("風門", "풍문", "Fengmen"), "LI4": ("合谷", "합곡", "Hegu"), "ST41": ("解谿", "해계", "Jiexi"),
         "ST36": ("足三里", "족삼리", "Zusanli"), "ST40": ("豊隆", "풍륭", "Fenglong"), "CV12": ("中脘", "중완", "Zhongwan"),
         "CV17": ("膻中", "전중", "Danzhong"), "CV4": ("關元", "관원", "Guanyuan")}
FMA_FILE = {"EX-HN5": "GB01"}
REGION = {"GV20": "정수리", "GV21": "정수리 앞", "GV22": "앞정수리(숫구멍)", "GV23": "앞머리 정중", "GV24": "앞머리 발제",
          "GV29": "미간", "BL2": "눈썹 안쪽", "ST8": "이마 모서리", "TE23": "눈썹 바깥", "EX-HN5": "관자", "GB7": "귀 앞 관자",
          "GB20": "뒤통수밑", "BL12": "등 위(T2)", "LI4": "손등", "ST41": "발목 앞", "ST36": "종아리 앞", "ST40": "종아리 앞",
          "CV12": "윗배 정중", "CV17": "가슴 정중", "CV4": "아랫배 정중"}

ORD = {w: i + 1 for i, w in enumerate(["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
                                          "ninth", "tenth", "eleventh", "twelfth"])}
# 뇌신경 분지 + 상부 경신경 — TCC(삼차-경수 복합체: V + C1–C3, B1-02) 판정용
CN = {"Ophthalmic nerve": "V1", "Frontal nerve": "V1", "Supra-orbital nerve": "V1", "Supratrochlear nerve": "V1",
      "Infratrochlear nerve": "V1", "Maxillary nerve": "V2", "Zygomaticotemporal nerve": "V2", "Zygomatic nerve": "V2",
      "Mandibular nerve": "V3", "Auriculotemporal nerve": "V3", "Trigeminal nerve": "V",
      "Facial nerve": "VII", "Temporal branch of facial nerve": "VII", "Zygomatic branch of facial nerve": "VII",
      "Posterior auricular nerve": "VII", "Spinal accessory nerve": "XI"}
B1_SEG = {"Suboccipital nerve": "C1", "Greater occipital nerve": "C2", "Lesser occipital nerve": "C2-C3",
          "Great auricular nerve": "C2-C3", "Transverse cervical nerve": "C2-C3", "Cervical nerve plexus": "C1-C4",
          "Dorsal scapular nerve": "C5", "Sciatic nerve": "L4-S3", "Common fibular nerve": "L4-S2", "Deep fibular nerve": "L4-S1",
          "Medial terminal branch of deep fibular nerve": "L5-S1", "Superficial fibular nerve": "L5-S1",
          "Medial dorsal cutaneous nerve": "L5-S1", "Lateral sural cutaneous nerve": "L5-S2",
          "Set of medial crural cutaneous branches of saphenous nerve": "L3-L4", "Sacral nerve plexus": "L4-S4",
          "Iliohypogastric nerve": "L1", "Hypogastric branch of iliohypogastric nerve": "L1", "Subcostal nerve": "T12",
          "Deep branch of ulnar nerve": "C8-T1", "Peripheral segment of ulnar nerve": "C8-T1",
          "Set of dorsal digital branches of radial nerve": "C6-C7"}
SEG_ORDER = [f"C{i}" for i in range(1, 9)] + [f"T{i}" for i in range(1, 13)] + [f"L{i}" for i in range(1, 6)] + [f"S{i}" for i in range(1, 6)]
CN_ORDER = ["V1", "V2", "V3", "V", "VII", "XI"]


def seg_range(s):
    if "-" not in s:
        return [s]
    a, b = s.split("-")
    return SEG_ORDER[SEG_ORDER.index(a):SEG_ORDER.index(b) + 1]


def nerve_segments(label):
    if label in B1_SEG:
        return seg_range(B1_SEG[label]), "B1"
    m = re.search(r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) "
                  r"(intercostal|cervical|thoracic|lumbar|sacral)", label.lower())
    if m:
        pre = {"intercostal": "T", "cervical": "C", "thoracic": "T", "lumbar": "L", "sacral": "S"}[m.group(2)]
        return [f"{pre}{ORD[m.group(1)]}"], "FMA 라벨"
    if label.lower().startswith("anterior cutaneous branch of subcostal"):
        return ["T12"], "FMA 라벨"
    return [], ""


def features(code):
    j = json.loads((HERE / "fma" / f"{FMA_FILE.get(code, re.sub(r'([A-Z]+)(\d+)$', lambda m: f'{m.group(1)}{int(m.group(2)):02d}', code))}.json").read_text(encoding="utf-8"))
    S, N, G, R, cn, multiseg = set(), set(), {}, set(), set(), []
    for s in j["structures"]:
        if not any(m in OK_MATCH for m in s["match"]):
            continue
        S.add(s["fma_id"])
        nerves = [s["fma_label"]] if s["category"] == "신경" else []
        for v in (s.get("nerve_trunks") or {}).values():
            nerves += [x[1] for x in v]
        for x in s.get("branch_chain") or []:
            if "nerve" in str(x[1]).lower() or "plexus" in str(x[1]).lower():
                nerves.append(x[1])
        nerves = [n for n in nerves if n and n not in GENERIC]
        s_seg = {}
        for n in nerves:
            segs, src = nerve_segments(n)
            for g in segs:
                s_seg.setdefault(g, set()).add(src)
        for g in list((s.get("segments") or {}).get("direct", {})) + list((s.get("segments") or {}).get("inferred_from_nerve_chain", [])):
            s_seg.setdefault(g, set()).add("FMA")
        core = {g for g, src in s_seg.items() if src & {"FMA", "FMA 라벨"}}
        if s["category"] == "근육" and len(core) > 4:
            multiseg.append(s["fma_label"])
            continue
        for n in nerves:
            N.add(n)
            if n in CN:
                cn.add(CN[n])
        for g, src in s_seg.items():
            G.setdefault(g, set()).update(src)
        for x in (s.get("relations") or {}).get("contained_in", []):
            R.add(x[1])
        for x in s.get("is_a") or []:
            R.add(x[1])
    if "V" in cn and cn & {"V1", "V2", "V3"}:
        cn.discard("V")
    R.add("REGION:" + REGION[code])
    G_all = set(G) | cn  # 뇌신경 분지를 분절과 같은 축에 둔다
    return {"S": S, "N": N, "G": G_all, "G_src": {g: sorted(v) for g, v in G.items()}, "R": R, "cranial": sorted(cn, key=CN_ORDER.index),
            "multiseg": multiseg, "n_struct": len(S),
            "tcc": sorted((cn & {"V1", "V2", "V3", "V"}) | (set(G) & {"C1", "C2", "C3"}), key=lambda x: (CN_ORDER + SEG_ORDER).index(x))}


def jac(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def simmat(codes, F, w):
    n = len(codes)
    M = np.eye(n)
    for i, k in combinations(range(n), 2):
        M[i, k] = M[k, i] = sum(w[key] * jac(F[codes[i]][key], F[codes[k]][key]) for key in w)
    return M


def silhouette(D, lab):
    sc = []
    for i in range(len(lab)):
        same = [D[i, k] for k in range(len(lab)) if lab[k] == lab[i] and k != i]
        if not same:
            sc.append(0.0)
            continue
        a = np.mean(same)
        b = min(np.mean([D[i, k] for k in range(len(lab)) if lab[k] == c]) for c in set(lab) if c != lab[i])
        sc.append((b - a) / max(a, b))
    return float(np.mean(sc))


def ari(l1, l2):
    pairs = list(combinations(range(len(l1)), 2))
    a = sum(1 for i, k in pairs if l1[i] == l1[k] and l2[i] == l2[k])
    b = sum(1 for i, k in pairs if l1[i] == l1[k])
    c = sum(1 for i, k in pairs if l2[i] == l2[k])
    exp, mx = b * c / len(pairs), (b + c) / 2
    return (a - exp) / (mx - exp) if mx != exp else 1.0


def main():
    HP = json.loads((HERE / "headache_points.json").read_text(encoding="utf-8"))
    codes = list(NAMES)
    F = {c: features(c) for c in codes}
    W = {"N": 0.35, "G": 0.30, "S": 0.20, "R": 0.15}
    W_EQ = {k: 0.25 for k in W}
    M, M_eq = simmat(codes, F, W), simmat(codes, F, W_EQ)
    Z = linkage(squareform(1 - M, checks=False), method="average")
    coph, _ = cophenet(Z, squareform(1 - M, checks=False))
    best = max(range(3, 9), key=lambda k: silhouette(1 - M, fcluster(Z, k, "maxclust")))
    lab = fcluster(Z, best, "maxclust")
    lab_eq = fcluster(linkage(squareform(1 - M_eq, checks=False), method="average"), best, "maxclust")
    stab = ari(list(lab), list(lab_eq))

    # 처방(배오)별 해부 응집도: 구성혈 쌍 평균 유사도, TCC 포함 비율
    rx_rows = []
    for r in RX:
        idx = [codes.index(p) for p in r["points"]]
        coh = float(np.mean([M[a, b] for a, b in combinations(idx, 2)])) if len(idx) > 1 else float("nan")
        tcc = sum(1 for p in r["points"] if F[p]["tcc"])
        tier1 = sum(1 for p in r["points"] if HP[p]["tier"] == "I")
        rx_rows.append({**r, "cohesion": None if np.isnan(coh) else round(coh, 3), "tcc_n": tcc, "tier1_n": tier1, "n": len(idx)})

    pts = []
    for i, c in enumerate(codes):
        top = sorted(((M[i, k], codes[k]) for k in range(len(codes)) if k != i), reverse=True)[:3]
        used = [r["id"] for r in RX if c in r["points"]]
        pts.append({"code": c, "hanja": NAMES[c][0], "kr": NAMES[c][1], "pinyin": NAMES[c][2], "tier": HP[c]["tier"],
                    "han": "·".join(g[:2] for g in HP[c]["groups_han"]), "later": "·".join(g[:2] for g in HP[c]["groups_later"]),
                    "cluster": int(lab[i]), "region": REGION[c], "cranial": ",".join(F[c]["cranial"]),
                    "segments": ",".join(g for g in SEG_ORDER if g in F[c]["G"]), "tcc": ",".join(F[c]["tcc"]),
                    "n_rx": len(used), "rx": ",".join(used), "n_struct": F[c]["n_struct"],
                    "nearest3": "; ".join(f"{x}({y:.2f})" for y, x in top)})
    out = {"codes": codes, "weights": W, "k": best, "cophenetic": round(float(coph), 3), "ari": round(stab, 3),
           "linkage": Z.tolist(), "labels": [int(x) for x in lab], "rx": rx_rows,
           "features": {c: {"N": sorted(F[c]["N"]), "G": [g for g in SEG_ORDER if g in F[c]["G"]], "G_src": F[c]["G_src"],
                            "cranial": F[c]["cranial"], "tcc": F[c]["tcc"], "S": sorted(F[c]["S"]), "multiseg": F[c]["multiseg"]} for c in codes},
           "tier": {c: HP[c]["tier"] for c in codes}}
    (HERE / "hd_clusters.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    np.savetxt(HERE / "hd_similarity.csv", M, delimiter=",", fmt="%.3f", header=",".join(codes), comments="")
    with open(HERE / "hd_points.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pts[0]))
        w.writeheader()
        w.writerows(pts)
    print(f"n={len(codes)} k={best} cophenetic={coph:.3f} ARI={stab:.3f}")
    for k in sorted(set(lab)):
        mem = [codes[i] for i in range(len(codes)) if lab[i] == k]
        print(k, [f"{c}{NAMES[c][0]}" for c in mem])
    for r in rx_rows:
        print(r["id"], r["type"], r["n"], "응집", r["cohesion"], "TCC", r["tcc_n"], "1층", r["tier1_n"])
    for p in pts:
        print(p["code"], p["hanja"], p["tier"], p["cluster"], "CN", p["cranial"], "| TCC", p["tcc"], "| seg", p["segments"], "|", p["nearest3"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

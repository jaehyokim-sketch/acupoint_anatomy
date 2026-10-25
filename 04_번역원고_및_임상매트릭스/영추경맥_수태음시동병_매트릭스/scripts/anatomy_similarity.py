# -*- coding: utf-8 -*-
"""[경혈해부] Rank 5·6: 수태음 시동병 대응 경혈의 FMA 해부 유사도 → 계층 층위(UPGMA)·순위.

입력: candidates.csv(추출), fma/<코드>.json(fma_query.py profile --json)
출력: similarity.csv, ranking.csv, clusters.json, segments.csv
특징:  S 구조(FMA ID) · N 신경 영역(구조 신경 + 지배신경 + 줄기 사슬) · G 척수 분절(FMA + B1 보완) · R 부위·구획
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import cophenet, fcluster, linkage
from scipy.spatial.distance import squareform

HERE = Path(__file__).resolve().parent
OK_MATCH = ("exact", "exact+muscle", "exact+nerve", "exact-muscle", "exact(set)", "exact+region", "parent(branch_of)")
GENERIC = {"Thoracic nerve", "Cervical nerve", "Lumbar nerve", "Sacral nerve", "Intercostal nerve", "None", ""}

# ---- 판정 결과(추출 스크립트 + 수작업 판정, 보고서 4·5절) ----
TIER = {}   # 코드 → (층, 근거 요약)
EXCLUDE = {"GB10": "《外台》 단계 天容 주치 착입(《通考》 浮白 按) — 오록", "GB38": "缺盆中痛은 《聚英》 母子補瀉 경맥병후 전재와 이를 이은 교재 — 순환 근거"}
ADD = {"LU3": ("II", "是動病 '大輸' 처방(經渠+天府, 標本脈)의 구성혈 — 배오 층")}

ORD = {w: i + 1 for i, w in enumerate(["first", "second", "third", "fourth", "fifth", "sixth", "seventh",
                                          "eighth", "ninth", "tenth", "eleventh", "twelfth"])}
# B1 규범 해부 분절 보완(B1-01 Gray's 42e, B1-03 Moore 8e) — FMA 분절 미기재 신경
B1_SEG = {
    "Medial pectoral nerve": "C8-T1", "Lateral pectoral nerve": "C5-C7", "Long thoracic nerve": "C5-C7",
    "Dorsal scapular nerve": "C5", "Suprascapular nerve": "C5-C6", "Thoracodorsal nerve": "C6-C8",
    "Subclavian nerve": "C5-C6", "Axillary nerve": "C5-C6", "Anterior branch of axillary nerve": "C5-C6",
    "Posterior branch of axillary nerve": "C5-C6", "Musculocutaneous nerve": "C5-C7",
    "Peripheral segment of musculocutaneous nerve": "C5-C7", "Lateral cutaneous nerve of forearm": "C5-C6",
    "Median nerve": "C6-T1", "Peripheral segment of median nerve": "C6-T1", "Anterior interosseous nerve": "C7-C8",
    "Thenar muscular branch of median nerve": "C8-T1", "Radial nerve": "C5-T1", "Peripheral segment of radial nerve": "C5-T1",
    "Posterior interosseous nerve": "C7-C8", "Superficial branch of radial nerve": "C6-C7",
    "Set of dorsal digital branches of radial nerve": "C6-C7", "Posterior cutaneous nerve of forearm": "C5-C8",
    "Inferior lateral cutaneous nerve of arm": "C5-C6", "Ulnar nerve": "C8-T1", "Peripheral segment of ulnar nerve": "C8-T1",
    "Deep branch of ulnar nerve": "C8-T1", "Palmar branch of ulnar nerve": "C8", "Medial cutaneous nerve of forearm": "C8-T1",
    "Brachial nerve plexus": "C5-T1", "Cervical nerve plexus": "C1-C4", "Ansa cervicalis": "C1-C3",
    "Supraclavicular nerve": "C3-C4", "Peripheral segment of supraclavicular nerve": "C3-C4",
    "Medial supraclavicular nerve": "C3-C4", "Intermediate supraclavicular nerve": "C3-C4",
    "Transverse cervical nerve": "C2-C3", "Greater occipital nerve": "C2", "Descending branch of hypoglossal nerve": "C1",
    "Sciatic nerve": "L4-S3", "Common fibular nerve": "L4-S2", "Deep fibular nerve": "L4-S1",
    "Medial terminal branch of deep fibular nerve": "L5-S1", "Superficial fibular nerve": "L5-S1",
    "Intermediate dorsal cutaneous nerve": "L5-S1", "Tibial nerve": "L4-S3", "Lateral plantar nerve": "S1-S2",
    "Superficial branch of lateral plantar nerve": "S1-S2", "Medial calcaneal branch of tibial nerve": "S1-S2",
    "Lateral sural cutaneous nerve": "L5-S2", "Saphenous nerve": "L3-L4",
    "Set of medial crural cutaneous branches of saphenous nerve": "L3-L4", "Femoral nerve": "L2-L4",
    "Sacral nerve plexus": "L4-S4", "Iliohypogastric nerve": "L1", "Ilioinguinal nerve": "L1", "Subcostal nerve": "T12",
}
CRANIAL = {"Spinal accessory nerve": "CN XI", "External branch of accessory nerve": "CN XI", "Facial nerve": "CN VII",
           "Cervical branch of facial nerve": "CN VII", "Hypoglossal nerve": "CN XII", "Vagus nerve": "CN X"}
SEG_ORDER = [f"C{i}" for i in range(1, 9)] + [f"T{i}" for i in range(1, 13)] + [f"L{i}" for i in range(1, 6)] + [f"S{i}" for i in range(1, 6)]

# 체표 부위(B1-05 WHO 표준 정위 기준, 거친 구분)
REGION = {
    "LU1": "흉벽 전외측", "LU3": "위팔 앞", "LU4": "위팔 앞", "LU5": "팔오금", "LU6": "아래팔 앞", "LU7": "손목 노쪽",
    "LU8": "손목 노쪽", "LU9": "손목 노쪽", "LU11": "손가락", "LI1": "손가락", "LI3": "손", "SI2": "손가락",
    "HT6": "손목 자쪽", "HT7": "손목 자쪽", "PC1": "흉벽 전외측", "SP18": "흉벽 전외측", "GB23": "흉벽 외측",
    "ST16": "흉벽 앞", "ST18": "흉벽 앞", "LR14": "흉벽 앞(하부)", "KI22": "흉벽 앞(흉골 옆)", "KI23": "흉벽 앞(흉골 옆)",
    "KI24": "흉벽 앞(흉골 옆)", "KI25": "흉벽 앞(흉골 옆)", "KI27": "흉벽 앞(흉골 옆)", "CV15": "앞 정중(명치)",
    "CV18": "앞 정중(흉골)", "CV21": "앞 정중(흉골)", "CV22": "목 앞(흉골위패임)", "ST9": "목 앞", "ST12": "빗장위오목",
    "BL13": "등(흉추 옆)", "BL14": "등(흉추 옆)", "BL17": "등(흉추 옆)", "GV14": "등 정중(C7)", "GB21": "어깨 위",
    "KI4": "발목 안쪽", "GB41": "발등",
}


def pad(c):
    m = re.match(r"([A-Z]+)(\d+)", c)
    return f"{m.group(1)}{int(m.group(2)):02d}"


def seg_range(s):
    if "-" not in s:
        return [s]
    a, b = s.split("-")
    i, j = SEG_ORDER.index(a), SEG_ORDER.index(b)
    return SEG_ORDER[i:j + 1]


def nerve_segments(label):
    """신경 라벨 → 분절(규칙: 늑간·후지·전지 서수 → 해당 분절, 그 외 B1 표)."""
    if label in B1_SEG:
        return seg_range(B1_SEG[label]), "B1"
    m = re.search(r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) "
                  r"(intercostal|cervical|thoracic|lumbar|sacral)", label.lower())
    if m:
        n, kind = ORD[m.group(1)], m.group(2)
        pre = {"intercostal": "T", "cervical": "C", "thoracic": "T", "lumbar": "L", "sacral": "S"}[kind]
        return [f"{pre}{n}"], "FMA 라벨"
    return [], ""


def features(code):
    j = json.loads((HERE / "fma" / f"{pad(code)}.json").read_text(encoding="utf-8"))
    S, N, G, R, cranial, multiseg = set(), set(), {}, set(), set(), []
    for s in j["structures"]:
        if not any(m in OK_MATCH for m in s["match"]):
            continue
        S.add(s["fma_id"])
        nerves = []
        if s["category"] == "신경":
            nerves.append(s["fma_label"])
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
        # 다분절 근육(척추세움근 등, 5개 분절 이상)은 분절·신경 특징에서 제외 — 래퍼 5-1절 acupoints_by_segment 규칙
        core = {g for g, src in s_seg.items() if src & {"FMA", "FMA 라벨"}}  # B1 줄기 범위(예: 노신경 C5–T1)는 판정에서 뺌
        if s["category"] == "근육" and len(core) > 4:
            multiseg.append(s["fma_label"])
            continue
        for n in nerves:
            N.add(n)
            if n in CRANIAL:
                cranial.add(CRANIAL[n])
        for g, src in s_seg.items():
            G.setdefault(g, set()).update(src)
        for k in ("contained_in",):
            for x in (s.get("relations") or {}).get(k, []):
                R.add(x[1])
        for x in s.get("is_a") or []:
            R.add(x[1])
    R.add("REGION:" + REGION.get(code, "?"))
    return {"S": S, "N": N, "G": set(G), "G_src": {g: sorted(v) for g, v in G.items()}, "R": R,
            "cranial": sorted(cranial), "n_struct": len(S), "multiseg": multiseg}


def jac(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def simmat(codes, F, w):
    n = len(codes)
    M = np.eye(n)
    for i in range(n):
        for k in range(i + 1, n):
            s = sum(w[key] * jac(F[codes[i]][key], F[codes[k]][key]) for key in w)
            M[i, k] = M[k, i] = s
    return M


def silhouette(D, lab):
    n = len(lab)
    sc = []
    for i in range(n):
        same = [D[i, k] for k in range(n) if lab[k] == lab[i] and k != i]
        if not same:
            sc.append(0.0)
            continue
        a = np.mean(same)
        b = min(np.mean([D[i, k] for k in range(n) if lab[k] == c]) for c in set(lab) if c != lab[i])
        sc.append((b - a) / max(a, b))
    return float(np.mean(sc))


def ari(l1, l2):
    from itertools import combinations
    pairs = list(combinations(range(len(l1)), 2))
    a = sum(1 for i, k in pairs if l1[i] == l1[k] and l2[i] == l2[k])
    b = sum(1 for i, k in pairs if l1[i] == l1[k])
    c = sum(1 for i, k in pairs if l2[i] == l2[k])
    n = len(pairs)
    exp = b * c / n
    mx = (b + c) / 2
    return (a - exp) / (mx - exp) if mx != exp else 1.0


def main():
    cand = list(csv.DictReader(open(HERE / "candidates.csv", encoding="utf-8-sig")))
    info = {}
    for r in cand:
        if r["code"] in EXCLUDE:
            continue
        nh = int(r["n_groups_han"])
        spec_h = r["specific_han"]
        tier = "I" if (nh >= 2 and spec_h) else ("II" if nh >= 1 else "III")
        info[r["code"]] = {**r, "tier": tier}
    for c, (t, why) in ADD.items():
        info[c] = {"code": c, "name": "天府", "pinyin": "Tiānfǔ", "tier": t, "groups_han": "B_喘咳", "groups_all": "B_喘咳",
                   "n_groups_han": "1", "n_groups_all": "1", "specific_han": "", "note": why}
    info["LU8"]["note"] = "한대 단독: 咳上氣喘·心痛欲嘔 / 是動病 핵심(胸中彭彭·交兩手而瞀)은 經渠+天府 '大輸' 처방 구절"
    info["LU8"]["tier"] = "II"
    codes = sorted(info, key=lambda c: ({"I": 0, "II": 1, "III": 2}[info[c]["tier"]], c))
    F = {c: features(c) for c in codes}

    W = {"N": 0.35, "G": 0.30, "S": 0.20, "R": 0.15}
    W_EQ = {k: 0.25 for k in W}
    M = simmat(codes, F, W)
    M_eq = simmat(codes, F, W_EQ)
    D = 1 - M
    Z = linkage(squareform(D, checks=False), method="average")
    coph, _ = cophenet(Z, squareform(D, checks=False))
    best = max(range(3, 9), key=lambda k: silhouette(D, fcluster(Z, k, "maxclust")))
    lab = fcluster(Z, best, "maxclust")
    Z_eq = linkage(squareform(1 - M_eq, checks=False), method="average")
    lab_eq = fcluster(Z_eq, best, "maxclust")
    stab = ari(list(lab), list(lab_eq))

    # 순위: ① 太淵(LU9, 4개 증상군 모두 한대 단독) 기준 유사도 ② 1층(Tier I) 중심성
    i9 = codes.index("LU9")
    t1 = [codes.index(c) for c in codes if info[c]["tier"] == "I" and c != "LU9"]
    rank = []
    for i, c in enumerate(codes):
        cen = float(np.mean([M[i, k] for k in t1 if k != i])) if t1 else 0
        top = sorted(((M[i, k], codes[k]) for k in range(len(codes)) if k != i), reverse=True)[:3]
        rank.append({"code": c, "name": info[c]["name"], "tier": info[c]["tier"], "cluster": int(lab[i]),
                     "sim_LU9": round(float(M[i, i9]), 3), "sim_LU9_eq": round(float(M_eq[i, i9]), 3),
                     "centrality_tierI": round(cen, 3), "region": REGION.get(c, ""),
                     "segments": ",".join(g for g in SEG_ORDER if g in F[c]["G"]),
                     "cranial": ",".join(F[c]["cranial"]), "n_struct": F[c]["n_struct"],
                     "nearest3": "; ".join(f"{x}({y:.2f})" for y, x in top)})
    rank.sort(key=lambda r: -r["sim_LU9"])
    for k, r in enumerate(rank, 1):
        r["rank_LU9"] = k

    # 군집 요약: 군집 내 공통 신경·분절
    clusters = {}
    for cl in sorted(set(lab)):
        mem = [codes[i] for i in range(len(codes)) if lab[i] == cl]
        idx = [codes.index(c) for c in mem]
        within = float(np.mean([M[a, b] for a in idx for b in idx if a < b])) if len(idx) > 1 else 1.0
        from collections import Counter
        nc = Counter(n for c in mem for n in F[c]["N"])
        gc = Counter(g for c in mem for g in F[c]["G"])
        clusters[int(cl)] = {"members": mem, "mean_within_sim": round(within, 3),
                             "shared_nerves": [n for n, v in nc.most_common(8) if v >= max(2, len(mem) // 2)],
                             "segments_majority": [g for g in SEG_ORDER if gc.get(g, 0) >= max(1, (len(mem) + 1) // 2)],
                             "tiers": dict(Counter(info[c]["tier"] for c in mem))}
    out = {"codes": codes, "weights": W, "weights_eq": W_EQ, "k": best, "cophenetic": round(float(coph), 3),
           "ari_weight_sensitivity": round(stab, 3), "linkage": Z.tolist(), "labels": [int(x) for x in lab],
           "labels_eq": [int(x) for x in lab_eq], "clusters": clusters,
           "info": {c: {k: v for k, v in info[c].items() if k in ("name", "pinyin", "tier", "groups_han", "groups_all", "note")} for c in codes},
           "features": {c: {"N": sorted(F[c]["N"]), "G": [g for g in SEG_ORDER if g in F[c]["G"]], "G_src": F[c]["G_src"],
                            "cranial": F[c]["cranial"], "S": sorted(F[c]["S"]), "region": REGION.get(c), "multiseg_excluded": F[c]["multiseg"]} for c in codes},
           "excluded": EXCLUDE}
    (HERE / "clusters.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    np.savetxt(HERE / "similarity.csv", M, delimiter=",", fmt="%.3f", header=",".join(codes), comments="")
    with open(HERE / "ranking.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rank[0]))
        w.writeheader()
        w.writerows(rank)
    print(f"n={len(codes)} k={best} cophenetic={coph:.3f} ARI(가중치 vs 등가중치)={stab:.3f}")
    for cl, d in clusters.items():
        print(cl, d["mean_within_sim"], d["tiers"], d["members"], d["segments_majority"], d["shared_nerves"][:5])
    for r in rank[:15]:
        print(r["rank_LU9"], r["code"], r["name"], r["tier"], r["cluster"], r["sim_LU9"], r["sim_LU9_eq"], r["centrality_tierI"], r["nearest3"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

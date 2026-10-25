# -*- coding: utf-8 -*-
"""[경혈해부] 오십견(누견풍) 15혈 — FMA 해부 분석 (Rank 5·6, FMA 5-1절).

① FMA 프로파일 특징 → 가중 Jaccard 유사도 → UPGMA 층위(등가중치 민감도)
② 어깨관절 신경지배 정합(Hilton 법칙: 어깨위·겨드랑·가쪽가슴근신경, C5–C6; B1-01·B1-03)
③ 운동 방향별 기능 해부 매트릭스: 각 혈의 FMA 근육이 해당 운동의 주동근(agonist)인지 제한 구조(restraint)인지 (B1-03 규범 운동학)
④ BodyParts3D 메쉬 측정: 회전근개 부피, 기흉 위험 혈 심부 구조 ↔ 오른폐 최소 거리 (B1 보조)

출력: fs_results.json, fs_similarity.csv
"""
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
sys.path.insert(0, str(HERE.parent / "lu_sd"))
from anatomy_similarity import B1_SEG as UL_B1, nerve_segments as ul_nerve_segments, SEG_ORDER  # noqa: E402

OK = ("exact", "exact+muscle", "exact+nerve", "exact-muscle", "exact(set)", "exact+region", "parent(branch_of)")
GENERIC = {"Thoracic nerve", "Cervical nerve", "Lumbar nerve", "Sacral nerve", "Intercostal nerve", "None", ""}
POINTS = {  # 보고서 4절 15혈
    "LI15": ("肩髃", "견우", "Jianyu"), "TE14": ("肩髎", "견료", "Jianliao"), "EX-UE": ("肩前", "견전(견내릉)", "Jianqian"),
    "SI9": ("肩貞", "견정", "Jianzhen"), "SI10": ("臑俞", "노수", "Naoshu"), "SI11": ("天宗", "천종", "Tianzong"),
    "LI16": ("巨骨", "거골", "Jugu"), "LU2": ("雲門", "운문", "Yunmen"), "GB21": ("肩井", "견정", "Jianjing"),
    "ST38": ("條口", "조구", "Tiaokou"), "BL57": ("承山", "승산", "Chengshan"), "TE3": ("中渚", "중저", "Zhongzhu"),
    "LI11": ("曲池", "곡지", "Quchi"), "LI4": ("合谷", "합곡", "Hegu"), "GB34": ("陽陵泉", "양릉천", "Yanglingquan")}
REGION = {"LI15": "어깨 가쪽(봉우리 앞)", "TE14": "어깨 가쪽(봉우리 뒤)", "EX-UE": "어깨 앞(겨드랑 앞주름 위)", "SI9": "어깨 뒤(겨드랑 뒤주름 위)",
          "SI10": "어깨 뒤(어깨뼈가시 아래)", "SI11": "어깨뼈 가시아래오목", "LI16": "어깨 위(빗장뼈 가쪽끝–가시 사이)", "LU2": "빗장아래 오목",
          "GB21": "어깨 위(목–봉우리 중간)", "ST38": "종아리 앞", "BL57": "종아리 뒤", "TE3": "손등", "LI11": "팔꿈치 가쪽", "LI4": "손등",
          "GB34": "종아리 가쪽(종아리뼈머리)"}
LOWER_B1 = {"Sciatic nerve": "L4-S3", "Common fibular nerve": "L4-S2", "Deep fibular nerve": "L4-S1", "Superficial fibular nerve": "L5-S1",
            "Tibial nerve": "L4-S3", "Lateral sural cutaneous nerve": "L5-S2", "Medial sural cutaneous nerve": "S1-S2",
            "Posterior femoral cutaneous nerve": "S1-S3", "Set of medial crural cutaneous branches of saphenous nerve": "L3-L4",
            "Sacral nerve plexus": "L4-S4", "Spinal accessory nerve": "CN XI", "Lateral supraclavicular nerve": "C3-C4",
            "Inferior subscapular nerve": "C5-C6", "Set of muscular branches of axillary nerve": "C5-C6",
            "Superior lateral cutaneous nerve of arm": "C5-C6", "Deep branch of ulnar nerve": "C8-T1"}
SHOULDER_JOINT_N = {"Suprascapular nerve", "Axillary nerve", "Lateral pectoral nerve", "Set of muscular branches of axillary nerve"}

# 肩前(EX-UE) — 2대 교재 데이터셋 미수록 → B1 수작업 대응(B1-01·B1-03)
EXUE = [(32521, "Deltoid", "근육", "Axillary nerve"), (37664, "Coracobrachialis", "근육", "Musculocutaneous nerve"),
        (37682, "Short head of biceps brachii", "근육", "Musculocutaneous nerve"), (38153, "Tendon of long head of biceps brachii", "근육", None),
        (9627, "Pectoralis major", "근육", "Lateral pectoral nerve"), (22680, "Anterior circumflex humeral artery", "혈관", None),
        (13324, "Cephalic vein", "혈관", None), (37072, "Axillary nerve", "신경", None), (37064, "Musculocutaneous nerve", "신경", None),
        (65296, "Lateral pectoral nerve", "신경", None)]

# 운동 방향별 기능 해부(B1-03 Moore 8e 'Movements of glenohumeral joint'; 관절낭 제한은 B1-01 Gray's)
MOTIONS = {
    "ER 외회전": {"agonist": {32546: "Infraspinatus", 32550: "Teres minor"}, "restraint": {13413: "Subscapularis", 9627: "Pectoralis major", 13357: "Latissimus dorsi", 32549: "Teres major"},
                "capsule": "앞 관절낭·부리위팔인대·위/중간 오목위팔인대(rotator interval)"},
    "IR 내회전": {"agonist": {13413: "Subscapularis", 9627: "Pectoralis major", 13357: "Latissimus dorsi", 32549: "Teres major"}, "restraint": {32546: "Infraspinatus", 32550: "Teres minor"},
                "capsule": "뒤 관절낭"},
    "FL 굽힘(전방거상)": {"agonist": {32521: "Deltoid", 9627: "Pectoralis major", 37664: "Coracobrachialis", 37682: "Short head of biceps brachii"},
                      "restraint": {13357: "Latissimus dorsi", 32549: "Teres major", 37692: "Long head of triceps brachii"}, "capsule": "아래 관절낭(겨드랑오목)·뒤 관절낭"},
    "AB 벌림(외전)": {"agonist": {9629: "Supraspinatus", 32521: "Deltoid"}, "restraint": {9627: "Pectoralis major", 13357: "Latissimus dorsi", 32549: "Teres major"},
                   "capsule": "아래 관절낭(겨드랑오목)·아래 오목위팔인대"},
    "EX 폄(후방신전)": {"agonist": {13357: "Latissimus dorsi", 32549: "Teres major", 37692: "Long head of triceps brachii", 32521: "Deltoid"},
                    "restraint": {9627: "Pectoralis major", 37664: "Coracobrachialis", 37682: "Short head of biceps brachii"}, "capsule": "앞 관절낭·부리위팔인대"},
}
# 보고서 5절이 각 운동 제한에 배정한 혈(대조용)
REPORT_MAP = {"ER 외회전": ["SI11", "SI10", "TE14"], "IR 내회전": ["LU2", "EX-UE", "SI9"], "FL 굽힘(전방거상)": ["LI15", "LU1", "LI14"],
              "AB 벌림(외전)": ["LI15", "TE14", "LI16"], "EX 폄(후방신전)": ["SI9", "TE10", "TE4"]}


def fma_file(c):
    m = re.match(r"([A-Z]+)(\d+)$", c)
    return HERE / "fma" / f"{m.group(1)}{int(m.group(2)):02d}.json"


def seg_of(label):
    if label in LOWER_B1:
        v = LOWER_B1[label]
        if v.startswith("CN"):
            return [], ""
        a, *b = v.split("-")
        return (SEG_ORDER[SEG_ORDER.index(a):SEG_ORDER.index(b[0]) + 1] if b else [a]), "B1"
    return ul_nerve_segments(label)


def structures(c):
    if c == "EX-UE":
        out = []
        for fid, lab, cat, n in EXUE:
            out.append({"fma_id": fid, "fma_label": lab, "category": cat, "match": ["exact"], "nerve_trunks": ({"x": [[0, n]]} if n else {}),
                        "branch_chain": [], "relations": {}, "is_a": [], "segments": {"direct": {}, "inferred_from_nerve_chain": []}})
        return out
    return json.loads(fma_file(c).read_text(encoding="utf-8"))["structures"]


def features(c):
    S, N, G, R, musc, multiseg = set(), set(), {}, set(), {}, []
    for s in structures(c):
        if not any(m in OK for m in s["match"]):
            continue
        S.add(s["fma_id"])
        if s["category"] == "근육":
            musc[s["fma_id"]] = s["fma_label"]
        nerves = [s["fma_label"]] if s["category"] == "신경" else []
        for v in (s.get("nerve_trunks") or {}).values():
            nerves += [x[1] for x in v]
        for x in s.get("branch_chain") or []:
            if "nerve" in str(x[1]).lower() or "plexus" in str(x[1]).lower():
                nerves.append(x[1])
        nerves = [n for n in nerves if n and n not in GENERIC]
        s_seg = {}
        for n in nerves:
            segs, src = seg_of(n)
            for g in segs:
                s_seg.setdefault(g, set()).add(src)
        for g in list((s.get("segments") or {}).get("direct", {})) + list((s.get("segments") or {}).get("inferred_from_nerve_chain", [])):
            s_seg.setdefault(g, set()).add("FMA")
        core = {g for g, src in s_seg.items() if src & {"FMA", "FMA 라벨"}}
        if s["category"] == "근육" and len(core) > 4:
            multiseg.append(s["fma_label"])
            continue
        N.update(nerves)
        for g, src in s_seg.items():
            G.setdefault(g, set()).update(src)
        for x in (s.get("relations") or {}).get("contained_in", []):
            R.add(x[1])
        for x in s.get("is_a") or []:
            R.add(x[1])
    R.add("REGION:" + REGION[c])
    return {"S": S, "N": N, "G": set(G), "G_src": {g: sorted(v) for g, v in G.items()}, "R": R, "muscles": musc, "multiseg": multiseg,
            "shoulder_joint_nerves": sorted(N & SHOULDER_JOINT_N), "XI": "Spinal accessory nerve" in N}


def jac(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def simmat(codes, F, w):
    M = np.eye(len(codes))
    for i, k in combinations(range(len(codes)), 2):
        M[i, k] = M[k, i] = sum(w[x] * jac(F[codes[i]][x], F[codes[k]][x]) for x in w)
    return M


def ari(l1, l2):
    pr = list(combinations(range(len(l1)), 2))
    a = sum(1 for i, k in pr if l1[i] == l1[k] and l2[i] == l2[k])
    b = sum(1 for i, k in pr if l1[i] == l1[k])
    c = sum(1 for i, k in pr if l2[i] == l2[k])
    e, m = b * c / len(pr), (b + c) / 2
    return (a - e) / (m - e) if m != e else 1.0


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


def mesh_measures():
    sys.path.insert(0, r"G:\내 드라이브\도서 번역\.claude\skills\acupoint-anatomy\scripts\fma")
    import mesh3d
    out = {"volumes": [], "lung_distance": []}
    for fid in (9629, 32546, 13413, 32550, 32549):
        m, _ = mesh3d.load_mesh(fid, "right")
        if m is not None:
            out["volumes"].append({"fma_id": fid, "label": mesh3d._label(fid), **{k: v for k, v in mesh3d.metrics(m).items() if k in ("volume_cm3", "watertight", "extent_mm")}})
    # BodyParts3D의 폐(7309)·위엽(7333) 메쉬는 기관지 나무뿐이고 실질·흉막 표면이 없다 → 폐 거리 측정 불가.
    # 대리 지표: 폐첨·흉막 꼭대기를 둘러싸는 첫째·둘째갈비뼈까지 최소 거리(B1-03). 흉막까지의 거리가 아니다.
    ribs = {"Right first rib": mesh3d.load_mesh(7857, "right")[0], "Right second rib": mesh3d.load_mesh(mesh3d.resolve("Right second rib"), "right")[0]}
    targets = {"LI16 巨骨": [9629], "GB21 肩井": [32519, 9629, 33586], "LU2 雲門": [13410, 13109, 13373], "SI11 天宗": [32546], "LI15 肩髃": [9629, 13413]}
    for pt, fids in targets.items():
        for fid in fids:
            m, _ = mesh3d.load_mesh(fid, "right" if fid not in (33586, 13373) else None)
            if m is None:
                continue
            row = {"point": pt, "fma_id": fid, "label": mesh3d._label(fid)}
            for rn, rm in ribs.items():
                d = mesh3d.min_distance(m, rm, n=15000)
                row[rn] = d["min_distance_mm"]
            out["lung_distance"].append(row)
    return out


def main():
    codes = list(POINTS)
    F = {c: features(c) for c in codes}
    W = {"N": 0.35, "G": 0.30, "S": 0.20, "R": 0.15}
    M, Meq = simmat(codes, F, W), simmat(codes, F, {k: 0.25 for k in W})
    Z = linkage(squareform(1 - M, checks=False), "average")
    coph, _ = cophenet(Z, squareform(1 - M, checks=False))
    k = max(range(3, 9), key=lambda k: silhouette(1 - M, fcluster(Z, k, "maxclust")))
    lab = fcluster(Z, k, "maxclust")
    lab_eq = fcluster(linkage(squareform(1 - Meq, checks=False), "average"), k, "maxclust")
    kin = {}
    for mot, d in MOTIONS.items():
        rows = {}
        for c in codes:
            ag = [d["agonist"][f] for f in F[c]["muscles"] if f in d["agonist"]]
            rs = [d["restraint"][f] for f in F[c]["muscles"] if f in d["restraint"]]
            if ag or rs:
                rows[c] = {"agonist": ag, "restraint": rs}
        kin[mot] = {"capsule": d["capsule"], "points": rows, "report_points": REPORT_MAP[mot]}
    res = {"codes": codes, "names": POINTS, "region": REGION, "weights": W, "k": k, "cophenetic": round(float(coph), 3),
           "ari": round(ari(list(lab), list(lab_eq)), 3), "linkage": Z.tolist(), "labels": [int(x) for x in lab],
           "features": {c: {"N": sorted(F[c]["N"]), "G": [g for g in SEG_ORDER if g in F[c]["G"]], "G_src": F[c]["G_src"], "S": sorted(F[c]["S"]),
                            "muscles": F[c]["muscles"], "multiseg": F[c]["multiseg"], "shoulder_joint_nerves": F[c]["shoulder_joint_nerves"],
                            "XI": F[c]["XI"]} for c in codes},
           "kinesiology": kin, "mesh": mesh_measures()}
    (HERE / "fs_results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    np.savetxt(HERE / "fs_similarity.csv", M, delimiter=",", fmt="%.3f", header=",".join(codes), comments="")
    print(f"k={k} coph={coph:.3f} ARI={res['ari']}")
    for kk in (3, 5, 7):
        g = {}
        for c, l in zip(codes, fcluster(Z, kk, "maxclust")):
            g.setdefault(int(l), []).append(c)
        print(kk, list(g.values()))
    for c in codes:
        print(c, POINTS[c][0], "| seg", ",".join(g for g in SEG_ORDER if g in F[c]["G"]), "| 관절신경", F[c]["shoulder_joint_nerves"], "| XI", F[c]["XI"])
    for mot, d in kin.items():
        print(mot, "| 보고서:", d["report_points"], "|", {c: (v["agonist"], v["restraint"]) for c, v in d["points"].items()})
    print(json.dumps(res["mesh"], ensure_ascii=False, indent=0)[:1500])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

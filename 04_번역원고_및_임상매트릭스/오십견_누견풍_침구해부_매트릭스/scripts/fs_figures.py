# -*- coding: utf-8 -*-
"""[경혈해부] 오십견 15혈 FMA 그림: F1 층위·히트맵 / F2 관절 신경·분절 / F3 운동 기능해부 / F4 체표 분포 / F5 3D 4종.

사용: python fs_figures.py <출력 폴더> [ko|en]
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse, Patch, Polygon, Rectangle
from scipy.cluster.hierarchy import dendrogram, fcluster

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1])
LANG = sys.argv[2] if len(sys.argv) > 2 else "ko"
plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft JhengHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
R = json.loads((HERE / "fs_results.json").read_text(encoding="utf-8"))
codes, Z, F, NM = R["codes"], np.array(R["linkage"]), R["features"], R["names"]
M = np.loadtxt(HERE / "fs_similarity.csv", delimiter=",", skiprows=1)
L7 = fcluster(Z, 7, "maxclust")


def grp(c):
    mem = {x for x, l in zip(codes, L7) if l == L7[codes.index(c)]}
    return ("S1" if "SI11" in mem else "S2" if "LI16" in mem else "S3" if c == "EX-UE" else "S4" if c == "LU2" else
            "D1" if "ST38" in mem else "D2")


G = {c: grp(c) for c in codes}
GCOL = {"S1": "#1f6fb2", "S2": "#2a9d8f", "S3": "#e67e22", "S4": "#8e44ad", "D1": "#c0392b", "D2": "#7f6a3c"}
TX = {
    "ko": {"G": {"S1": "S1 어깨 가쪽·뒤(肩髃·肩髎·肩貞·臑兪·天宗)", "S2": "S2 어깨 위(巨骨·肩井)", "S3": "S3 어깨 앞(肩前)", "S4": "S4 빗장아래(雲門)",
                 "D1": "D1 하지(條口·承山·陽陵泉)", "D2": "D2 손·팔꿈치(中渚·合谷·曲池)"},
           "f1": "오십견 15혈의 FMA 해부 유사도 계층(UPGMA)", "f1s": "유사도 = 0.35·신경 + 0.30·분절 + 0.20·FMA 구조 + 0.15·부위 · 코페네틱 {c} · 등가중치 ARI {a}",
           "dist": "거리 (1 − 유사도)", "sim": "해부 유사도",
           "f2": "어깨관절 신경지배(Hilton 법칙)·척수 분절 매트릭스", "jn": "어깨관절 지배신경(C5–C6)", "on": "기타 신경", "seg": "분절(FMA)", "segb": "분절(B1 보완)",
           "f3": "운동 방향별 기능 해부 — 각 혈의 FMA 근육이 주동근(A)인가 제한 구조(R)인가",
           "f3s": "파랑 A = 그 운동의 주동근(능동 운동 시 수축·통증) · 빨강 R = 그 운동을 늘여 막는 근육(수동 제한) · 검은 테두리 = 원 보고서 5절이 그 운동 제한에 배정한 혈",
           "agon": "주동근(A)", "rest": "제한 근육(R)", "rep": "원 보고서 배정 혈", "cap": "관절낭 제한",
           "f4": "체표 분포도 — 색 = 해부 층위(7군)", "ant": "앞면", "post": "뒷면", "limb": "원위혈",
           "nm": {"Suprascapular nerve": "어깨위신경", "Axillary nerve": "겨드랑신경", "Lateral pectoral nerve": "가쪽가슴근신경",
                  "Musculocutaneous nerve": "근육피부신경", "Spinal accessory nerve": "더부신경(XI)", "Dorsal scapular nerve": "등쪽어깨신경",
                  "Supraclavicular nerve": "빗장위신경", "Radial nerve": "노신경"}},
    "en": {"G": {"S1": "S1 Lateral/posterior shoulder (LI15, TE14, SI9, SI10, SI11)", "S2": "S2 Top of shoulder (LI16, GB21)", "S3": "S3 Anterior shoulder (Jianqian)",
                 "S4": "S4 Infraclavicular (LU2)", "D1": "D1 Lower limb (ST38, BL57, GB34)", "D2": "D2 Hand & elbow (TE3, LI4, LI11)"},
           "f1": "FMA anatomical similarity hierarchy (UPGMA) of the 15 frozen-shoulder points",
           "f1s": "Similarity = 0.35·nerves + 0.30·segments + 0.20·FMA structures + 0.15·region · cophenetic {c} · ARI vs equal weights {a}",
           "dist": "Distance (1 − similarity)", "sim": "Anatomical similarity",
           "f2": "Glenohumeral innervation (Hilton's law) and spinal segments", "jn": "Glenohumeral joint nerves (C5–C6)", "on": "Other nerves",
           "seg": "Segments (FMA)", "segb": "Segments (B1 supplement)",
           "f3": "Functional anatomy by direction of motion — is the point's FMA muscle an agonist (A) or a restraint (R)?",
           "f3s": "Blue A = agonist of that motion (contracts, painful on active motion) · Red R = muscle stretched by the motion (passive restraint) · Black outline = points the original report (Section 5) assigned to that restriction",
           "agon": "Agonist (A)", "rest": "Restraining muscle (R)", "rep": "Assigned in original report", "cap": "Capsular restraint",
           "f4": "Surface map — colour = anatomical group (7 clusters)", "ant": "Anterior", "post": "Posterior", "limb": "Distal points",
           "nm": {k: k for k in ["Suprascapular nerve", "Axillary nerve", "Lateral pectoral nerve", "Musculocutaneous nerve", "Spinal accessory nerve",
                                 "Dorsal scapular nerve", "Supraclavicular nerve", "Radial nerve"]}},
}[LANG]


def lab(c):
    return f"{c} {NM[c][0]}"


def f1():
    fig = plt.figure(figsize=(14, 8.5), dpi=150)
    ad = fig.add_axes([0.05, 0.14, 0.2, 0.7])
    dn = dendrogram(Z, orientation="left", labels=[lab(c) for c in codes], ax=ad, link_color_func=lambda k: "#555", leaf_font_size=10)
    order = [codes[i] for i in dn["leaves"]]
    ad.invert_yaxis()
    ad.set_xlabel(TX["dist"])
    for s in ("top", "right", "left"):
        ad.spines[s].set_visible(False)
    idx = [codes.index(c) for c in order]
    ah = fig.add_axes([0.36, 0.14, 0.5, 0.7])
    im = ah.imshow(M[np.ix_(idx, idx)], cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    ah.set_xticks(range(len(order)))
    ah.set_xticklabels(order, rotation=90, fontsize=9)
    ah.set_yticks([])
    for k, c in enumerate(order):
        ah.add_patch(Rectangle((len(order) - 0.3, k - 0.5), 0.9, 1, color=GCOL[G[c]], clip_on=False))
    cb = fig.add_axes([0.9, 0.3, 0.012, 0.4])
    fig.colorbar(im, cax=cb).set_label(TX["sim"])
    fig.legend(handles=[Patch(color=GCOL[k], label=v) for k, v in TX["G"].items()], loc="lower center", ncol=3, fontsize=8.5, frameon=False)
    fig.suptitle(TX["f1"], x=0.05, ha="left", fontsize=14, weight="bold", y=0.97)
    fig.text(0.05, 0.92, TX["f1s"].format(c=R["cophenetic"], a=R["ari"]), fontsize=9, color="#333")
    fig.savefig(OUT / f"Fig_A_FMA_해부유사도_계층_{LANG}.png", facecolor="white")
    plt.close(fig)
    return order


def f2(order):
    NERV = ["Suprascapular nerve", "Axillary nerve", "Lateral pectoral nerve", "Musculocutaneous nerve", "Radial nerve", "Spinal accessory nerve",
            "Dorsal scapular nerve", "Supraclavicular nerve"]
    SEG = ["C3", "C4", "C5", "C6", "C7", "C8", "T1", "T2", "L3", "L4", "L5", "S1", "S2", "S3"]
    cols = NERV + SEG
    fig, ax = plt.subplots(figsize=(14, 7.5), dpi=150)
    for r, c in enumerate(order):
        N = set(F[c]["N"])
        for k, n in enumerate(NERV):
            hit = n in N or any(x.startswith(n.split()[0]) and "nerve" in x and n.split()[0] in x for x in N if n in ("Supraclavicular nerve",) and "supraclavicular" in x.lower())
            if n == "Axillary nerve":
                hit = hit or "Set of muscular branches of axillary nerve" in N
            if n == "Radial nerve":
                hit = hit or "Peripheral segment of radial nerve" in N
            if n == "Supraclavicular nerve":
                hit = any("supraclavicular" in x.lower() for x in N)
            if hit:
                ax.add_patch(Rectangle((k, r), 1, 1, color="#c0392b" if k < 3 else "#e59866"))
        for k, g in enumerate(SEG):
            if g in F[c]["G_src"]:
                fma = any(s in ("FMA", "FMA 라벨") for s in F[c]["G_src"][g])
                ax.add_patch(Rectangle((len(NERV) + k, r), 1, 1, color="#1f6fb2" if fma else "#74b9ff"))
    ax.add_patch(Rectangle((0, -0.9), 3, len(order) + 1.1, fc="none", ec="#c0392b", lw=2.2, clip_on=False))
    c5 = len(NERV) + SEG.index("C5")
    ax.add_patch(Rectangle((c5, -0.9), 2, len(order) + 1.1, fc="none", ec="#c0392b", lw=2.2, clip_on=False))
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(order), -1.2)
    ax.set_xticks(np.arange(len(cols)) + 0.5)
    ax.set_xticklabels([TX["nm"][n] for n in NERV] + SEG, rotation=45, ha="right", fontsize=8.5)
    ax.set_yticks(np.arange(len(order)) + 0.5)
    ax.set_yticklabels([lab(c) for c in order], fontsize=9.5)
    for t, c in zip(ax.get_yticklabels(), order):
        t.set_color(GCOL[G[c]])
    for k in range(len(cols) + 1):
        ax.axvline(k, color="#eee", lw=0.5)
    for k in range(len(order) + 1):
        ax.axhline(k, color="#eee", lw=0.5)
    ax.axvline(len(NERV), color="#333", lw=1)
    ax.legend(handles=[Patch(color="#c0392b", label=TX["jn"]), Patch(color="#e59866", label=TX["on"]), Patch(color="#1f6fb2", label=TX["seg"]),
                       Patch(color="#74b9ff", label=TX["segb"])], loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4, fontsize=9, frameon=False)
    ax.set_title(TX["f2"], loc="left", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / f"Fig_B_관절신경_분절_{LANG}.png", facecolor="white")
    plt.close(fig)


def f3():
    sh = ["LI15", "TE14", "EX-UE", "SI9", "SI10", "SI11", "LI16", "LU2", "GB21"]
    mots = list(R["kinesiology"])
    fig, ax = plt.subplots(figsize=(14, 7.8), dpi=150)
    for i, m in enumerate(mots):
        d = R["kinesiology"][m]
        for k, c in enumerate(sh):
            v = d["points"].get(c, {"agonist": [], "restraint": []})
            if v["agonist"]:
                ax.add_patch(Rectangle((k + 0.03, i + 0.05), 0.47, 0.9, color="#2e86de", alpha=0.85))
                ax.text(k + 0.265, i + 0.5, "A\n" + "\n".join(x.split()[0][:9] for x in v["agonist"][:3]), ha="center", va="center", fontsize=6.3, color="white")
            if v["restraint"]:
                ax.add_patch(Rectangle((k + 0.5, i + 0.05), 0.47, 0.9, color="#e74c3c", alpha=0.85))
                ax.text(k + 0.735, i + 0.5, "R\n" + "\n".join(x.split()[0][:9] for x in v["restraint"][:3]), ha="center", va="center", fontsize=6.3, color="white")
            if c in d["report_points"]:
                ax.add_patch(Rectangle((k, i), 1, 1, fc="none", ec="black", lw=2.4))
        ax.text(len(sh) + 0.15, i + 0.5, f"{TX['cap']}: {d['capsule']}", va="center", fontsize=8)
    ax.set_xlim(0, len(sh) + 4.2)
    ax.set_ylim(len(mots), 0)
    ax.set_xticks(np.arange(len(sh)) + 0.5)
    ax.set_xticklabels([lab(c) for c in sh], fontsize=9.5)
    ax.set_yticks(np.arange(len(mots)) + 0.5)
    ax.set_yticklabels(mots, fontsize=10)
    for k in range(len(sh) + 1):
        ax.axvline(k, color="#ccc", lw=0.6)
    for k in range(len(mots) + 1):
        ax.axhline(k, xmax=len(sh) / (len(sh) + 4.2), color="#ccc", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(handles=[Patch(color="#2e86de", label=TX["agon"]), Patch(color="#e74c3c", label=TX["rest"]),
                       Patch(fc="none", ec="black", lw=2, label=TX["rep"])], loc="upper center", bbox_to_anchor=(0.35, -0.06), ncol=3, fontsize=9, frameon=False)
    ax.set_title(TX["f3"], loc="left", fontsize=13, weight="bold")
    fig.text(0.01, 0.01, TX["f3s"], fontsize=8, color="#333")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(OUT / f"Fig_C_운동방향_기능해부_{LANG}.png", facecolor="white")
    plt.close(fig)


ANT = {"LI15": (27, 150), "EX-UE": (31, 140), "LU2": (37, 152), "LI16": (31, 158)}
POST = {"TE14": (77, 150), "SI9": (72, 138), "SI10": (73, 147), "SI11": (65, 142), "GB21": (64, 160), "LI16": (73, 157)}
LIMB = {"LI11": (17, 115), "TE3": (9, 70), "LI4": (12, 74), "ST38": (38, 30), "GB34": (33, 47), "BL57": (60, 28)}


def body(ax, x0, back=False):
    sk = dict(fc="#f7efe6", ec="#9c8a7a", lw=1.2)
    ax.add_patch(Ellipse((x0 + 50, 182), 17, 21, **sk))
    ax.add_patch(Polygon([(x0 + 26, 160), (x0 + 74, 160), (x0 + 70, 88), (x0 + 30, 88)], **sk))
    for s in (1, -1):
        X = (lambda v: x0 + v) if s == 1 else (lambda v: x0 + 100 - v)
        ax.add_patch(Polygon([(X(26), 160), (X(19), 150), (X(14), 115), (X(8), 82), (X(3), 66), (X(6), 54), (X(16), 58), (X(17), 78),
                              (X(20), 112), (X(26), 140), (X(29), 152)], **sk))
        ax.add_patch(Polygon([(X(31), 88), (X(49), 88), (X(47), 50), (X(46), 12), (X(48), 2), (X(34), 0), (X(36), 12), (X(33), 50)], **sk))


def f4():
    fig, ax = plt.subplots(figsize=(15, 10), dpi=150)
    body(ax, 0)
    body(ax, 110, back=True)
    for P, dx in ((ANT, 0), (POST, 110), (LIMB, 0)):
        for c, (x, y) in P.items():
            xx = x + dx
            if P is LIMB and c == "BL57":
                xx = 110 + 100 - x
            ax.scatter(xx, y, s=140, color=GCOL[G[c]], edgecolor="black", zorder=5)
            ax.annotate(lab(c), (xx, y), xytext=(6, 4), textcoords="offset points", fontsize=8.5, zorder=6,
                        bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))
    ax.text(50, 207, TX["ant"], ha="center", fontsize=12, weight="bold")
    ax.text(160, 207, TX["post"], ha="center", fontsize=12, weight="bold")
    ax.set_xlim(-5, 215)
    ax.set_ylim(-5, 212)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(handles=[Patch(color=GCOL[k], label=v) for k, v in TX["G"].items()], loc="lower right", fontsize=8.5)
    ax.set_title(TX["f4"], loc="left", fontsize=14, weight="bold")
    fig.savefig(OUT / f"Fig_D_체표분포도_{LANG}.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)


def f5():
    sys.path.insert(0, r"G:\내 드라이브\도서 번역\.claude\skills\acupoint-anatomy\scripts\fma")
    import mesh3d
    BONE = "#d8cfb8"
    SUB = {32521: [34680, 34682, 34684], 9626: [33586, 33584, 33581], 9627: [13373]}

    def load(fid, side="right"):
        parts = SUB.get(fid, [fid])
        ms = [m for m in (mesh3d.load_mesh(p, side if p not in (33586, 33584, 33581, 34680, 34682, 34684, 13373) else None)[0] for p in parts) if m is not None]
        if not ms:
            return None
        import trimesh
        return trimesh.util.concatenate(ms)

    bones = [(13395, "right"), (23130, "right"), (13322, "right")]
    ko = LANG == "ko"
    scenes = [
        ("E1_외회전_제한구조", "외회전(ER) — 주동근(파랑) vs 제한 근육(빨강)" if ko else "External rotation — agonists (blue) vs restraining muscles (red)",
         [(32546, "#2e86de"), (32550, "#5dade2"), (13413, "#e74c3c"), (9627, "#f1948a"), (32549, "#c0392b")], bones, "iso"),
        ("E2_어깨뒤_S1", "S1 어깨 가쪽·뒤 군집 공유 구조(肩髃·肩髎·肩貞·臑兪·天宗)" if ko else "S1 lateral/posterior shoulder group — shared structures",
         [(32521, "#d35400"), (32546, "#2e86de"), (32550, "#5dade2"), (32549, "#c0392b"), (37692, "#8e44ad"), (9629, "#16a085"), (13413, "#e74c3c")], bones, "iso"),
        ("E3_기흉안전_갈비뼈거리", "기흉 위험 혈 심부 구조 ↔ 첫째·둘째갈비뼈(흉막 꼭대기 대리 지표) 최소 거리" if ko else "Deep structures of pneumothorax-risk points ↔ first/second ribs (proxy for the pleural dome) — minimum distances",
         [(13410, "#e74c3c"), (13373, "#f5b7b1"), (13109, "#f39c12"), (9629, "#16a085"), (32519, "#8e44ad"), (9626, "#7f8c8d")],
         [(7857, "right"), ("Right second rib", "right"), (13322, "right"), (13395, "right"), (24138, None)], "iso"),
    ]
    dist = {d["label"]: (d.get("Right first rib"), d.get("Right second rib")) for d in R["mesh"]["lung_distance"]}
    for key, title, structs, bns, view in scenes:
        items = []
        for fid, col in structs:
            m = load(fid, None if fid == 7309 else "right")
            if m is None:
                continue
            labl = mesh3d._label(fid)
            dd = dist.get(labl) or next((v for k, v in dist.items() if k.endswith(labl.split()[-1]) and labl.split()[0] in k), None)
            extra = (f" — {'갈비뼈1/2까지' if ko else 'to rib 1/2'} {dd[0]}/{dd[1]} mm" if (key.startswith("E3") and dd) else "")
            items.append((m, col, f"FMA:{fid} {labl}{extra}", 0.35 if fid in (7309, 9626, 32521, 9627) else 1.0))
        for b, side in bns:
            b = mesh3d.resolve(b) if isinstance(b, str) else b
            m, _ = mesh3d.load_mesh(b, side)
            if m is not None:
                rib = key.startswith("E3") and b in (7857, mesh3d.resolve("Right second rib"))
                items.append((m, "#5d6d7e" if rib else BONE, f"FMA:{b} {mesh3d._label(b)} ({'흉막 대리 지표' if ko and rib else 'pleural proxy' if rib else '뼈대' if ko else 'skeleton'})", 0.85 if rib else 0.3))
        note = ("BodyParts3D 4.0 (DBCLS, CC BY 4.0) 표준 모델 — 개인차·경혈 위치 미반영(B1 보조). 거리는 구조 표면 사이 최소값이며 자침 경로 길이가 아니다."
                if ko else "BodyParts3D 4.0 (DBCLS, CC BY 4.0) reference model — no individual variation or point positions (B1 supplementary). Distances are minimum surface-to-surface values, not needle-path depths.")
        mesh3d.render(items, str(OUT / f"Fig_{key}_3D_{LANG}.png"), title, view, note)
        print("[3D]", key, len(items))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    order = f1()
    f2(order)
    f3()
    f4()
    f5()
    print("ok", LANG)

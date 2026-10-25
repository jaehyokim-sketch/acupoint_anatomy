# -*- coding: utf-8 -*-
"""[경혈해부] 『동의보감』 두통 鍼灸法 — 그림 4종(처방 매트릭스 / 해부 유사도 계층 / 신경·분절 매트릭스 / 체표 분포도).

사용: python hd_figures.py <출력 폴더> [ko|en]
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
sys.path.insert(0, str(HERE))
from hd_similarity import NAMES, RX, SEG_ORDER  # noqa: E402

D = json.loads((HERE / "hd_clusters.json").read_text(encoding="utf-8"))
codes, Z, FEAT, TIER = D["codes"], np.array(D["linkage"]), D["features"], D["tier"]
M = np.loadtxt(HERE / "hd_similarity.csv", delimiter=",", skiprows=1)
TIER_COL = {"I": "#c0392b", "II": "#e08e0b", "III": "#7f8c8d"}
L1 = fcluster(Z, 4, "maxclust")
L2 = fcluster(Z, 9, "maxclust")


def lab(c):
    return f"{c} {NAMES[c][0]}"


def group_name(c, level):
    lab_ = (L1 if level == 1 else L2)[codes.index(c)]
    mem = {x for x, l in zip(codes, L1 if level == 1 else L2) if l == lab_}
    if level == 1:
        return "H" if "GV20" in mem else "U" if "LI4" in mem else "L" if "ST36" in mem else "T"
    return ("Ha" if "GV20" in mem else "Hb" if "TE23" in mem else "Hc" if "GB20" in mem else "Hd" if "BL12" in mem else
            "U" if "LI4" in mem else "L" if "ST36" in mem else "T")


G2 = {c: group_name(c, 2) for c in codes}
G2_COL = {"Ha": "#1f6fb2", "Hb": "#2a9d8f", "Hc": "#8e44ad", "Hd": "#b07aa1", "U": "#e67e22", "L": "#c0392b", "T": "#7f6a3c"}

TX = {
    "ko": {
        "tier": {"I": "1층: 한대 단독 주치에 두통", "II": "2층: 후대 단독 주치에만 두통", "III": "3층: 두통 단독 주치 없음(배오로만 쓰임)"},
        "G2": {"Ha": "Ha 이마·정수리 정중(V1)", "Hb": "Hb 관자(V3·VII)", "Hc": "Hc 뒤통수밑(C1–C3)", "Hd": "Hd 등 위(風門)",
               "U": "U 손(合谷)", "L": "L 종아리·발목(L4–S1)", "T": "T 체간 정중(中脘·膻中·關元)"},
        "f0": "『동의보감』 두통 15유형 × 鍼灸法 20혈 — 처방 매트릭스",
        "f0sub": "● 鍼(取) · ▲ 灸 · 열 머리 색 = 단독 주치 층 · 열 순서 = 해부 유사도 계통수 순서 · 회색 행 = 鍼灸法 처방 없음(약물·吐下法만)",
        "norx": "鍼灸法 없음",
        "f1": "두통 鍼灸法 20혈의 해부 유사도 계층(UPGMA)",
        "f1sub": "유사도 = 0.35·신경 영역 + 0.30·분절·뇌신경 분지 + 0.20·FMA 구조 + 0.15·부위 (가중 Jaccard) · 코페네틱 {coph} · 등가중치 ARI {ari}",
        "dist": "거리 (1 − 유사도)", "sim": "해부 유사도", "cut4": "대분류(4군)", "cut9": "중분류(9군)",
        "f2": "뇌신경 분지·척수 분절 매트릭스 — 삼차-경수 복합체(TCC) 수렴",
        "tcc": "TCC: 삼차신경 V1–V3 + C1–C3 (B1-02)", "fma": "FMA·FMA 라벨", "b1": "B1 보완", "cn": "뇌신경 분지",
        "f3": "체표 분포도 — 색 = 중분류, 모양 = 단독 주치 층, 크기 = 쓰인 처방 수",
        "front": "앞얼굴", "lat": "옆머리(오른쪽)", "body": "몸통·사지", "size": "크기 = 쓰인 처방 수(1~4)",
        "back_note": "風門(BL12)은 등(T2 옆) — 앞면에 위치만 표시",
    },
    "en": {
        "tier": {"I": "Tier I: headache in Han-era single-point indications", "II": "Tier II: headache only in later single-point indications",
                 "III": "Tier III: no single-point headache indication (used only in combinations)"},
        "G2": {"Ha": "Ha Forehead & vertex midline (V1)", "Hb": "Hb Temple (V3, VII)", "Hc": "Hc Suboccipital (C1–C3)", "Hd": "Hd Upper back (BL12)",
               "U": "U Hand (LI4)", "L": "L Leg & ankle (L4–S1)", "T": "T Trunk midline (CV12, CV17, CV4)"},
        "f0": "Donguibogam (東醫寶鑑) headache: 15 types × 20 points of the acupuncture section — prescription matrix",
        "f0sub": "● needling (取/鍼) · ▲ moxibustion (灸) · column header colour = single-point tier · column order = anatomical dendrogram · grey rows = no acupuncture prescription (herbal/emetic/purgative only)",
        "norx": "no acupuncture",
        "f1": "Anatomical similarity hierarchy (UPGMA) of the 20 headache points",
        "f1sub": "Similarity = 0.35·nerve territory + 0.30·segments & cranial-nerve divisions + 0.20·FMA structures + 0.15·region (weighted Jaccard) · cophenetic {coph} · ARI vs equal weights {ari}",
        "dist": "Distance (1 − similarity)", "sim": "Anatomical similarity", "cut4": "Major (4)", "cut9": "Intermediate (9)",
        "f2": "Cranial-nerve divisions and spinal segments — trigeminocervical complex (TCC) convergence",
        "tcc": "TCC: trigeminal V1–V3 + C1–C3 (B1-02)", "fma": "FMA / FMA label", "b1": "B1 supplement", "cn": "Cranial-nerve division",
        "f3": "Surface map — colour = intermediate group, shape = single-point tier, size = number of prescriptions",
        "front": "Face (anterior)", "lat": "Head (right lateral)", "body": "Trunk & limbs", "size": "Size = number of prescriptions (1–4)",
        "back_note": "BL12 lies on the back (beside T2) — position indicated on the anterior figure only",
    },
}[LANG]

TYPES = [  # (동의보감 절, 유형, 연결 처방)
    ("1.7", "頭風證", ["R6"]), ("1.10", "正頭痛", ["R2", "R1"]), ("1.11", "偏頭痛", ["R1"]), ("1.12", "風寒頭痛", []),
    ("1.13", "濕熱頭痛", []), ("1.14", "厥逆頭痛(腦逆·腎厥)", ["R3", "R4"]), ("1.15", "痰厥頭痛", ["R5"]),
    ("1.16", "氣厥頭痛(氣虛·血虛)", []), ("1.17", "熱厥頭痛", []), ("1.18", "濕厥頭痛", []), ("1.19", "醉後頭痛", ["R9"]),
    ("1.22", "腦風證", ["R7"]), ("1.23", "首風證", []), ("1.24", "眉稜骨痛", ["R8"]), ("1.25", "眞頭痛(不治)", []),
]
RXD = {r["id"]: r for r in RX}


def fig_rx(order):
    fig, ax = plt.subplots(figsize=(16, 9.5), dpi=150)
    n, m = len(TYPES), len(order)
    for i, (sec, t, rxs) in enumerate(TYPES):
        if not rxs:
            ax.add_patch(Rectangle((0, i), m, 1, color="#eeeeee"))
            ax.text(m / 2, i + 0.5, TX["norx"], ha="center", va="center", fontsize=8, color="#999")
        for rid in rxs:
            r = RXD[rid]
            moxa = "灸" in r["method"] and "鍼" not in r["method"]
            for p in r["points"]:
                k = order.index(p)
                ax.scatter(k + 0.5, i + 0.5, marker="^" if moxa else "o", s=170, color=G2_COL[G2[p]], edgecolor="black", zorder=3)
                if rid == "R6" and p == "GV20":  # 百會: 鍼과 灸 모두
                    ax.scatter(k + 0.5, i + 0.5, marker="^", s=60, color="white", edgecolor="black", zorder=4)
        ax.text(-0.2, i + 0.5, f"{sec} {t}" + (f"  [{','.join(rxs)}]" if rxs else ""), ha="right", va="center", fontsize=9.5)
    for k in range(m + 1):
        ax.axvline(k, color="#ddd", lw=0.6)
    for i in range(n + 1):
        ax.axhline(i, color="#ddd", lw=0.6)
    ax.set_xlim(0, m)
    ax.set_ylim(n, -1.6)
    ax.set_yticks([])
    ax.set_xticks(np.arange(m) + 0.5)
    ax.set_xticklabels([lab(c) for c in order], rotation=60, ha="right", fontsize=9)
    for t, c in zip(ax.get_xticklabels(), order):
        t.set_color(TIER_COL[TIER[c]])
        t.set_fontweight("bold" if TIER[c] == "I" else "normal")
    for k, c in enumerate(order):
        ax.add_patch(Rectangle((k, -1.4), 1, 0.9, color=G2_COL[G2[c]]))
    ax.set_title(TX["f0"], loc="left", fontsize=14, weight="bold", pad=30)
    ax.text(0, -2.3, TX["f0sub"], fontsize=8.5, color="#333")
    h = [Patch(color=G2_COL[k], label=v) for k, v in TX["G2"].items()] + [Patch(color=TIER_COL[k], label=v) for k, v in TX["tier"].items()]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.45, -0.22), ncol=4, fontsize=8.5, frameon=False)
    fig.subplots_adjust(left=0.24, right=0.99, top=0.88, bottom=0.27)
    fig.savefig(OUT / f"Fig1_처방매트릭스_{LANG}.png", facecolor="white")
    plt.close(fig)


def fig_tree():
    fig = plt.figure(figsize=(15, 9.5), dpi=150)
    axd = fig.add_axes([0.05, 0.12, 0.22, 0.72])
    dn = dendrogram(Z, orientation="left", labels=[lab(c) for c in codes], ax=axd, link_color_func=lambda k: "#555", leaf_font_size=9.5)
    order = [codes[i] for i in dn["leaves"]]
    axd.invert_yaxis()
    axd.set_xlabel(TX["dist"])
    for s in ("top", "right", "left"):
        axd.spines[s].set_visible(False)
    axd.axvline(Z[-4, 2] + 1e-3, color="#c0392b", ls="--", lw=1)
    axd.axvline(Z[-9, 2] + 1e-3, color="#e08e0b", ls=":", lw=1)
    axd.text(Z[-4, 2] + 0.01, -1.0, TX["cut4"], color="#c0392b", fontsize=8, ha="right")
    axd.text(Z[-9, 2] - 0.01, -1.0, TX["cut9"], color="#e08e0b", fontsize=8, ha="left")
    for t in axd.get_yticklabels():
        c = t.get_text().split()[0]
        t.set_color(TIER_COL[TIER[c]])
        t.set_fontweight("bold" if TIER[c] == "I" else "normal")
    idx = [codes.index(c) for c in order]
    axh = fig.add_axes([0.37, 0.12, 0.52, 0.72])
    im = axh.imshow(M[np.ix_(idx, idx)], cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    axh.set_xticks(range(len(order)))
    axh.set_xticklabels(order, rotation=90, fontsize=8.5)
    axh.set_yticks([])
    for k, c in enumerate(order):
        axh.add_patch(Rectangle((-1.6, k - 0.5), 0.9, 1, color=TIER_COL[TIER[c]], clip_on=False))
        axh.add_patch(Rectangle((len(order) - 0.3, k - 0.5), 0.9, 1, color=G2_COL[G2[c]], clip_on=False))
    cb = fig.add_axes([0.915, 0.3, 0.012, 0.4])
    fig.colorbar(im, cax=cb).set_label(TX["sim"])
    fig.legend(handles=[Patch(color=TIER_COL[k], label=v) for k, v in TX["tier"].items()] +
               [Patch(color=G2_COL[k], label=v) for k, v in TX["G2"].items()], loc="lower center", ncol=4, fontsize=8.5,
               frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(TX["f1"], x=0.05, ha="left", fontsize=14, weight="bold", y=0.97)
    fig.text(0.05, 0.925, TX["f1sub"].format(coph=D["cophenetic"], ari=D["ari"]), fontsize=9, color="#333")
    fig.savefig(OUT / f"Fig2_해부유사도_계층_{LANG}.png", facecolor="white")
    plt.close(fig)
    return order


def fig_nerve(order):
    CNS = ["V1", "V2", "V3", "VII", "XI"]
    SEGS = SEG_ORDER[:22] + ["L1", "L2", "L3", "L4", "L5", "S1", "S2", "S3"]
    SEGS = list(dict.fromkeys(SEGS))
    cols = CNS + SEGS
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=150)
    for r, c in enumerate(order):
        f = FEAT[c]
        for k, g in enumerate(cols):
            if g in CNS:
                if g in f["cranial"] or (g in ("V1", "V2", "V3") and "V" in f["cranial"]):
                    ax.add_patch(Rectangle((k, r), 1, 1, color="#6c5ce7"))
            elif g in f["G_src"]:
                fma = any(s in ("FMA", "FMA 라벨") for s in f["G_src"][g])
                ax.add_patch(Rectangle((k, r), 1, 1, color="#1f6fb2" if fma else "#74b9ff"))
    ax.add_patch(Rectangle((0, -1.0), 3, len(order) + 1.2, fc="none", ec="#c0392b", lw=2.2, clip_on=False))
    c1 = len(CNS) + SEGS.index("C1")
    ax.add_patch(Rectangle((c1, -1.0), 3, len(order) + 1.2, fc="none", ec="#c0392b", lw=2.2, clip_on=False))
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(order), -1.4)
    ax.set_xticks(np.arange(len(cols)) + 0.5)
    ax.set_xticklabels(cols, fontsize=8)
    ax.set_yticks(np.arange(len(order)) + 0.5)
    ax.set_yticklabels([lab(c) for c in order], fontsize=9)
    for t, c in zip(ax.get_yticklabels(), order):
        t.set_color(TIER_COL[TIER[c]])
    for k in range(len(cols) + 1):
        ax.axvline(k, color="#eee", lw=0.5)
    for k in range(len(order) + 1):
        ax.axhline(k, color="#eee", lw=0.5)
    ax.axvline(len(CNS), color="#333", lw=1)
    ax.legend(handles=[Patch(color="#6c5ce7", label=TX["cn"]), Patch(color="#1f6fb2", label=TX["fma"]), Patch(color="#74b9ff", label=TX["b1"]),
                       Patch(fc="none", ec="#c0392b", lw=2, label=TX["tcc"])], loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=4,
              fontsize=9, frameon=False)
    ax.set_title(TX["f2"], loc="left", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / f"Fig3_신경분절_매트릭스_{LANG}.png", facecolor="white")
    plt.close(fig)


# 모식 좌표(B1-05 정위의 상대 위치만, 축척 아님). 앞얼굴은 대상자 오른쪽을 그림 왼쪽에 둔다.
FACE = {"GV29": (50, 66), "BL2": (43, 67), "TE23": (31, 67), "EX-HN5": (25, 61), "ST8": (29, 91), "GV24": (50, 95), "GV23": (50, 100)}
LAT = {"GV20": (62, 114), "GV21": (50, 112), "GV22": (40, 108), "GV23": (33, 104), "GV24": (29, 99), "ST8": (31, 92),
       "TE23": (24, 70), "EX-HN5": (31, 64), "GB7": (60, 76), "GB20": (88, 50)}
BODY = {"LI4": (14, 74), "ST36": (37, 34), "ST40": (39, 26), "ST41": (40, 6), "CV12": (50, 112), "CV17": (50, 136), "CV4": (50, 96), "BL12": (58, 148)}
OFF = {"GV24": (8, -6), "GV23": (8, 4), "GV22": (-10, 6), "GV21": (-6, 9), "GV20": (6, 8), "ST8": (-14, 0), "TE23": (-14, 0), "EX-HN5": (-14, -6),
       "GB7": (8, -2), "GB20": (6, 4), "GV29": (6, -8), "BL2": (-6, 9), "LI4": (-12, 0), "ST36": (8, 0), "ST40": (8, 0), "ST41": (8, 0),
       "CV12": (8, 0), "CV17": (8, 0), "CV4": (8, 0), "BL12": (8, 0)}
NRX = {c: sum(1 for r in RX if c in r["points"]) for c in codes}
MK = {"I": "o", "II": "s", "III": "^"}


def dots(ax, P):
    for c, (x, y) in P.items():
        ax.scatter(x, y, s=60 + 70 * NRX[c], marker=MK[TIER[c]], color=G2_COL[G2[c]], edgecolor="black", lw=0.7, zorder=5)
        o = OFF.get(c, (6, 3))
        ax.annotate(lab(c), (x, y), xytext=o, textcoords="offset points", fontsize=8, ha="right" if o[0] < 0 else "left", va="center",
                    zorder=6, bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))


def fig_map():
    fig, axs = plt.subplots(1, 3, figsize=(17, 8), dpi=150, gridspec_kw={"width_ratios": [1, 1.1, 1]})
    sk = dict(fc="#f7efe6", ec="#9c8a7a", lw=1.3)
    a = axs[0]
    a.add_patch(Ellipse((50, 72), 62, 86, **sk))
    for x in (38, 62):
        a.add_patch(Ellipse((x, 60), 11, 5, fc="white", ec="#9c8a7a"))
    a.plot([30, 46], [67, 68], color="#7a6a5a", lw=2)
    a.plot([54, 70], [68, 67], color="#7a6a5a", lw=2)
    a.plot([50, 50], [58, 45], color="#cdbfb2")
    a.plot([24, 76], [93, 93], color="#cdbfb2", ls="--")
    dots(a, FACE)
    a.set_title(TX["front"])
    b = axs[1]
    b.add_patch(Polygon([(62, 44), (86, 44), (88, 20), (60, 20)], **sk))
    b.add_patch(Ellipse((58, 76), 74, 84, **sk))
    b.add_patch(Polygon([(22, 66), (14, 56), (22, 54)], **sk))
    b.add_patch(Ellipse((68, 64), 9, 15, fc="#efe3d6", ec="#9c8a7a"))
    b.plot([24, 60], [101, 117], color="#cdbfb2", ls="--")
    dots(b, LAT)
    b.set_title(TX["lat"])
    c = axs[2]
    c.add_patch(Ellipse((50, 172), 18, 22, **sk))
    c.add_patch(Polygon([(30, 158), (70, 158), (68, 88), (32, 88)], **sk))
    for s in (1, -1):
        X = (lambda v: v) if s == 1 else (lambda v: 100 - v)
        c.add_patch(Polygon([(X(30), 158), (X(22), 120), (X(14), 80), (X(10), 70), (X(18), 70), (X(22), 82), (X(30), 120)], **sk))
        c.add_patch(Polygon([(X(33), 88), (X(48), 88), (X(45), 6), (X(36), 2), (X(35), 6)], **sk))
    dots(c, BODY)
    c.text(50, -8, TX["back_note"], ha="center", fontsize=7.5, color="#555")
    c.set_title(TX["body"])
    for ax_, (xl, yl) in zip(axs, (((10, 90), (20, 125)), ((5, 105), (15, 128)), ((0, 100), (-12, 190)))):
        ax_.set_xlim(*xl)
        ax_.set_ylim(*yl)
        ax_.set_aspect("equal")
        ax_.axis("off")
    h = [Patch(color=G2_COL[k], label=v) for k, v in TX["G2"].items()]
    h += [Line2D([], [], marker=MK[k], ls="", color="#666", markeredgecolor="black", markersize=9, label=v) for k, v in TX["tier"].items()]
    h += [Line2D([], [], ls="", label=TX["size"])]
    fig.legend(handles=h, loc="lower center", ncol=4, fontsize=8.5, frameon=False)
    fig.suptitle(TX["f3"], x=0.02, ha="left", fontsize=14, weight="bold")
    fig.subplots_adjust(bottom=0.2, top=0.9, wspace=0.05)
    fig.savefig(OUT / f"Fig4_체표분포도_{LANG}.png", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    order = fig_tree()
    fig_rx(order)
    fig_nerve(order)
    fig_map()
    (HERE / "hd_order.json").write_text(json.dumps(order), encoding="utf-8")
    print("ok", LANG, order)

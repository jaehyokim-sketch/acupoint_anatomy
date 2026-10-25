# -*- coding: utf-8 -*-
"""[경혈해부] 수태음 시동병 대응 경혈 — 해부 유사도 그림 3종(계통수·히트맵 / 분절 매트릭스 / 체표 분포도).

사용: python make_figures.py <출력 폴더> [ko|en]
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, FancyBboxPatch, Patch, Polygon, Rectangle
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import dendrogram, fcluster

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1])
LANG = sys.argv[2] if len(sys.argv) > 2 else "ko"
plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft JhengHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

D = json.loads((HERE / "clusters.json").read_text(encoding="utf-8"))
codes = D["codes"]
Z = np.array(D["linkage"])
M = np.loadtxt(HERE / "similarity.csv", delimiter=",", skiprows=1)
INFO = D["info"]
FEAT = D["features"]
TRAD = {"太渊": "太淵", "经渠": "經渠", "列缺": "列缺", "尺泽": "尺澤", "侠白": "俠白", "孔最": "孔最", "天府": "天府",
        "中府": "中府", "少商": "少商", "三间": "三間", "商阳": "商陽", "前谷": "前谷", "神门": "神門", "阴郄": "陰郄",
        "天池": "天池", "天溪": "天谿", "辄筋": "輒筋", "膺窗": "膺窗", "乳根": "乳根", "期门": "期門", "步廊": "步廊",
        "神封": "神封", "灵墟": "靈墟", "神藏": "神藏", "俞府": "俞府", "鸠尾": "鳩尾", "玉堂": "玉堂", "璇玑": "璇璣",
        "天突": "天突", "人迎": "人迎", "缺盆": "缺盆", "肺俞": "肺俞", "厥阴俞": "厥陰俞", "膈俞": "膈俞", "大椎": "大椎",
        "肩井": "肩井", "大钟": "大鐘", "足临泣": "足臨泣"}


def lab(c):
    return f"{c} {TRAD.get(INFO[c]['name'], INFO[c]['name'])}"


T = {
    "ko": {
        "f1_title": "수태음 시동병 대응 38혈의 해부 유사도 계층(UPGMA)",
        "f1_sub": "유사도 = 0.35·신경 영역 + 0.30·척수 분절 + 0.20·FMA 구조 + 0.15·부위·구획 (가중 Jaccard) · 코페네틱 상관 {coph} · 등가중치 대비 군집 일치 ARI {ari}",
        "dist": "거리 (1 − 유사도)", "cut5": "대분류 절단(8군)", "cut12": "중분류 절단(12군)",
        "tier": {"I": "1층: 한대 단독 주치(2개 증상군 이상)", "II": "2층: 한대 1개 증상군·배오", "III": "3층: 후대 문헌만"},
        "sim": "해부 유사도",
        "f2_title": "척수 분절 매트릭스 — FMA 분절 + B1 규범 해부 보완",
        "f2_band1": "심장·폐 내장분절 T1–T5 (B1-02·B3-03)", "f2_band2": "심통 연관통 위팔 안쪽 C8–T1 (B3-03)",
        "f2_band3": "빗장위·목 연관 C3–C4 (가로막신경·빗장위신경)",
        "f2_fma": "FMA segmental_supply·신경 라벨", "f2_b1": "B1 보완(Gray's·Moore)", "f2_cn": "뇌신경",
        "f3_title": "체표 분포도 — 대분류 층위·주치 층(모양)·太淵 유사도(크기)",
        "front": "앞면", "back": "뒷면",
        "L1": {"A": "A 팔신경얼기 영역(상지·앞가슴벽)", "B1": "B1 등 흉추 옆·어깨 위", "B2": "B2 목 앞·빗장위", "C": "C 하지 원위", "D": "D 단독(鳩尾·玉堂·期門·大椎)"},
        "size": "원 크기 = 太淵(LU9)과의 유사도",
    },
    "en": {
        "f1_title": "Anatomical similarity hierarchy (UPGMA) of 38 points matching the Lung-meridian shidong disorder (是動病)",
        "f1_sub": "Similarity = 0.35·nerve territory + 0.30·spinal segments + 0.20·FMA structures + 0.15·region/compartment (weighted Jaccard) · cophenetic r {coph} · ARI vs equal weights {ari}",
        "dist": "Distance (1 − similarity)", "cut5": "Major cut (8 groups)", "cut12": "Intermediate cut (12 groups)",
        "tier": {"I": "Tier I: Han-era single-point indications (≥2 symptom groups)", "II": "Tier II: one Han-era group / combination",
                 "III": "Tier III: later texts only"},
        "sim": "Anatomical similarity",
        "f2_title": "Spinal-segment matrix — FMA segments + B1 normative-anatomy supplement",
        "f2_band1": "Cardiac & pulmonary viscerotome T1–T5 (B1-02, B3-03)", "f2_band2": "Cardiac referred pain, medial arm C8–T1 (B3-03)",
        "f2_band3": "Supraclavicular/neck referral C3–C4 (phrenic, supraclavicular nn.)",
        "f2_fma": "FMA segmental_supply / nerve label", "f2_b1": "B1 supplement (Gray's, Moore)", "f2_cn": "Cranial n.",
        "f3_title": "Surface map — major layer (colour), indication tier (shape), similarity to Taiyuan (size)",
        "front": "Anterior", "back": "Posterior",
        "L1": {"A": "A Brachial-plexus field (upper limb, anterior chest)", "B1": "B1 Paravertebral back & shoulder",
               "B2": "B2 Anterior neck & supraclavicular", "C": "C Distal lower limb", "D": "D Singletons (CV15, CV18, LR14, GV14)"},
        "size": "Marker size = similarity to Taiyuan (LU9)",
    },
}[LANG]

TIER_COL = {"I": "#c0392b", "II": "#e08e0b", "III": "#7f8c8d"}
lab5 = fcluster(Z, 8, "maxclust")  # 대분류 = 8군 절단
# 대분류 이름 붙이기: 구성원으로 판정
L1 = {}
for c, l in zip(codes, lab5):
    L1.setdefault(int(l), []).append(c)
L1_NAME = {}
for l, mem in L1.items():
    L1_NAME[l] = "A" if "LU9" in mem else "B1" if "BL13" in mem else "B2" if "ST12" in mem else "C" if "KI4" in mem else "D"
L1_COL = {"A": "#1f6fb2", "B1": "#2a9d8f", "B2": "#27ae60", "C": "#8e44ad", "D": "#b8860b"}
code_L1 = {c: L1_NAME[int(l)] for c, l in zip(codes, lab5)}


def fig1():
    fig = plt.figure(figsize=(17, 13), dpi=150)
    axd = fig.add_axes([0.04, 0.08, 0.20, 0.80])
    dn = dendrogram(Z, orientation="left", labels=[lab(c) for c in codes], ax=axd,
                    link_color_func=lambda k: "#555", leaf_font_size=9)
    order = [codes[i] for i in dn["leaves"]]
    axd.invert_yaxis()
    axd.set_xlabel(T["dist"])
    for side in ("top", "right", "left"):
        axd.spines[side].set_visible(False)
    axd.axvline(Z[-8, 2] + 1e-3, color="#c0392b", ls="--", lw=1)
    axd.axvline(Z[-12, 2] + 1e-3, color="#e08e0b", ls=":", lw=1)
    axd.text(Z[-8, 2] + 0.01, -1.0, T["cut5"], color="#c0392b", fontsize=8, ha="right")
    axd.text(Z[-12, 2] - 0.01, -1.0, T["cut12"], color="#e08e0b", fontsize=8, ha="left")
    for t in axd.get_yticklabels():
        c = t.get_text().split()[0]
        t.set_color(TIER_COL[INFO[c]["tier"]])
        t.set_fontweight("bold" if INFO[c]["tier"] == "I" else "normal")
    idx = [codes.index(c) for c in order]
    axh = fig.add_axes([0.335, 0.08, 0.56, 0.80])
    im = axh.imshow(M[np.ix_(idx, idx)], cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    axh.set_xticks(range(len(order)))
    axh.set_xticklabels(order, rotation=90, fontsize=8)
    axh.set_yticks([])
    for k, c in enumerate(order):
        axh.add_patch(Rectangle((-1.6, k - 0.5), 0.9, 1, color=TIER_COL[INFO[c]["tier"]], clip_on=False))
        axh.add_patch(Rectangle((len(order) - 0.3, k - 0.5), 0.9, 1, color=L1_COL[code_L1[c]], clip_on=False))
    cb = fig.add_axes([0.915, 0.30, 0.012, 0.4])
    fig.colorbar(im, cax=cb).set_label(T["sim"])
    fig.legend(handles=[Patch(color=TIER_COL[k], label=v) for k, v in T["tier"].items()] +
               [Patch(color=L1_COL[k], label=v) for k, v in T["L1"].items()],
               loc="lower center", ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(T["f1_title"], x=0.04, ha="left", fontsize=15, weight="bold", y=0.975)
    fig.text(0.04, 0.935, T["f1_sub"].format(coph=D["cophenetic"], ari=D["ari_weight_sensitivity"]), fontsize=9.5, color="#333")
    fig.savefig(OUT / f"Fig1_해부유사도_계층_히트맵_{LANG}.png", facecolor="white")
    plt.close(fig)
    return order


SEGS = [f"C{i}" for i in range(1, 9)] + [f"T{i}" for i in range(1, 13)] + [f"L{i}" for i in range(1, 6)] + [f"S{i}" for i in range(1, 5)]
CNS = ["CN VII", "CN X", "CN XI", "CN XII"]


def fig2(order):
    fig, ax = plt.subplots(figsize=(15, 13), dpi=150)
    cols = CNS + SEGS
    for r, c in enumerate(order):
        src = FEAT[c]["G_src"]
        for k, g in enumerate(cols):
            if g in CNS:
                if g in FEAT[c]["cranial"]:
                    ax.add_patch(Rectangle((k, r), 1, 1, color="#6c5ce7"))
                continue
            if g in src:
                fma = any(s in ("FMA", "FMA 라벨") for s in src[g])
                ax.add_patch(Rectangle((k, r), 1, 1, color="#1f6fb2" if fma else "#74b9ff"))
    t0, t5 = len(CNS) + SEGS.index("T1"), len(CNS) + SEGS.index("T5") + 1
    ax.add_patch(Rectangle((t0, -1.2), t5 - t0, len(order) + 1.4, fc="none", ec="#c0392b", lw=2.2, clip_on=False))
    c8 = len(CNS) + SEGS.index("C8")
    ax.add_patch(Rectangle((c8, -0.8), 2, len(order) + 0.8, fc="#f39c12", alpha=0.12, ec="#f39c12", lw=1.2, ls="--"))
    c3 = len(CNS) + SEGS.index("C3")
    ax.add_patch(Rectangle((c3, -0.8), 2, len(order) + 0.8, fc="#16a085", alpha=0.10, ec="#16a085", lw=1.2, ls=":"))
    ax.set_xlim(0, len(cols))
    ax.set_ylim(len(order), -1.5)
    ax.set_xticks(np.arange(len(cols)) + 0.5)
    ax.set_xticklabels([g.replace("CN ", "") if g in CNS else g for g in cols], fontsize=8.5)
    ax.set_yticks(np.arange(len(order)) + 0.5)
    ax.set_yticklabels([lab(c) for c in order], fontsize=9)
    for t, c in zip(ax.get_yticklabels(), order):
        t.set_color(TIER_COL[INFO[c]["tier"]])
    for k in range(len(cols) + 1):
        ax.axvline(k, color="#eee", lw=0.5)
    for k in range(len(order) + 1):
        ax.axhline(k, color="#eee", lw=0.5)
    ax.axvline(len(CNS), color="#333", lw=1)
    ax.text(len(CNS) / 2, -0.6, T["f2_cn"], ha="center", fontsize=9)
    ax.legend(handles=[Patch(color="#1f6fb2", label=T["f2_fma"]), Patch(color="#74b9ff", label=T["f2_b1"]),
                       Patch(color="#6c5ce7", label=T["f2_cn"]),
                       Patch(fc="none", ec="#c0392b", lw=2, label=T["f2_band1"]),
                       Patch(fc="#f39c12", alpha=0.3, label=T["f2_band2"]), Patch(fc="#16a085", alpha=0.3, label=T["f2_band3"])],
              loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=3, fontsize=9, frameon=False)
    ax.set_title(T["f2_title"], loc="left", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / f"Fig2_척수분절_매트릭스_{LANG}.png", facecolor="white")
    plt.close(fig)


# 체표 좌표(모식, 오른쪽 몸을 그림 왼쪽에 둔 앞면 / 뒷면) — B1-05 WHO 정위의 상대 위치만 반영, 축척 아님
FRONT = {"CV22": (50, 160), "CV21": (50, 154), "CV18": (50, 141), "CV15": (50, 121), "ST9": (44.5, 167), "ST12": (38, 157.5),
         "KI27": (44, 155), "KI25": (44, 146), "KI24": (44, 141.5), "KI23": (44, 137), "KI22": (44, 132.5),
         "LU1": (32, 151), "ST16": (38, 141.5), "ST18": (38, 128), "SP18": (29.5, 137), "PC1": (35, 135.5),
         "LR14": (38, 122), "GB23": (26.5, 131), "LU3": (21.5, 140), "LU4": (20.8, 135.5), "LU5": (16.5, 116),
         "LU6": (14.5, 104), "LU7": (11.3, 85), "LU8": (10.6, 82), "LU9": (10, 79), "HT6": (14.6, 81.5), "HT7": (14.9, 79),
         "LU11": (5.5, 63), "LI1": (8.2, 58), "LI3": (8.8, 66), "SI2": (14.6, 62), "KI4": (44.8, 9), "GB41": (36.5, 3)}
OFFSET = {"LU9": (-22, -10), "LU8": (-24, 0), "LU7": (-22, 10), "HT6": (14, 6), "HT7": (14, -8), "LU11": (-18, -4),
          "LI3": (-18, 6), "LI1": (-8, -12), "SI2": (8, -2), "LU3": (-14, 4), "LU4": (-16, -8), "LU5": (8, 0), "LU6": (9, 0),
          "ST16": (-16, 8), "KI24": (10, 10), "CV18": (24, 2), "CV21": (24, -4), "KI27": (-14, 6), "KI25": (10, 2),
          "SP18": (10, 12), "PC1": (2, -11), "KI23": (10, 3), "KI22": (10, 0), "ST18": (-14, -8), "GB23": (-16, -8),
          "LU1": (-14, 6), "ST12": (-14, 6), "CV22": (12, 6), "ST9": (12, 4), "LR14": (-14, -6), "CV15": (12, -4)}
BACK = {"GV14": (50, 162), "BL13": (56.5, 150), "BL14": (56.5, 146), "BL17": (56.5, 134), "GB21": (36, 161)}


def body(ax, x0):
    sk = dict(fc="#f7efe6", ec="#9c8a7a", lw=1.2)
    ax.add_patch(Ellipse((x0 + 50, 182), 17, 21, **sk))
    ax.add_patch(Polygon([(x0 + 46, 173), (x0 + 54, 173), (x0 + 56, 162), (x0 + 44, 162)], **sk))
    ax.add_patch(Polygon([(x0 + 26, 160), (x0 + 74, 160), (x0 + 72, 120), (x0 + 68, 95), (x0 + 70, 88), (x0 + 30, 88),
                          (x0 + 32, 95), (x0 + 28, 120)], **sk))
    for s in (1, -1):  # 팔
        xs = (lambda v: x0 + v) if s == 1 else (lambda v: x0 + 100 - v)
        ax.add_patch(Polygon([(xs(26), 160), (xs(19), 150), (xs(14), 115), (xs(8), 82), (xs(3), 66), (xs(6), 54),
                              (xs(16), 58), (xs(17), 78), (xs(20), 112), (xs(26), 140), (xs(29), 152)], **sk))
        ax.add_patch(Polygon([(xs(31), 88), (xs(49), 88), (xs(47), 50), (xs(46), 12), (xs(48), 2), (xs(34), 0),
                              (xs(36), 12), (xs(33), 50)], **sk))
    ax.plot([x0 + 50, x0 + 50], [88, 163], color="#cdbfb2", lw=0.8, ls="--")


def fig3():
    fig, ax = plt.subplots(figsize=(16, 15), dpi=150)
    body(ax, 0)
    body(ax, 110)
    # 앞가슴 T1–T5 피절 띠(B1-03 근사)
    for y0, y1, g in ((156, 150, "T1"), (150, 144, "T2"), (144, 138, "T3"), (138, 132, "T4"), (132, 126, "T5")):
        ax.add_patch(Rectangle((28.5, y1), 43, y0 - y1, fc="#c0392b", alpha=0.05 + 0.02 * int(g[1]), ec="none"))
        ax.text(72.5, (y0 + y1) / 2, g, fontsize=7, color="#c0392b", va="center")
    sims = {r: M[codes.index(r), codes.index("LU9")] for r in codes}
    marker = {"I": "o", "II": "s", "III": "^"}
    for pts, dx in ((FRONT, 0), (BACK, 110)):
        for c, (x, y) in pts.items():
            if c not in codes:
                continue
            ax.scatter(x + dx, y, s=40 + 260 * sims[c], marker=marker[INFO[c]["tier"]], color=L1_COL[code_L1[c]],
                       edgecolor="black", linewidth=0.7, zorder=5, alpha=0.9)
            off = OFFSET.get(c, (5, 3))
            ax.annotate(lab(c), (x + dx, y), xytext=off, textcoords="offset points", fontsize=7.6, zorder=6,
                        ha="right" if off[0] < 0 else "left", va="center",
                        arrowprops=dict(arrowstyle="-", color="#777", lw=0.5) if abs(off[0]) > 12 or abs(off[1]) > 9 else None,
                        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
    ax.text(50, 207, T["front"], ha="center", fontsize=12, weight="bold")
    ax.text(160, 207, T["back"], ha="center", fontsize=12, weight="bold")
    ax.set_xlim(-5, 215)
    ax.set_ylim(-5, 212)
    ax.set_aspect("equal")
    ax.axis("off")
    h = [Patch(color=L1_COL[k], label=v) for k, v in T["L1"].items()]
    h += [Line2D([], [], marker=marker[k], ls="", color="#555", markeredgecolor="black", markersize=9, label=v)
          for k, v in T["tier"].items()]
    h += [Line2D([], [], ls="", label=T["size"])]
    ax.legend(handles=h, loc="lower right", fontsize=9, frameon=True, bbox_to_anchor=(1.0, 0.0))
    ax.set_title(T["f3_title"], loc="left", fontsize=14, weight="bold")
    fig.savefig(OUT / f"Fig3_체표분포도_{LANG}.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    order = fig1()
    fig2(order)
    fig3()
    (HERE / "leaf_order.json").write_text(json.dumps(order), encoding="utf-8")
    print("ok", LANG, order)

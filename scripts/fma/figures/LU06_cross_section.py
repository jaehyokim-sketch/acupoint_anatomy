# -*- coding: utf-8 -*-
"""공최(LU06) T1 자침 높이(완횡문 상 7寸) 아래팔 앞면 중간부 횡단면 해부 모식도.

오른팔 해부학적 자세(전완 회외·손바닥 앞), 몸쪽에서 먼쪽을 봄(위에서 내려다봄).
앞쪽 = 위, 노쪽(가쪽) = 오른쪽, 자쪽(안쪽) = 왼쪽.

겉모양(가로 ≈ 63mm · 앞뒤 ≈ 45mm)은 성인 전완 중간부 규범 치수를 근사한 개략 축척이고,
각 구조의 경계·깊이는 LU6 실측값이 아니다. 자침 깊이 띠만 한대(漢代) 2.3mm/푼 환산값을
단면과 같은 mm 축척으로 그린다.

사용: python LU06_cross_section.py [out1.png out2.png ...]
      인자가 없으면 보고서 폴더와 스크립트 폴더 두 곳에 저장한다.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]  # 간체자(泽·针·经 등)는 YaHei로 대체
plt.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_OUT = [
    REPO / "01_경혈별_해부생리_분석보고서" / "LU_수태음폐경" / "LU06_공최" / "LU06_공최_횡단면_해부모식도.png",
    HERE / "LU06_cross_section.png",
]
OUTS = [Path(a) for a in sys.argv[1:]] or DEFAULT_OUT

# ── 색 ────────────────────────────────────────────────────────────────────────
SKIN_FC, SKIN_EC = "#f6dccb", "#b07a5a"
SUBQ_FC = "#fbeee6"
L2_FC, L2_EC = "#dd6a60", "#8f2d2a"          # Layer 2 근막·표층근
L3_FC, L3_EC = "#c5805c", "#7a4a2e"          # Layer 3 중간·심층근
NA_FC, NA_EC = "#cfc3b8", "#8a7d72"          # 교재 미기재(해부 맥락용)
BONE_FC, BONE_EC = "#efe8d2", "#7d6f4f"      # Layer 5 뼈·골막
IOM_C = "#6d5f8f"
ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
CLASSIC, MODERN = "#0e9488", "#d62828"       # 고전 3푼 / 현대 0.5~1寸
TXT_M, TXT_N, TXT_V, TXT_B = "#8f2d2a", "#8a6d00", "#2f5fb3", "#5b4f33"
GREY = "#5f6672"


def chaikin(pts, n=4):
    p = np.asarray(pts, float)
    for _ in range(n):
        q = p * 0.75 + np.roll(p, -1, 0) * 0.25
        r = p * 0.25 + np.roll(p, -1, 0) * 0.75
        p = np.empty((len(p) * 2, 2))
        p[0::2], p[1::2] = q, r
    return p


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, alpha=1.0, ls="-", n=4):
    ax.add_patch(Polygon(chaikin(pts, n), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls))


# ── 도면 틀 ───────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(16.5, 13.4), dpi=170)
ax = fig.add_axes([0.0, 0.375, 1.0, 0.615])      # 16.50 x 8.241 in → 가로:세로 = 2.0023
ax.set_xlim(-78, 82)
ax.set_ylim(-41.4, 38.5)                          # 160.0 / 2.0023 = 79.9 → 축척 왜곡 없음
ax.set_aspect("equal", adjustable="datalim")
ax.axis("off")

# ── Layer 1 피부·피하 / 심부근막 ───────────────────────────────────────────────
skin = [(0, 22), (9, 21.5), (18, 19), (25, 14.5), (30, 8), (32, 0), (31, -8), (27, -15),
        (19, -20), (8, -22.5), (-4, -23), (-15, -21), (-24, -16), (-30, -8), (-32, 1),
        (-29, 10), (-22, 17), (-11, 21)]
blob(ax, skin, SKIN_FC, SKIN_EC, 1.7, 1.0)                                              # 피부·피하조직
blob(ax, [(x * 0.90, y * 0.90 - 0.6) for x, y in skin], SUBQ_FC, "#8a6a55", 1.0, 1.4, ls="--")  # 아래팔근막

# ── Layer 5 뼈·뼈사이막 ───────────────────────────────────────────────────────
blob(ax, [(10, -5.5), (16, -3.5), (23, -7.5), (24, -13.5), (17.5, -16.5), (10.5, -12.5)],
     BONE_FC, BONE_EC, 1.4, 4.0, n=2)                                                   # 노뼈 Radius
blob(ax, [(14, -6.5), (19, -9), (16, -12.5), (12.5, -10)], "#f9f5e8", "#bfb391", 0.6, 4.3, n=2)  # 노뼈 골수강
blob(ax, [(-13, -4.5), (-15, -11.5), (-20, -16), (-25, -12), (-24, -6), (-18, -3)],
     BONE_FC, BONE_EC, 1.4, 4.0, n=2)                                                   # 자뼈 Ulna
blob(ax, [(-17, -7), (-19, -12), (-22.5, -10.5), (-21, -6.5)], "#f9f5e8", "#bfb391", 0.6, 4.3, n=2)
ax.plot([-13.2, -6, 2, 10.2], [-7.6, -8.6, -8.9, -8.6], color=IOM_C, lw=2.4, zorder=4.2, solid_capstyle="round")

# ── 뒤칸(교재 미기재, 해부 맥락용) ─────────────────────────────────────────────
blob(ax, [(23.5, -3.5), (28, -5.5), (28.5, -11), (24.5, -15.5), (21, -12), (21.5, -6.5)],
     NA_FC, NA_EC, 0.9, 2.8, ls=":")                                                    # 긴·짧은노쪽손목폄근
blob(ax, [(16.5, -8.5), (21, -9.5), (21.5, -13), (17, -14), (14.5, -11)],
     NA_FC, NA_EC, 0.9, 2.9, ls=":")                                                    # 긴엄지벌림근·짧은엄지폄근
blob(ax, [(-2, -12), (10, -11.5), (19, -12.5), (22, -16.5), (15.5, -19.5), (4, -19.5), (-4, -16)],
     NA_FC, NA_EC, 0.9, 2.7, ls=":")                                                    # 손가락폄근·새끼폄근
blob(ax, [(-6.5, -14), (-2, -16.5), (-4.5, -20.5), (-11.5, -21), (-15, -18), (-14, -14)],
     NA_FC, NA_EC, 0.9, 2.8, ls=":")                                                    # 자쪽손목폄근

# ── Layer 3 중간·심층근 ───────────────────────────────────────────────────────
blob(ax, [(-10, 10.5), (-2, 12.5), (6.5, 10), (9.5, 3.5), (4, -1.5), (-6, -2), (-13, 1.5), (-14.5, 6)],
     L3_FC, L3_EC, 1.1, 2.6, ls="--")                                                   # 얕은손가락굽힘근 [김재효]
blob(ax, [(5.5, 2), (13, 3), (17, -1), (15, -5.5), (8, -5.5), (4.5, -2)],
     L3_FC, L3_EC, 1.1, 2.9, ls="--")                                                   # 긴엄지굽힘근 [김재효]
blob(ax, [(-5, 1), (-12, 2), (-18, 0), (-20.5, -5), (-15, -8.5), (-8, -6.5), (-4.5, -3)],
     NA_FC, NA_EC, 0.9, 2.7, ls=":")                                                    # 깊은손가락굽힘근(미기재)

# ── Layer 2 근막·표층근 ───────────────────────────────────────────────────────
blob(ax, [(15, 13.5), (20.5, 14.2), (26, 9.5), (27.8, 3.5), (25, -0.5), (19, 0.5), (15, 5.5)],
     L2_FC, L2_EC, 1.2, 3.0)                                                            # 위팔노근
blob(ax, [(19.5, -0.5), (23.5, -1.5), (24, -5), (20.5, -5.5), (18.5, -3)],
     "#e39082", L2_EC, 1.1, 3.1)                                                        # 원엎침근 정지 건성부
blob(ax, [(6.5, 15.8), (12.5, 14.8), (15.5, 9.5), (12, 5), (6.5, 5.5), (4, 10.5)],
     L2_FC, L2_EC, 1.2, 3.0)                                                            # 노쪽손목굽힘근
blob(ax, [(1, 18), (5, 17.5), (5.5, 13), (2, 11.5), (-1.5, 13.5)],
     "#e8857a", L2_EC, 1.1, 3.0, ls="--")                                               # 긴손바닥근 [공통교재]
blob(ax, [(-8, 15.5), (-14, 16.5), (-21, 13), (-24, 6), (-21, 1), (-14, 3), (-9, 8)],
     "#e8857a", L2_EC, 1.1, 3.0, ls="--")                                               # 자쪽손목굽힘근 [공통교재]


def dot(x, y, r, fc, ec="#333", z=6, lw=0.8):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=lw, zorder=z))


# ── Layer 4 신경혈관속 + 부수 신경혈관 ────────────────────────────────────────
dot(10.2, 4.7, 1.95, ART, z=6.3)                                                        # 노동맥
dot(7.7, 3.9, 1.2, VEIN); dot(12.7, 3.5, 1.2, VEIN)                                     # 노정맥(동반정맥)
dot(14.9, 5.8, 1.75, NERVE, z=6.3)                                                      # 노신경 얕은가지
dot(-15.6, 2.4, 1.6, ART); dot(-17.9, 1.4, 1.0, VEIN); dot(-13.3, 1.2, 1.0, VEIN)       # 자동맥·동반정맥
dot(-19.6, 3.4, 1.55, NERVE)                                                            # 자신경
dot(-3.4, 0.3, 1.75, NERVE)                                                             # 정중신경
dot(-1.6, -5.6, 1.15, ART); dot(1.4, -5.6, 1.25, NERVE)                                 # 앞뼈사이 동맥·신경
dot(-1.2, -10.6, 1.1, ART); dot(1.8, -10.6, 1.2, NERVE)                                 # 뒤뼈사이 동맥·신경
dot(25.6, 12.4, 1.6, NERVE)                                                             # 가쪽아래팔피부신경
dot(28.6, 7.3, 2.1, VEIN)                                                               # 노쪽피부정맥
dot(29.4, -1.2, 1.45, VEIN)                                                             # 덧노쪽피부정맥
dot(-2.0, 19.6, 1.7, VEIN)                                                              # 정중앞팔정맥
dot(-26.4, 9.2, 2.0, VEIN)                                                              # 자쪽피부정맥
dot(-28.6, 2.6, 1.45, NERVE)                                                            # 안쪽아래팔피부신경


# ── 자침선(T1) ────────────────────────────────────────────────────────────────
# 자입점 E는 노동맥(10.2, 4.7)을 지나는 직자축이 매끈해진 피부 윤곽을 뚫는 지점(수치해로 고정).
# 이 배치에서 노동맥은 피부에서 약 15.9mm 깊이에 놓여, 0.5寸(11.5mm)으로는 못 미치고 1寸(23.0mm)이면 지난다.
E = np.array([15.905, 19.486])         # 피부 자입점(위팔노근 내측연)
D = np.array([-0.360, -0.933])         # 피부면 수직 직자 방향
P = np.array([0.933, -0.360])          # 자침축의 법선


def at(z):
    return E + D * z


Z_CLASSIC, Z_MOD_LO, Z_MOD_HI = 6.9, 11.5, 23.0
for z0, z1, c, a in [(0, Z_CLASSIC, CLASSIC, 0.62), (Z_CLASSIC, Z_MOD_LO, "#9aa3ad", 0.45),
                     (Z_MOD_LO, Z_MOD_HI, MODERN, 0.55)]:
    (x0, y0), (x1, y1) = at(z0), at(z1)
    ax.plot([x0, x1], [y0, y1], color=c, lw=8.5, alpha=a, solid_capstyle="butt", zorder=5.5)
ax.plot(*zip(at(-7.5), at(Z_MOD_HI)), color="#1f2328", lw=1.3, zorder=7.2)
ax.add_patch(FancyArrowPatch(at(Z_MOD_HI - 4.0), at(Z_MOD_HI), arrowstyle="-|>", mutation_scale=15,
                             lw=1.3, color="#1f2328", zorder=7.3))
for z in (0, Z_CLASSIC, Z_MOD_LO, Z_MOD_HI):                                 # 깊이 눈금
    a0, a1 = at(z) - P * 4.4, at(z) - P * 2.2
    ax.plot([a0[0], a1[0]], [a0[1], a1[1]], color="#3c434d", lw=0.9, zorder=7.1)
for z, txt, c in [(Z_CLASSIC, "6.9mm", "#0b6a62"), (Z_MOD_HI, "23.0mm", MODERN)]:
    t = at(z) - P * 6.4
    ax.text(t[0], t[1], txt, fontsize=8.2, weight="bold", color=c, ha="right", va="center", zorder=7.6,
            bbox=dict(boxstyle="round,pad=0.22", fc="#ffffff", ec=c, lw=0.7, alpha=0.92))
ax.add_patch(Circle(E, 1.15, fc="#ffffff", ec="#1f2328", lw=1.3, zorder=7.4))

# 자침 깊이 안내 상자
ax.add_patch(FancyBboxPatch((-36.0, 23.8), 54.0, 8.8, boxstyle="round,pad=0.6,rounding_size=1.6",
                            fc="#ffffff", ec="#9aa3ad", lw=1.0, zorder=9))
ax.text(-34.0, 30.6, "LU6 공최 자침점 (T1, 腕上七寸 · 위팔노근 내측연 직자)",
        fontsize=11.0, weight="bold", color="#1f2328", va="center", zorder=10)
for i, (c, txt) in enumerate([
        (CLASSIC, "고전 3푼 = 6.9mm — ① 피부·피하 ~ ② 근막·표층근 상연에 머묾"),
        (MODERN, "현대 0.5~1寸 = 11.5~23.0mm — ④ 노동·정맥·노신경 얕은가지 도달 가능")]):
    y = 27.8 - i * 2.6
    ax.plot([-33.8, -30.2], [y, y], color=c, lw=6.2, alpha=0.6, solid_capstyle="butt", zorder=10)
    ax.text(-29.2, y, txt, fontsize=8.6, color="#1f2328", va="center", zorder=10)
ax.add_patch(FancyArrowPatch((12.0, 24.2), (E[0] + 0.7, E[1] + 1.7), arrowstyle="-|>", mutation_scale=12,
                             lw=1.1, color="#5f6672", zorder=9.5, connectionstyle="arc3,rad=-0.25"))


def lab(x, y, tx, ty, text, color="#222", fs=8.5, extra=None):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=10,
                ha="left" if tx > x else "right", va="center", linespacing=1.45,
                arrowprops=dict(arrowstyle="-", lw=0.65, color="#8b929c", shrinkA=0, shrinkB=1.5))
    if extra:
        ax.annotate("", xy=extra, xytext=(tx + (1.2 if tx > x else -1.2), ty),
                    arrowprops=dict(arrowstyle="-", lw=0.65, color="#8b929c", shrinkA=0, shrinkB=1.5), zorder=9.8)


R, L = 34.0, -34.0
# 가쪽(노쪽) 계열 — 오른쪽
lab(25.6, 12.4, R, 30.0, "① 가쪽아래팔피부신경 Lateral cutaneous n. of forearm  FMA:39080  [공통]", TXT_N)
lab(28.6, 7.3, R, 24.92, "① 노쪽피부정맥 Cephalic v.  FMA:13324  [공통]", TXT_V)
lab(29.4, -1.2, R, 19.83, "① 덧노쪽피부정맥 Accessory cephalic v.  FMA:22970  [공통]", TXT_V)
lab(22.0, 8.0, R, 14.75, "② 위팔노근 Brachioradialis  FMA:38485  [공통]\n    노신경 지배 · 분절 C6(주)·C5", TXT_M)
lab(10.0, 11.0, R, 9.67, "② 노쪽손목굽힘근 Flexor carpi radialis  FMA:38459  [공통]\n    정중신경 지배 · 분절 C6(주)·C7", TXT_M)
lab(14.9, 5.8, R, 4.58, "④ 노신경 얕은가지 Superficial branch of radial n.  FMA:292885  [공통]", TXT_N)
lab(10.2, 4.7, R, -0.5, "④ 노동맥·노정맥 Radial a. / v.  FMA:22730 · 22947  [공통]", "#b02020")
lab(21.3, -3.2, R, -5.58, "② 원엎침근 Pronator teres  FMA:38450  [공통] · 분절 C7(주)·C6\n    (이 높이에서는 노뼈 가쪽 정지 건성부)", TXT_M)
lab(11.0, -1.5, R, -10.67, "③ 긴엄지굽힘근 Flexor pollicis longus  FMA:38481  [김재효]\n    (교재 표기 '깊은엄지굽힘근') · 앞뼈사이신경 · 분절 C8(주)·C7", TXT_M)
lab(17.0, -10.0, R, -15.75, "⑤ 노뼈 Radius  FMA:23463 (앞면 골막 = Layer 5)", TXT_B)
lab(25.0, -9.5, R, -20.83, "긴·짧은노쪽손목폄근 ECRL·ECRB (뒤칸, 교재 미기재)", GREY)
lab(18.0, -11.2, R, -25.92, "긴엄지벌림근·짧은엄지폄근 APL·EPB (뒤칸, 교재 미기재)", GREY)
lab(12.0, -15.5, R, -31.0, "손가락폄근·새끼폄근 EDC·EDM (뒤칸, 교재 미기재)", GREY)
# 안쪽(자쪽) 계열 — 왼쪽
lab(-2.0, 19.6, L, 23.0, "정중앞팔정맥 Median antebrachial v. (교재 미기재)", TXT_V)
lab(2.5, 15.0, L, 17.9, "② 긴손바닥근 Palmaris longus  FMA:38462  [공통교재 단독]", TXT_M)
lab(-17.0, 10.0, L, 12.8, "② 자쪽손목굽힘근 Flexor carpi ulnaris  FMA:38465  [공통교재 단독]\n    자신경 지배 · 분절 C8(주)·C7·T1", TXT_M)
lab(-26.4, 9.2, L, 7.7, "① 자쪽피부정맥 Basilic v. · 안쪽아래팔피부신경 (교재 미기재)", TXT_V, extra=(-28.6, 2.6))
lab(-16.5, 2.2, L, 2.6, "자동맥·자신경 Ulnar a. / n. (자쪽손목굽힘근 밑, 교재 미기재)", GREY)
lab(-8.0, 6.5, L, -2.5, "③ 얕은손가락굽힘근 Flexor digitorum superficialis  FMA:38469  [김재효]\n    정중신경 지배 · 분절 C8(주)·T1", TXT_M)
lab(-3.4, 0.3, L, -7.6, "정중신경 Median n.  FMA:14385 (FDS–FDP 사이, 교재 미기재)", TXT_N)
lab(-14.0, -3.5, L, -12.7, "깊은손가락굽힘근 FDP (교재 미기재)", GREY)
lab(-1.6, -5.6, L, -17.8, "앞·뒤뼈사이 신경혈관다발 (뼈사이막 앞·뒤, 교재 미기재)", GREY, extra=(-1.2, -10.6))
lab(-19.0, -10.0, L, -22.9, "⑤ 자뼈 Ulna  FMA:23466 · 뼈사이막 Interosseous membrane  FMA:35187", TXT_B,
    extra=(-6.0, -8.75))
lab(-9.0, -17.0, L, -28.0, "자쪽손목폄근 ECU (뒤칸, 교재 미기재)", GREY)

# ── 제목 ──────────────────────────────────────────────────────────────────────
ax.text(-76, 38.0, "공최(孔最, LU06) T1 자침 높이 — 아래팔 앞면 중간부(완횡문 상 7寸) 횡단면 해부 실체 모식도",
        fontsize=16.2, weight="bold", va="top")
ax.text(-76, 35.0,
        "오른팔 해부학적 자세(전완 회외·손바닥 앞) · 몸쪽에서 먼쪽을 봄(위에서 내려다봄) · "
        "앞쪽 = 위, 노쪽(가쪽) = 오른쪽, 자쪽(안쪽) = 왼쪽",
        fontsize=9.8, color="#444", va="top")

# ── 범례 ──────────────────────────────────────────────────────────────────────
for i, (fc, ec, ls, t) in enumerate([
        (SKIN_FC, SKIN_EC, "-", "① 피부·피하"), (L2_FC, L2_EC, "-", "② 근막·표층근"),
        (L3_FC, L3_EC, "-", "③ 중간·심층근"), (BONE_FC, BONE_EC, "-", "⑤ 뼈·골막"),
        (NA_FC, NA_EC, ":", "교재 미기재")]):
    x = -31.5 + i * 13.0
    ax.add_patch(Rectangle((x, -35.6), 3.2, 2.4, fc=fc, ec=ec, lw=1.0, ls=ls, zorder=9))
    ax.text(x + 4.0, -34.4, t, fontsize=8.6, va="center", zorder=9)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    x = -31.0 + i * 10.0
    dot(x, -39.4, 1.5, c, z=9)
    ax.text(x + 2.6, -39.4, t, fontsize=8.6, va="center", zorder=9)
ax.plot([3, 13], [-39.4, -39.4], color="#1f2328", lw=2.0, zorder=9, solid_capstyle="butt")
for xx in (3, 13):
    ax.plot([xx, xx], [-38.5, -40.3], color="#1f2328", lw=1.2, zorder=9)
ax.text(8, -37.3, "10 mm", fontsize=8.4, ha="center", zorder=9)
ax.text(18, -39.4, "④ 신경혈관속은 점(동맥·정맥·신경)으로 표시", fontsize=8.6, va="center", zorder=9)

# ── T2 대비 패널 ──────────────────────────────────────────────────────────────
ax2 = fig.add_axes([0.028, 0.145, 0.950, 0.215])
ax2.set_xlim(-14, 428)
ax2.set_ylim(-14, 15)
ax2.axis("off")
ax2.add_patch(FancyBboxPatch((-11, -13.0), 436, 27.6, boxstyle="round,pad=0.4,rounding_size=2.0",
                             fc="#fbfaf8", ec="#c9cfd8", lw=1.1, zorder=0))
ax2.text(-6, 13.5, "대비 — T2 泽田(사와다) 공최는 단면 높이 자체가 다르다 (아래팔 근위부)",
         fontsize=11.6, weight="bold", va="center", zorder=3)

# 전완 긴축 모식(尺泽 0mm → 太渊 250mm, 12寸 골도 250mm 가정)
LIMB_Y = 0.5
ax2.add_patch(Polygon(chaikin([(0, LIMB_Y + 4.2), (120, LIMB_Y + 3.5), (250, LIMB_Y + 2.3),
                               (250, LIMB_Y - 2.3), (120, LIMB_Y - 3.5), (0, LIMB_Y - 4.2)], 3),
                      closed=True, fc=SKIN_FC, ec=SKIN_EC, lw=1.2, zorder=1))
ax2.add_patch(Rectangle((42, LIMB_Y - 4.0), 20, 8.0, fc=CLASSIC, ec="none", alpha=0.22, zorder=1.5))
ax2.plot([52, 52], [LIMB_Y - 4.0, LIMB_Y + 4.0], color=CLASSIC, lw=1.7, ls=(0, (4, 2)), zorder=2)
ax2.plot([75, 75], [LIMB_Y - 3.8, LIMB_Y + 3.8], color="#8b929c", lw=1.3, ls=(0, (2, 2)), zorder=2)
ax2.plot([104, 104], [LIMB_Y - 5.4, LIMB_Y + 5.4], color=MODERN, lw=2.1, zorder=2)
for x, t, ha in [(0, "尺泽 LU5", "left"), (250, "太渊 LU9", "right")]:
    ax2.plot([x, x], [LIMB_Y - 5.0, LIMB_Y + 5.0], color="#5b4f33", lw=1.5, zorder=2)
    ax2.text(x, -5.2, t, fontsize=8.4, ha=ha, va="top", color="#5b4f33", weight="bold", zorder=3)
ax2.text(6, 11.0, "T2 泽田 공최 — 尺泽下 3横指 (약 2~3寸)\n촉진 취혈: 압통·경결·함하팽륭(魄門 진단 반응점)",
         fontsize=8.5, ha="left", va="top", color="#0b6a62", weight="bold", linespacing=1.55, zorder=3)
ax2.text(120, 11.0, "T1 표준 공최 (완상 7寸 = 尺泽下 5寸)\n▲ 위 횡단면의 높이",
         fontsize=8.8, ha="left", va="top", color=MODERN, weight="bold", linespacing=1.55, zorder=3)
ax2.text(75, -5.2, "근현대 10寸 골도의 '완상 7寸'\n(≈ 尺泽下 3寸) — 讹传 이식 경유점",
         fontsize=8.0, ha="center", va="top", color="#6b7280", linespacing=1.5, zorder=3)
ax2.annotate("", xy=(104, -10.2), xytext=(52, -10.2),
             arrowprops=dict(arrowstyle="<->", lw=1.1, color="#3c434d"), zorder=3)
ax2.text(78, -11.9, "Δ ≈ 2~3寸 ≈ 42~62mm  ≫ 15mm → 분기(보고서 7절)",
         fontsize=8.4, ha="center", va="center", color="#3c434d", zorder=3)
ax2.text(-10, -8.8, "12寸 골도 250mm 가정", fontsize=7.6, ha="left", va="top",
         color="#8b929c", zorder=3)

ax2.plot([268, 268], [-11.5, 12.6], color="#c9cfd8", lw=1.0, zorder=2)
ax2.text(276, 12.2, "T2 높이(아래팔 근위부)의 해부 실체 — 위 횡단면에는 존재하지 않는다",
         fontsize=9.0, weight="bold", va="top", color="#1f2328", zorder=3)
ax2.text(276, 8.4,
         "· 표층: 위팔노근(FMA:38485)과 원엎침근(FMA:38450) 근위부 사이의 경계 함요처\n"
         "· 심층: 노신경 줄기(FMA:37069) → 얕은가지(FMA:292885)·깊은가지 분기점\n"
         "· 노쪽되돌이동맥(radial recurrent a.) 주행 — 직자 시 직접 접촉 가능(SI 50)\n"
         "· 피하: 가쪽아래팔피부신경(FMA:39080)\n"
         "· 취혈 원리: 골도 수치가 아니라 손가락 촉진으로 병리 반응점을 포착(아시혈적)\n"
         "· 2대 교재 미수록 · 실측 없음 → B-Check 4/12, ARI-Core 35 (D·H, 가설)",
         fontsize=8.3, va="top", color="#2b313a", linespacing=1.62, zorder=3)

# ── 주석 ──────────────────────────────────────────────────────────────────────
ax3 = fig.add_axes([0.028, 0.004, 0.950, 0.135])
ax3.set_xlim(0, 1)
ax3.set_ylim(0, 1)
ax3.axis("off")
ax3.text(0.0, 1.0,
         "테두리 약속 — 실선: 2대 교재 공통 기재 구조 · 파선: 한 교재만 기재([공통교재 단독] / [김재효]) · "
         "점선 회색: 교재 미기재(해부 맥락용 참조 구조). ①~⑤는 보고서 4절 Layer 순서.\n"
         "자침 — 위팔노근 내측연에서 피부면에 수직으로 직자. 고전 3푼(《黄帝明堂经》 \"刺入三分\" = 6.9mm)은 "
         "① 피부·피하 ~ ② 근막·표층근 상연에 머문다.\n"
         "          현대 상한 1寸(23.0mm)은 위팔노근 밑 ④ 노동맥·노정맥·노신경 얕은가지에 이를 수 있으므로, "
         "박동을 확인하고 깊이를 조절하거나 사자한다(보고서 5절, SI 75).\n"
         "T2 대비 — 泽田 공최(尺泽下 3横指 ≒ 2~3寸, 《针灸真髓》 1941)는 아래팔 근위부여서 이 단면에 나타나지 않는다. "
         "위 패널로 높이 차와 심부 구조 차이를 대비한다(보고서 7절·10-2절).\n"
         "근거·한계 — 구조명과 교재 귀속은 2대 교재 데이터셋, FMA ID·지배신경·척수분절은 "
         "FMA 5.1.0(nerve_supply · segmental_supply) 기준.\n"
         "          겉모양(가로 ≈ 63mm · 앞뒤 ≈ 45mm)과 자침 깊이 띠는 같은 mm 축척이나, "
         "각 구조의 경계·깊이는 LU6 실측값이 아닌 모식 배치이다.",
         fontsize=8.5, color="#333", va="top", linespacing=1.72)

for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor="white")
    print("saved", out)

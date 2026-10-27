# -*- coding: utf-8 -*-
"""내관(PC06) 자침 높이(완횡문 상 2寸) 아래팔 원위부 횡단면 해부 모식도.

오른팔 해부학적 자세(전완 회외·손바닥 앞), 몸쪽에서 먼쪽을 봄(위에서 내려다봄).
앞쪽(손바닥) = 위, 노쪽(가쪽·엄지) = 오른쪽, 자쪽(안쪽·새끼손가락) = 왼쪽.

겉모양(가로 ≈ 56mm · 앞뒤 ≈ 32mm)은 성인 전완 원위부 규범 치수를 근사한 개략 축척이고,
각 구조의 경계·깊이는 PC06 표준 해부 실측 배치이다. 자침 깊이 띠는 한대(漢代) 2.3mm/푼 환산값을
단면과 같은 mm 축척으로 그린다.

사용: python PC06_cross_section.py [out1.png out2.png ...]
      인자가 없으면 보고서 폴더와 스크립트 폴더 두 곳에 저장한다.
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_OUT = [
    REPO / "01_경혈별_해부생리_분석보고서" / "PC_수궐음심포경" / "PC06_내관" / "PC06_내관_횡단면_해부모식도.png",
    HERE / "PC06_cross_section.png",
]
OUTS = [Path(a) for a in sys.argv[1:]] or DEFAULT_OUT

# ── 색 ────────────────────────────────────────────────────────────────────────
SKIN_FC, SKIN_EC = "#f6dccb", "#b07a5a"
SUBQ_FC = "#fbeee6"
L2_FC, L2_EC = "#dd6a60", "#8f2d2a"          # Layer 2 근막·표층근/건
L3_FC, L3_EC = "#c5805c", "#7a4a2e"          # Layer 3 중간·심층근
NA_FC, NA_EC = "#cfc3b8", "#8a7d72"          # 교재 미기재(해부 맥락용)
BONE_FC, BONE_EC = "#efe8d2", "#7d6f4f"      # Layer 5 뼈·골막
IOM_C = "#6d5f8f"
ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
CLASSIC_3, CLASSIC_5, MODERN = "#0e9488", "#2563eb", "#d62828"  # 고전 3푼 / 고전 5푼 / 현대 1寸
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
ax = fig.add_axes([0.0, 0.375, 1.0, 0.615])
ax.set_xlim(-78, 82)
ax.set_ylim(-41.4, 38.5)
ax.set_aspect("equal", adjustable="datalim")
ax.axis("off")

# ── Layer 1 피부·피하 / 심부근막 (원위부 타원형 전완 단면) ───────────────────────
skin = [(0, 15.2), (8, 14.8), (16, 13.6), (23, 10.6), (27.5, 5.0), (28.2, 0.0), (27.0, -5.5), (22.5, -11.0),
        (15.5, -14.2), (6.5, -15.5), (-2.5, -15.5), (-11.5, -14.4), (-19.0, -11.8), (-25.0, -6.8), (-27.2, 0.0),
        (-26.0, 6.0), (-21.0, 11.4), (-11.5, 14.2)]
blob(ax, skin, SKIN_FC, SKIN_EC, 1.7, 1.0)                                              # 피부·피하조직
blob(ax, [(x * 0.91, y * 0.91 - 0.2) for x, y in skin], SUBQ_FC, "#8a6a55", 1.0, 1.4, ls="--")  # 아래팔근막

# ── Layer 5 뼈·뼈사이막 ───────────────────────────────────────────────────────
# 노뼈 Radius (원위 골간단: 삼각형-사각 단면, 앞면은 오목)
blob(ax, [(10.5, -3.5), (15.5, -2.5), (22.5, -4.5), (24.0, -10.5), (18.5, -13.5), (11.5, -10.5)],
     BONE_FC, BONE_EC, 1.4, 4.0, n=2)
blob(ax, [(14.0, -5.0), (18.5, -6.5), (17.0, -10.5), (13.5, -8.5)], "#f9f5e8", "#bfb391", 0.6, 4.3, n=2)

# 자뼈 Ulna (원위부 원형-타원형 단면)
blob(ax, [(-13.5, -3.5), (-15.5, -9.5), (-21.0, -12.5), (-23.5, -8.0), (-21.5, -3.5), (-16.5, -2.5)],
     BONE_FC, BONE_EC, 1.4, 4.0, n=2)
blob(ax, [(-16.0, -5.0), (-18.0, -9.0), (-20.5, -7.5), (-19.0, -4.5)], "#f9f5e8", "#bfb391", 0.6, 4.3, n=2)

# 뼈사이막 (Interosseous membrane)
ax.plot([-13.5, -7.0, 1.0, 10.5], [-6.5, -7.5, -7.8, -7.0], color=IOM_C, lw=2.4, zorder=4.2, solid_capstyle="round")

# 네모엎침근 (Pronator quadratus, FMA:38453) — 노뼈·자뼈 앞면을 연결하는 심층 평판근
blob(ax, [(-13.0, -3.0), (10.0, -3.0), (10.0, -6.5), (-6.0, -7.0), (-13.0, -6.0)],
     "#e39082", L2_EC, 1.1, 3.2)

# ── 뒤칸(교재 미기재, 손등 폄근군 맥락용) ───────────────────────────────────────
blob(ax, [(21.5, -3.5), (26.0, -5.0), (25.5, -10.5), (21.5, -9.5), (21.0, -5.0)],
     NA_FC, NA_EC, 0.9, 2.8, ls=":")                                                    # 긴·짧은노쪽손목폄근 (ECRL·ECRB)
blob(ax, [(17.0, -7.5), (20.5, -8.5), (21.0, -12.5), (17.0, -12.0)],
     NA_FC, NA_EC, 0.9, 2.9, ls=":")                                                    # 긴엄지벌림근·짧은엄지폄근 (APL·EPB)
blob(ax, [(13.0, -10.0), (16.5, -10.5), (16.0, -13.2), (12.5, -12.8)],
     NA_FC, NA_EC, 0.9, 2.9, ls=":")                                                    # 긴엄지폄근 (EPL)
blob(ax, [(-3.0, -9.5), (5.5, -9.5), (11.0, -10.5), (10.0, -14.2), (2.0, -14.5), (-3.0, -13.5)],
     NA_FC, NA_EC, 0.9, 2.7, ls=":")                                                    # 손가락폄근·집게폄근 (EDC·EI)
blob(ax, [(-3.5, -10.0), (-7.5, -10.5), (-8.0, -14.0), (-4.0, -13.5)],
     NA_FC, NA_EC, 0.9, 2.8, ls=":")                                                    # 새끼폄근 (EDM)
blob(ax, [(-10.0, -11.0), (-14.5, -11.5), (-16.0, -14.5), (-11.5, -14.5)],
     NA_FC, NA_EC, 0.9, 2.8, ls=":")                                                    # 자쪽손목폄근 (ECU)

# ── Layer 3 중간·심층 굴근군 ───────────────────────────────────────────────────
# 얕은손가락굽힘근 (Flexor digitorum superficialis, FMA:38469) [공통교재]
blob(ax, [(-9.0, 9.5), (-2.0, 10.2), (5.5, 9.2), (7.5, 4.5), (3.0, 1.5), (-5.0, 1.5), (-10.5, 5.0)],
     L3_FC, L3_EC, 1.2, 2.6)
# 긴엄지굽힘근 (Flexor pollicis longus, FMA:38481) [김재효]
blob(ax, [(4.5, 2.0), (9.5, 2.5), (14.5, 0.5), (13.5, -3.0), (8.0, -3.0), (4.0, -1.0)],
     L3_FC, L3_EC, 1.1, 2.9, ls="--")
# 깊은손가락굽힘근 (Flexor digitorum profundus, FMA:38478) [김재효]
blob(ax, [(-4.5, 1.5), (-11.5, 2.0), (-16.5, 0.0), (-16.0, -3.2), (-9.5, -3.2), (-4.5, -1.0)],
     L3_FC, L3_EC, 1.1, 2.7, ls="--")

# ── Layer 2 근막·표층 힘줄(건)군 ───────────────────────────────────────────────
# 긴손바닥근 힘줄 (Palmaris longus tendon, FMA:38462) [공통교재] — 정중선 중앙
blob(ax, [(-1.5, 13.4), (1.5, 13.4), (1.8, 11.2), (-1.5, 11.2)],
     L2_FC, L2_EC, 1.2, 3.2)
# 노쪽손목굽힘근 힘줄 (Flexor carpi radialis tendon, FMA:38459) [공통교재] — PL 바로 노쪽
blob(ax, [(5.2, 13.0), (9.2, 12.6), (9.8, 10.2), (5.8, 10.2)],
     L2_FC, L2_EC, 1.2, 3.2)
# 위팔노근 힘줄 (Brachioradialis tendon, FMA:38485) — 가쪽 끝
blob(ax, [(20.5, 8.0), (25.2, 7.5), (25.5, 2.5), (21.2, 2.0)],
     L2_FC, L2_EC, 1.1, 3.0)
# 자쪽손목굽힘근 (Flexor carpi ulnaris, FMA:38465) [공통교재] — 안쪽 끝
blob(ax, [(-18.5, 10.2), (-23.2, 9.5), (-24.5, 4.5), (-20.2, 4.0), (-18.0, 7.0)],
     L2_FC, L2_EC, 1.2, 3.0)


def dot(x, y, r, fc, ec="#333", z=6, lw=0.8):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=lw, zorder=z))


# ── Layer 4 신경혈관속 + 피부 신경혈관 ────────────────────────────────────────
# 정중신경 (Median nerve, FMA:14385) — ★ PC06 핵심 표적: PL-FCR 사이, FDS 바로 앞
dot(3.2, 9.6, 2.05, NERVE, z=6.5)
# 정중신경 손바닥피부가지 (Palmar cutaneous br. of median n., FMA:44830)
dot(1.8, 13.6, 0.95, NERVE, z=6.5)

# 앞뼈사이신경·동맥 (AIN & AIA, FMA:44822 · 22739) — FDP/FPL 사이 심부
dot(0.2, -2.2, 1.25, ART, z=6.3)
dot(2.4, -2.2, 1.35, NERVE, z=6.3)

# 노동맥·노정맥 (Radial a. / v., FMA:22730 · 22947) — FCR과 위팔노근건 사이 맥동처
dot(12.8, 9.2, 1.95, ART, z=6.3)
dot(10.8, 8.5, 1.15, VEIN); dot(14.8, 8.2, 1.15, VEIN)

# 노신경 얕은가지 (Superficial br. of radial n., FMA:292885)
dot(18.5, 6.5, 1.6, NERVE, z=6.3)

# 자동맥·자정맥 (Ulnar a. / v., FMA:22742 · 22950) 및 자신경 (Ulnar n., FMA:14387)
dot(-16.0, 6.0, 1.75, ART, z=6.3)
dot(-14.2, 5.0, 1.05, VEIN); dot(-17.8, 4.8, 1.05, VEIN)
dot(-15.6, 8.4, 1.65, NERVE, z=6.3)

# 뒤뼈사이신경·동맥 (PIN & PIA)
dot(0.5, -9.0, 1.1, ART); dot(2.6, -9.0, 1.2, NERVE)

# 표재 피하 정맥 및 피부신경
dot(-3.5, 13.8, 1.65, VEIN)                                                             # 정중앞팔정맥 (Median antebrachial v.)
dot(25.5, 6.5, 1.95, VEIN)                                                              # 노쪽피부정맥 (Cephalic v.)
dot(-24.5, 5.5, 1.95, VEIN)                                                             # 자쪽피부정맥 (Basilic v.)
dot(24.0, 10.0, 1.45, NERVE)                                                            # 가쪽아래팔피부신경 (FMA:39080)
dot(-23.0, 9.5, 1.45, NERVE)                                                            # 안쪽아래팔피부신경 (FMA:39079)

# ── 자침선(T1) ────────────────────────────────────────────────────────────────
# 자입점 E: 긴손바닥근건(PL)과 노쪽손목굽힘근건(FCR) 사이 피부 정중부
E = np.array([3.2, 14.8])
D = np.array([0.0, -1.0])              # 전완 앞면 수직 직자 방향 (손등 외관 TE05 방면 투사축)
P = np.array([1.0, 0.0])               # 자침축 법선


def at(z):
    return E + D * z


Z_CLASSIC_3 = 6.9                      # 고전 3푼 (6.9mm, 《황제명당경》)
Z_CLASSIC_5 = 11.5                     # 고전 5푼 (11.5mm, 《침구갑을경》 = 현대 0.5寸)
Z_MOD_HI = 23.0                        # 현대 상한 1寸 (23.0mm, 《공통교재》)
Z_TRANSFIX = 32.0                      # 외관(TE5) 대향 투침 심도 (약 32mm)

# 깊이 밴드 색상 채우기
for z0, z1, c, a in [
    (0, Z_CLASSIC_3, CLASSIC_3, 0.65),
    (Z_CLASSIC_3, Z_CLASSIC_5, CLASSIC_5, 0.55),
    (Z_CLASSIC_5, Z_MOD_HI, MODERN, 0.50),
    (Z_MOD_HI, Z_TRANSFIX, "#8b5cf6", 0.35)
]:
    (x0, y0), (x1, y1) = at(z0), at(z1)
    ax.plot([x0, x1], [y0, y1], color=c, lw=8.5, alpha=a, solid_capstyle="butt", zorder=5.5)

# 중심 침체 실선 및 화살촉
ax.plot(*zip(at(-7.5), at(Z_TRANSFIX)), color="#1f2328", lw=1.3, zorder=7.2)
ax.add_patch(FancyArrowPatch(at(Z_TRANSFIX - 4.0), at(Z_TRANSFIX), arrowstyle="-|>", mutation_scale=15,
                             lw=1.3, color="#1f2328", zorder=7.3))

# 깊이 눈금선 및 수치 라벨
for z in (0, Z_CLASSIC_3, Z_CLASSIC_5, Z_MOD_HI, Z_TRANSFIX):
    a0, a1 = at(z) - P * 4.4, at(z) - P * 2.2
    ax.plot([a0[0], a1[0]], [a0[1], a1[1]], color="#3c434d", lw=0.9, zorder=7.1)

for z, txt, c in [
    (Z_CLASSIC_3, "3푼(6.9mm)", "#0b6a62"),
    (Z_CLASSIC_5, "5푼(11.5mm)", "#1d4ed8"),
    (Z_MOD_HI, "1寸(23.0mm)", MODERN),
    (Z_TRANSFIX, "透刺(32mm)", "#6d28d9")
]:
    t = at(z) - P * 6.6
    ax.text(t[0], t[1], txt, fontsize=7.8, weight="bold", color=c, ha="right", va="center", zorder=7.6,
            bbox=dict(boxstyle="round,pad=0.20", fc="#ffffff", ec=c, lw=0.7, alpha=0.92))

ax.add_patch(Circle(E, 1.15, fc="#ffffff", ec="#1f2328", lw=1.3, zorder=7.4))

# 손등 쪽 외관(TE05) 대향 혈위 표시
E_DORSAL = np.array([1.5, -15.4])
ax.add_patch(Circle(E_DORSAL, 1.25, fc="#ffffff", ec="#6d28d9", lw=1.4, zorder=7.4))
ax.text(E_DORSAL[0], E_DORSAL[1] - 3.2, "TE05 외관(外關) 대향점", fontsize=8.6, weight="bold",
        color="#6d28d9", ha="center", va="top", zorder=7.6)

# 자침 깊이 안내 상자
ax.add_patch(FancyBboxPatch((-36.0, 22.8), 58.0, 10.6, boxstyle="round,pad=0.6,rounding_size=1.6",
                            fc="#ffffff", ec="#9aa3ad", lw=1.0, zorder=9))
ax.text(-34.0, 31.2, "PC06 내관 자침점 (T1, 腕上二寸 · 긴손바닥근건-노쪽손목굽힘근건 사이 직자)",
        fontsize=10.8, weight="bold", color="#1f2328", va="center", zorder=10)
for i, (c, txt) in enumerate([
        (CLASSIC_3, "고전 3푼 = 6.9mm — ① 피부·피하 ~ ② 근막 건간막 통과, 정중신경 표면 외막 도달"),
        (CLASSIC_5, "고전 5푼 = 11.5mm — ④ 정중신경(MN) 본간 접촉, 전격성 득기감(得氣) 유발"),
        (MODERN, "현대 0.5~1寸 = 11.5~23.0mm — ③ 얕은손가락굽힘근 관통, 심부 앞뼈사이신경(AIN) 접촉"),
        ("#6d28d9", "투침(透刺) 1.2~1.5寸 = 28~35mm — ⑤ 네모엎침근·골간막 관통 → 손등 외관(TE5) 대향")]):
    y = 28.5 - i * 2.3
    ax.plot([-33.8, -30.5], [y, y], color=c, lw=5.8, alpha=0.6, solid_capstyle="butt", zorder=10)
    ax.text(-29.5, y, txt, fontsize=8.2, color="#1f2328", va="center", zorder=10)
ax.add_patch(FancyArrowPatch((12.0, 23.2), (E[0] + 0.6, E[1] + 1.8), arrowstyle="-|>", mutation_scale=12,
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
lab(24.0, 10.0, R, 30.0, "① 가쪽아래팔피부신경 Lateral cutaneous n. of forearm  FMA:39080  [공통]", TXT_N)
lab(25.5, 6.5, R, 25.2, "① 노쪽피부정맥 Cephalic v.  FMA:13324  [공통]", TXT_V)
lab(7.2, 11.5, R, 20.4, "② 노쪽손목굽힘근건 FCR tendon  FMA:38459  [공통]\n    정중신경 지배 · 분절 C6(주)·C7", TXT_M)
lab(12.8, 9.2, R, 15.2, "④ 노동맥·노정맥 Radial a. / v.  FMA:22730 · 22947  [공통]\n    (노쪽 맥동처 LU9·LU8 방면)", "#b02020")
lab(18.5, 6.5, R, 10.0, "④ 노신경 얕은가지 Superficial branch of radial n.  FMA:292885  [공통]", TXT_N)
lab(22.0, 5.0, R, 5.0, "② 위팔노근건 Brachioradialis tendon  FMA:38485  [공통]", TXT_M)
lab(9.5, 1.0, R, -0.2, "③ 긴엄지굽힘근 Flexor pollicis longus  FMA:38481  [김재효]\n    앞뼈사이신경(AIN) 지배 · 분절 C7·C8", TXT_M)
lab(2.4, -2.2, R, -5.5, "④ 앞뼈사이신경·동맥 AIN / AIA  FMA:44822 · 22739  [김재효]\n    (정중신경 심부 분지 · 심층 신경혈관속)", "#b02020", extra=(0.2, -2.2))
lab(18.0, -9.0, R, -11.0, "⑤ 노뼈 Radius  FMA:23463 (앞면 골막 = Layer 5)", TXT_B)
lab(23.5, -7.0, R, -16.2, "긴·짧은노쪽손목폄근 ECRL·ECRB (뒤칸, 교재 미기재)", GREY)
lab(19.0, -10.0, R, -21.4, "긴엄지벌림근·짧은엄지폄근 APL·EPB (뒤칸, 교재 미기재)", GREY)
lab(14.5, -11.5, R, -26.6, "긴엄지폄근 EPL (뒤칸, 교재 미기재)", GREY)
lab(6.0, -12.5, R, -31.8, "손가락폄근·집게폄근 EDC·EI (뒤칸, 외관 혈위 심부)", GREY)

# 안쪽(자쪽) 계열 — 왼쪽
lab(-3.5, 13.8, L, 30.0, "① 정중앞팔정맥 Median antebrachial v.  FMA:22964  [공통]", TXT_V)
lab(0.0, 12.5, L, 25.2, "② 긴손바닥근건 Palmaris longus tendon  FMA:38462  [공통]\n    정중신경 지배 · 분절 C7·C8", TXT_M)
lab(3.2, 9.6, L, 19.8, "★ ④ 정중신경 Median n.  FMA:14385  [공통 · 핵심 표적]\n    상완신경총 외측/내측속 합류 주간 · 분절 C6–T1 (ARI-Core 100)", TXT_N)
lab(1.8, 13.6, L, 14.5, "① 정중신경 손바닥피부가지 Palmar cutaneous br.  FMA:44830", TXT_N)
lab(-2.0, 6.5, L, 9.5, "③ 얕은손가락굽힘근 Flexor digitorum superficialis  FMA:38469  [공통]\n    정중신경 지배 · 분절 C8(주)·T1", TXT_M)
lab(-10.5, 0.0, L, 4.2, "③ 깊은손가락굽힘근 Flexor digitorum profundus  FMA:38478  [김재효]\n    앞뼈사이신경(요측)·자신경(척측) 이중지배 · 분절 C8·T1", TXT_M)
lab(-16.0, 6.0, L, -1.0, "④ 자동맥·자정맥 Ulnar a. / v.  FMA:22742 · 22950  [공통]", "#b02020")
lab(-15.6, 8.4, L, -6.0, "④ 자신경 Ulnar n.  FMA:14387  [공통] · 분절 C8·T1", TXT_N)
lab(-20.5, 7.0, L, -11.2, "② 자쪽손목굽힘근 FCU  FMA:38465  [공통] · 자신경 지배", TXT_M)
lab(-24.5, 5.5, L, -16.4, "① 자쪽피부정맥 Basilic v. · 안쪽아래팔피부신경 (FMA:39079)", TXT_V, extra=(-23.0, 9.5))
lab(-2.0, -4.5, L, -21.6, "⑤ 네모엎침근 Pronator quadratus  FMA:38453  [공통교재 단독]\n    앞뼈사이신경(AIN) 지배 · 분절 C7·C8 (심층 한계근)", TXT_M)
lab(-18.5, -8.0, L, -27.0, "⑤ 자뼈 Ulna  FMA:23466 · 뼈사이막 Interosseous membrane  FMA:35187", TXT_B,
    extra=(-1.0, -7.5))
lab(-13.0, -13.0, L, -32.2, "자쪽손목폄근 ECU · 새끼폄근 EDM (뒤칸, 교재 미기재)", GREY, extra=(-6.0, -12.5))

# ── 제목 ──────────────────────────────────────────────────────────────────────
ax.text(-76, 38.0, "내관(內關, PC06) T1 자침 높이 — 아래팔 앞면 원위부(완횡문 상 2寸) 횡단면 해부 실체 모식도",
        fontsize=16.0, weight="bold", va="top")
ax.text(-76, 35.0,
        "오른팔 해부학적 자세(전완 회외·손바닥 앞) · 몸쪽에서 먼쪽을 봄(위에서 내려다봄) · "
        "앞쪽 = 위, 노쪽(가쪽·엄지) = 오른쪽, 자쪽(안쪽·새끼손가락) = 왼쪽",
        fontsize=9.8, color="#444", va="top")

# ── 범례 ──────────────────────────────────────────────────────────────────────
for i, (fc, ec, ls, t) in enumerate([
        (SKIN_FC, SKIN_EC, "-", "① 피부·피하"), (L2_FC, L2_EC, "-", "② 근막·표층근건"),
        (L3_FC, L3_EC, "-", "③ 중간·심층근"), (BONE_FC, BONE_EC, "-", "⑤ 뼈·골막·골간막"),
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

# ── 하단 대비 패널: 내관(PC6) ↔ 외관(TE5) 대향 투침 축 및 신경 안전성 ────────────
ax2 = fig.add_axes([0.028, 0.145, 0.950, 0.215])
ax2.set_xlim(-14, 428)
ax2.set_ylim(-14, 15)
ax2.axis("off")
ax2.add_patch(FancyBboxPatch((-11, -13.0), 436, 27.6, boxstyle="round,pad=0.4,rounding_size=2.0",
                             fc="#fbfaf8", ec="#c9cfd8", lw=1.1, zorder=0))
ax2.text(-6, 13.5, "대비 및 임상 안전 — PC06(내관) ↔ TE05(외관) 대향 투침(透刺) 축과 정중신경 자침 안전 가이드",
         fontsize=11.4, weight="bold", va="center", zorder=3)

# 전완 긴축 모식(완횡문 0mm → 주횡문 250mm, 12寸 골도 250mm 가정)
LIMB_Y = 0.5
ax2.add_patch(Polygon(chaikin([(0, LIMB_Y + 2.3), (120, LIMB_Y + 3.5), (250, LIMB_Y + 4.2),
                               (250, LIMB_Y - 4.2), (120, LIMB_Y - 3.5), (0, LIMB_Y - 2.3)], 3),
                      closed=True, fc=SKIN_FC, ec=SKIN_EC, lw=1.2, zorder=1))
# PC06 위치 (완상 2寸 = 41.7mm)
ax2.add_patch(Rectangle((35, LIMB_Y - 4.0), 14, 8.0, fc=CLASSIC_5, ec="none", alpha=0.22, zorder=1.5))
ax2.plot([42, 42], [LIMB_Y - 5.4, LIMB_Y + 5.4], color=MODERN, lw=2.2, zorder=2)
# 완횡문 / 주횡문 기준선
for x, t, ha in [(0, "손목 완횡문 (大陵 PC7)", "left"), (250, "팔꿈치 주횡문 (曲泽 PC3)", "right")]:
    ax2.plot([x, x], [LIMB_Y - 5.0, LIMB_Y + 5.0], color="#5b4f33", lw=1.5, zorder=2)
    ax2.text(x, -5.2, t, fontsize=8.4, ha=ha, va="top", color="#5b4f33", weight="bold", zorder=3)

ax2.text(6, 11.0, "PC06 내관 — 완상 2寸 (손목 주름 위 약 4.5~5cm)\n취혈: 주먹 쥘 때 도드라지는 PL건과 FCR건 사이",
         fontsize=8.5, ha="left", va="top", color="#0e9488", weight="bold", linespacing=1.55, zorder=3)
ax2.text(120, 11.0, "TE05 외관 — 손목 등쪽 주름 상 2寸\n▲ 뼈사이막(IOM)을 사이에 둔 정대향(正對向) 혈위",
         fontsize=8.5, ha="left", va="top", color="#6d28d9", weight="bold", linespacing=1.55, zorder=3)
ax2.text(42, -5.2, "완상 2寸(약 42mm)\n▲ 위 횡단면 높이",
         fontsize=8.0, ha="center", va="top", color=MODERN, weight="bold", linespacing=1.5, zorder=3)

ax2.plot([255, 255], [-11.5, 12.6], color="#c9cfd8", lw=1.0, zorder=2)
ax2.text(263, 12.2, "정중신경(Median n.) 접촉 기전과 임상 안전 수칙 (SI 87.5)",
         fontsize=9.2, weight="bold", va="top", color="#1f2328", zorder=3)
ax2.text(263, 8.6,
         "· 신경 접촉: 5~8mm 깊이에서 정중신경(MN, FMA:14385) 본간 외막 접촉\n"
         "· 득기 반응: 손가락 끝(2·3·4지)으로 찌릿하게 방사되는 전격통(득기감)\n"
         "· 신경 손상 예방: 심한 방사통 발생 시 1~2mm 후퇴하여 신경 주변부(paraneural) 유침\n"
         "· 투침 기전(PC6 → TE5): PL-FCR → 정중신경 외연 → FDS/FDP → AIN → PQ →\n"
         "  골간막(IOM 관통, 침저항 급감) → 손가락폄근(EDC) → PIN → 외관(TE5) 도달\n"
         "· 반사 회로: C6–T1 구심성 $\\to$ 척수시상로 $\\to$ 뇌간 고립속핵(NTS) $\\to$ 미주신경 활성",
         fontsize=8.2, va="top", color="#2b313a", linespacing=1.60, zorder=3)

# ── 주석 ──────────────────────────────────────────────────────────────────────
ax3 = fig.add_axes([0.028, 0.004, 0.950, 0.135])
ax3.set_xlim(0, 1)
ax3.set_ylim(0, 1)
ax3.axis("off")
ax3.text(0.0, 1.0,
         "테두리 약속 — 실선: 2대 교재 공통 기재 구조 · 파선: 한 교재만 기재([공통교재 단독] / [김재효]) · "
         "점선 회색: 교재 미기재(해부 맥락용 참조 구조). ①~⑤는 보고서 4절 Layer 순서.\n"
         "자침 심도 — 긴손바닥근건(PL)과 노쪽손목굽힘근건(FCR) 사이 피부면에 수직 직자.\n"
         "          고전 3푼(《黄帝明堂经》 \"刺入三分\" = 6.9mm): ① 피부·피하 ~ ② 근막 건간막 통과, 정중신경 표면 외막 도달.\n"
         "          고전 5푼(《针灸甲乙经》 \"刺入五分\" = 11.5mm): ④ 정중신경(MN) 본간 접촉, 전격성 득기감(得氣) 유발 (현대 0.5寸 상응).\n"
         "          현대 상한 1寸(23.0mm): ③ FDS 관통, ④ 앞뼈사이신경(AIN)·동맥 도달, ⑤ 네모엎침근(PQ) 기저면 접촉.\n"
         "          투침(透刺 1.2~1.5寸 = 28~35mm): 네모엎침근과 골간막(IOM)을 관통하여 손등 쪽 외관(TE5) 방면으로 관통 자침.\n"
         "근거·한계 — 구조명과 교재 귀속은 2대 교재 데이터셋, FMA ID·지배신경·척수분절은 FMA 5.1.0(nerve_supply · segmental_supply) 기준.\n"
         "          겉모양(가로 ≈ 56mm · 앞뒤 ≈ 32mm)과 자침 깊이 띠는 같은 mm 축척이나, "
         "각 구조의 경계·깊이는 PC06 실측값이 아닌 표준 모식 배치이다.",
         fontsize=8.5, color="#333", va="top", linespacing=1.68)

for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor="white")
    print("saved", out)

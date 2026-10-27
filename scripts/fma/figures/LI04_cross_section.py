# -*- coding: utf-8 -*-
"""LI04 합곡 해부 모식도 (축척 아님). ST36·GB21과 같은 방식.
(A) 오른손등에서 본 T1(고전: 第1·2掌骨底 결합부 앞, 동맥 박동처)·T2(현대 국표: 第2掌骨 노쪽 중점) 위치
(B) T2 높이 손 횡단면(손가락 끝에서 몸쪽으로 봄, 손등=위, 노쪽(엄지)=오른쪽)
구조·FMA ID·분절은 fma_query.py profile LI04 + entity, 2대 교재 데이터셋, papers.id 2292(Casey 2022 사체 25손) 기준."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch, Ellipse

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = sys.argv[1]


def chaikin(pts, n=4):
    p = np.asarray(pts, float)
    for _ in range(n):
        q, r = p * 0.75 + np.roll(p, -1, 0) * 0.25, p * 0.25 + np.roll(p, -1, 0) * 0.75
        m = np.empty((len(p) * 2, 2)); m[0::2], m[1::2] = q, r
        p = m
    return p


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, ls="-"):
    ax.add_patch(Polygon(chaikin(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
fig = plt.figure(figsize=(16.5, 8.6), dpi=160)
axA = fig.add_axes([0.0, 0.13, 0.28, 0.80]); axB = fig.add_axes([0.28, 0.13, 0.72, 0.80])

# ---------------- (A) 손등 표면: T1·T2 위치
ax = axA
ax.set_xlim(-60, 60); ax.set_ylim(-75, 85); ax.set_aspect("equal"); ax.axis("off")
blob(ax, [(-40, -70), (35, -70), (42, -20), (58, 10), (55, 30), (40, 28), (28, 8), (30, 60), (22, 75), (12, 70),
          (6, 80), (-4, 80), (-10, 74), (-18, 78), (-28, 74), (-36, 66), (-42, 40)], "#f6dccb", "#b07a5a", 1.4, 1)
ax.plot([24, 50], [-30, 22], color="#7d6f4f", lw=5, solid_capstyle="round", zorder=2)        # 첫째 손허리뼈
ax.plot([14, 18], [-32, 40], color="#7d6f4f", lw=5, solid_capstyle="round", zorder=2)        # 둘째 손허리뼈
ax.plot([0, 2], [-30, 42], color="#b5a78a", lw=4, solid_capstyle="round", zorder=2)
ax.plot([30, 46], [-48, -28], color="#2f5fb3", lw=1.2, ls=":", zorder=2)                      # 긴엄지폄근 힘줄
ax.text(47, -50, "긴엄지폄근 힘줄\n(해부학적 코담배갑 경계)", fontsize=7.5, color="#2f5fb3", ha="center")
ax.add_patch(Circle((21, -22), 3.2, fc="#e9a0a0", ec="#b02020", lw=1.4, zorder=4))
ax.text(21, -22, "T1", ha="center", va="center", fontsize=8.5, weight="bold", zorder=5)
ax.add_patch(Circle((20, 4), 3.2, fc="#fff3a0", ec="#8a6d00", lw=1.4, zorder=4))
ax.text(20, 4, "T2", ha="center", va="center", fontsize=8.5, weight="bold", zorder=5)
ax.plot([21], [-13], marker="D", ms=5, color="#555", zorder=4)
ax.text(-2, -13, "1959 上海 취혈점\n(근위 1/3)", fontsize=7.5, ha="right", va="center", color="#444")
ax.annotate("", xy=(30, 4), xytext=(30, -22), arrowprops=dict(arrowstyle="<->", lw=1, color="#333"))
ax.text(33, -9, "Δ ≈ 20~30mm\n(추정, 실측 아님)", fontsize=8, va="center")
ax.text(-55, 82, "(A) 오른손등 — 두 Target 위치", fontsize=11.5, weight="bold", va="top")
ax.text(-55, 74, "T1 고전: 岐骨間 陷中, '動脈應手'(第1·2掌骨底 결합부 앞)\nT2 현대 국표: 第2掌骨 노쪽 중점", fontsize=8.2, va="top",
        color="#333", linespacing=1.5)
ax.text(-55, -60, "붉은 원 = 노동맥 박동처 가까이(T1)", fontsize=7.8, color="#b02020")

# ---------------- (B) T2 높이 횡단면
ax = axB
ax.set_xlim(-118, 205); ax.set_ylim(-70, 75); ax.set_aspect("equal"); ax.axis("off")
outline = [(-78, 18), (-60, 30), (-20, 34), (20, 34), (44, 28), (62, 14), (70, -6), (64, -26), (46, -36),
           (20, -38), (-20, -40), (-60, -34), (-80, -16)]
blob(ax, outline, "#f6dccb", "#b07a5a", 1.6, 1)
blob(ax, [(x * 0.93, y * 0.9) for x, y in outline], "#fbeee6", "#8a6a55", 0.8, 1.5, ls="--")
for cx, cy, rx, ry, lab in [(14, 12, 9, 7, "MC2"), (-12, 12, 8, 7, "MC3"), (-36, 11, 7, 6, ""), (-58, 9, 6, 5, "")]:
    ax.add_patch(Ellipse((cx, cy), 2 * rx, 2 * ry, fc="#efe8d2", ec="#7d6f4f", lw=1.3, zorder=4))
    if lab:
        ax.text(cx, cy, lab, ha="center", va="center", fontsize=7.5, color="#5b4f33", zorder=5)
ax.add_patch(Ellipse((50, -6), 16, 12, angle=-35, fc="#efe8d2", ec="#7d6f4f", lw=1.3, zorder=4))
ax.text(50, -6, "MC1", ha="center", va="center", fontsize=7.5, color="#5b4f33", zorder=5)
blob(ax, [(22, 22), (38, 20), (48, 6), (40, -4), (28, 2), (22, 10)], "#d9534f", "#8f2d2a", 1.1, 3)     # 첫째 등쪽뼈사이근
blob(ax, [(-24, -6), (0, -4), (30, -10), (44, -18), (30, -24), (-6, -20), (-26, -16)], "#e57f6c", "#8f2d2a", 1.1, 3)  # 엄지모음근
blob(ax, [(-4, 4), (4, 2), (2, -2), (-4, -2)], "#c9a27e", "#7a5a3a", 0.8, 3)
blob(ax, [(-28, 4), (-20, 3), (-21, -2), (-28, -2)], "#c9a27e", "#7a5a3a", 0.8, 3)
for x in (-12, -34, -54):
    blob(ax, [(x - 6, -26), (x + 6, -26), (x + 6, -32), (x - 6, -32)], "#e6d7c3", "#8a6a55", 0.7, 3)
blob(ax, [(46, -26), (62, -14), (62, -28), (50, -32)], "#d88c6f", "#8f4a2a", 0.9, 3)                     # 엄지두덩근


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


dot(30, 23, 1.6, ART)                         # 첫째 등쪽손허리동맥
dot(26, 24.5, 1.2, VEIN)
dot(25, 31, 1.8, VEIN); dot(5, 32, 1.6, VEIN); dot(-30, 31, 1.6, VEIN)       # 손등정맥그물
dot(33, 31, 1.4, NERVE); dot(16, 32, 1.4, NERVE)                              # 노신경 얕은가지 손등가지
dot(22, -2, 1.7, ART)                         # 노쪽집게동맥
dot(-6, -8, 1.9, ART); dot(-18, -9, 1.5, ART)  # 깊은손바닥동맥활
dot(-2, -10.5, 1.6, NERVE); dot(-13, -11.5, 1.4, NERVE)   # 자신경 깊은가지
dot(28, 4, 1.3, NERVE)                       # 첫째 등쪽뼈사이근 안 자신경 깊은가지 분지

ax.plot([22, 22], [46, 34], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((22, 34.5), (25, 6), arrowstyle="-|>", mutation_scale=15, lw=2.0, color="#111", zorder=9))
ax.add_patch(FancyArrowPatch((25, 6), (26, -14), arrowstyle="-|>", mutation_scale=11, lw=1.2, color="#555", ls="--", zorder=9))
ax.add_patch(FancyArrowPatch((22, 34.5), (16, 8), arrowstyle="-|>", mutation_scale=11, lw=1.1, color="#2a9d8f", ls="--", zorder=9))
ax.text(24, 49, "T2 자침점", fontsize=11, weight="bold", ha="center")


def lab(x, y, tx, ty, text, color="#222", fs=8.8):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 70, -82
lab(33, 31, R, 66, "① 노신경 얕은가지 손등가지  FMA:292885 (B1·papers.id 2292)\n    교재 '등쪽손가락신경'은 FMA 집합 대응 → 검토", "#8a6d00")
lab(25, 31, R, 52, "① 손등정맥그물  FMA:67977  [공통]", "#2f5fb3")
lab(30, 23, R, 40, "① 등쪽손허리동·정맥  FMA:321491 / 22954  [공통]", "#b02020")
lab(40, 14, R, 28, "② 첫째 등쪽뼈사이근  FMA:37424  [공통]\n    지배: 자신경 깊은가지(근육 안을 지남, papers.id 2292) · 분절 T1(주)·C8", "#8f2d2a")
lab(22, -2, R, 12, "③ 노쪽집게동맥  FMA:22763  [공통] (노동맥 가지)", "#b02020")
lab(36, -18, R, -4, "③ 엄지모음근 가로갈래 FMA:46120 [공통교재]\n    · 빗갈래 FMA:46119 [김재효] — 분절 C8·T1", "#8f2d2a")
lab(56, -24, R, -22, "엄지두덩근 (교재 미기재)", "#8f4a2a")
lab(-2, -10.5, 4, -50, "③~④ 자신경 깊은가지  FMA:44877  [김재효]", "#8a6d00")
lab(-6, -8, -10, -59, "④ 깊은손바닥동맥활  FMA:22838 (교재 미기재)", "#b02020")
lab(-54, -29, -62, -48, "굽힘근 힘줄 (손바닥, 경로 밖)", "#8a6a55")
lab(-28, 1, -70, 28, "손바닥쪽 뼈사이근 (MC = 손허리뼈)", "#7a5a3a")

ax.text(-122, 73, "(B) T2 높이 손 횡단면 — 해부 실체 모식도", fontsize=11.5, weight="bold", va="top")
ax.text(-122, 66, "오른손 · 손가락 끝에서 몸쪽으로 봄 · 손등=위, 노쪽(엄지)=오른쪽 · 축척 아님", fontsize=8.6, color="#444", va="top")
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-108 + i * 15, -62), 1.8, fc=c, ec="#333", lw=0.8))
    ax.text(-105 + i * 15, -62, t, va="center", fontsize=8.5)

fig.text(0.01, 0.95, "합곡(LI04) 해부 실체 모식도 — 두 Target(고전 T1 · 현대 T2)", fontsize=15, weight="bold")
fig.text(0.01, 0.015,
         "검은 실선: T2 직자 0.5~1寸(11.5~23mm, 교재·通考) → ② 첫째 등쪽뼈사이근. 회색 점선: 1寸 근처에서 ③ 엄지모음근 도달(추정). 청록 점선: 针尖偏向第二掌骨(1959 上海, 80°).\n"
         "자신경 깊은가지·깊은손바닥동맥활은 엄지모음근과 손바닥쪽 뼈사이근 사이(④)에 있어 劳宫·后溪 방향 透刺(2~3寸, 上海《针灸学》) 때 가까워진다.\n"
         "T1은 노동맥이 첫째 등쪽뼈사이근 두 갈래 사이로 손바닥 쪽으로 들어가는 자리 가까이라 '動脈應手'(窦太師)로 기술되었다(B1-01, papers.id 2054). "
         "孕婦禁針은 여러 문헌에 있다(5절). 층 두께·거리는 실측값이 없어 임의 배치. [공통]=두 교재 공통.",
         fontsize=8.5, color="#333", va="bottom", linespacing=1.55)
fig.savefig(OUT, facecolor="white")
print("saved", OUT)

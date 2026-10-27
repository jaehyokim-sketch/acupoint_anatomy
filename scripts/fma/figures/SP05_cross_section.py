# -*- coding: utf-8 -*-
"""SP05 상구 높이 발목 횡단면 모식도 (오른발, 위에서 내려다봄, 앞쪽 위·안쪽 왼쪽). 축척 아님.
ST36_cross_section.py와 같은 방식. 구조·FMA ID는 fma_query.py profile SP05와 2대 교재 데이터셋, 심도·자침 방향은 SP05 보고서 4·5절."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Ellipse, FancyArrowPatch

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]   # 간체자는 YaHei로 대체
plt.rcParams["axes.unicode_minus"] = False
OUT = sys.argv[1]


def chaikin(pts, n=4):
    p = np.asarray(pts, float)
    for _ in range(n):
        q = p * 0.75 + np.roll(p, -1, 0) * 0.25
        r = p * 0.25 + np.roll(p, -1, 0) * 0.75
        p = np.empty((len(p) * 2, 2))
        p[0::2], p[1::2] = q, r
    return p


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, ls="-"):
    ax.add_patch(Polygon(chaikin(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


fig, ax = plt.subplots(figsize=(13, 10.4), dpi=170)
ax.set_xlim(-118, 118); ax.set_ylim(-84, 82); ax.set_aspect("equal"); ax.axis("off")

skin = [(0, 34), (-16, 33), (-30, 26), (-38, 10), (-38, -8), (-30, -26), (-14, -38), (0, -44), (14, -38),
        (28, -28), (36, -10), (36, 8), (28, 24), (14, 32)]
blob(ax, skin, "#f6dccb", "#b07a5a", 1.6, 1)
blob(ax, [(x * 0.9, y * 0.9 - 0.5) for x, y in skin], "#fbeee6", "#8a6a55", 0.9, 1.5, ls="--")   # 심부근막

# 뼈: 목말뼈(중앙), 안쪽복사(정강뼈, 안쪽), 가쪽복사(종아리뼈, 가쪽 뒤)
blob(ax, [(-15, 15), (0, 18), (15, 13), (18, -4), (6, -14), (-12, -10), (-17, 2)], "#efe8d2", "#7d6f4f", 1.4, 4)
blob(ax, [(-33, 10), (-24, 13), (-20, 2), (-22, -10), (-30, -12), (-34, -2)], "#e6dcc0", "#7d6f4f", 1.4, 4)
blob(ax, [(19, -2), (27, 2), (30, -12), (24, -20), (18, -14)], "#e6dcc0", "#7d6f4f", 1.4, 4)
# 삼각인대(안쪽인대) — 안쪽복사와 목말뼈 사이, 앞쪽 섬유는 앞으로
blob(ax, [(-21, 14), (-14, 17), (-15, 12), (-18, 2), (-19, -8), (-21, -2), (-22, 8)], "#b9a6d8", "#5d4a8a", 1.0, 4.5)
# 관절주머니(앞쪽) — 점선
ax.plot(*chaikin([(-15, 17), (-6, 20.5), (6, 20.5), (16, 15)], 3)[:-6].T, color="#5d4a8a", lw=1.0, ls="--", zorder=4.6)
# 아래폄근지지띠(小腿十字韧带) — 앞쪽 힘줄 위
ax.plot(*chaikin([(-24, 27), (-10, 30.5), (8, 30.5), (24, 25)], 3)[:-6].T, color="#6d5f8f", lw=2.0, zorder=5)

# 힘줄
TEND = "#f3e4b5"
ax.add_patch(Ellipse((-12, 24.5), 7.5, 5.5, fc="#e9a39d", ec="#8f2d2a", lw=1.2, zorder=6))     # 앞정강근 힘줄
ax.add_patch(Ellipse((-2.5, 25.5), 4.5, 3.6, fc=TEND, ec="#8a6a3a", lw=1.0, zorder=6))         # 긴엄지폄근 힘줄
for x, y in ((8, 25.5), (12.5, 24.5), (16.5, 22.5)):
    ax.add_patch(Ellipse((x, y), 3.6, 2.8, fc=TEND, ec="#8a6a3a", lw=0.9, zorder=6))          # 긴발가락폄근 힘줄
for x, y, w in ((-27, -15, 4.5), (-23, -19.5, 3.6), (-10, -22, 4.2)):
    ax.add_patch(Ellipse((x, y), w, w * 0.8, fc=TEND, ec="#8a6a3a", lw=0.9, zorder=6))        # 뒤정강근·긴발가락굽힘근·긴엄지굽힘근
for x, y in ((26, -22), (23, -25.5)):
    ax.add_patch(Ellipse((x, y), 4, 3, fc=TEND, ec="#8a6a3a", lw=0.9, zorder=6))              # 종아리근 힘줄
ax.add_patch(Ellipse((1, -36), 15, 6, fc=TEND, ec="#8a6a3a", lw=1.1, zorder=6))               # 발꿈치힘줄


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
dot(3, 21.2, 1.5, ART); dot(1, 20.5, 1.0, VEIN); dot(5.2, 20.3, 1.0, VEIN); dot(6.8, 22.4, 1.3, NERVE)   # 앞정강동정맥·깊은종아리신경
dot(-17.5, -22, 1.5, ART); dot(-19.6, -23.2, 1.0, VEIN); dot(-15.4, -23.6, 1.0, VEIN); dot(-14, -20.6, 1.6, NERVE)  # 뒤정강·정강신경
dot(-32, 17.5, 2.2, VEIN); dot(-33.5, 13.5, 1.3, NERVE); dot(-27, 23.5, 1.1, NERVE)     # 큰두렁정맥·두렁신경(가지)
dot(-6, 31, 1.2, NERVE); dot(12, 30, 1.1, NERVE)                                         # 안쪽발등피부신경 / 얕은종아리신경 가지
dot(-22.5, 17.5, 1.1, ART); dot(-25.5, 15.8, 0.9, ART)                                   # 안쪽앞복사동맥 / 안쪽복사동맥그물
dot(17, -33, 1.4, VEIN); dot(20, -31, 1.2, NERVE)                                        # 작은두렁정맥·장딴지신경

# SP05 자침 경로: 앞정강근 힘줄 안쪽, 안쪽복사 앞아래 오목
ax.plot([-25.5, -20], [28.6, 44], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((-25.2, 28.2), (-19.0, 17.6), arrowstyle="-|>", mutation_scale=15, lw=2.0, color="#111", zorder=9))
ax.add_patch(FancyArrowPatch((-25.2, 28.2), (-15.5, 12.0), arrowstyle="-|>", mutation_scale=11, lw=1.2, color="#c1121f", ls="--", zorder=8.5))
ax.text(-21, 49, "SP05 상구 자침점", ha="left", va="bottom", fontsize=12.5, weight="bold", zorder=10)
ax.text(-21, 48, "안쪽복사 앞아래 오목 · 앞정강근 힘줄 안쪽", ha="left", va="top", fontsize=8.6, color="#333", zorder=10)


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 50, -50
lab(-6, 31, R, 65, "① 안쪽발등피부신경 Medial dorsal cutaneous n.  FMA:44809 [공통교재]\n    ← 얕은종아리신경 → 온종아리신경", "#8a6d00")
lab(0, 30.4, R, 54, "아래폄근지지띠(小腿十字韧带)  — 穴位通鉴 국소해부 기술", "#4b3f6f")
lab(-12, 24.5, R, 43, "② 앞정강근 힘줄 Tendon of tibialis anterior  FMA:47050\n    (교재: 앞정강근 FMA:22532 [공통] · 분절 L4(주)·L5)", "#8f2d2a")
lab(-2.5, 25.5, R, 33, "긴엄지폄근 힘줄 (교재 미기재)", "#7a5a3a")
lab(6.8, 22.4, R, 25, "앞정강동정맥·깊은종아리신경 (교재 미기재)", "#555")
lab(-10, 19.5, R, 16, "④ 관절주머니(점선) — 목말종아리관절 앞쪽", "#5d4a8a")
lab(10, 2, R, 4, "목말뼈 Talus", "#5b4f33")
lab(25, -9, R, -8, "가쪽복사(종아리뼈)", "#5b4f33")
lab(26, -22, R, -20, "종아리근 힘줄", "#7a5a3a")
lab(20, -31, R, -32, "장딴지신경·작은두렁정맥", "#555")
lab(1, -36, R, -44, "발꿈치힘줄", "#7a5a3a")

lab(-27, 23.5, L, 34, "① 두렁신경 Saphenous n.  FMA:45262 [공통] ← 넙다리신경", "#8a6d00")
lab(-32, 17.5, L, 23, "① 큰두렁정맥 Great saphenous v.  FMA:21376 [공통]\n    (안쪽복사 바로 앞 피하 — 자침 시 눈으로 확인)", "#2f5fb3")
lab(-22.5, 17.5, L, 12, "③ 안쪽앞복사동맥 FMA:43905 [공통교재, 수동 대응]", "#b02020")
lab(-25.5, 15.8, L, 5, "③ 안쪽복사동맥그물 FMA:69733 [김재효]", "#b02020")
lab(-19, 6, L, -3, "④ 삼각인대(안쪽인대) Medial ligament of ankle  FMA:44055 [김재효]", "#5d4a8a")
lab(-28, 0, L, -11, "안쪽복사(정강뼈)  — 촉진 랜드마크", "#5b4f33")
lab(-27, -15, L, -19, "뒤정강근·긴발가락굽힘근 힘줄", "#7a5a3a")
lab(-14, -20.6, L, -27, "정강신경·뒤정강동정맥", "#555")
lab(-10, -22, L, -35, "긴엄지굽힘근 힘줄", "#7a5a3a")

ax.text(-114, 80, "상구(SP05) 높이 발목 횡단면 — 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-114, 73.5, "오른발 · 위에서 내려다봄 · 앞쪽=위, 안쪽=왼쪽 · 안쪽복사 아래끝 높이 · 축척 아님", fontsize=9.5, color="#444", va="top")
ax.text(-114, -54, "검은 실선: 직자 3~5푼(6.9~11.5mm; 明堂·甲乙 '刺入三分', 경락수혈학 3~5푼) — 피하·지지띠 아래 결합조직에서 멈춤.\n"
        "빨간 점선: 상한 8푼(18.4mm; 침구의학·通考 '直刺0.5~0.8寸') — 삼각인대 앞섬유·관절주머니에 근접. 上海《针灸学》은 '横刺透解溪'도 기술.\n"
        "큰두렁정맥·두렁신경은 자침점 안쪽 피하를 지나므로 정맥을 눈으로 확인하고 피한다. 금침 기록 없음(자침깊이 DB), 《千金翼方》 '忌灸'(뜸 금기 이문).\n"
        "①~④는 보고서 4절 Layer 순서. [공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. FMA 5.1.0 기준, 층 두께·거리는 SP05 실측값이 없어 임의 배치.\n"
        "교재의 '안쪽발목동맥(medial tarsal a., FMA:44598)'은 이 단면보다 원위(발배뼈 높이)의 발등동맥 가지라 그리지 않았다.",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-108 + i * 17, -46), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-105 + i * 17, -46, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

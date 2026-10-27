# -*- coding: utf-8 -*-
"""SP06 삼음교 높이(현대 정위: 안쪽복사 끝 위 3寸) 하퇴 하1/3 횡단면 모식도 (오른다리, 위에서 내려다봄, 앞쪽 위·안쪽 왼쪽). 축척 아님.
ST36_cross_section.py와 같은 방식. 구조·FMA ID·지배·분절은 fma_query.py profile SP06 및 2대 교재 데이터셋,
자침 근거는 《针灸腧穴通考》 SP6 【操作】(L1353~1385), 국소해부는 《中国针灸穴位通鉴》 SP6 局部解剖(L1518~1526)."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch, Ellipse

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
ax.set_xlim(-120, 120); ax.set_ylim(-86, 78); ax.set_aspect("equal"); ax.axis("off")

skin = [(0, 40), (16, 38), (30, 30), (38, 14), (38, -6), (32, -24), (20, -38), (6, -46), (-8, -44), (-22, -36),
        (-34, -22), (-40, -6), (-38, 10), (-28, 26), (-14, 36)]
blob(ax, skin, "#f6dccb", "#b07a5a", 1.6, 1)
blob(ax, [(x * 0.9, y * 0.9 - 1) for x, y in skin], "#fbeee6", "#8a6a55", 1.0, 1.5, ls="--")

# 뼈 (하1/3: 정강뼈는 둥근 삼각형, 종아리뼈는 가쪽 뒤)
blob(ax, [(-8, 31), (-20, 23), (-29, 7), (-25, -5), (-9, -7), (4, 4), (1, 19)], "#efe8d2", "#7d6f4f", 1.4, 4)
blob(ax, [(-11, 19), (-19, 9), (-11, 3), (-5, 9)], "#f9f5e8", "#bfb391", 0.6, 4.5)
ax.add_patch(Circle((24, -6), 5.6, fc="#efe8d2", ec="#7d6f4f", lw=1.4, zorder=4))
ax.plot([4, 11, 18, 21], [4, 0, -3, -4], color="#6d5f8f", lw=2.2, zorder=4.2)        # 종아리뼈사이막

# 앞칸·가쪽칸
blob(ax, [(1, 32), (10, 33), (13, 24), (8, 15), (2, 18)], "#e57f6c", "#8f2d2a", 1.0, 3)       # 앞정강근(하부)
blob(ax, [(13, 22), (19, 25), (21, 14), (15, 9), (11, 13)], "#e57f6c", "#8f2d2a", 1.0, 3)     # 긴엄지폄근
blob(ax, [(20, 30), (29, 26), (31, 15), (24, 9), (20, 15)], "#e57f6c", "#8f2d2a", 1.0, 3)     # 긴발가락폄근
blob(ax, [(30, 10), (36, 2), (34, -12), (28, -12), (30, -2)], "#d88c6f", "#8f4a2a", 1.0, 3)   # 종아리근

# 뒤칸 깊은층
blob(ax, [(-3, -7), (8, -5), (16, -11), (9, -17), (-3, -14)], "#c9a27e", "#7a5a3a", 1.1, 3)   # 뒤정강근
blob(ax, [(-24, -7), (-10, -9), (-9, -18), (-20, -19), (-27, -13)], "#d4ad86", "#7a5a3a", 1.1, 3)  # 긴발가락굽힘근
blob(ax, [(13, -14), (25, -13), (28, -22), (16, -26)], "#c9a27e", "#7a5a3a", 1.0, 3)          # 긴엄지굽힘근
ax.plot([-28, -12, 6, 26], [-17, -21, -24, -19], color="#8a6a55", lw=1.0, ls="--", zorder=3.5)  # 가로근육사이막
# 뒤칸 얕은층
blob(ax, [(-28, -22), (-6, -26), (16, -28), (28, -26), (24, -34), (6, -38), (-14, -36), (-26, -30)], "#b56b5a", "#6e3a2e", 1.0, 3)  # 가자미근
ax.add_patch(Ellipse((4, -42), 15, 5, fc="#efe3c8", ec="#7d6f4f", lw=1.0, zorder=3.2))          # 발꿈치힘줄


def dot(x, y, r, fc, z=6):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
dot(0, -21, 1.9, ART); dot(-2.6, -22.2, 1.2, VEIN); dot(2.6, -22.6, 1.2, VEIN); dot(4.8, -19.4, 1.9, NERVE)  # 뒤정강 혈관·정강신경
dot(12.5, 8.5, 1.6, ART); dot(15.0, 9.8, 1.4, NERVE)                                                  # 앞정강 혈관·깊은종아리신경
dot(-35, 0, 2.3, VEIN); dot(-36.5, -4, 1.4, NERVE); dot(-37.5, 7, 1.1, NERVE)                      # 큰두렁정맥·두렁신경 가지
dot(29, 22, 1.3, NERVE)                                                                                # 얕은종아리신경(피하)
dot(20, -36.5, 1.7, VEIN); dot(17, -38.5, 1.3, NERVE)                                                  # 작은두렁정맥·장딴지신경

# 자침: 정강뼈 안쪽면 뒤모서리 바로 뒤에서 가쪽으로 직자
ax.plot([-52, -40], [-12, -12], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((-40, -12), (-14, -14.5), arrowstyle="-|>", mutation_scale=16, lw=2.2, color="#111", zorder=9))
ax.add_patch(FancyArrowPatch((-14, -14.5), (2.5, -19), arrowstyle="-|>", mutation_scale=12, lw=1.5, color="#c1121f", ls="--", zorder=9))
ax.plot([-34.2], [-12.3], marker="|", ms=13, mew=2.2, color="#1d6fd6", zorder=10)
ax.text(-54, -6.5, "SP6 삼음교 자침점", ha="right", va="center", fontsize=12.5, weight="bold", zorder=10)
ax.text(-54, -12, "정강뼈 안쪽면 뒤모서리 뒤 · 안쪽복사 끝 위 3寸", ha="right", va="center", fontsize=8.6, color="#333")
ax.text(-42, -19.5, "고전 3푼\n(6.9mm)", ha="right", fontsize=7.8, color="#1d6fd6", zorder=10)


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 50, -50
lab(5, 25, R, 62, "앞정강근·긴엄지폄근·긴발가락폄근 (앞칸)", "#8f2d2a")
lab(15, 9.8, R, 50, "깊은종아리신경·앞정강동맥 (사이막 앞)", "#8a6d00")
lab(16, -2, R, 39, "종아리뼈사이막 FMA:35187", "#4b3f6f")
lab(33, -4, R, 17, "종아리근 (가쪽칸)", "#8f4a2a")
lab(24, -6, R, 28, "종아리뼈 Fibula FMA:24479", "#5b4f33")
lab(8, -11, R, 6, "③ 뒤정강근 Tibialis posterior FMA:51099 [김재효]\n    분절 L5·S1", "#7a5a3a")
lab(20, -20, R, -18, "긴엄지굽힘근 FMA:22593 (교재 미기재)", "#7a5a3a")
lab(4.8, -19.4, R, -6, "④ 정강신경 Tibial n. FMA:19035 [공통]\n    → 궁둥신경 → 엉치신경얼기", "#8a6d00")
lab(0, -21, R, -30, "④ 뒤정강동맥·정맥 FMA:43895 / 44332 [공통]", "#b02020")
lab(14, -32, R, -41, "② 가자미근 Soleus FMA:22542 [공통] · 분절 S1·S2", "#6e3a2e")
lab(20, -36.5, R, -52, "작은두렁정맥·장딴지신경 (뒤 피하)", "#2f5fb3")
lab(4, -42, R, -62, "발꿈치힘줄 FMA:51061", "#5b4f33")

lab(-14, 20, L, 60, "정강뼈 Tibia FMA:24476 (안쪽면은 피하)", "#5b4f33")
lab(-37.5, 7, L, 44, "① 두렁신경 안쪽종아리피부가지 FMA:75559 [공통]", "#8a6d00")
lab(-35, 0, L, 30, "① 큰두렁정맥 Great saphenous v. FMA:21376 [공통]", "#2f5fb3")
lab(-20, -14, L, -30, "③ 긴발가락굽힘근 FDL FMA:51071 [공통]\n    분절 S1·S2(주)·L5 — 직자 1~1.5寸 도달층(추정)", "#7a5a3a")
lab(-12, -20, L, -46, "가로근육사이막 (뒤칸 얕은층/깊은층 경계)", "#8a6a55")
lab(-36.5, -4, L, 18, "두렁신경 Saphenous n. FMA:45262 (넙다리신경 가지)", "#8a6d00")

ax.text(-116, 76, "삼음교(SP6, 현대 정위) 높이 하퇴 하1/3 횡단면 — 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-116, 69.5, "오른다리 · 위에서 내려다봄 · 앞쪽=위, 안쪽=왼쪽 · 축척 아님  ·  [주의] 孕妇禁针(铜人 '妊娠不可刺', 교재) — 자침깊이 DB '0'(금침) 기록은 없음",
        fontsize=9.3, color="#444", va="top")
ax.text(-116, -70,
        "검은 실선: 직자(현대 교재·通考 1~1.5寸 = 23~34.5mm) — 큰두렁정맥·두렁신경을 피해 정강뼈 뒤모서리 뒤로 들어가 긴발가락굽힘근에 이른다(추정). 파란 표시: 고전 3푼(《甲乙》·《铜人》 '针入三分').\n"
        "빨간 점선: 더 깊이 들어가면 정강신경·뒤정강동정맥 — 上海《针灸学》 \"麻电感向足底放散\"(通考 L1385)은 정강신경 자극을 뜻한다. 층 두께·거리는 SP6 실측값이 없어 임의 배치.\n"
        "[공통]=두 교재 공통, [김재효]=김재효 교재만 기재. 《黄帝明堂经》의 원래 '三阴交'(안쪽복사 위 8寸, 通考 名实考)는 이 단면보다 5寸 위로, 그림에 없다(보고서 7절).\n"
        "구조·FMA ID·분절은 FMA 5.1.0과 2대 교재 데이터셋 기준. 근육 분절은 FMA segmental_supply, 신경 분절은 FMA 미기재.",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-110 + i * 17, -60), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-107 + i * 17, -60, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

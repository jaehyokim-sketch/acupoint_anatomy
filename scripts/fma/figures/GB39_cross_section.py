# -*- coding: utf-8 -*-
"""GB39 현종 높이(外踝上3寸) 하퇴 하1/3 횡단면 모식도 (오른다리, 위에서 내려다봄, 앞쪽 위·안쪽 왼쪽). 축척 아님.
ST36_cross_section.py와 같은 방식. T1 고전 맥동점(경골 쪽 앞정강동맥) / T2 WHO 비골 전연 두 표적을 함께 표시.
구조·FMA ID·지배·분절은 fma_query.py profile GB39 및 2대 교재 데이터셋, 표적·심도·안전은 GB39 보고서 4·5·7절 기준."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch

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

skin = [(0, 42), (20, 40), (36, 30), (46, 12), (46, -10), (38, -32), (20, -48), (0, -54), (-20, -50),
        (-36, -38), (-44, -18), (-44, 4), (-36, 24), (-20, 38)]
blob(ax, skin, "#f6dccb", "#b07a5a", 1.6, 1)
blob(ax, [(x * 0.92, y * 0.92 - 1) for x, y in skin], "#fbeee6", "#8a6a55", 1.0, 1.5, ls="--")   # 종아리근막

# 뼈: 정강뼈(앞안쪽, 하1/3에서는 단면이 작아짐), 종아리뼈(가쪽, 뒤로 치우침)
blob(ax, [(-14, 33), (-26, 18), (-34, 2), (-24, -6), (-8, -2), (2, 8), (-4, 22)], "#efe8d2", "#7d6f4f", 1.4, 4)
blob(ax, [(-16, 20), (-24, 8), (-14, 3), (-8, 9)], "#f9f5e8", "#bfb391", 0.6, 4.5)
ax.add_patch(Circle((27, -4), 6.0, fc="#efe8d2", ec="#7d6f4f", lw=1.4, zorder=4))
ax.plot([2, 9, 15, 22], [8, 5, 1, -3], color="#6d5f8f", lw=2.2, zorder=4.2)      # 종아리뼈사이막

# 앞칸: 앞정강근(이 높이에서는 힘줄화) · 긴엄지폄근 · 긴발가락폄근 · 셋째종아리근
blob(ax, [(-6, 36), (4, 37), (6, 28), (2, 22), (-4, 26)], "#d9534f", "#8f2d2a", 1.0, 3)        # 앞정강근(건)
blob(ax, [(5, 30), (12, 33), (16, 24), (12, 14), (6, 16)], "#e9897a", "#8f2d2a", 1.0, 3)       # 긴엄지폄근
blob(ax, [(15, 35), (28, 30), (34, 18), (30, 6), (22, 6), (16, 16)], "#e57f6c", "#8f2d2a", 1.0, 3)  # 긴발가락폄근
blob(ax, [(30, 22), (36, 20), (37, 12), (32, 10)], "#f0a090", "#8f2d2a", 0.8, 3.2, ls="--")    # 셋째종아리근(김재효)
# 가쪽칸: 짧은종아리근(근복) · 긴종아리근(힘줄)
blob(ax, [(34, 8), (42, 4), (42, -12), (34, -16), (32, -8)], "#d88c6f", "#8f4a2a", 1.0, 3)
ax.add_patch(Circle((40, -16), 3.4, fc="#f3d2b3", ec="#8f4a2a", lw=1.0, zorder=3.4))
# 뒤칸 깊은층: 긴엄지굽힘근(종아리뼈 뒤) · 뒤정강근 · 긴발가락굽힘근
blob(ax, [(14, -10), (28, -12), (32, -22), (22, -30), (10, -24)], "#c9a27e", "#7a5a3a", 1.0, 3)   # 긴엄지굽힘근
blob(ax, [(-2, -4), (12, -6), (10, -18), (-2, -16)], "#d6b896", "#7a5a3a", 0.9, 3)              # 뒤정강근
blob(ax, [(-22, -10), (-6, -10), (-6, -20), (-20, -22)], "#d6b896", "#7a5a3a", 0.9, 3)          # 긴발가락굽힘근
# 뒤칸 얕은층: 가자미근 · 발꿈치힘줄 형성부
blob(ax, [(-30, -26), (-8, -30), (14, -34), (30, -30), (24, -42), (0, -46), (-24, -40)], "#b56b5a", "#6e3a2e", 1.0, 3)
ax.plot([-26, -6, 14, 26], [-22, -26, -30, -26], color="#8a6a55", lw=1.0, ls="--", zorder=3.5)  # 가로근육사이막


def dot(x, y, r, fc, ec="#333", z=6):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
dot(6.5, 11.5, 2.0, ART); dot(4.2, 10.2, 1.2, VEIN); dot(8.8, 9.8, 1.2, VEIN); dot(10.8, 13.0, 1.7, NERVE)   # 앞정강 신경혈관속
dot(20, -16, 1.6, ART); dot(17.6, -17.2, 1.0, VEIN); dot(22.4, -17.6, 1.0, VEIN)                         # 종아리동·정맥
ax.plot([22, 24, 25], [-4, 3, 8], color=ART, lw=1.3, ls=":", zorder=5.5)                                 # 관통가지
dot(-12, -24, 1.7, ART); dot(-14.2, -25.2, 1.0, VEIN); dot(-9.8, -25.4, 1.0, VEIN); dot(-7, -23, 1.8, NERVE)  # 뒤정강·정강신경
dot(35, 31, 1.6, NERVE)                                                                                  # 얕은종아리신경(피하)
dot(42, -30, 1.3, NERVE)                                                                                 # 가쪽장딴지피부신경
dot(-40, -4, 2.0, VEIN); dot(-39, -9, 1.3, NERVE)                                                       # 큰두렁정맥·두렁신경
dot(6, -52, 1.6, VEIN); dot(10, -51, 1.2, NERVE)                                                         # 작은두렁정맥·장딴지신경

# 표적과 자침 경로
for x, txt, col in ((-2, "T1", "#7b2cbf"), (28, "T2", "#111")):
    ax.plot([x, x], [54, 43], color=col, lw=1.0, zorder=7)
    ax.text(x, 56, txt, ha="center", va="bottom", fontsize=12.5, weight="bold", color=col, zorder=9)
ax.add_patch(FancyArrowPatch((-2, 43), (5, 15), arrowstyle="-|>", mutation_scale=15, lw=2.0, color="#7b2cbf", zorder=8))
ax.add_patch(FancyArrowPatch((28, 40.5), (28, 24), arrowstyle="-|>", mutation_scale=15, lw=2.0, color="#111", zorder=8))
ax.annotate("", xy=(-2, 63), xytext=(28, 63), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#444"))
ax.text(13, 64.5, "Δ ≈ 20~35mm (채점자 추정, 실측 아님)", ha="center", fontsize=8.6, color="#333")
ax.plot([-14], [37.5], marker="v", ms=8, color="#7d6f4f", zorder=9)
ax.text(-16, 41, "정강뼈 앞모서리", ha="right", fontsize=8.5, color="#5b4f33")


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=10,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 58, -58
RIGHT = [  # (anchor_x, anchor_y, text, color) — 위에서 아래 순서로 배치해 지시선 교차를 줄인다
    (24, 24, "② 긴발가락폄근 Extensor digitorum longus  FMA:22534  [공통] · L5(주)·S1", "#8f2d2a"),
    (35, 31, "① 얕은종아리신경 Superficial fibular n.  FMA:44699  [공통] (피하)", "#8a6d00"),
    (10.8, 13, "④ 깊은종아리신경 Deep fibular n.  FMA:44771  [공통]", "#8a6d00"),
    (6.5, 11.5, "④ 앞정강동·정맥 Anterior tibial a./v.  FMA:43894 / 44331  [공통]", "#b02020"),
    (34, 16, "② 셋째종아리근 Fibularis tertius  FMA:22538  [김재효] (점선)", "#8f2d2a"),
    (24, 3, "종아리동맥 관통가지 (점선)  FMA:44033  [김재효]", "#b02020"),
    (39, -2, "② 짧은종아리근 Fibularis brevis  FMA:22540  [공통] · L5·S1", "#8f4a2a"),
    (31, -7, "⑤ 종아리뼈 Fibula  FMA:24479", "#5b4f33"),
    (40, -16, "② 긴종아리근(힘줄) Fibularis longus  FMA:22539  [공통교재]", "#8f4a2a"),
    (20, -16, "종아리동·정맥 Fibular a./v.  FMA:43921 / 44558  [김재효] (뒤칸)", "#b02020"),
    (26, -24, "긴엄지굽힘근 Flexor hallucis longus  FMA:22593  [김재효] (뒤칸, 정강신경)", "#7a5a3a"),
    (42, -30, "① 가쪽장딴지피부신경 Lateral sural cutaneous n.  FMA:44697  [김재효]", "#8a6d00"),
    (-7, -23, "정강신경·뒤정강동정맥 (뒤칸 깊은층, 교재 미기재)", "#555"),
]
for i, (x, y, t, c) in enumerate(RIGHT):
    lab(x, y, R, 58 - i * 9.2, t, c)

lab(-20, 14, L, 30, "⑤ 정강뼈 Tibia  FMA:24476", "#5b4f33")
lab(0, 31, L, 50, "② 앞정강근(힘줄화) Tibialis anterior  FMA:22532 (교재 미기재)", "#8f2d2a")
lab(10, 24, L, 37, "③ 긴엄지폄근 Extensor hallucis longus  FMA:22533  [공통]", "#8f2d2a")
lab(10, 4, L, 9, "④ 종아리뼈사이막 Interosseous membrane  FMA:35187", "#4b3f6f")
lab(-40, -4, L, -2, "큰두렁정맥·두렁신경 (피하, 안쪽)", "#2f5fb3")
lab(-14, -16, L, -15, "긴발가락굽힘근 · 뒤정강근 (뒤칸 깊은층)", "#7a5a3a")
lab(-10, -38, L, -32, "가자미근 · 발꿈치힘줄 형성부", "#6e3a2e")
lab(6, -52, L, -46, "작은두렁정맥·장딴지신경 (피하, 뒤)", "#2f5fb3")

ax.text(-114, 80, "현종(GB39) 높이 하퇴 하1/3 횡단면 — 해부 실체 모식도 (T1·T2 분기)", fontsize=15.5, weight="bold", va="top")
ax.text(-114, 73.5, "오른다리 · 위에서 내려다봄 · 앞쪽=위, 안쪽=왼쪽 · 外踝(尖)上 3寸 높이 · 축척 아님", fontsize=9.5, color="#444", va="top")
ax.text(-114, -62, "보라 화살표 T1 고전 맥동점(《明堂》 \"動者脈中·按之陽明脈絶\", 通考 L431·552, papers.id 1624): 경골 쪽 앞정강동맥 위 → 6푼(13.8mm) 직자로 ④ 신경혈관속 접촉 가능, 동맥 회피·심도 제한(SI 50)\n"
        "검은 화살표 T2 WHO 비골 전연(外踝尖上3寸, 腓骨前缘): 5~8푼(11.5~18.4mm) → ①~② 층 중심, 깊으면 ④ 도달 가능(SI 75). Δ > 15mm → 분기(보고서 7절)\n"
        "[공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 김재효 단독 구조(긴엄지굽힘근·종아리동정맥)는 FMA상 뒤칸 깊은층·정강신경 계통.\n"
        "구조·FMA ID·지배·분절은 FMA 5.1.0과 2대 교재 데이터셋 기준. 층 두께·거리는 GB39 실측값이 없어 임의 배치",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-108 + i * 17, -55), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-105 + i * 17, -55, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

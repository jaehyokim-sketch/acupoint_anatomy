# -*- coding: utf-8 -*-
"""LU09 태연 높이 손목(먼쪽 손목 주름) 횡단면 모식도 (오른손목, 몸쪽에서 내려다봄, 손바닥쪽 위·노쪽 오른쪽). 축척 아님.
ST36_cross_section.py와 같은 방식. 구조·FMA ID·지배·분절은 fma_query.py profile LU09 및 2대 교재 데이터셋, 위치·안전 기술은 《针灸腧穴通考》 L2193~2455."""
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
        p = np.empty((len(p) * 2, 2)); p[0::2], p[1::2] = q, r
    return p


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, ls="-"):
    ax.add_patch(Polygon(chaikin(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


fig, ax = plt.subplots(figsize=(13, 9.6), dpi=170)
ax.set_xlim(-124, 124); ax.set_ylim(-78, 76); ax.set_aspect("equal"); ax.axis("off")

skin = [(-58, 6), (-52, 22), (-34, 32), (-10, 35), (14, 34), (36, 28), (52, 16), (58, 0), (54, -16), (40, -28),
        (16, -34), (-10, -34), (-36, -30), (-52, -18)]
blob(ax, skin, "#f6dccb", "#b07a5a", 1.6, 1)
blob(ax, [(x * 0.92, y * 0.9) for x, y in skin], "#fbeee6", "#8a6a55", 0.9, 1.5, ls="--")   # 아래팔근막·굽힘근지지띠 쪽

# 뼈: 노뼈 먼쪽끝(붓돌기 쪽, 오른쪽)·자뼈머리(왼쪽)
blob(ax, [(0, -6), (16, -2), (34, -4), (46, -10), (44, -20), (28, -24), (8, -22), (-2, -16)], "#efe8d2", "#7d6f4f", 1.4, 3)
blob(ax, [(-36, -6), (-24, -4), (-20, -14), (-30, -20), (-40, -14)], "#efe8d2", "#7d6f4f", 1.4, 3)
ax.plot([48], [-12], marker="^", ms=7, color="#7d6f4f", zorder=4)
ax.text(36, -15, "붓돌기 ▶", fontsize=8, color="#5b4f33", zorder=9, ha="center")


def ell(x, y, w, h, fc, ec, z=4, ls="-"):
    ax.add_patch(Ellipse((x, y), w, h, fc=fc, ec=ec, lw=1.0, zorder=z, ls=ls))


TEND, TEND2 = "#f3efe4", "#e2d8bd"
# 손바닥쪽 힘줄
ell(16, 14, 9, 7, TEND, "#8a7a4a")          # 노쪽손목굽힘근 힘줄 (공통)
ell(10, 3, 8, 6, TEND2, "#8a7a4a")          # 긴엄지굽힘근 힘줄 (김재효)
ell(-3, 24, 6, 4, TEND, "#8a7a4a")          # 긴손바닥근 힘줄 (교재 미기재)
for (x, y) in [(-10, 12), (-18, 14), (-14, 5), (-22, 6)]:
    ell(x, y, 6, 5, TEND, "#9a9a9a")         # 손가락굽힘근 힘줄 (김재효: 얕은손가락굽힘근)
ell(-40, 12, 8, 6, TEND, "#9a9a9a")         # 자쪽손목굽힘근 힘줄
# 노쪽 가장자리: 긴엄지벌림근·짧은엄지폄근 힘줄, 위팔노근 힘줄(붓돌기 닿음)
ell(48, 4, 7, 6, "#efc9b8", "#8f4a2a"); ell(52, -4, 5, 5, "#efc9b8", "#8f4a2a")
ell(40, -1, 6, 4, TEND2, "#8a7a4a", z=3.6)
# 손등쪽 힘줄
ell(16, -28, 6, 4.5, "#efc9b8", "#8f4a2a")  # 긴엄지폄근 (공통교재)
ell(30, -26, 6, 4.5, TEND, "#9a9a9a"); ell(24, -30, 5.5, 4, TEND, "#9a9a9a")
for x in (-2, -10, -18):
    ell(x, -29, 6, 4, TEND, "#9a9a9a")
# 네모엎침근: 이 평면보다 몸쪽(점선)
blob(ax, [(-30, -2), (0, 0), (30, 0), (30, 5), (0, 7), (-30, 4)], "none", "#6e3a2e", 1.0, 3.7, ls="--")


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
dot(31, 13, 2.6, ART); dot(27.6, 11.4, 1.3, VEIN); dot(34.6, 11.4, 1.3, VEIN)     # 노동맥·노정맥 (공통)
dot(2, 13, 2.2, NERVE)                                                          # 정중신경 (교재 미기재)
dot(-31, 15, 1.9, ART); dot(-35, 16, 1.7, NERVE)                                # 자동맥·자신경
dot(52, -18, 2.0, VEIN); dot(46, -24, 1.4, VEIN)                                # 노쪽피부정맥·덧노쪽피부정맥
dot(55, -10, 1.5, NERVE); dot(50, -22, 1.3, NERVE)                              # 노신경 얕은가지
dot(40, 25, 1.4, NERVE); dot(30, 30, 1.3, NERVE)                                # 가쪽아래팔피부신경

# 자침: 노동맥 박동을 확인해 피한 직자 2~5푼
ax.plot([25, 25], [48, 35.3], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((25, 35.5), (25, 20), arrowstyle="-|>", mutation_scale=15, lw=2.0, color="#111", zorder=9))
ax.text(23, 46, "LU09 태연 자침점", ha="right", va="center", fontsize=12.5, weight="bold", zorder=9)
ax.text(23, 40.5, "먼쪽 손목 주름 노쪽 · 긴엄지벌림근 힘줄 자쪽 오목", ha="right", va="center", fontsize=8.5, color="#333", zorder=9)
ax.text(28, 46, "★ 노동맥: 박동을 손가락으로 밀어 피하고 직자 2~5푼(4.6~11.5mm)", ha="left", va="center", fontsize=9.2,
        color="#b01e2e", weight="bold", zorder=9)


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 64, -64
lab(40, 25, R, 34, "① 가쪽아래팔피부신경  FMA:39080  [공통]", "#8a6d00")
lab(31, 13, R, 22, "② 노동맥·노정맥 Radial a./v.  FMA:22730 / 22947  [공통]", "#b02020")
lab(48, 4, R, 10, "② 긴엄지벌림근 힘줄  FMA:38515  [공통교재]\n    뒤뼈사이신경(노신경) · 분절 C7(주)·C8", "#8f4a2a")
lab(40, -1, R, -2, "위팔노근 힘줄  FMA:40689  [김재효]", "#8a7a4a")
lab(55, -10, R, -13, "① 노신경 얕은가지  FMA:292885  [공통]", "#8a6d00")
lab(52, -18, R, -23, "① 노쪽피부정맥  FMA:13324 [공통] · 덧노쪽피부정맥 22970 [김재효]", "#2f5fb3")
lab(16, -28, R, -46, "긴엄지폄근 힘줄  FMA:38521  [공통교재] (손등쪽, 자침 경로 밖)", "#8f4a2a")
lab(30, -18, R, -35, "노뼈 먼쪽끝  (손배뼈와의 사이 = 정위 기준, 通考 L2207)", "#5b4f33")

lab(16, 14, L, 50, "② 노쪽손목굽힘근 힘줄  FMA:38582  [공통]\n    정중신경 가지 · 분절 C6(주)·C7", "#8a7a4a")
lab(-18, 14, L, 36, "손가락굽힘근 힘줄  (얕은손가락굽힘근 FMA:38469 [김재효])", "#777")
lab(-31, 15, L, 24, "자동맥·자신경 (자쪽, 경로 밖)", "#555")
lab(2, 13, L, 12, "정중신경 (교재 미기재, 경로 밖 자쪽)", "#8a6d00")
lab(10, 3, L, 6, "③ 긴엄지굽힘근 힘줄  FMA:38673  [김재효]", "#8a7a4a")
lab(-28, 3, L, -10, "네모엎침근 FMA:38453 [김재효] — 이 평면보다 몸쪽(점선)", "#6e3a2e")
lab(-30, -12, L, -26, "자뼈머리", "#5b4f33")

ax.text(-120, 74, "태연(LU09) 높이 손목 횡단면 — 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-120, 67.5, "오른손목 · 먼쪽 손목 주름 높이 · 몸쪽에서 내려다봄 · 손바닥쪽=위, 노쪽(가쪽)=오른쪽 · 축척 아님", fontsize=9.5,
        color="#444", va="top")
ax.text(-120, -52, "자침 화살표: 직자 2~5푼(자침깊이 DB: 明堂·甲乙·경험방·동의보감 2푼, 교재·通考 3~5푼). 금침 기록은 DB에 없으나 《针方六集》 \"不宜用针\", 《窦太师针经》 \"孕妇不可针\",\n"
        "7판 《针灸学》 \"避开桡动脉\"(通考 L2437·2435·2451). 노동맥은 손목 주름 높이에서 긴엄지벌림근 힘줄 노쪽으로 비켜 가는 변이가 많다(通考 L2211: 붓돌기 아래 44.8%, 위 15.5%, 같은 높이 27.6%).\n"
        "[공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 김재효 교재의 원엎침근·얕은손가락굽힘근 근복은 아래팔 몸쪽 구조라 이 높이에 없다(힘줄만 표시).\n"
        "구조·FMA ID·지배·분절은 FMA 5.1.0과 2대 교재 데이터셋 기준. 층 두께·거리는 LU09 실측값이 없어 임의 배치.",
        fontsize=8.3, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-114 + i * 17, -44), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-111 + i * 17, -44, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

# -*- coding: utf-8 -*-
"""LU03 천부·LU04 협백 높이 위팔 위·중간 1/3 횡단면 모식도 (오른팔, 위에서 내려다봄, 앞쪽 위·안쪽 왼쪽). 축척 아님.
ST36_cross_section.py와 같은 방식. Target 1 고전 동맥점(cLU3/4, 안쪽 위팔두갈래근고랑) / Target 2 WHO 정위(pLU3/4, 위팔두갈래근 가쪽 모서리).
LU03(앞겨드랑주름 아래 3촌)과 LU04(4촌)는 1촌 차이로 단면 구성이 거의 같아 한 장에 그리고, 높이에 따라 달라지는 구조는 점선으로 표시.
구조·FMA ID·지배·분절은 fma_query.py profile LU03/LU04 및 2대 교재 데이터셋, 표적·심도·안전은 통합보고서 4·5·7절 기준."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
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

skin = [(0, 46), (22, 42), (38, 30), (46, 10), (44, -14), (34, -34), (16, -46), (-4, -48), (-24, -42),
        (-40, -28), (-46, -6), (-42, 16), (-30, 34), (-14, 44)]
blob(ax, skin, "#f6dccb", "#b07a5a", 1.6, 1)
blob(ax, [(x * 0.92, y * 0.92 - 1) for x, y in skin], "#fbeee6", "#8a6a55", 1.0, 1.5, ls="--")   # 위팔근막

ax.add_patch(Circle((4, -4), 10, fc="#efe8d2", ec="#7d6f4f", lw=1.4, zorder=4))                  # 위팔뼈
ax.add_patch(Circle((4, -4), 5, fc="#f9f5e8", ec="#bfb391", lw=0.6, zorder=4.5))

# 앞칸
blob(ax, [(-14, 30), (2, 38), (16, 37), (30, 28), (32, 18), (20, 14), (4, 16), (-12, 18)], "#d9534f", "#8f2d2a", 1.1, 3)  # 위팔두갈래근
ax.plot([6, 8], [37, 15], color="#8f2d2a", lw=0.8, ls=":", zorder=3.2)                           # 긴갈래(가쪽)·짧은갈래(안쪽) 경계
blob(ax, [(-10, 14), (6, 12), (22, 12), (26, 4), (14, 4), (-4, 4), (-12, 6)], "#e9897a", "#8f2d2a", 1.0, 3)     # 위팔근(깊은층)
blob(ax, [(-24, 18), (-14, 20), (-12, 10), (-20, 6), (-26, 10)], "#f0a090", "#8f2d2a", 0.9, 3.1, ls="--")     # 부리위팔근(cLU3 높이)
# 뒤칸: 위팔세갈래근
blob(ax, [(-30, -10), (-14, -14), (4, -18), (22, -16), (36, -14), (34, -28), (16, -40), (-6, -42), (-26, -32)], "#b56b5a", "#6e3a2e", 1.0, 3)
ax.plot([-28, -16, -6], [-12, -10, -6], color="#8a6a55", lw=1.1, ls="--", zorder=3.5)            # 안쪽 근육사이막
ax.plot([16, 28, 38], [-6, -8, -10], color="#8a6a55", lw=1.1, ls="--", zorder=3.5)               # 가쪽 근육사이막
# 어깨세모근 정지부·큰가슴근 정지부 (천부 높이, 김재효)
blob(ax, [(32, 22), (40, 14), (40, 0), (34, 4), (32, 14)], "none", "#6e3a2e", 1.0, 3.6, ls="--")
blob(ax, [(18, 34), (28, 30), (26, 26), (16, 30)], "none", "#6e3a2e", 1.0, 3.6, ls="--")


def dot(x, y, r, fc, ec="#333", z=6):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
# 안쪽 위팔두갈래근고랑 신경혈관속 (cLU)
dot(-26, 4, 2.4, ART); dot(-28.8, 2.6, 1.3, VEIN); dot(-23.4, 2.0, 1.3, VEIN)
dot(-22, 8, 2.0, NERVE)              # 정중신경(동맥 가쪽·앞)
dot(-30, -2, 1.8, NERVE)             # 자신경(동맥 안쪽·뒤)
dot(-32, 8, 1.3, NERVE)              # 안쪽아래팔피부신경
dot(-38, 2, 2.0, VEIN)               # 자쪽피부정맥(피하→근막 관통)
dot(-40, -10, 1.2, NERVE)            # 안쪽위팔피부신경(T1)
dot(-34, -24, 1.2, NERVE)            # 갈비사이위팔신경(T2)
# 근피신경 (위팔두갈래근–위팔근 사이)
dot(14, 13, 1.8, NERVE)
# 노신경·깊은위팔동맥 (뒤, 나선고랑)
dot(14, -14, 1.8, NERVE); dot(11, -15, 1.3, ART)
# 피하 가쪽
dot(36, 26, 2.0, VEIN)               # 노쪽피부정맥
dot(42, 4, 1.2, NERVE)               # 위가쪽위팔피부신경(겨드랑신경)
dot(41, -12, 1.2, NERVE)             # 아래가쪽위팔피부신경(노신경)

# 표적과 자침 경로
ax.plot([-58, -47], [7, 6.5], color="#7b2cbf", lw=1.0, zorder=7)                        # T1: 안쪽 면에서 고랑으로
ax.add_patch(FancyArrowPatch((-47, 6.5), (-31.5, 5.5), arrowstyle="-|>", mutation_scale=14, lw=2.0, color="#7b2cbf", zorder=8))
ax.text(-40, 54, "T1 cLU3/4", ha="center", va="bottom", fontsize=11.5, weight="bold", color="#7b2cbf", zorder=9)
ax.plot([-40, -50, -52], [53, 20, 8.5], color="#7b2cbf", lw=0.8, ls=":", zorder=7)
ax.plot([33, 33], [52, 36], color="#111", lw=1.0, zorder=7)
ax.text(33, 54, "T2 pLU3/4", ha="center", va="bottom", fontsize=11.5, weight="bold", color="#111", zorder=9)
ax.add_patch(FancyArrowPatch((33, 35), (24, 16), arrowstyle="-|>", mutation_scale=14, lw=2.0, color="#111", zorder=8))
ax.annotate("", xy=(-40, 63), xytext=(33, 63), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#444"))
ax.text(-3.5, 64.5, "Δ ≈ 28~29mm (모델 추정, 실측 아님)", ha="center", fontsize=8.6, color="#333")


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=10,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 56, -60
RIGHT = [
    (22, 32, "큰가슴근 정지부 Pectoralis major  FMA:9627  [김재효] (천부 높이, 점선)", "#6e3a2e"),
    (18, 26, "② 위팔두갈래근 Biceps brachii  FMA:37670 [공통교재] · 긴갈래 FMA:37683 [김재효] · C5·C6", "#8f2d2a"),
    (36, 26, "① 노쪽피부정맥 Cephalic v.  FMA:13324  [공통]", "#2f5fb3"),
    (14, 13, "④ 근육피부신경 Musculocutaneous n.  FMA:37064  [김재효]", "#8a6d00"),
    (37, 12, "어깨세모근 정지부 Deltoid  FMA:32521  [김재효] (천부 높이, 점선)", "#6e3a2e"),
    (42, 4, "① 위가쪽위팔피부신경  FMA:65303  [김재효] (겨드랑신경)", "#8a6d00"),
    (20, 8, "③ 위팔근 Brachialis  FMA:37667 (교재 미기재)", "#8f2d2a"),
    (41, -12, "① 아래가쪽위팔피부신경  FMA:44949  [공통교재] (노신경)", "#8a6d00"),
    (4, -4, "⑤ 위팔뼈 Humerus  FMA:13303", "#5b4f33"),
    (14, -14, "노신경·깊은위팔동맥 (뒤, 나선고랑, 교재 미기재)", "#555"),
    (20, -28, "위팔세갈래근 Triceps brachii (뒤칸)", "#6e3a2e"),
]
for i, (x, y, t, c) in enumerate(RIGHT):
    lab(x, y, R, 58 - i * 11, t, c)

LEFT = [
    (-20, 14, "③ 부리위팔근 Coracobrachialis  FMA:37664 (cLU3 높이, 교재 미기재)", "#8f2d2a"),
    (-22, 8, "④ 정중신경 Median n.  FMA:14385  [공통교재] (동맥 가쪽)", "#8a6d00"),
    (-32, 8, "④ 안쪽아래팔피부신경 (교재 미기재)", "#8a6d00"),
    (-26, 4, "④ 위팔동·정맥 Brachial a./v.  FMA:22689 / 22934  [공통교재]", "#b02020"),
    (-38, 2, "① 자쪽피부정맥 Basilic v.  FMA:22908 (교재 미기재)", "#2f5fb3"),
    (-30, -2, "④ 자신경 Ulnar n.  FMA:37319 (동맥 안쪽, 교재 미기재)", "#8a6d00"),
    (-40, -10, "① 안쪽위팔피부신경  FMA:65246 (안쪽다발, T1)", "#8a6d00"),
    (-22, -11, "안쪽 근육사이막  FMA:37886", "#8a6a55"),
    (-34, -24, "① 갈비사이위팔신경  FMA:11307 (둘째 갈비사이신경 가쪽피부가지, T2)", "#8a6d00"),
]
for i, (x, y, t, c) in enumerate(LEFT):
    lab(x, y, L, 40 - i * 9.5, t, c)

ax.text(-114, 80, "천부(LU3)·협백(LU4) 높이 위팔 위·중간 1/3 횡단면 — 해부 실체 모식도 (Target 1·2 분기)", fontsize=15, weight="bold", va="top")
ax.text(-114, 73.5, "오른팔 · 위에서 내려다봄 · 앞쪽=위, 안쪽(몸통 쪽)=왼쪽 · LU3=앞겨드랑주름 아래 3촌, LU4=4촌(구성 거의 같음) · 축척 아님", fontsize=9.3, color="#444", va="top")
ax.text(-114, -56, "보라 화살표 T1(고전 '臂臑內廉動脈中', 송석모·通考): 안쪽 위팔두갈래근고랑 위팔동맥 박동 위. 고전 4푼(9.2mm)이 ④ 위팔동맥·정중신경 깊이와 겹침\n"
        "→ 동맥을 손가락으로 비켜 고정하고 ≤ 3~4푼 얕게, 전격감 시 즉시 발침, 직접 뜸 금지(보고서 5절 안전 수칙, SI 50).\n"
        "검은 화살표 T2(WHO 위팔두갈래근 가쪽 모서리): 교재 5~10푼(11.5~23mm) → ②~③ 근육층, 하한에서 ④ 근육피부신경 도달 가능(SI 75).\n"
        "[공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 공통교재의 정중신경·위팔동정맥은 T1 쪽 구조, 김재효의 근육피부신경 계열은 T2 쪽 구조(6절 혼합형 판정).\n"
        "구조·FMA ID는 FMA 5.1.0과 2대 교재 데이터셋 기준(위가쪽위팔피부신경은 교재 표기 누락으로 자동 대응 실패 → FMA:65303 수동 대응). 층 두께·거리는 실측값이 없어 임의 배치",
        fontsize=8.3, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-108 + i * 17, -50), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-105 + i * 17, -50, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

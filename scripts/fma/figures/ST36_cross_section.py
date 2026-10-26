# -*- coding: utf-8 -*-
"""ST36 높이 하퇴 상1/3 횡단면 모식도 (오른다리, 위에서 내려다봄, 앞쪽 위·안쪽 왼쪽). 축척 아님."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]   # 간체자(胫 등)는 YaHei로 대체
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


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, alpha=1.0, ls="-"):
    ax.add_patch(Polygon(chaikin(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, alpha=alpha, ls=ls))


fig, ax = plt.subplots(figsize=(13, 10.4), dpi=170)
ax.set_xlim(-118, 118); ax.set_ylim(-92, 88); ax.set_aspect("equal"); ax.axis("off")

skin = [(0, 50), (24, 46), (42, 34), (54, 12), (54, -14), (46, -38), (24, -58), (0, -64), (-24, -60),
        (-44, -46), (-54, -22), (-54, 2), (-44, 26), (-24, 44)]
blob(ax, skin, "#f6dccb", "#b07a5a", 1.6, 1)                                   # 피부·피하
blob(ax, [(x * 0.92, y * 0.92 - 1) for x, y in skin], "#fbeee6", "#8a6a55", 1.0, 1.5, ls="--")  # 종아리근막(심부근막)

# 뼈
blob(ax, [(-15, 44), (-30, 27), (-46, 6), (-36, -4), (-12, 1), (5, 8), (-2, 24)], "#efe8d2", "#7d6f4f", 1.4, 4)
blob(ax, [(-17, 28), (-29, 13), (-15, 7), (-6, 13)], "#f9f5e8", "#bfb391", 0.6, 4.5)
ax.add_patch(Circle((31, -15), 6.5, fc="#efe8d2", ec="#7d6f4f", lw=1.4, zorder=4))
ax.plot([6, 13, 20, 26], [8, 3, -3, -10], color="#6d5f8f", lw=2.2, zorder=4.2)        # 종아리뼈사이막

# 앞칸 근육
blob(ax, [(-8, 41), (8, 41), (13, 30), (12, 16), (7, 10), (-1, 20), (-6, 32)], "#d9534f", "#8f2d2a", 1.1, 3)   # 앞정강근
blob(ax, [(16.5, 39), (31, 33), (37.5, 20), (34.5, 4), (27.5, -6), (20.5, 1), (15.5, 15), (15.5, 28)], "#e57f6c", "#8f2d2a", 1.1, 3)  # 긴발가락폄근
ax.plot([13.9, 14.0, 13.8], [41, 28, 15], color="#7b2fbf", lw=0.9, ls=(0, (3, 2)), zorder=3.6)                # 앞정강근–긴발가락폄근 근간 중격(兩筋間)
# 가쪽칸
blob(ax, [(38, 22), (49, 12), (50, -12), (42, -22), (36, -20), (38, -6), (36, 8)], "#d88c6f", "#8f4a2a", 1.0, 3)  # 긴종아리근
# 뒤칸 깊은층
blob(ax, [(2, 4), (13, -1), (24, -13), (20, -22), (6, -17), (-4, -8)], "#c9a27e", "#7a5a3a", 1.0, 3)  # 뒤정강근
blob(ax, [(-26, -4), (-10, -3), (-6, -12), (-14, -18), (-26, -14)], "#c9a27e", "#7a5a3a", 1.0, 3)  # 긴발가락굽힘근
# 뒤칸 얕은층
blob(ax, [(-36, -16), (-12, -22), (12, -24), (36, -26), (44, -34), (24, -42), (-6, -44), (-36, -32)], "#b56b5a", "#6e3a2e", 1.0, 3)  # 가자미근
blob(ax, [(-44, -36), (-24, -44), (-4, -48), (-6, -58), (-24, -58), (-42, -48)], "#a65a4a", "#5e2e24", 1.0, 3)  # 장딴지근 안쪽갈래
blob(ax, [(2, -48), (24, -44), (44, -38), (36, -50), (18, -58), (2, -58)], "#a65a4a", "#5e2e24", 1.0, 3)  # 장딴지근 가쪽갈래
ax.plot([-30, -10, 10, 28], [-12, -20, -22, -20], color="#8a6a55", lw=1.0, ls="--", zorder=3.5)        # 가로근육사이막


def dot(x, y, r, fc, ec="#333", z=6):
    ax.add_patch(Circle((x, y), r, fc=fc, ec=ec, lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
# 앞정강 신경혈관속 (종아리뼈사이막 앞)
dot(10.5, 9.5, 2.1, ART); dot(7.8, 8.2, 1.3, VEIN); dot(13.0, 8.0, 1.3, VEIN); dot(15.6, 11.2, 1.8, NERVE)
# 뒤정강 혈관·정강신경
dot(-4, -21, 1.8, ART); dot(-6.4, -22.3, 1.1, VEIN); dot(-1.6, -22.6, 1.1, VEIN); dot(1.4, -19.6, 1.9, NERVE)
# 얕은종아리신경 (가쪽칸)
dot(37.5, -9, 1.6, NERVE)
# 피하
dot(-49, -8, 2.2, VEIN); dot(-48, -14, 1.4, NERVE)            # 큰두렁정맥 + 두렁신경
dot(-50, 4, 1.2, NERVE); dot(-47, 13, 1.2, NERVE)             # 두렁신경 안쪽종아리피부가지
dot(2, -61, 1.8, VEIN)                                         # 작은두렁정맥
dot(47, -32, 1.4, NERVE)                                       # 가쪽장딴지피부신경

# 가로 방향 3계통 자침 경로 (보고서 7절): Target 1≡3 · Target 2 · 내측 편위(기록만)
T13, T2, MED = "#111", "#7b2fbf", "#8a8a8a"
# Target 1≡3: 胻外廉 / WHO — 정강뼈 앞모서리 외측 1횡지, 앞정강근 근복
ax.add_patch(FancyArrowPatch((3, 48.5), (8.5, 15.5), arrowstyle="-|>", mutation_scale=16, lw=2.0, color=T13, zorder=8))
ax.add_patch(FancyArrowPatch((3, 48.5), (1.0, 14.0), arrowstyle="-|>", mutation_scale=12, lw=1.1, color="#666", ls="--", zorder=8))
# Target 2: 兩筋間 — 근간 중격을 따라 앞정강 신경혈관속으로
ax.add_patch(FancyArrowPatch((13.9, 47.5), (13.6, 14.2), arrowstyle="-|>", mutation_scale=16, lw=2.0, color=T2, zorder=8))
# 내측 편위: 《圣惠》 筋骨之间 — 정강뼈 가쪽면과 앞정강근 사이
ax.add_patch(FancyArrowPatch((-9.5, 47.5), (-4.5, 27.5), arrowstyle="-|>", mutation_scale=12, lw=1.4, color=MED, ls="-.", zorder=8))
for x, y, c in [(3, 49.6, T13), (13.9, 48.6, T2), (-9.5, 48.2, MED)]:
    ax.plot([x], [y + 1.2], marker="v", ms=7, color=c, zorder=9)
ax.plot([-15], [46.5], marker="v", ms=8, color="#7d6f4f", zorder=9)
# 정강뼈 앞모서리 기준 가로 거리(추정)
ax.annotate("", xy=(-15, 53.5), xytext=(3, 53.5), arrowprops=dict(arrowstyle="<->", lw=0.9, color="#444"))
ax.text(-16.5, 53.5, "정강뼈 앞모서리 ↔ 1횡지 ≈ 1.5~2cm", ha="right", va="center", fontsize=8.2, color="#333")
ax.annotate("", xy=(-15, 58.5), xytext=(13.9, 58.5), arrowprops=dict(arrowstyle="<->", lw=0.9, color=T2))
ax.text(-16.5, 58.5, "정강뼈 앞모서리 ↔ ≈ 2.5~3.5cm (추정) · 「訛穴」 '自骨邊橫量一寸'", ha="right", va="center", fontsize=8.2, color=T2)
# 계통 라벨
ax.annotate("Target 1≡3 · 胻外廉 / WHO\n《灵枢》《明堂》 · 《铜人》 卷上 '大筋内' → 앞정강근 근복",
            xy=(3, 51.5), xytext=(1, 66), fontsize=9.3, color=T13, weight="bold", ha="right", va="center",
            arrowprops=dict(arrowstyle="-", lw=0.7, color=T13, relpos=(1, 0)))
ax.annotate("Target 2 · 兩筋間 (근간 중격)\n王冰 주 · 《铜人》 卷下 · 《圣济》 · 「訛穴」",
            xy=(13.9, 50.5), xytext=(20, 67), fontsize=9.3, color=T2, weight="bold", ha="left", va="center",
            arrowprops=dict(arrowstyle="-", lw=0.7, color=T2, relpos=(0, 0)))
ax.annotate("내측 편위 (기록만, Target 제외)\n《太平圣惠方》 '筋骨之间'",
            xy=(-9.5, 49.6), xytext=(-40, 46.5), fontsize=8.8, color="#666", ha="right", va="center",
            arrowprops=dict(arrowstyle="-", lw=0.7, color=MED, relpos=(1, 0.5)))


def lab(x, y, tx, ty, text, color="#222", fs=9.2):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=10,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 64, -64
lab(4, 33, R, 57.5, "② 앞정강근 Tibialis anterior  FMA:22532\n    지배: 깊은종아리신경 · 분절 L4(주)·L5", "#8f2d2a")
lab(26, 22, R, 44, "② 긴발가락폄근 Extensor digitorum longus  FMA:22534\n    지배: 깊은종아리신경 · 분절 L5(주)·S1", "#8f2d2a")
lab(15.6, 11.2, R, 28, "③ 깊은종아리신경 Deep fibular nerve  FMA:44771", "#8a6d00")
lab(10.5, 9.5, R, 17, "③ 앞정강동맥·정맥 Anterior tibial a./v.  FMA:43894 / 44331", "#b02020")
lab(20, -3, R, 6, "④ 종아리뼈사이막 Interosseous membrane of leg  FMA:35187", "#4b3f6f")
lab(44, -2, R, -6, "긴종아리근 Fibularis longus (가쪽칸)  FMA:22539", "#8f4a2a")
lab(37.5, -9, R, -16, "① 얕은종아리신경 Superficial fibular n.  FMA:44699 [공통교재]", "#8a6d00")
lab(47, -32, R, -30, "① 가쪽장딴지피부신경 Lateral sural cutaneous n.  FMA:44697", "#8a6d00")
lab(31, -15, R, -40, "종아리뼈 Fibula  FMA:24479", "#5b4f33")
lab(1.4, -19.6, R, -64, "정강신경·뒤정강동정맥 (뒤칸 깊은층)", "#555")
lab(-24, 20, L, 40, "정강뼈 Tibia  FMA:24476", "#5b4f33")
lab(-48.5, 8, L, 22, "① 두렁신경 안쪽종아리피부가지  FMA:75559 [김재효]", "#8a6d00")
lab(-49, -8, L, 6, "큰두렁정맥·두렁신경 (피하, 안쪽)", "#2f5fb3")
lab(-18, -10, L, -12, "긴발가락굽힘근 (뒤칸 깊은층)", "#7a5a3a")
lab(10, -10, R, -50, "뒤정강근 Tibialis posterior (뒤칸 깊은층, 사이막 뒤)", "#7a5a3a")
lab(-20, -34, L, -30, "가자미근 Soleus", "#6e3a2e")
lab(-26, -52, L, -48, "장딴지근 안쪽·가쪽갈래", "#5e2e24")
lab(2, -61, L, -64, "작은두렁정맥 (피하, 뒤)", "#2f5fb3")

ax.text(-114, 86, "족삼리(ST36) 높이 하퇴 상1/3 횡단면 — 가로 방향 3계통 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-114, 79.5, "오른다리 · 위에서 내려다봄 · 앞쪽=위, 안쪽=왼쪽 · 축척 아님 · 세로 위치는 3계통 모두 膝下(犊鼻下) 3寸", fontsize=9.5, color="#444", va="top")
ax.text(-114, -72, "검정 실선: Target 1≡3 — 정강뼈 앞모서리 외측 1횡지, ② 앞정강근 근복(고전 1촌 23mm 도달층) → 현대 상한 2촌 직자 시 ③ 신경혈관속 근접(추정). "
        "회색 점선: 정강뼈 쪽으로 약간 기울인 자침(\"直刺，稍偏向胫骨方向\", 通考) — ③ 회피\n"
        "보라 실선: Target 2 — '兩筋間' = 앞정강근–긴발가락폄근 근간 중격(보라 파선). 근복을 거치지 않고 중격을 따라 ③ 앞정강동맥·깊은종아리신경에 닿는다. "
        "'極重按之 則足跗上動脈止'(王冰)·'以手按兩筋間 則足跗上太衝脈不動'(「訛穴」)은\n    이 깊이에서 앞정강동맥이 눌리는 소견으로 읽힌다(추론). 《铜人》 卷下 '針入五分'(11.5mm)이 심도 상한 근거. "
        "Target 2–3 Δ ≈ 10~15mm(추정, 분기 경계값 근접)\n"
        "회색 일점쇄선: 《太平圣惠方》 '胻骨外，大筋内，筋骨之间' — 정강뼈 가쪽면과 앞정강근 사이. 《通考》 '过于偏内侧' → Target으로 세우지 않고 기록만\n"
        "①~④는 보고서 4절 Layer 순서. 구조·FMA ID·지배·분절은 FMA 5.1.0(contained_in · nerve_supply · segmental_supply)과 2대 교재 데이터셋 기준. "
        "층 두께·거리는 ST36 실측값이 없어 임의 배치",
        fontsize=8.6, color="#333", va="top", linespacing=1.55)

for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-108 + i * 17, -57), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-105 + i * 17, -57, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

# -*- coding: utf-8 -*-
"""PC09 중충 — 가운데손가락 끝마디 정중 시상(세로) 단면 모식도 (노쪽에서 봄, 먼쪽=오른쪽, 손등=위). 축척 아님.
ST36·GB21 그림과 같은 방식. 구조·FMA ID는 fma_query.py profile PC09와 2대 교재 데이터셋, 자침·안전은 PC09 보고서 4·5·6절."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]   # 간체자는 YaHei로 대체
plt.rcParams["axes.unicode_minus"] = False
OUT = sys.argv[1]


def chaikin(pts, n=4, closed=True):
    p = np.asarray(pts, float)
    for _ in range(n):
        nxt = np.roll(p, -1, 0) if closed else p[1:]
        cur = p if closed else p[:-1]
        q, r = cur * 0.75 + nxt * 0.25, cur * 0.25 + nxt * 0.75
        mid = np.empty((len(q) * 2, 2)); mid[0::2], mid[1::2] = q, r
        p = mid if closed else np.vstack([p[:1], mid, p[-1:]])
    return p


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, ls="-"):
    ax.add_patch(Polygon(chaikin(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


fig, ax = plt.subplots(figsize=(13, 10.4), dpi=170)
ax.set_xlim(-122, 122); ax.set_ylim(-80, 82); ax.set_aspect("equal"); ax.axis("off")

# 손가락 윤곽(피부) — 손등 위, 바닥 아래, 끝 오른쪽
skin = [(-80, 16), (-40, 17), (0, 17), (26, 16), (40, 12), (48, 4), (50, -4), (46, -14), (34, -22), (14, -25),
        (-10, -23), (-40, -22), (-80, -22)]
blob(ax, skin, "#f6dccb", "#b07a5a", 2.0, 1)
blob(ax, [(-80, 13), (-40, 14), (0, 14), (24, 13), (37, 9.5), (45, 3), (46.5, -4), (43, -12), (32, -19), (14, -22),
          (-10, -20), (-40, -19), (-80, -19)], "#fbeee6", "none", 0, 1.2)
# 바닥쪽 지방 패드 + 섬유 격막
blob(ax, [(-8, -6), (20, -4), (38, -3), (43, -8), (38, -16), (20, -20), (0, -19), (-12, -15)], "#fff3c4", "#c9b37a", 0.8, 1.6)
for x in (2, 12, 22, 32):
    ax.plot([x, x + 3], [-5.5, -18.5], color="#c9b37a", lw=0.8, zorder=1.7)

# 뼈: 중간마디 머리, 끝마디(기저부 → 끝마디거친면 tuft)
blob(ax, [(-80, 8), (-50, 8), (-44, 5), (-42, 0), (-44, -6), (-50, -9), (-80, -9)], "#efe8d2", "#7d6f4f", 1.3, 3)
blob(ax, [(-40, 7), (-30, 8), (0, 5), (18, 4), (26, 5), (30, 2), (29, -3), (25, -5), (16, -4), (0, -5), (-30, -8), (-40, -7), (-38, 0)],
     "#efe8d2", "#7d6f4f", 1.3, 3)
ax.plot([-41, -41], [-6, 6], color="#9a8a66", lw=0.8, ls="--", zorder=3.2)        # 먼쪽 손가락뼈사이관절

# 손톱 장치: 손톱판·손톱바닥·손톱바탕질·손톱주름
blob(ax, [(-16, 14.2), (0, 15.4), (24, 15), (38, 12), (41, 10.2), (38, 10.5), (24, 12.5), (0, 12.8), (-14, 12)],
     "#e8eef5", "#6b7a8f", 1.2, 4)
blob(ax, [(-14, 12), (0, 12.6), (24, 12.3), (37, 10.2), (30, 6), (18, 6.2), (0, 7), (-14, 8.5)], "#f3b5b0", "#b5655e", 0.8, 3.5)
blob(ax, [(-26, 12), (-14, 12.5), (-13, 8.6), (-24, 8.8)], "#e98a80", "#a04a42", 0.8, 3.6)
ax.plot(*chaikin([(-30, 17), (-22, 16.5), (-15, 15.2)], closed=False).T, color="#b07a5a", lw=1.6, zorder=4.5)

# 깊은손가락굽힘근 힘줄 → 끝마디 기저부 바닥쪽 부착
blob(ax, [(-80, -11), (-48, -11.5), (-40, -10.5), (-34, -8.2), (-32, -10.5), (-40, -14), (-80, -14.5)], "#e7d7bf", "#8f7a55", 1.0, 2.6)


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
# 고유바닥쪽손가락신경·동맥 말단망(지첨 패드) — 본간은 손가락 양옆(이 정중면 밖)
for (x, y, k) in [(30, -10, "N"), (34, -6.5, "A"), (37, -11, "N"), (40, -6, "A"), (24, -14, "V"), (42, -2, "N"), (16, -9, "A")]:
    dot(x, y, 1.3, {"N": NERVE, "A": ART, "V": VEIN}[k])
dot(4, 9.8, 1.2, NERVE); dot(12, 9.4, 1.2, ART)                    # 손톱바닥: 등쪽가지·등쪽손가락동맥

# 자침: 지첨 중앙 1푼(2.3mm) 점자·직자
ax.plot([64, 50.6], [-2.5, -2.5], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((50.6, -2.5), (45.4, -2.5), arrowstyle="-|>", mutation_scale=15, lw=2.4, color="#111", zorder=9))
ax.plot(*chaikin([(47.5, 9), (49.4, 2), (49.6, -6), (47.2, -12)], closed=False).T, color="#1b7f3b", lw=1.2, ls="--", zorder=8.5)
ax.text(66, 5, "PC09 중충 자침점\n(가운데손가락 끝 중앙, 손톱 끝에서 약 1푼)", ha="left", va="center", fontsize=11.5, weight="bold", zorder=10)
ax.text(66, -8, "직자·점자 1푼(2.3mm) — ① 층 안에서 끝남\n(《明堂》 \"刺入一分\", 《通考》 \"浅刺0.1寸，或点刺出血\")", ha="left", va="center", fontsize=8.8, zorder=10)
ax.add_patch(Circle((-20, 19.5), 1.9, fc="white", ec="#6a1b9a", lw=1.6, zorder=9)); ax.plot([-20], [19.5], "o", ms=2.5, color="#6a1b9a", zorder=10)


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 66, -84
lab(30, 14, R, 32, "손톱판 (손등쪽)", "#4a5a6f")
lab(18, 9.5, R, 42, "손톱바닥 — 등쪽가지 분포 (B1-03: 정중신경 고유바닥쪽손가락신경의 등쪽가지)", "#b5655e")
lab(12, 9.4, R, 52, "등쪽손가락동맥  FMA:321492  [공통]", "#b02020")
lab(27, 1, R, 21, "⑤ 끝마디뼈 거친면(tuft) 골막 — 1푼으로 닿지 않음", "#5b4f33")
lab(37, -11, R, -34, "① 고유바닥쪽손가락신경 말단  FMA:75484 (Set)  [공통]\n    ← 정중신경 고유바닥쪽손가락가지 FMA:44853 [김재효] ← 정중신경 FMA:14385", "#8a6d00")
lab(34, -6.5, R, -22, "① 고유바닥쪽손가락동맥 말단망  FMA:70804 (Set)  [공통]", "#b02020")
lab(24, -14, R, -44, "① 바닥쪽손가락정맥  FMA:70895 (Set)  [공통]", "#2f5fb3")
lab(30, -18, R, -54, "지첨 섬유지방 패드(격막 구획) — 점자출혈은 ① 미세혈관망", "#8a7a4a")

lab(-20, 19.5, L, 50, "⊙ 변이 정위: 노쪽 손톱뿌리각 위 0.1촌 (窦太师 이후)\n    지면 앞쪽(노쪽) — 첨단과 약 10~15mm, 분기 기준 미달", "#6a1b9a")
lab(4, 9.8, L, 38, "등쪽손가락신경 [공통교재] — FMA 대응표는 'Set of dorsal digital\n    branches of radial nerve'(FMA:75490)로 연결 → 가운데손가락 끝은 부적합", "#8a6d00")
lab(-20, 10.5, L, 25, "손톱바탕질 · 손톱주름", "#a04a42")
lab(-41, 3, L, 10, "먼쪽 손가락뼈사이관절 (점선)", "#5b4f33")
lab(-36, -10, L, -6, "③ 깊은손가락굽힘근 힘줄  FMA:38478  [공통교재]\n    끝마디 기저부 바닥쪽 부착 — 첨단 자침 경로 밖\n    지배: 정중신경 앞뼈사이신경·자신경 가지 · 분절 C8(주)·T1", "#8f7a55")
lab(-60, -20.5, L, -30, "바닥쪽 피부(두꺼운 무모 피부, 기계·통각 수용기 밀집)", "#7a5a46")

ax.text(-118, 80, "중충(PC09) — 가운데손가락 끝마디 세로(정중 시상) 단면 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-118, 73.5, "노쪽에서 봄 · 먼쪽=오른쪽, 손등=위 · 축척 아님  ·  SI 100 (금침 기록 없음, 표준 심도 전체가 ① 피부·피하)",
        fontsize=9.3, color="#444", va="top")
ax.text(-118, -60, "검은 화살표: 첨단 중앙 직자·점자 1푼(2.3mm, 자침깊이 DB 전 문헌 1푼). 녹색 점선 = 1푼 도달 깊이 — 주요 신경간·동맥·장기와 10mm 이상 떨어짐.\n"
        "고유바닥쪽손가락신경·동맥의 본간은 손가락 양옆(이 정중면 밖)을 지나며, 첨단 중앙에서는 이미 말단망이다. 지첨은 통증이 매우 강해 실신 등 자극 반응 주의(일반 임상 주의).\n"
        "[공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 깊은손가락굽힘근(공통교재만)은 기저부에 붙어 자침 경로 밖이므로 김재효의 근육 공란이 지첨 해부에 더 맞다(보고서 6절).\n"
        "구조·FMA ID는 FMA 5.1.0과 2대 교재 데이터셋 기준. 층 두께·거리는 PC09 실측값이 없어 임의 배치.",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-112 + i * 17, -52), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-109 + i * 17, -52, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

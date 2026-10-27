# -*- coding: utf-8 -*-
"""BL02 찬죽 — 이마패임(额切迹, 도르래위패임)을 지나는 시상 단면 모식도 (왼쪽 얼굴을 바깥쪽에서 봄, 앞쪽=왼쪽). 축척 아님.
ST36·GB21 그림과 같은 방식. 구조·FMA ID는 fma_query.py profile BL02와 2대 교재 데이터셋, 자침 경로·안전은 BL02 보고서 4·5·10절."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Ellipse, FancyArrowPatch

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


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, ls="-", closed=True):
    ax.add_patch(Polygon(chaikin(pts, closed=closed), closed=closed, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls))


fig, ax = plt.subplots(figsize=(13, 10.4), dpi=170)
ax.set_xlim(-122, 122); ax.set_ylim(-86, 82); ax.set_aspect("equal"); ax.axis("off")

# 연부조직 바탕 (이마·눈썹·윗눈꺼풀)
soft = [(-40, 62), (-44, 40), (-47, 18), (-48, 8), (-46, -2), (-40, -10), (-30, -16), (-24, -26), (-26, -40),
        (40, -40), (40, 62)]
blob(ax, soft, "#fbeee6", "none", 0, 0.5)
skin = chaikin([(-40, 62), (-44, 40), (-47, 18), (-48, 8), (-46, -2), (-40, -10), (-30, -16), (-24, -26), (-26, -40)], closed=False)
ax.plot(skin[:, 0], skin[:, 1], color="#b07a5a", lw=2.2, zorder=6)
inner = skin + np.array([3.0, 0])
ax.fill_betweenx(skin[:, 1], skin[:, 0], inner[:, 0], color="#f6dccb", zorder=1)
for i, y in enumerate(np.linspace(4, 14, 9)):                      # 눈썹 털
    ax.plot([-48.5 + 0.2 * i, -53], [y, y + 3.5], color="#5a4636", lw=1.1, zorder=6)

# 이마뼈: 바깥판 → 눈확위모서리(额切迹 높이) → 눈확 천장
bone = [(-28, 62), (-31, 36), (-33, 16), (-34, 6), (-31, 1), (-20, -1), (0, 1), (24, 4), (40, 6),
        (40, 13), (24, 11), (2, 9), (-20, 7), (-24, 10), (-24, 30), (-20, 62)]
blob(ax, bone, "#efe8d2", "#7d6f4f", 1.4, 4)
ax.plot([-34.6, -35.2, -34.2], [20, 8, 2], color="#6d5f8f", lw=1.6, zorder=4.3)   # 골막

# 근육
blob(ax, [(-41, 60), (-38, 60), (-36, 34), (-37, 24), (-40, 26), (-42, 40)], "#d9534f", "#8f2d2a", 1.0, 3)          # 이마힘살
blob(ax, [(-44, 22), (-40, 22), (-38, 10), (-40, -4), (-36, -12), (-31, -15), (-35, -16), (-41, -10), (-45, 0), (-46, 12)],
     "#e57f6c", "#8f2d2a", 1.0, 3)                                                                                          # 눈둘레근
blob(ax, [(-39, 16), (-36, 17), (-35.5, 11), (-38, 9)], "#c0392b", "#6e1f1a", 1.0, 3.4)                                 # 눈썹주름근
blob(ax, [(-44.5, 10), (-42.5, 11), (-42, 5), (-44, 4)], "#f0a08f", "#8f2d2a", 0.9, 3.4)                                # 눈썹내림근

# 눈확: 눈확사이막, 눈확 지방, 안구, 눈꺼풀올림근
ax.plot(*chaikin([(-32, 0), (-29, -6), (-27, -12), (-26, -18)], closed=False).T, color="#8a6a55", lw=1.2, ls="--", zorder=3.6)
blob(ax, [(-26, -2), (36, 2), (38, -36), (-20, -40), (-25, -20)], "#fff3c4", "#c9b37a", 0.7, 1.6)
ax.add_patch(Circle((6, -20), 17, fc="#ffffff", ec="#6b7a8f", lw=1.4, zorder=3))
ax.add_patch(Ellipse((-11, -20), 5, 13, fc="#cfe3f7", ec="#2f5fb3", lw=1.0, zorder=3.2))
blob(ax, [(36, 0), (10, -2), (-16, -8), (-24, -14), (-23, -11), (-14, -4), (10, 1), (36, 3)], "#c9a27e", "#7a5a3a", 0.8, 3.1)


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
# 도르래위 신경·동정맥: 额切迹에서 나와 위로 (단면 안)
dot(-36.6, 3.2, 1.6, NERVE); dot(-36.4, 6.2, 1.3, ART); dot(-38.8, 4.6, 1.1, VEIN)
ax.add_patch(FancyArrowPatch((-37.5, 7), (-38.6, 30), arrowstyle="-|>", mutation_scale=8, lw=0.9, color="#c9a000", zorder=6))
dot(-42.5, 24, 1.1, NERVE)                                         # 피부가지
dot(-40.5, 14.5, 1.0, NERVE)                                       # 얼굴신경 관자가지 분지(근육 진입)

# 자침 경로
ax.plot([-62, -48.3], [8, 8], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((-48.3, 8), (-35.8, 8), arrowstyle="-|>", mutation_scale=15, lw=2.2, color="#111", zorder=9))
ax.add_patch(FancyArrowPatch((-48.3, 8), (-12, -18), arrowstyle="-|>", mutation_scale=13, lw=1.4, color="#c1121f", ls="--", zorder=8))
ax.plot([-28.5, -24.5], [-7.5, -3.5], color="#c1121f", lw=2.4, zorder=9); ax.plot([-28.5, -24.5], [-3.5, -7.5], color="#c1121f", lw=2.4, zorder=9)
ax.add_patch(Circle((-46.6, 12), 1.9, fc="white", ec="#1b7f3b", lw=1.6, zorder=9)); ax.plot([-46.6], [12], "o", ms=2.5, color="#1b7f3b", zorder=10)
ax.text(-63, 13, "BL02 찬죽 자침점\n(눈썹머리 오목, 额切迹)", ha="right", va="center", fontsize=11.5, weight="bold", zorder=10)
ax.text(-36, -66, "", fontsize=1)


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 50, -68
lab(-38.5, 46, R, 62, "② 이마힘살 Frontalis  FMA:46757  [공통]  (얼굴신경 지배)", "#8f2d2a")
lab(-37.2, 13, R, 28, "③ 눈썹주름근 Corrugator supercilii  FMA:46794  [공통]", "#6e1f1a")
lab(-38.6, 24, R, 50, "④ 도르래위신경 Supratrochlear n.  FMA:52642  [김재효]\n    ← 이마신경 FMA:52638 [공통교재] ← 눈신경 V1", "#8a6d00")
lab(-36.4, 6.2, R, 17, "④ 도르래위동·정맥  FMA:50025 / 50898  [공통]\n    정맥 → 눈구석정맥 → 얼굴정맥 (FMA drains_into)", "#b02020")
lab(-34.9, 15, R, 39, "⑤ 이마뼈 골막(额切迹) — 직자 종점", "#4b3f6f")
lab(10, 7, R, 6, "이마뼈 Frontal bone (눈확 천장)", "#5b4f33")
lab(0, -4, R, -6, "윗눈꺼풀올림근 · 눈확 지방 (교재 미기재)", "#7a5a3a")
lab(14, -26, R, -30, "안구 — 눈확위모서리 아래·뒤", "#4a5a6f")
lab(-28, -10, R, -18, "눈확사이막 (점선)", "#8a6a55")

lab(-42.8, 7, L, 0, "② 눈썹내림근 Depressor supercilii  FMA:46798  [김재효]", "#8f2d2a")
lab(-43, -5, L, -12, "② 눈둘레근 Orbicularis oculi  FMA:46779  [공통]\n    얼굴신경 관자·광대가지 지배", "#8f2d2a")
lab(-40.5, 14.5, L, 30, "③ 얼굴신경 관자가지 Temporal br. of facial n.\n    FMA:53291 [김재효] (← 얼굴신경 FMA:50868 [공통교재])", "#8a6d00")
lab(-42.5, 24, L, 46, "① 도르래위신경 피부가지 (피하)", "#8a6d00")

ax.text(-118, 80, "찬죽(BL02) — 이마패임(额切迹)을 지나는 시상 단면 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-118, 73.5, "왼쪽 얼굴 · 바깥쪽에서 봄 · 앞쪽=왼쪽, 위쪽=위 · 축척 아님  ·  [주의] SI 0: 《医学入门》 \"禁用针灸\"(후대 단일 기록) — 실제 위험은 깊이보다 방향",
        fontsize=9.3, color="#444", va="top")
ax.text(-118, -50, "검은 실선 화살표: 직자(《通考》 0.1~0.3촌, DB 1~3푼 = 2.3~6.9mm) — 수 mm에서 이마뼈 额切迹 골막(⑤)에 닿아 멈춤. 도르래위 혈관(④) 접촉·혈종 주의.\n"
        "녹색 원(⊙): 沿皮 횡자(窦氏 \"沿皮向鱼腰\", 7版 \"向眉中…平刺\") — 지면 밖 바깥쪽 鱼腰 방향, ①~② 층을 수평 통과. 기본 자침법.\n"
        "빨간 점선: 아래·뒤쪽 경사 심자(《聚英》이 비판한 \"卧针直抵睛明\" 포함) → 눈확사이막을 지나 눈확 안 진입 위험. 금지 방향.\n"
        "①~⑤는 보고서 4.3절 Layer 순서. [공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 공통교재의 이마신경·얼굴신경은 김재효의 도르래위신경·관자가지의\n"
        "FMA상 상위 줄기(같은 계통, 기재 수준 차이). 눈확위 신경혈관속(김재효)은 额切迹 바깥쪽 眶上切迹을 지나 이 단면 밖. 층 두께·거리는 BL02 실측값이 없어 임의 배치.",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-112 + i * 17, -42), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-109 + i * 17, -42, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

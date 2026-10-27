# -*- coding: utf-8 -*-
"""GV20 백회 — 정수리(시상봉합) 관상 단면 모식도 (앞에서 봄, 위쪽=위). 두피 5층을 과장해 그림 — 축척 아님.
ST36·GB21 그림과 같은 방식. 구조·FMA ID는 fma_query.py profile GV20과 2대 교재 데이터셋, 층·자침·안전은 GV20 보고서 4·5절."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]   # 간체자는 YaHei로 대체
plt.rcParams["axes.unicode_minus"] = False
OUT = sys.argv[1]
C = np.array([0.0, -100.0])          # 머리 곡률 중심 (가상)
A0, A1 = 64, 116                       # 그리는 각도 범위(도)


def arc(r, a0=A0, a1=A1, n=160):
    t = np.radians(np.linspace(a0, a1, n))
    return np.c_[C[0] + r * np.cos(t), C[1] + r * np.sin(t)]


def band(ax, r_in, r_out, fc, ec="none", z=1, lw=0.6, a0=A0, a1=A1):
    pts = np.vstack([arc(r_out, a0, a1), arc(r_in, a0, a1)[::-1]])
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))


def pol(r, deg):
    t = np.radians(deg)
    return C[0] + r * np.cos(t), C[1] + r * np.sin(t)


fig, ax = plt.subplots(figsize=(13, 10.4), dpi=170)
ax.set_xlim(-122, 122); ax.set_ylim(-62, 82); ax.set_aspect("equal"); ax.axis("off")

# 층 반지름 (과장)
R = dict(skin=150, ct=145, gal=138, loose=135, peri=131, bone=129.5, dura=118, brain=116.5)
band(ax, R["ct"], R["skin"], "#f6dccb", "#b07a5a", 2)                  # ① 피부
band(ax, R["gal"], R["ct"], "#fbeee6", "#c9a58a", 2)                   # ① 치밀 피하결합조직
band(ax, R["loose"], R["gal"], "#d9534f", "#8f2d2a", 2.2)              # ② 머리덮개널힘줄
band(ax, R["peri"], R["loose"], "#fff6dc", "#c9b37a", 2)               # ③ 건막하 소성결합조직
band(ax, R["bone"], R["peri"], "#b9a8d6", "#6d5f8f", 2.3)              # ⑤ 머리뼈바깥막
band(ax, R["dura"], R["bone"], "#efe8d2", "#7d6f4f", 2.4, 1.2)          # 두정골
band(ax, 121, 126.5, "#e2d6b4", "none", 2.45)                          # 판사이층(diploe)
band(ax, R["brain"], R["dura"], "#c7d3e0", "#5a6b80", 2.5)             # 경막
band(ax, 80, R["brain"], "#eceff3", "none", 0.8)                       # 뇌(지주막하·피질)
# 시상봉합
ax.plot(*np.array([pol(R["bone"], 90), pol(R["dura"], 90)]).T, color="#5b4f33", lw=1.4, ls=(0, (2, 1.5)), zorder=3)
# 상시상정맥동 (삼각형) + 대뇌낫
top = pol(R["dura"] - 0.2, 90)
ax.add_patch(Polygon([pol(R["dura"], 87.2), pol(R["dura"], 92.8), (0, C[1] + R["dura"] - 11)], closed=True,
                     fc="#2f5fb3", ec="#1f3f7a", lw=1.2, zorder=4))
ax.plot([0, 0], [C[1] + R["dura"] - 11, C[1] + 84], color="#5a6b80", lw=2.0, zorder=3)
# 마루이끌정맥: 건막하층 → 마루뼈구멍 → 상시상정맥동
ev = np.array([pol(133, 99.5), pol(129, 99), pol(124, 97.2), pol(119.5, 94.5), pol(116.5, 92.3)])
ax.plot(ev[:, 0], ev[:, 1], color="#2f5fb3", lw=3.2, zorder=5, solid_capstyle="round")
ax.add_patch(Circle(pol(133.5, 99.8), 1.3, fc="#2f5fb3", ec="#333", lw=0.7, zorder=6))


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
for deg, kind in [(73, "ART"), (74.6, "VEIN"), (101.5, "NERVE"), (104, "NERVE"), (106, "NERVE"), (109, "ART"), (110.5, "VEIN")]:
    x, y = pol(141.5, deg)
    dot(x, y, 1.4 if kind != "ART" else 1.6, {"ART": ART, "VEIN": VEIN, "NERVE": NERVE}[kind])

# 자침: 평자(沿皮刺) / 직자 3푼
px, py = pol(R["skin"], 90)
ax.plot([px, px], [py + 12, py + 0.5], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((px, py), (px, C[1] + R["peri"] - 0.6), arrowstyle="-|>", mutation_scale=15, lw=2.2, color="#111", zorder=9))
sx, sy = pol(141, 90)
ax.add_patch(FancyArrowPatch((sx - 1, sy), pol(141, 80), arrowstyle="-|>", mutation_scale=13, lw=2.0, color="#1b7f3b", zorder=9,
                             connectionstyle="arc3,rad=-0.04"))
ax.text(px + 2, py + 10, "GV20 백회 자침점 (정중선·시상봉합 위, 두 귀끝 연결선 중점)", ha="left", va="center", fontsize=12, weight="bold", zorder=10)
ax.text(-2, py + 4.5, "직자 2~3푼(4.6~6.9mm)\n→ ⑤ 골막에서 정지", ha="right", va="center", fontsize=8.6, zorder=10)


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


RX, LX = 68, -68
lab(*pol(147.5, 70), RX, 56, "① 피부", "#7a5a46")
lab(*pol(140.5, 67.5), RX, 39, "① 치밀 피하결합조직 — 신경·혈관 말단이 지나는 층", "#7a5a46")
lab(*pol(141.5, 73), RX, 47, "① 얕은관자동·정맥 마루가지  FMA:49670 / 50932  [김재효/공통]\n    얕은관자동맥 FMA:49650 [공통교재] ← 바깥목동맥", "#b02020")
lab(*pol(136.5, 70), RX, 29, "② 머리덮개널힘줄 Galea  FMA:46768  [공통]", "#8f2d2a")
lab(*pol(133, 68), RX, 21, "③ 건막하 소성결합조직 (활주층)", "#8a7a4a")
lab(*pol(130.2, 67), RX, 13, "⑤ 머리뼈바깥막 Pericranium  FMA:76623  [김재효]", "#4b3f6f")
lab(*pol(124, 70), RX, 5, "두정골 · 시상봉합 (두개골이 심부를 차단)", "#5b4f33")
lab(*pol(117.2, 74), RX, -4, "경막", "#5a6b80")
lab(0, C[1] + R["dura"] - 5, RX, -14, "상시상정맥동 Superior sagittal sinus  FMA:50767", "#1f3f7a")

lab(*pol(141.5, 104), LX, 44, "① 큰뒤통수신경 Greater occipital n.  FMA:65443  [공통]\n    ← C2 뒤가지 (분절 C2)", "#8a6d00")
lab(*pol(141.5, 106), LX, 33, "① 눈확위·도르래위신경 말단  FMA:52655 / 52642  [김재효]\n    ← 이마신경 ← 눈신경 V1", "#8a6d00")
lab(*pol(141.5, 101.5), LX, 56, "① 귓바퀴관자신경 Auriculotemporal n.  FMA:53000  [공통교재]\n    ← 아래턱신경 V3", "#8a6d00")
lab(*pol(141.5, 109.7), LX, 22, "① 뒤통수동·정맥 Occipital a./v.  FMA:49586 / 50802  [공통]", "#b02020")
lab(*pol(129, 99), LX, 10, "③→ 마루이끌정맥 Parietal emissary v.  FMA:50791  [공통]\n    마루뼈구멍 → 상시상정맥동 (FMA tributary 사슬)", "#2f5fb3")
lab(sx - 1, sy, LX, -6, "평자·沿皮刺 경로 (窦氏 \"沿皮向前/向後一寸\", 교재 횡자 5~8푼)\n    ①층 안을 앞뒤 방향으로 진행 — 지면에서는 바깥쪽 화살표로 표시", "#1b7f3b")

ax.text(-118, 80, "백회(GV20) — 정수리 시상봉합 관상 단면 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-118, 73.5, "앞에서 봄 · 위쪽=위 · 두피 5층(피부·치밀결합조직·널힘줄·소성결합조직·골막)을 과장해 그림, 축척 아님  ·  SI 75 (금침 기록 없음)",
        fontsize=9.3, color="#444", va="top")
ax.text(-118, -26, "검은 실선 화살표: 직자 2~3푼(《明堂》 \"刺入三分\" 6.9mm, 동인 2푼) — ⑤ 머리뼈바깥막에서 멈추고 두개골이 경막·상시상정맥동·뇌를 차단한다.\n"
        "녹색 화살표: 평자(沿皮刺) — 현대 교재·《通考》 선호 자침법(横刺). 5~8푼은 두피 안 경로 길이이며 수직 심도가 아니다.\n"
        "마루이끌정맥은 ③ 건막하층의 두피 정맥을 두개 안 상시상정맥동과 잇는다(FMA tributary 사슬; 감염 확산 경로는 규범 해부 B1-01).\n"
        "주의: 소아 숫구멍 미폐쇄·뇌수종에는 신중(上海《针灸学》, 通考 L2612). 정수리는 V1·V3·C2 분포가 수렴 — 공통교재는 V3, 김재효는 V1을 기재(상보).\n"
        "[공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 층 두께는 보고서 4.2절 개략값(두피 전층 약 5~7mm)을 과장한 것이며 GV20 실측 아님.",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-112 + i * 17, -19), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-109 + i * 17, -19, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

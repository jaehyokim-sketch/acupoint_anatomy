# -*- coding: utf-8 -*-
"""CV12(중완) 높이 상복벽 횡단면 모식도 + 체형별 허용 자침 심도(ANIR) 대조도.

패널 A: CV12 높이(배꼽 위 4촌, 앞정중선) 상복벽 횡단면. 영상의학 관례(보는 이의 왼쪽 = 환자의 오른쪽).
        세로축은 초음파 실측 평균 심도(mm)에 맞추고, 가로 방향은 축척이 아니다.
패널 B: 초음파 실측 피부-벽측복막 심도(ANIR)의 체형별 분포와 역대 문헌 자침 심도 환산값 대조.
사용법: python CV12_cross_section.py <출력.png>
"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch, Circle

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = sys.argv[1] if len(sys.argv) > 1 else "CV12_cross_section.png"


def chaikin(pts, n=4):
    p = np.asarray(pts, float)
    for _ in range(n):
        q = p * 0.75 + np.roll(p, -1, 0) * 0.25
        r = p * 0.25 + np.roll(p, -1, 0) * 0.75
        p = np.empty((len(p) * 2, 2))
        p[0::2], p[1::2] = q, r
    return p


fig = plt.figure(figsize=(15.4, 13.4), dpi=170)
gs = fig.add_gridspec(2, 1, height_ratios=[1.58, 1.0], hspace=0.30,
                      left=0.012, right=0.988, top=0.962, bottom=0.085)

# =========================== 패널 A : 횡단면 ===========================
ax = fig.add_subplot(gs[0])
ax.set_xlim(-250, 250)
ax.set_ylim(-52, 11)
ax.axis("off")

SKIN, FAT = "#f3d8c3", "#fdf2d8"
SHEATH, MUSC = "#efe3d2", "#d9534f"
ALBA, TFAS, PPF = "#e4dcc2", "#cfe0ef", "#fbeede"
PERI, LIVER, STOM = "#7b4fae", "#9c6b52", "#cf9f7f"
ART, VEIN, NERVE = "#c0392b", "#2f5fb3", "#d4a017"

XL, XR = -90, 90          # 복벽 모식도 가로 범위
HALF_ALBA = 11            # 백선 반폭


def band(y0, y1, fc, ec="#9a8a7a", lw=0.8, x0=XL, x1=XR, z=2):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, lw=lw, zorder=z))


band(-2.0, 0.0, SKIN, "#b07a5a", 1.4)                                  # Layer 1 피부
band(-16.0, -2.0, FAT, "#c9a97a", 1.0)                                 # Layer 1 피하조직
band(-19.0, -16.0, ALBA, "#8a7a52", 1.3, -HALF_ALBA, HALF_ALBA)        # Layer 2 백선
for x0, x1 in [(XL, -HALF_ALBA), (HALF_ALBA, XR)]:                     # Layer 2 배곧은근집·배곧은근
    ax.add_patch(Rectangle((x0, -25.5), x1 - x0, 9.5, fc=SHEATH, ec="#8a7a52", lw=1.2, zorder=2))
    ax.add_patch(Polygon(chaikin([(x0 + 5, -17.5), (x1 - 5, -17.5), (x1 - 7, -24.3), (x0 + 7, -24.3)]),
                         closed=True, fc=MUSC, ec="#8f2d2a", lw=1.0, zorder=2.4))
band(-21.0, -19.0, TFAS, "#5f8ab0", 1.0, -HALF_ALBA, HALF_ALBA)        # Layer 3 배가로근막(백선 뒤)
band(-26.5, -25.5, TFAS, "#5f8ab0", 1.0, XL, XR)                       # Layer 3 배가로근막(근육 뒤)
band(-25.0, -21.0, PPF, "#c9a97a", 0.9, -HALF_ALBA, HALF_ALBA)         # Layer 3 복막외지방
band(-29.3, -26.5, PPF, "#c9a97a", 0.9, XL, XR)
ax.plot([-HALF_ALBA, HALF_ALBA], [-25.3, -25.3], color=PERI, lw=3.0, zorder=3.4)   # Layer 4 벽측복막
ax.plot([XL, -HALF_ALBA], [-29.5, -29.5], color=PERI, lw=2.2, zorder=3.4)
ax.plot([HALF_ALBA, XR], [-29.5, -29.5], color=PERI, lw=2.2, zorder=3.4)
ax.plot([-HALF_ALBA, -HALF_ALBA], [-25.3, -29.5], color=PERI, lw=2.2, zorder=3.4)
ax.plot([HALF_ALBA, HALF_ALBA], [-25.3, -29.5], color=PERI, lw=2.2, zorder=3.4)

# Layer 5 복강 장기
ax.add_patch(Polygon(chaikin([(-88, -27.5), (-14, -26.2), (16, -29), (22, -37), (-12, -45), (-58, -45), (-86, -37)]),
                     closed=True, fc=LIVER, ec="#5e3a28", lw=1.3, zorder=2.6))
ax.add_patch(Polygon(chaikin([(24, -29), (74, -28), (88, -34), (76, -45), (38, -46), (20, -38)]),
                     closed=True, fc=STOM, ec="#8a5f3a", lw=1.3, zorder=2.6))
ax.add_patch(Polygon(chaikin([(32, -31.5), (70, -30.6), (79, -34.5), (70, -42), (42, -42.5), (29, -37)]),
                     closed=True, fc="#f6e9da", ec="#8a5f3a", lw=0.8, zorder=2.7))

# 혈관·신경
for sx in (-1, 1):
    ax.add_patch(Circle((sx * 34, -20.6), 2.1, fc=ART, ec="#333", lw=0.7, zorder=5))     # 위배벽동맥
    ax.add_patch(Circle((sx * 43, -20.6), 2.1, fc=VEIN, ec="#333", lw=0.7, zorder=5))    # 위배벽정맥
    ax.add_patch(Circle((sx * 20, -9.5), 2.0, fc=NERVE, ec="#333", lw=0.7, zorder=5))    # T7·T8 앞피부가지
    ax.add_patch(Circle((sx * 58, -8.0), 1.9, fc=ART, ec="#333", lw=0.6, zorder=5))      # 얕은배벽동맥
    ax.add_patch(Circle((sx * 67, -8.0), 1.9, fc=VEIN, ec="#333", lw=0.6, zorder=5))     # 얕은배벽정맥

# 자침선 (앞정중선 백선 직자)
ax.add_patch(FancyArrowPatch((0, 4.2), (0, -24.6), arrowstyle="-|>", mutation_scale=18,
                             color="#8b0000", lw=2.6, zorder=7))
ax.annotate("", xy=(-78, -25.3), xytext=(-78, 0),
            arrowprops=dict(arrowstyle="<->", color="#8b0000", lw=1.5))
ax.text(-75.5, -12.6, "ANIR\n25.3 ± 10.2mm", fontsize=9.0, color="#8b0000", va="center", weight="bold")

# 오른쪽 : 문헌별 자침 심도 눈금
for d, txt, col in [(-4.6, "4.6mm   《黃帝明堂經》(黃龍祥 輯校) 2푼", "#6a6a6a"),
                    (-11.5, "11.5mm   《鍼灸腧穴通考》 하한 5푼", "#2d6a4f"),
                    (-18.4, "18.4mm   《東醫寶鑑》·《鍼灸經驗方》 8푼", "#2d6a4f"),
                    (-25.3, "25.3mm   벽측복막 평균 = 허용 자침 종점(n=83)", "#8b0000"),
                    (-27.6, "27.6mm   《鍼灸甲乙經》 12푼(一寸二分)", "#8b0000"),
                    (-34.5, "34.5mm   경혈학 공통교재·《通考》 상한 15푼", "#8b0000")]:
    ax.plot([96, 112], [d, d], color=col, lw=1.6, zorder=7.5)
    ax.text(115, d, txt, fontsize=9.0, color=col, va="center", zorder=7.5)
ax.plot([96, 96], [-36.5, -3.0], color="#999", lw=1.0, zorder=7)
ax.text(96, 0.4, "문헌별 자침 심도 (1푼 = 2.3mm)", fontsize=9.2, color="#333", weight="bold", va="bottom")

# 왼쪽 : Layer 라벨 (슬롯 고정, 지시선)
SLOTS = [(-1.0, 1.6), (-9.0, -0.6), (-17.5, -5.2), (-20.0, -9.8), (-23.0, -14.4),
         (-25.3, -19.0), (-20.6, -23.6), (-9.5, -28.2), (-8.0, -32.8), (-36, -37.4), (-36, -42.0)]
LABELS = [
    (0, "Layer 1  피부 Skin (0~2mm)", "#8a4a2a"),
    (0, "Layer 1  피하조직·지방 (2~16mm)  —  실측 16.0 ± 7.7mm", "#8a6a2a"),
    (0, "Layer 2  백선 linea alba  FMA:11336  —  무근육·혈관 빈약 간극 (자입 기준점)", "#6a5a22"),
    (0, "Layer 3  배가로근막 transversalis fascia  FMA:12265  [김재효 교재 단독]", "#2f6a9b"),
    (0, "Layer 3  복막외지방 preperitoneal fat", "#9a7a3a"),
    (0, "Layer 4  벽측복막 parietal peritoneum  —  자침 허용 종점", "#6a3f9f"),
    (-34, "Layer 2~3  위배벽동ㆍ정맥  FMA:10646 · FMA:4731  (배곧은근 뒤면)", "#c0392b"),
    (-20, "Layer 1  T7·T8 갈비사이신경 앞피부가지  FMA:8870 · FMA:8881", "#8a6a00"),
    (-58, "Layer 1  얕은배벽동ㆍ정맥  FMA:20734 · FMA:44318  [김재효 교재 단독]", "#2f5fb3"),
    (-48, "Layer 5  간 좌엽 left lobe of liver  —  피험자 62.7%(52/83)에서 CV12 직하 관찰", "#5e3a28"),
    (52, "Layer 5  위 전벽 anterior wall of stomach  —  간 미관찰 31례에서 직접 관찰", "#8a5f3a"),
]
for (ay, ly), (ax_x, text, col) in zip(SLOTS, LABELS):
    ax.annotate(text, xy=(ax_x, ay), xytext=(-248, ly), fontsize=9.0, color=col,
                ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=col, lw=0.8, shrinkA=2, shrinkB=2,
                                connectionstyle="angle,angleA=0,angleB=90,rad=4"), zorder=8)

ax.text(-248, 10.6, "A. 중완(中脘, CV12) 높이 상복벽 횡단면 — 앞정중선 자입 경로와 Layer 1~5 해부 실체",
        fontsize=15.0, weight="bold", va="top")
ax.text(-248, 7.6, "앞정중선, 배꼽 중심 위 4촌(검상돌기-배꼽 연선 중점) · 영상의학 관례(보는 이의 왼쪽 = 환자의 오른쪽) · "
                   "가로 방향은 축척 아님 · 세로(깊이)는 초음파 실측 평균값(mm)에 맞춤",
        fontsize=9.4, color="#444", va="top")
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-172 + i * 26, -47.5), 2.1, fc=c, ec="#333", lw=0.8))
    ax.text(-167 + i * 26, -47.5, t, va="center", fontsize=9.2)

# =========================== 패널 B : 체형별 ANIR ===========================
bx = fig.add_subplot(gs[1])
groups = ["전체 (n=83)", "저체중 (n=14)", "정상 (n=47)", "과체중 (n=22)",
          "남성·저체중 (n=7)", "여성·저체중 (n=7)"]
mean = [25.3, 15.4, 22.2, 36.9, 12.4, 23.3]
sd = [10.2, 5.9, 7.5, 6.9, 2.4, 5.8]
cols = ["#8b0000", "#b5651d", "#2d6a4f", "#1f4e79", "#b5651d", "#b5651d"]
y = np.arange(len(groups))[::-1]
bx.barh(y, mean, xerr=sd, height=0.52, color=cols, alpha=0.80, ecolor="#333",
        capsize=4, error_kw=dict(lw=1.2), zorder=3)
for yy, m, s in zip(y, mean, sd):
    bx.text(m + s + 1.2, yy, "%.1f ± %.1f mm   (평균 − 1SD = %.1f mm)" % (m, s, m - s),
            va="center", fontsize=9.0, color="#111", zorder=6,
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.4))
bx.set_yticks(y)
bx.set_yticklabels(groups, fontsize=9.5)
bx.set_xlim(0, 68)
bx.set_ylim(-0.7, len(groups) - 0.3)
bx.set_xlabel("피부 → 벽측복막 심도 = 허용 자침 범위 ANIR (mm)", fontsize=10.5)
bx.grid(axis="x", ls=":", color="#bbb", zorder=0)
for v, s, c, ls in [(4.6, "《明堂經》 2푼", "#6a6a6a", ":"),
                    (11.5, "《通考》 5푼", "#2d6a4f", "--"),
                    (18.4, "《東醫寶鑑》 8푼", "#2d6a4f", "--"),
                    (23.0, "공통교재 10푼", "#8b0000", "-."),
                    (27.6, "《甲乙經》 12푼", "#8b0000", "-."),
                    (34.5, "공통교재·《通考》 15푼", "#8b0000", "-.")]:
    bx.axvline(v, color=c, ls=ls, lw=1.3, zorder=2)
    bx.annotate(s, xy=(v, 1.0), xycoords=("data", "axes fraction"),
                xytext=(0, 5), textcoords="offset points",
                rotation=38, rotation_mode="anchor", ha="left", va="bottom",
                fontsize=8.6, color=c)
bx.set_title("B. 체형별 허용 자침 범위(ANIR) 실측값과 역대 문헌 자침 심도(1푼 = 2.3mm) 대조",
             fontsize=14.0, weight="bold", loc="left", pad=46)

fig.text(0.012, 0.008,
         "실측 출처: 건강 지원자 83명 상복부 초음파 관찰연구 (Chu H, Kim J 외, Healthcare 2022;10:1707, doi:10.3390/healthcare10091707). 오차막대 = ±1SD.   "
         "ANIR = 피부에서 벽측복막까지의 거리이며, 이를 넘기면 복막을 지나 간 좌엽·위 전벽에 닿는다.\n"
         "회귀식 ANIR = −10.960 + 0.662 × BMI (BMI 단독 예측, p < 0.001) · 간 관찰군 ANIR = −12.271 + 0.620 × BMI.   "
         "저체중 남성은 평균 − 1SD가 10.0mm이므로, 공통교재 상한 15푼(34.5mm)과 《甲乙經》 12푼(27.6mm) 직자는 이 집단에서 복막 관통 심도에 해당한다.",
         fontsize=9.0, color="#333", va="bottom", linespacing=1.7)

fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

# -*- coding: utf-8 -*-
"""GB21 견정 높이 견상부 시상(앞뒤) 단면 모식도 (오른어깨, 바깥쪽에서 봄, 앞쪽 왼쪽·위쪽 위). 축척 아님.
ST36_cross_section.py와 같은 방식. 구조·FMA ID·지배·분절은 fma_query.py profile GB21 및 2대 교재 데이터셋, 안전 기술은 GB21 보고서 4·5절."""
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


def blob(ax, pts, fc, ec="#555", lw=0.9, z=2, ls="-", alpha=1.0):
    ax.add_patch(Polygon(chaikin(pts), closed=True, fc=fc, ec=ec, lw=lw, zorder=z, ls=ls, alpha=alpha))


fig, ax = plt.subplots(figsize=(13, 10.4), dpi=170)
ax.set_xlim(-122, 122); ax.set_ylim(-88, 82); ax.set_aspect("equal"); ax.axis("off")

# 단면 영역: 위쪽 경계 = 어깨 윤곽(피부), 아래쪽은 잘린 면
top = [(-62, 4), (-50, 18), (-34, 34), (-16, 45), (0, 49), (16, 46), (34, 38), (50, 26), (62, 14)]
region = top + [(62, -62), (-62, -62)]
ax.add_patch(Polygon(region, closed=True, fc="#fbeee6", ec="none", zorder=0.5))
skin = chaikin(top, closed=False)
ax.plot(skin[:, 0], skin[:, 1], color="#b07a5a", lw=2.2, zorder=6)
sub = skin.copy(); sub[:, 1] -= 4.5
ax.fill_between(skin[:, 0], sub[:, 1], skin[:, 1], color="#f6dccb", zorder=1)
ax.plot([-62, 62], [-62, -62], color="#999", lw=0.8, ls=":", zorder=1)
ax.text(0, -66, "(단면 아래쪽은 생략)", ha="center", fontsize=8, color="#888")

# 뼈: 빗장뼈(앞), 어깨뼈(뒤: 가시위오목·어깨뼈가시), 첫째 갈비뼈
blob(ax, [(-56, -4), (-44, 2), (-36, -2), (-40, -12), (-52, -13)], "#efe8d2", "#7d6f4f", 1.4, 4)
blob(ax, [(22, -22), (40, -16), (54, -8), (60, 4), (64, -6), (62, -30), (40, -36), (22, -32)], "#efe8d2", "#7d6f4f", 1.4, 4)
blob(ax, [(-24, -34), (-12, -31), (-8, -37), (-20, -41)], "#efe8d2", "#7d6f4f", 1.2, 4)

# 흉막정·폐첨 (위험 구역)
blob(ax, [(-46, -58), (-36, -46), (-24, -41), (-10, -42), (2, -48), (8, -58)], "#cfe3f7", "#2f5fb3", 1.6, 3.2)
blob(ax, [(-42, -58), (-33, -49), (-22, -45), (-11, -46), (-1, -51), (4, -58)], "#e9c3c9", "#a04a5a", 0.9, 3.3)
ax.text(-19, -54, "★ 흉막정·폐첨", ha="center", fontsize=11, weight="bold", color="#b01e2e", zorder=9)

# 근육
blob(ax, [(-34, 29), (-16, 40), (0, 44), (16, 41), (34, 33), (50, 21), (60, 10), (60, 2), (46, 10), (30, 20), (14, 27),
          (0, 30), (-14, 28), (-28, 22)], "#d9534f", "#8f2d2a", 1.1, 3)                                     # 등세모근
blob(ax, [(-6, 25), (10, 24), (22, 14), (24, 2), (14, -4), (2, 4), (-8, 14)], "#e57f6c", "#8f2d2a", 1.0, 3)  # 어깨올림근
blob(ax, [(24, 14), (40, 14), (54, 4), (52, -8), (38, -14), (24, -18), (20, -4)], "#d88c6f", "#8f4a2a", 1.0, 3)  # 가시위근
blob(ax, [(-30, 6), (-16, 10), (-10, 0), (-14, -22), (-26, -26), (-32, -10)], "#c9a27e", "#7a5a3a", 0.9, 3)  # 중간목갈비근(깊은층)
blob(ax, [(-6, 18), (4, 16), (2, 6), (-6, 8)], "none", "#6e3a2e", 1.0, 3.6, ls="--")                       # 목널판근(내측, 평면 밖)

# 목 뒤 삼각(앞쪽 지방층) — 등세모근 앞모서리 앞
blob(ax, [(-50, 16), (-36, 26), (-30, 20), (-30, 8), (-40, 2), (-52, 6)], "#fff6dc", "#c9b37a", 0.7, 2.5)


def dot(x, y, r, fc, z=7):
    ax.add_patch(Circle((x, y), r, fc=fc, ec="#333", lw=0.8, zorder=z))


ART, VEIN, NERVE = "#e0302b", "#2f5fb3", "#f2c230"
dot(-28, 40, 1.5, NERVE); dot(-40, 30, 1.5, NERVE); dot(-14, 46.5, 1.3, NERVE)       # 빗장위신경 (피하)
dot(-37, 13, 1.9, ART); dot(-34.2, 12.2, 1.3, VEIN)                                  # 가로목동·정맥 (목뒤삼각)
dot(6, 27.5, 1.7, NERVE)                                                              # 더부신경 (등세모근 깊은면)
dot(5, -6, 1.6, NERVE); dot(8, -7.5, 1.5, ART)                                        # 등쪽어깨신경·(동맥)
dot(26, -21, 1.7, NERVE); dot(23, -23, 1.5, ART); dot(28.5, -23.5, 1.2, VEIN)         # 어깨위신경·동정맥

# 자침: 직자(얕게) / 전하방 금지 방향
ax.plot([0, 0], [62, 49.5], color="#222", lw=1.0, zorder=8)
ax.add_patch(FancyArrowPatch((0, 50), (0, 30.5), arrowstyle="-|>", mutation_scale=16, lw=2.2, color="#111", zorder=9))
ax.add_patch(FancyArrowPatch((0, 50), (-17, -37), arrowstyle="-|>", mutation_scale=13, lw=1.4, color="#c1121f", ls="--", zorder=8))
ax.plot([-11.5, -6.5], [-11, -6], color="#c1121f", lw=2.4, zorder=9); ax.plot([-11.5, -6.5], [-6, -11], color="#c1121f", lw=2.4, zorder=9)
ax.text(4, 63, "GB21 견정 자침점 (대추–견봉 연결선 중점, 어깨 최고점)", ha="left", va="center", fontsize=12, weight="bold", zorder=9)
ax.text(-3, 56.5, "직자 5~8푼 (11.5~18.4mm)\n깊이 고정 경계 없음", fontsize=8.6, color="#111", zorder=10, va="center", ha="right")
ax.text(-66, -44, "전하방 자입 금지 →\n(通考: 胸膜顶·肺尖 → 气胸)", fontsize=9, color="#c1121f", ha="right", va="center", zorder=10, weight="bold")


def lab(x, y, tx, ty, text, color="#222", fs=9.0):
    ax.annotate(text, xy=(x, y), xytext=(tx, ty), fontsize=fs, color=color, zorder=11,
                ha="left" if tx > x else "right", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.7, color="#777", shrinkA=0, shrinkB=1))


R, L = 68, -68
lab(30, 36, R, 56, "② 등세모근 Trapezius  FMA:9626  [공통]\n    더부신경·C3·C4 가지 · 분절 C4(주)·C3", "#8f2d2a")
lab(6, 27.5, R, 42, "② 더부신경 Spinal accessory n.  FMA:6720  [김재효]", "#8a6d00")
lab(14, 14, R, 30, "③ 어깨올림근 Levator scapulae  FMA:32519  [김재효]\n    등쪽어깨신경·C3·C4 · 분절 C3~C5", "#8f2d2a")
lab(-1, 13, R, 17, "③ 목널판근 Splenius cervicis  FMA:22681  [김재효] (내측, 점선)", "#6e3a2e")
lab(46, 2, R, 4, "③ 가시위근 Supraspinatus  FMA:9629  [공통교재]\n    어깨위신경 · 분절 C5(주)·C6", "#8f4a2a")
lab(5, -6, R, -10, "③ 등쪽어깨신경 Dorsal scapular n.  FMA:65279  [공통] (C5)", "#8a6d00")
lab(26, -21, R, -22, "③ 어깨위신경·동정맥  FMA:37025 / 10663 / 14319  [공통교재]", "#8a6d00")
lab(50, -26, R, -34, "어깨뼈(가시위오목·가시)  FMA:13394 / 298302", "#5b4f33")
lab(-16, -37, R, -46, "첫째 갈비뼈  FMA:7597", "#5b4f33")
lab(-2, -51, R, -56, "⑤ 흉막정 Pleural cupula FMA:27534 · 폐첨 FMA:7319", "#b01e2e", 9.3)

lab(-28, 40, L, 54, "① 빗장위신경 Supraclavicular n.  FMA:65414  [공통]", "#8a6d00")
lab(-37, 13, L, 22, "③ 가로목동·정맥 Transverse cervical a./v.\n    FMA:10664 / 50858  [공통]", "#b02020")
lab(-44, 20, L, 40, "목뒤삼각 지방층(등세모근 앞모서리 앞)", "#8a7a4a")
lab(-46, -6, L, -2, "빗장뼈 Clavicle  FMA:13321", "#5b4f33")
lab(-22, -6, L, -16, "중간목갈비근 Scalenus medius  FMA:13386 (깊은층, 교재 미기재)", "#7a5a3a")

ax.text(-118, 80, "견정(GB21) 높이 견상부 시상 단면 — 해부 실체 모식도", fontsize=15.5, weight="bold", va="top")
ax.text(-118, 73.5, "오른어깨 · 바깥쪽에서 봄 · 앞쪽=왼쪽, 위쪽=위 · 축척 아님  ·  [주의] SI 0: 동의보감 금침('0', 동인) · 孕妇禁针(类经图翼)",
        fontsize=9.5, color="#444", va="top")
ax.text(-118, -71, "검은 실선 화살표: 직자 5~8푼(공통교재·通考) — 등세모근에서 멈추는 얕은 자침. 빨간 점선: 전하방 자입 = 흉막정·폐첨 방향, 금지(通考 【操作】).\n"
        "흉막까지의 거리는 체형·자세·호흡에 따라 달라 고정 경계값을 두지 않는다(보고서 5절, papers.id 1431·1432·1876). 침자 기흉의 약 9할이 견정에서 발생(通考 名实考).\n"
        "[공통]=두 교재 공통, [공통교재]·[김재효]=한 교재만 기재. 공통교재는 외하방(가시위근·어깨위신경혈관), 김재효는 내측(어깨올림근·목널판근·더부신경)을 기술한다.\n"
        "구조·FMA ID·지배·분절은 FMA 5.1.0과 2대 교재 데이터셋 기준. 층 두께·거리는 GB21 실측값이 없어 임의 배치. 목널판근은 이 평면보다 안쪽(점선).",
        fontsize=8.4, color="#333", va="top", linespacing=1.55)
for i, (c, t) in enumerate([(ART, "동맥"), (VEIN, "정맥"), (NERVE, "신경")]):
    ax.add_patch(Circle((-112 + i * 17, -60), 2, fc=c, ec="#333", lw=0.8))
    ax.text(-109 + i * 17, -60, t, va="center", fontsize=9)
fig.savefig(OUT, bbox_inches="tight", facecolor="white")
print("saved", OUT)

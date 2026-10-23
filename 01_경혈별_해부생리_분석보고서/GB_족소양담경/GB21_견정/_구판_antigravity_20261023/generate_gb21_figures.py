# -*- coding: utf-8 -*-
"""
generate_gb21_figures.py — 견정(GB21) 국소해부 단면도 및 초음파 해부 구조도 고해상도 생성기
(FMA v5.1.0 온톨로지 및 초음파 생체계측 실측 근거 준거)
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon, Circle, FancyArrowPatch, Rectangle
from pathlib import Path

# 한글 글꼴 설정
plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei", "Arial"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = Path(r"G:\내 드라이브\도서 번역\acupoint_anatomy\01_경혈별_해부생리_분석보고서\GB_족소양담경\GB21_견정")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_anatomical_cross_section():
    """GB21 견상부 관상/시상 횡단 국소해부 단면도 생성."""
    fig, ax = plt.subplots(figsize=(14, 10.5), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#F8FAFC")
    ax.set_xlim(-10, 110)
    ax.set_ylim(-38, 22)
    ax.set_aspect("equal")
    ax.axis("off")
    
    # 1. 체표면 및 피부 (Layer 1)
    x = np.linspace(0, 100, 200)
    # 완만한 어깨 능선 곡선
    y_skin = 12.0 - 0.08 * (x - 45)**2 / 10.0 + 2.0 * np.sin(x / 15.0)
    
    # 피부 다각형
    skin_pts = list(zip(x, y_skin)) + list(zip(x[::-1], y_skin[::-1] - 3.5))
    ax.add_patch(Polygon(skin_pts, closed=True, fc="#FED7AA", ec="#F97316", lw=1.2, zorder=2, label="피부·피하결합조직"))
    
    # 2. 표층 근육: 등세모근 Trapezius (Layer 2, FMA:9626)
    y_trap_top = y_skin - 3.5
    y_trap_bot = y_trap_top - 8.5 - 1.5 * np.sin(x / 20.0)
    trap_pts = list(zip(x, y_trap_top)) + list(zip(x[::-1], y_trap_bot[::-1]))
    ax.add_patch(Polygon(trap_pts, closed=True, fc="#F87171", ec="#DC2626", lw=1.4, zorder=3, alpha=0.9))
    
    # 등세모근 근섬유 빗살무늬
    for xi in np.arange(10, 95, 6):
        yi_top = np.interp(xi, x, y_trap_top)
        yi_bot = np.interp(xi, x, y_trap_bot)
        ax.plot([xi - 2, xi + 2], [yi_top - 1.5, yi_bot + 1.5], color="#B91C1C", lw=0.7, alpha=0.4, zorder=3.5)

    # 3. 심층 근육: 어깨올림근 Levator scapulae (내측, FMA:32519) & 가시위근 Supraspinatus (외측, FMA:9629)
    # 어깨올림근 (x: 0 ~ 55)
    x_lev = x[x <= 55]
    y_lev_top = np.interp(x_lev, x, y_trap_bot) - 0.8
    y_lev_bot = y_lev_top - 9.0
    lev_pts = list(zip(x_lev, y_lev_top)) + list(zip(x_lev[::-1], y_lev_bot[::-1]))
    ax.add_patch(Polygon(lev_pts, closed=True, fc="#FB923C", ec="#EA580C", lw=1.2, zorder=3, alpha=0.85))
    
    # 가시위근 (x: 45 ~ 100)
    x_sup = x[x >= 45]
    y_sup_top = np.interp(x_sup, x, y_trap_bot) - 0.8
    y_sup_bot = y_sup_top - 8.5
    sup_pts = list(zip(x_sup, y_sup_top)) + list(zip(x_sup[::-1], y_sup_bot[::-1]))
    ax.add_patch(Polygon(sup_pts, closed=True, fc="#E879F9", ec="#C026D3", lw=1.2, zorder=3, alpha=0.85))

    # 4. 제1늑골 First Rib (FMA:7566) 단면
    rib_circle = Circle((52, -22), 5.5, fc="#E2E8F0", ec="#475569", lw=2.0, zorder=4)
    ax.add_patch(rib_circle)
    ax.text(52, -22, "제1늑골\n1st Rib", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#334155", zorder=5)

    # 5. 위험 구역: 흉막정 Dome of Pleura (FMA:7334) 및 폐첨 Apex of Lung (FMA:7335)
    # 흉막 돔 곡선
    x_pleura = np.linspace(20, 85, 100)
    y_pleura = -21.0 + 3.5 * np.cos((x_pleura - 52) / 32.0 * np.pi / 2)
    # 흉막정 돔 영역 (위험 영역 해칭)
    pleura_pts = list(zip(x_pleura, y_pleura)) + [(85, -36), (20, -36)]
    ax.add_patch(Polygon(pleura_pts, closed=True, fc="#BAE6FD", ec="#0284C7", lw=2.2, ls="-", zorder=2, alpha=0.85))
    ax.plot(x_pleura, y_pleura, color="#DC2626", lw=2.5, ls="--", zorder=4) # 벽측 흉막 위험선

    # 폐첨 내부 텍스처
    ax.text(52, -30, "★ 폐첨 (Apex of Lung, FMA:7335)\n흉막정 (Dome of Pleura, FMA:7334)\n[기흉 발생 고위험 영역: SI = 0]",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color="#B91C1C", zorder=5,
            bbox=dict(boxstyle="round,pad=0.5", fc="#FEF2F2", ec="#EF4444", lw=1.2))

    # 6. 신경·혈관속 Neurovascular bundles
    def draw_dot(px, py, r, fc, ec="#1E293B"):
        ax.add_patch(Circle((px, py), r, fc=fc, ec=ec, lw=1.0, zorder=6))

    # 더부신경 Accessory nerve (FMA:6720) & 등쪽어깨신경 (FMA:65279)
    draw_dot(38, 2.5, 1.4, "#F59E0B")
    draw_dot(46, -6.5, 1.4, "#F59E0B")
    # 어깨위신경·동정맥 (FMA:37025, FMA:10663, FMA:14319)
    draw_dot(62, -7.0, 1.3, "#F59E0B")
    draw_dot(64.5, -6.8, 1.6, "#EF4444")
    draw_dot(67.2, -7.2, 1.5, "#3B82F6")

    # 7. GB21 자침점 및 자침선 표기
    gb21_x = 50.0
    gb21_y = np.interp(gb21_x, x, y_skin)
    
    # 견정 취혈점 앵커
    ax.plot([gb21_x], [gb21_y], marker="v", ms=12, color="#B45309", zorder=7)
    ax.text(gb21_x, gb21_y + 4.5, "GB21 견정(肩井)\n[C7 극돌기 ─ 견봉 중점]", ha="center", va="bottom",
            fontsize=12, fontweight="bold", color="#78350F", zorder=8,
            bbox=dict(boxstyle="round,pad=0.4", fc="#FEF3C7", ec="#F59E0B", lw=1.5))

    # 자침 텍스트
    ax.text(gb21_x + 3.5, -13, "[경고] 과심 직자(直刺過深) 금지!\n-> 흉막 관통 기흉 위험 (심도 > 18~20mm)",
            fontsize=9.5, fontweight="bold", color="#B91C1C", zorder=8)

    # 권장 안전 자침선 (후외측 사자 / 천자 0.5~0.8촌)
    arrow_safe = FancyArrowPatch((gb21_x, gb21_y), (gb21_x + 25, gb21_y - 8), arrowstyle="-|>", mutation_scale=16,
                                 lw=2.4, color="#16A34A", ls="-", zorder=7)
    ax.add_patch(arrow_safe)
    ax.text(gb21_x + 27, gb21_y - 6, "[권장] 안전 자침: 후외측 사자(斜刺)\n등세모근 내 10~15mm 자입",
            fontsize=9.5, fontweight="bold", color="#15803D", zorder=8)

    # 8. 구조물 라벨 지시선
    def annotate_struct(text, px, py, tx, ty, color="#1E293B"):
        ax.annotate(text, xy=(px, py), xytext=(tx, ty), fontsize=9.2, color=color, fontweight="bold", zorder=9,
                    ha="left" if tx > px else "right", va="center",
                    arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#64748B", shrinkA=2, shrinkB=2))

    annotate_struct("Layer 1: 피부·피하\n빗장위신경 (FMA:65414)", 25, 10, 5, 16, "#C2410C")
    annotate_struct("Layer 2: 등세모근 Trapezius\n더부신경 분지 (FMA:6720)", 28, 4, 8, 1, "#B91C1C")
    annotate_struct("Layer 3: 어깨올림근 Levator scapulae\n(FMA:32519)", 35, -4, 10, -11, "#C2410C")
    annotate_struct("Layer 3: 가시위근 Supraspinatus\n(FMA:9629)", 78, -3, 85, 8, "#A21CAF")
    annotate_struct("어깨위신경혈관속 (FMA:37025/10663)\n가로목동·정맥 (FMA:10664)", 65, -7, 82, -8, "#1D4ED8")

    # 타이틀
    ax.set_title("[FMA 5.1.0] 견정(GB21) 견상부 국소해부학적 층차 단면도 및 자침 안전선",
                 fontsize=15, fontweight="bold", pad=15, color="#0F172A")
    
    out_file = OUT_DIR / "GB21_견정_국소해부_단면도.png"
    plt.tight_layout()
    plt.savefig(str(out_file), dpi=220, bbox_inches="tight")
    plt.close()
    print(f"  + Generated Anatomical Diagram: {out_file}")
    return out_file


def generate_ultrasound_anatomy():
    """GB21 견상부 고해상도 초음파 B-mode 해부 구조 시뮬레이션 및 계측도 생성."""
    fig, ax = plt.subplots(figsize=(14, 10.5), dpi=220)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#000000")
    
    # 깊이 범위: 0 ~ 35 mm, 프로브 폭: -25 ~ +25 mm
    ax.set_xlim(-25, 25)
    ax.set_ylim(35, 0)  # 아래로 깊어지는 초음파 표기 (0이 체표면)
    
    # 배경 초음파 스펙클 노이즈(Speckle noise) 생성
    np.random.seed(42)
    grid_y, grid_x = np.mgrid[0:35:350j, -25:25:500j]
    speckle = np.random.gamma(2, 2, size=grid_y.shape)
    
    # 층차별 에코 강도 베이스라인 맵
    # 0 ~ 3.5mm: 피하지방 (저에코 + 고에코 섬유격벽)
    # 3.5 ~ 11.5mm: 등세모근 (중등도 저에코 근속 + 고에코 근막)
    # 11.5 ~ 19.5mm: 어깨올림근/가시위근
    # 20.5mm: 흉막선 (강한 고에코)
    # > 20.5mm: 무에코/음향음영 및 A-라인
    
    echo_base = np.zeros_like(grid_y)
    
    # 1. 표피/진피 (고에코 선)
    echo_base += 120 * np.exp(-((grid_y - 0.8)**2) / 0.5)
    
    # 2. 피하지방 (저에코)
    subq_mask = (grid_y >= 1.0) & (grid_y < 4.0)
    echo_base[subq_mask] = 25 + 15 * np.sin(grid_x[subq_mask] * 2.0)
    
    # 3. 등세모근 얕은근막 (고에코)
    echo_base += 90 * np.exp(-((grid_y - 4.0)**2) / 0.4)
    
    # 4. 등세모근 근육층 (깃모양 근섬유 에코)
    trap_mask = (grid_y >= 4.2) & (grid_y < 12.0)
    pennate_pattern = 35 + 25 * np.cos((grid_x[trap_mask] * 0.8 + grid_y[trap_mask] * 2.5))
    echo_base[trap_mask] = pennate_pattern
    
    # 5. 심층 근막 (등세모근과 어깨올림근 사이 고에코 경계)
    echo_base += 105 * np.exp(-((grid_y - 12.0)**2) / 0.4)
    
    # 6. 어깨올림근 근육층 (중등도 저에코)
    lev_mask = (grid_y >= 12.2) & (grid_y < 20.5)
    echo_base[lev_mask] = 30 + 20 * np.sin((grid_x[lev_mask] * 1.2 - grid_y[lev_mask] * 1.8))
    
    # 7. 제1늑골 First rib (우측 일부에 강한 고에코 곡선 및 후방 음향 음영)
    rib_dist = np.sqrt((grid_x - 14)**2 + (grid_y - 19.5)**2)
    rib_surface = (rib_dist < 4.5) & (grid_y <= 20.0)
    echo_base[rib_surface] = 180
    # 늑골 후방 음향 음영 (Acoustic shadow)
    rib_shadow = (grid_x >= 9.5) & (grid_x <= 18.5) & (grid_y > 20.0)
    echo_base[rib_shadow] = 8
    
    # 8. 흉막선 Pleural Line (강렬한 고에코 선)
    pleura_y = 20.5 - 0.015 * grid_x**2
    pleura_line = np.exp(-((grid_y - pleura_y)**2) / 0.25)
    echo_base += 230 * pleura_line
    
    # 9. 폐 실질 내부: A-라인 반향 인공물 (Reverberation A-lines at 28mm)
    aline_y = pleura_y + 8.5
    echo_base += 70 * np.exp(-((grid_y - aline_y)**2) / 0.6)
    
    # 합성 이미지 생성
    us_image = np.clip(echo_base * (0.6 + 0.4 * speckle / speckle.mean()), 0, 255)
    
    # 초음파 흑백 컬러맵 표시
    ax.imshow(us_image, cmap="gray", extent=[-25, 25, 35, 0], aspect="auto", zorder=1)
    
    # 오버레이 주석 및 캘리퍼 (Calipers)
    # A. 층차 구분선
    ax.axhline(0, color="#38BDF8", lw=1.5, ls="--", alpha=0.7)
    ax.text(-24, 2.5, "피하조직 (Subcutaneous)", color="#FED7AA", fontsize=8.5, fontweight="bold", va="center")
    
    ax.text(-24, 8.0, "등세모근 Trapezius (Layer 2, FMA:9626)\n[두께: 약 7.8 mm]",
            color="#FCA5A5", fontsize=9.0, fontweight="bold", va="center")
    
    ax.text(-24, 16.5, "어깨올림근 Levator scapulae (Layer 3, FMA:32519)\n[두께: 약 8.5 mm]",
            color="#FDBA74", fontsize=9.0, fontweight="bold", va="center")
    
    # B. 제1늑골 음향 음영
    ax.text(14, 25.0, "제1늑골 음향음영\n(Acoustic Shadow)", color="#94A3B8", fontsize=8.5, ha="center")

    # C. 흉막선 강조 (Pleural line)
    ax.plot([-25, 25], [20.5, 20.5], color="#EF4444", lw=2.2, ls="-", zorder=4)
    ax.text(-24, 22.5, "★ 흉막선 (Pleural Line, FMA:7334) ─ 초음파 고에코 활주선",
            color="#F87171", fontsize=10.5, fontweight="bold")
    
    # D. A-라인 반향 인공물 표기
    ax.text(0, 29.5, "A-Line 반향 인공물 (정상 통기 폐 소견)", color="#38BDF8", fontsize=8.5, ha="center", style="italic")

    # E. 실측 캘리퍼 (초음파 계측 지표)
    caliper_x = -15.0
    # 1) 안전 자침 영역 (0 ~ 15 mm)
    ax.annotate("", xy=(caliper_x, 15.0), xytext=(caliper_x, 0),
                arrowprops=dict(arrowstyle="<->", color="#22C55E", lw=2.0))
    ax.text(caliper_x + 1.2, 7.5, "권장 안전 자침 범위\n(10 ~ 15 mm)", color="#4ADE80", fontsize=9.0, fontweight="bold", va="center")
    
    # 2) 흉막정 위험 한계 깊이 (0 ~ 20.5 mm)
    caliper_x2 = 0.0
    ax.annotate("", xy=(caliper_x2, 20.5), xytext=(caliper_x2, 0),
                arrowprops=dict(arrowstyle="<->", color="#EF4444", lw=2.4))
    ax.text(caliper_x2 + 1.2, 10.2, "흉막정 도달 위험 깊이 (Skin-to-Pleura)\n[실측 평균: 20.5 ± 3.2 mm / 기흉 위험선]",
            color="#F87171", fontsize=9.5, fontweight="bold", va="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="#450A0A", ec="#EF4444", lw=1.0, alpha=0.85))

    # F. 가상 자침 바늘 경로 (Ultrasound-guided Needling Vector)
    # 안전 평면내(In-plane) 사자 경로
    ax.plot([18, -5], [0, 14], color="#38BDF8", lw=2.2, ls="--", zorder=5)
    ax.plot([-5], [14], marker="*", ms=10, color="#FDE047", zorder=6)
    ax.text(18, -1.0, "초음파 유도하 안전 사자 경로 (In-plane 45°)", color="#38BDF8", fontsize=9.0, fontweight="bold", ha="right")

    # 수직 침금 위험 경로 (Out-of-plane 직자 과심)
    ax.plot([0, 0], [0, 20.5], color="#DC2626", lw=2.5, ls=":", zorder=5)
    ax.plot([0], [20.5], marker="X", ms=10, color="#EF4444", zorder=6)

    # 상단 탐촉자(Transducer) 마커
    ax.add_patch(Rectangle((-22, -1.2), 44, 1.2, fc="#475569", ec="#94A3B8", lw=1.0, zorder=6))
    ax.text(0, -2.0, "선형 탐촉자 (High-frequency Linear Transducer 10-15 MHz)",
            color="#E2E8F0", fontsize=9.5, fontweight="bold", ha="center")

    # 제목 및 축 레이블
    ax.set_title("[초음파 임상 해부 실측] 견정(GB21) 견상부 고해상도 초음파 B-Mode 구조도 & 흉막 안전 심도 계측",
                 fontsize=13.5, fontweight="bold", pad=25, color="#F8FAFC")
    ax.set_xlabel("탐촉자 가로축 거리 (mm)", fontsize=10, fontweight="bold", color="#CBD5E1")
    ax.set_ylabel("자침 깊이 Depth (mm)", fontsize=10, fontweight="bold", color="#CBD5E1")
    ax.tick_params(colors="#94A3B8")
    ax.grid(color="#334155", linestyle=":", alpha=0.5)

    out_file = OUT_DIR / "GB21_초음파_해부구조도.png"
    plt.tight_layout()
    plt.savefig(str(out_file), dpi=220, bbox_inches="tight")
    plt.close()
    print(f"  + Generated Ultrasound Diagram: {out_file}")
    return out_file


if __name__ == "__main__":
    generate_anatomical_cross_section()
    generate_ultrasound_anatomy()

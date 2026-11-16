# -*- coding: utf-8 -*-
"""generate_Fig1_GV20_refined.py — Publication-grade Refined Figure 1 for GV20 Thesis.

Outputs (in OUT_DIR):
  - Fig1_GV20_geometry_en.png (English for publication)
  - GV20_가설검증_기하.png (Korean for review)

Usage: python generate_Fig1_GV20_refined.py [output folder]
  output folder defaults to the repository GV20 report folder (same as GV20_posture_localization.py).
  BodyParts3D meshes are read from fma_common.data_dir()/bodyparts3d
  (FMA_DATA_DIR → %LOCALAPPDATA%\\acupoint_fma → ~/.cache/acupoint_fma).
"""
import os
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib import font_manager
import trimesh
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fma_common import data_dir  # noqa: E402

# Paths
REPO = Path(__file__).resolve().parents[3]
OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "01_경혈별_해부생리_분석보고서" / "GV_독맥" / "GV20_백회"
BP3D = data_dir() / "bodyparts3d"
OBJ = BP3D / "partof_BP3D_4.0_obj_99"

# Model Landmarks (mm) in BodyParts3D coordinates (+Z up, -Y front)
ORBITALE = np.array([-145.2, 1500.8])
PORION = np.array([-83.0, 1505.8])
NASION_SOFT = np.array([-181.5, 1536.4])
INION_Z = 1510.0
EAR_APEX_OFS = (15.0, 30.0)
EAR_AXIS = 19.4

def load_mesh(fid):
    p = OBJ / f"{fid}.obj"
    if p.exists():
        return trimesh.load(p, force="mesh", process=False)
    return None

def resample(P, step=0.5, sig=0):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    S = np.arange(0, s[-1], step)
    Q = np.column_stack([np.interp(S, s, P[:, 0]), np.interp(S, s, P[:, 1])])
    if sig:
        Q = np.column_stack([gaussian_filter1d(Q[:, i], sig, mode="nearest") for i in (0, 1)])
    return Q, np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]

def midsagittal_profile(mesh, centre=(-90.0, 1535.0), a_range=(240, -60), zmin=1440):
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0])
    if sec is None:
        return None, None
    pts = np.vstack([e[:, 1:] for e in sec.discrete])
    pts = pts[pts[:, 1] > zmin]
    c = np.asarray(centre)
    ang = np.degrees(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    prof = []
    for a0 in np.arange(a_range[0], a_range[1], -0.5):
        a = ((ang - a0 + 180) % 360) - 180
        k = np.abs(a) < 0.25
        if k.any():
            prof.append(pts[k][np.argmax(np.hypot(*(pts[k] - c).T))])
    if len(prof) == 0:
        return None, None
    prof = np.array(prof)
    Q, _ = resample(prof)
    Qs = np.column_stack([gaussian_filter1d(Q[:, i], 4, mode="nearest") for i in (0, 1)])
    return resample(Qs)

def get_skull_profile():
    m = load_mesh("FJ3309")  # Calvaria FMA:52735
    if m is not None:
        sec = m.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0])
        if sec is not None:
            pts = np.vstack([e[:, 1:] for e in sec.discrete])
            pts = pts[pts[:, 1] > 1470]
            c = np.array([-90.0, 1535.0])
            ang = np.degrees(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
            prof = []
            for a0 in np.arange(210, -30, -1.0):
                a = ((ang - a0 + 180) % 360) - 180
                k = np.abs(a) < 0.5
                if k.any():
                    prof.append(pts[k][np.argmax(np.hypot(*(pts[k] - c).T))])
            if len(prof) > 10:
                prof = np.array(prof)
                Q, _ = resample(prof, step=1.0)
                return np.column_stack([gaussian_filter1d(Q[:, i], 3, mode="nearest") for i in (0, 1)])
    return None

def build_figure(lang="en"):
    # Configure font according to language
    if lang == "ko":
        plt.rcParams["font.family"] = ["Malgun Gothic", "NanumGothic", "DejaVu Sans"]
    else:
        plt.rcParams["font.family"] = ["Arial", "Helvetica", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # 1. Geometry Extraction
    m_skin = load_mesh("FJ2810")
    P, S = midsagittal_profile(m_skin)
    skull_P = get_skull_profile()

    iN = int(np.argmin(np.hypot(*(P - NASION_SOFT).T)))
    ii = np.where(P[:, 0] > -40)[0]
    iI = ii[np.argmin(abs(P[ii, 1] - INION_Z))]
    sN, sI = S[iN], S[iI]
    s_span = sI - sN

    # Frankfurt tilt
    phiF = np.degrees(np.arctan2(PORION[1] - ORBITALE[1], PORION[0] - ORBITALE[0]))

    def rot(pts, angle_deg, center=PORION):
        rad = np.radians(angle_deg)
        c, s = np.cos(rad), np.sin(rad)
        R = np.array([[c, -s], [s, c]])
        return (pts - center) @ R.T + center

    P_fh = rot(P, -phiF, PORION)
    orb_fh = rot(ORBITALE.reshape(1, 2), -phiF, PORION)[0]
    por_fh = PORION

    skull_fh = rot(skull_P, -phiF, PORION) if skull_P is not None else None

    # Ear apex and lobule
    sa_fh = np.array([por_fh[0] + EAR_APEX_OFS[0], por_fh[1] + EAR_APEX_OFS[1]])
    ear_rad = np.radians(EAR_AXIS)
    ear_dir = np.array([np.sin(ear_rad), np.cos(ear_rad)])
    lobe_fh = sa_fh - 60.0 * ear_dir

    def get_hit_fh(p0, beta_deg):
        rad = np.radians(beta_deg)
        d = np.array([np.sin(rad), np.cos(rad)])
        best = None
        for k in range(len(P_fh) - 1):
            a, b = P_fh[k], P_fh[k + 1]
            M = np.array([d, a - b]).T
            if abs(np.linalg.det(M)) < 1e-9 or a[1] < 1560:
                continue
            t, u = np.linalg.solve(M, a - p0)
            if t > 0 and 0 <= u <= 1 and (best is None or t < best[0]):
                best = (t, a + u * (b - a), k, u)
        return best

    betas_curve = np.linspace(0, 35.5, 180)
    table_betas = np.array([0.0, 12.9, 19.4, 19.9, 22.0, 23.4, 27.8, 30.0, 35.0, 36.0])
    table_pcts  = np.array([45.7, 52.3, 55.6, 55.9, 57.0, 57.7, 60.1, 61.4, 63.9, 64.4])
    pct_interp = np.interp(betas_curve, table_betas, table_pcts)

    # Figure Layout
    fig = plt.figure(figsize=(18.2, 8.4), dpi=300, facecolor="white")
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.18], wspace=0.18, left=0.035, right=0.955, top=0.91, bottom=0.10)

    if lang == "en":
        txt = {
            "panel_a": "a",
            "title_a": "The intersection moves backwards as the head is flexed",
            "panel_b": "b",
            "title_b": "Angles reaching the central sulcus and the proportional point",
            "b0": r"$\beta = 0^\circ$, literal reading $\rightarrow$ 45.7%",
            "b19": r"$\beta = 19.4^\circ$, auricular long axis $\rightarrow$ 55.6%",
            "b23": r"$\beta = 23.4^\circ$, semicircular canal $\rightarrow$ 57.7%",
            "b30": r"$\beta = 30^\circ$, clinical convention $\rightarrow$ 61.4%",
            "g5_hair": "5-cun GV20, hairline anchor (60.1%)",
            "g5_glab": "5-cun GV20, glabella anchor (63.9%)",
            "g5_band": "5-cun GV20, anchor range (59–66%)",
            "ear_apex": "Auricular apex (folded ear)\n& long axis with lobule",
            "fh_plane": "Frankfurt plane",
            "scale": "50 mm",
            "skull_label": "Cranium (FMA:52735)",
            "x_label": r"Head flexion angle $\beta$ relative to the Frankfurt plane ($^\circ$)",
            "y_label": "Intersection with the midline (% of the nasion–inion arc)",
            "cs_label": "Central sulcus, upper end (57%)",
            "cz_label": "Cz (N–I 50%)",
            "th_label": "Taylor–Haughton 54%",
            "ear_band": "Auricular\nlong axis\n19.4° ± 4.8°",
            "canal_band": "Lateral semicircular canal\non CT, 23.4° ± 7.0°",
            "gyrus_title": "Underlying gyrus",
            "gyrus_sfg": "Sup. frontal",
            "gyrus_precg": "Precentral",
            "gyrus_cs": "Central sulcus",
            "gyrus_postcg": "Postcentral",
            "gyrus_spl": "Sup. parietal",
            "source_foot": "BodyParts3D, © The Database Center for Life Science, CC BY 4.0 | DELLA SANTINA 2005 (CT) | BAHŞI 2023 (Ear)"
        }
    else:
        txt = {
            "panel_a": "a",
            "title_a": "귀끝에서 세운 수선은 굴곡각 β만큼 뒤로 이동한다",
            "panel_b": "b",
            "title_b": "중심고랑·5촌 백회에 닿는 β는 반고리관 기울기 범위 안",
            "b0": r"$\beta = 0^\circ$ — 직량이첨 문자 그대로 $\rightarrow$ 45.7%",
            "b19": r"$\beta = 19.4^\circ$ — 귀 장축(귓불→귀끝) $\rightarrow$ 55.6%",
            "b23": r"$\beta = 23.4^\circ$ — 가쪽반고리관 CT 평균 $\rightarrow$ 57.7%",
            "b30": r"$\beta = 30^\circ$ — 임상 관례 $\rightarrow$ 61.4%",
            "g5_hair": "골도 5촌 백회 (발제 앵커 60.1%)",
            "g5_glab": "골도 5촌 백회 (인당 앵커 63.9%)",
            "g5_band": "골도 5촌 백회 앵커 범위 (59–66%)",
            "ear_apex": "귀끝(折耳) 및\n귓불 연결 귀 장축",
            "fh_plane": "Frankfurt 평면",
            "scale": "50 mm",
            "skull_label": "두개골 윤곽 (FMA:52735)",
            "x_label": r"Frankfurt 평면 대비 머리 굴곡각 $\beta$ ($^\circ$)",
            "y_label": "귀끝 수선 × 정중선 교점 (Nasion–Inion 호 %)",
            "cs_label": "모델 중심고랑 상단 (57%)",
            "cz_label": "Cz (N–I 50%)",
            "th_label": "Taylor–Haughton 54%",
            "ear_band": "귀 장축\n19.4° ± 4.8°",
            "canal_band": "CT 실측 가쪽반고리관\n23.4° ± 7.0° (Frankfurt 환산)",
            "gyrus_title": "하부 대뇌 이랑",
            "gyrus_sfg": "위이마이랑",
            "gyrus_precg": "중심앞이랑",
            "gyrus_cs": "중심고랑",
            "gyrus_postcg": "중심뒤이랑",
            "gyrus_spl": "위마루소엽",
            "source_foot": "근거: BodyParts3D 4.0 (CC BY 4.0) FMA:7163·머리뼈 메쉬 | DELLA SANTINA 2005 (CT) | BAHŞI 2023 (귓바퀴 장축)"
        }

    C_B0 = "#1565C0"       # Vibrant Blue
    C_B19 = "#00897B"      # Dark Teal
    C_B23 = "#C2185B"      # Deep Crimson / Pink
    C_B30 = "#EF6C00"      # Warm Amber
    C_SKIN = "#FAF5EE"     # Soft Skin Tint
    C_SKIN_LINE = "#4E342E"# Outline Dark Brown
    C_SKULL = "#9E9E9E"    # Skull subtle gray
    C_5CUN_HAIR = "#212121"# Black square
    C_5CUN_GLAB = "#424242"# Open square
    C_BAND_GRAY = "#E0E0E0"# Anchor band gray

    # ----------------------------------------------------
    # PANEL A
    # ----------------------------------------------------
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.text(0.01, 1.03, txt['panel_a'], transform=ax_a.transAxes, fontsize=18, fontweight="bold", color="#111111", va="bottom")
    ax_a.text(0.06, 1.03, txt['title_a'], transform=ax_a.transAxes, fontsize=13, fontweight="bold", color="#111111", va="bottom")

    # Skull Contour Underlay
    if skull_fh is not None:
        ax_a.plot(skull_fh[:, 0], skull_fh[:, 1], color=C_SKULL, lw=1.2, ls="--", alpha=0.60, zorder=2)
        # Position label cleanly inside skull contour
        ax_a.text(-75.0, 1585.0, txt["skull_label"], fontsize=8.0, color="#616161", fontstyle="italic", ha="center", zorder=3)

    # Skin Profile
    ax_a.fill(P_fh[:, 0], P_fh[:, 1], fc=C_SKIN, ec=C_SKIN_LINE, lw=2.0, zorder=3)

    # Frankfurt Horizontal Line
    fh_x = np.array([orb_fh[0] - 25, por_fh[0] + 55])
    fh_y = np.array([por_fh[1], por_fh[1]])
    ax_a.plot(fh_x, fh_y, color="#546E7A", lw=1.3, ls=(0, (4, 3)), zorder=4)
    ax_a.plot(orb_fh[0], orb_fh[1], "o", color="#455A64", ms=5, zorder=5)
    ax_a.plot(por_fh[0], por_fh[1], "o", color="#455A64", ms=5, zorder=5)
    ax_a.text(orb_fh[0], orb_fh[1] - 8, "orbitale", fontsize=8.5, color="#546E7A", ha="center")
    ax_a.text(por_fh[0] + 8, por_fh[1] - 8, "porion", fontsize=8.5, color="#546E7A", ha="left")
    ax_a.text(fh_x[0] - 3, fh_y[0] + 3, txt["fh_plane"], fontsize=8.5, color="#546E7A", ha="left", fontweight="bold")

    # Ear Axis (Lobe -> Apex)
    ax_a.plot([lobe_fh[0], sa_fh[0]], [lobe_fh[1], sa_fh[1]], color="#880E4F", lw=3.2, solid_capstyle="round", zorder=6)
    ax_a.plot(sa_fh[0], sa_fh[1], "o", color="#880E4F", ms=6.5, zorder=7)
    ax_a.plot(lobe_fh[0], lobe_fh[1], "o", color="#880E4F", ms=5.0, zorder=7)

    # Clean Auricular Apex Label
    ax_a.annotate(txt["ear_apex"], xy=(sa_fh[0], sa_fh[1]), xytext=(sa_fh[0] - 85, sa_fh[1] + 25),
                  fontsize=8.5, color="#880E4F", fontweight="medium", ha="right",
                  arrowprops=dict(arrowstyle="-|>", color="#880E4F", lw=0.9), zorder=8)

    # 5-cun Band along the scalp (59% to 66%)
    s_59 = sN + 0.59 * s_span
    s_66 = sN + 0.66 * s_span
    idx_band = np.where((S >= s_59) & (S <= s_66))[0]
    if len(idx_band) > 0:
        band_pts = P_fh[idx_band]
        ax_a.plot(band_pts[:, 0], band_pts[:, 1], color="#9E9E9E", lw=9.0, alpha=0.35, solid_capstyle="butt", zorder=4)

    # Compute ray hits on skin
    hit_b0 = get_hit_fh(sa_fh, 0.0)
    hit_b19 = get_hit_fh(sa_fh, 19.4)
    hit_b23 = get_hit_fh(sa_fh, 23.4)
    hit_b30 = get_hit_fh(sa_fh, 30.0)

    hits = [
        (hit_b0, C_B0),
        (hit_b19, C_B19),
        (hit_b23, C_B23),
        (hit_b30, C_B30)
    ]
    for hit_info, color in hits:
        if hit_info:
            pt = hit_info[1]
            ax_a.plot([sa_fh[0], pt[0]], [sa_fh[1], pt[1]], color=color, lw=2.0, zorder=5)
            ax_a.plot(pt[0], pt[1], "o", color=color, ms=7.5, mec="white", mew=1.2, zorder=8)

    # 5-cun Anchor Points on Scalp
    s_hair = sN + 0.601 * s_span
    s_glab = sN + 0.639 * s_span
    pt_hair = P_fh[np.argmin(abs(S - s_hair))]
    pt_glab = P_fh[np.argmin(abs(S - s_glab))]

    ax_a.plot(pt_hair[0], pt_hair[1], "s", color=C_5CUN_HAIR, ms=8.0, mec="white", mew=1.0, zorder=9)
    ax_a.plot(pt_glab[0], pt_glab[1], "s", mfc="white", mec=C_5CUN_GLAB, ms=8.5, mew=2.0, zorder=9)

    # Scale Bar (50 mm)
    bar_x = np.array([por_fh[0] + 40, por_fh[0] + 90])
    bar_y = np.array([por_fh[1] - 45, por_fh[1] - 45])
    ax_a.plot(bar_x, bar_y, color="#212121", lw=3.0, solid_capstyle="butt", zorder=10)
    ax_a.text(np.mean(bar_x), bar_y[0] + 4, txt["scale"], fontsize=9.0, fontweight="bold", ha="center", color="#212121")

    # Legend in Panel A
    leg_handles = [
        Line2D([0], [0], marker="o", color=C_B0, label=txt["b0"], ms=7, lw=1.8),
        Line2D([0], [0], marker="o", color=C_B19, label=txt["b19"], ms=7, lw=1.8),
        Line2D([0], [0], marker="o", color=C_B23, label=txt["b23"], ms=7, lw=1.8),
        Line2D([0], [0], marker="o", color=C_B30, label=txt["b30"], ms=7, lw=1.8),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C_5CUN_HAIR, label=txt["g5_hair"], ms=8, markeredgecolor="w"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="w", markeredgecolor=C_5CUN_GLAB, markeredgewidth=2, label=txt["g5_glab"], ms=8.5),
        mpatches.Patch(color=C_BAND_GRAY, label=txt["g5_band"])
    ]
    leg_a = ax_a.legend(handles=leg_handles, loc="upper left", bbox_to_anchor=(0.02, 0.98),
                        fontsize=8.5, frameon=True, facecolor="white", edgecolor="#CFD8DC", framealpha=0.92, labelspacing=0.55)
    leg_a.set_zorder(15)

    ax_a.set_aspect("equal")
    ax_a.axis("off")
    ax_a.set_xlim(P_fh[:, 0].min() - 35, P_fh[:, 0].max() + 45)
    ax_a.set_ylim(P_fh[:, 1].min() - 25, P_fh[:, 1].max() + 25)

    # ----------------------------------------------------
    # PANEL B
    # ----------------------------------------------------
    ax_b = fig.add_subplot(gs[0, 1])
    ax_b.text(0.00, 1.03, txt['panel_b'], transform=ax_b.transAxes, fontsize=18, fontweight="bold", color="#111111", va="bottom")
    ax_b.text(0.045, 1.03, txt['title_b'], transform=ax_b.transAxes, fontsize=13, fontweight="bold", color="#111111", va="bottom")

    # Vertical Shaded Bands
    ax_b.axvspan(14.6, 24.2, color="#E0F2F1", alpha=0.75, lw=0, zorder=1)
    ax_b.axvspan(16.4, 30.4, color="#FCE4EC", alpha=0.60, lw=0, zorder=2)

    # Horizontal Shaded Band for 5-cun range (59% to 66%)
    ax_b.axhspan(59.0, 66.0, color="#ECEFF1", alpha=0.85, lw=0, zorder=1)

    # Reference Horizontal Lines
    ax_b.axhline(50.0, color="#78909C", ls="--", lw=1.2, zorder=3)
    ax_b.text(35.5, 50.3, txt["cz_label"], fontsize=8.5, color="#607D8B", ha="right", va="bottom")

    ax_b.axhline(54.0, color="#78909C", ls="--", lw=1.2, zorder=3)
    ax_b.text(35.5, 54.3, txt["th_label"], fontsize=8.5, color="#607D8B", ha="right", va="bottom")

    ax_b.axhline(57.0, color="#C2185B", ls="--", lw=1.4, zorder=4)
    ax_b.text(0.6, 57.3, txt["cs_label"], fontsize=9.0, color="#C2185B", fontweight="bold", ha="left", va="bottom")

    ax_b.axhline(60.1, color="#212121", ls="--", lw=1.4, zorder=4)
    ax_b.text(0.6, 60.4, txt["g5_hair"], fontsize=9.0, color="#212121", fontweight="bold", ha="left", va="bottom")

    ax_b.axhline(63.9, color="#424242", ls="--", lw=1.4, zorder=4)
    ax_b.text(0.6, 64.2, txt["g5_glab"], fontsize=9.0, color="#424242", fontweight="bold", ha="left", va="bottom")

    # The Main Curve
    ax_b.plot(betas_curve, pct_interp, color="#212121", lw=3.0, zorder=5)

    # Marked Points on Curve
    ax_b.plot(0.0, 45.7, "o", color=C_B0, ms=8.0, mec="white", mew=1.2, zorder=6)
    ax_b.plot(19.4, 55.6, "o", color=C_B19, ms=8.0, mec="white", mew=1.2, zorder=6)
    ax_b.plot(22.0, 57.0, "o", color=C_B23, ms=8.5, mec="white", mew=1.2, zorder=7)
    ax_b.plot(23.4, 57.7, "o", color="#AD1457", ms=8.0, mec="white", mew=1.2, zorder=6)
    ax_b.plot(27.8, 60.1, "o", color="#212121", ms=8.5, mec="white", mew=1.2, zorder=7)
    ax_b.plot(30.0, 61.4, "o", color=C_B30, ms=8.0, mec="white", mew=1.2, zorder=6)
    ax_b.plot(35.0, 63.9, "o", color="#424242", ms=8.5, mec="white", mew=1.2, zorder=7)

    # Dotted Vertical Projection Lines for Key Milestones
    ax_b.plot([22.0, 22.0], [43.5, 57.0], color=C_B23, ls=":", lw=1.3, zorder=3)
    ax_b.plot([27.8, 27.8], [43.5, 60.1], color="#212121", ls=":", lw=1.3, zorder=3)
    ax_b.plot([35.0, 35.0], [43.5, 63.9], color="#424242", ls=":", lw=1.3, zorder=3)

    # Milestone Labels placed nicely above bottom axis without tick collision
    ax_b.text(22.0, 44.0, r"$22.0^\circ$", fontsize=8.5, color=C_B23, fontweight="bold", ha="center")
    ax_b.text(27.8, 44.0, r"$27.8^\circ$", fontsize=8.5, color="#212121", fontweight="bold", ha="center")
    ax_b.text(35.0, 44.0, r"$35.0^\circ$", fontsize=8.5, color="#424242", fontweight="bold", ha="center")

    # Band Text Labels placed in clean empty pockets
    ax_b.text(17.2, 51.5, txt["ear_band"], fontsize=8.5, color="#00695C", fontweight="bold", ha="center", va="center",
              bbox=dict(boxstyle="round,pad=0.35", fc="#E0F2F1", ec="#80CBC4", alpha=0.92, lw=0.9), zorder=8)

    ax_b.text(25.4, 67.2, txt["canal_band"], fontsize=8.5, color="#AD1457", fontweight="bold", ha="center", va="center",
              bbox=dict(boxstyle="round,pad=0.35", fc="#FCE4EC", ec="#F48FB1", alpha=0.92, lw=0.9), zorder=8)

    # Axis Limits and Formatting
    ax_b.set_xlim(-0.8, 36.8)
    ax_b.set_ylim(43.5, 69.0)
    ax_b.set_xlabel(txt["x_label"], fontsize=11.5, fontweight="bold", labelpad=10, color="#111111")
    ax_b.set_ylabel(txt["y_label"], fontsize=11.5, fontweight="bold", labelpad=10, color="#111111")
    
    # Standard Tick Marks
    ax_b.set_xticks([0, 5, 10, 15, 20, 25, 30])
    ax_b.set_yticks(np.arange(45, 70, 5))
    ax_b.tick_params(axis="both", which="major", labelsize=9.5, direction="out", length=5, width=1.1)

    for spine in ["top", "right"]:
        ax_b.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax_b.spines[spine].set_linewidth(1.2)
        ax_b.spines[spine].set_color("#37474F")

    # Secondary Right Axis: Underlying Cortex Gyri
    ax_cortex = ax_b.twinx()
    ax_cortex.set_ylim(43.5, 69.0)
    ax_cortex.set_yticks([48.5, 54.5, 57.0, 59.5, 65.0])
    ax_cortex.set_yticklabels([txt["gyrus_sfg"], txt["gyrus_precg"], txt["gyrus_cs"], txt["gyrus_postcg"], txt["gyrus_spl"]],
                              fontsize=8.5, fontweight="bold")
    ax_cortex.tick_params(axis="y", length=0, pad=8, colors="#37474F")
    ax_cortex.set_ylabel(txt["gyrus_title"], fontsize=10.0, fontweight="bold", labelpad=12, color="#37474F")
    for s in ["top", "left", "bottom"]:
        ax_cortex.spines[s].set_visible(False)
    ax_cortex.spines["right"].set_color("#B0BEC5")
    ax_cortex.spines["right"].set_linewidth(1.0)

    # Subtle cortex region shading on right border
    ax_b.axvspan(36.2, 36.8, ymin=(43.5-43.5)/(69-43.5), ymax=(53.0-43.5)/(69-43.5), color="#BBDEFB", alpha=0.4, lw=0)
    ax_b.axvspan(36.2, 36.8, ymin=(53.0-43.5)/(69-43.5), ymax=(57.0-43.5)/(69-43.5), color="#F8BBD0", alpha=0.5, lw=0)
    ax_b.axvspan(36.2, 36.8, ymin=(57.0-43.5)/(69-43.5), ymax=(61.5-43.5)/(69-43.5), color="#C8E6C9", alpha=0.5, lw=0)
    ax_b.axvspan(36.2, 36.8, ymin=(61.5-43.5)/(69-43.5), ymax=(69.0-43.5)/(69-43.5), color="#FFE0B2", alpha=0.4, lw=0)

    # Footer note
    fig.text(0.955, 0.02, txt["source_foot"], fontsize=7.5, color="#78909C", ha="right", va="bottom")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / ("Fig1_GV20_geometry_en.png" if lang == "en" else "GV20_가설검증_기하.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"[{lang}] Successfully saved: {out_path} ({os.path.getsize(out_path):,} bytes)")

if __name__ == "__main__":
    print("Generating refined English Fig 1...")
    build_figure("en")

    print("Generating refined Korean Fig 1...")
    build_figure("ko")
    print("All figures refined and updated successfully!")

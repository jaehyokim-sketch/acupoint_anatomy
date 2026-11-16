# -*- coding: utf-8 -*-
"""generate_Fig1_GV20_3D_mesh.py — 3D Mesh Image and Interactive 3D Model for GV20 Thesis.

Generates (in OUT_DIR):
  1. Fig1_GV20_3D_mesh_render.png (High-res 3D multi-view image)
  2. Fig1_GV20_3D_interactive_model.html (Interactive Three.js 3D model)

Usage: python generate_Fig1_GV20_3D_mesh.py [output folder]
  output folder defaults to the repository GV20 report folder (same as GV20_posture_localization.py).
  BodyParts3D meshes are read from fma_common.data_dir()/bodyparts3d
  (FMA_DATA_DIR → %LOCALAPPDATA%\\acupoint_fma → ~/.cache/acupoint_fma).
"""
import os
import sys
import json
import base64
import html
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
import trimesh
from scipy.ndimage import gaussian_filter1d

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fma_common import data_dir  # noqa: E402

# Paths
REPO = Path(__file__).resolve().parents[3]
OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "01_경혈별_해부생리_분석보고서" / "GV_독맥" / "GV20_백회"
BP3D = data_dir() / "bodyparts3d"
OBJ = BP3D / "partof_BP3D_4.0_obj_99"

# Model Landmarks (mm) in BodyParts3D (+X left, -Y front, +Z up)
ORBITALE = np.array([-145.2, 1500.8])  # in YZ mid-sagittal
PORION = np.array([-83.0, 1505.8])     # in YZ mid-sagittal

PORION_R = np.array([-67.5, -83.0, 1505.8])
PORION_L = np.array([67.5, -83.0, 1505.8])
ORBITALE_R = np.array([-42.0, -145.2, 1500.8])
ORBITALE_L = np.array([42.0, -145.2, 1500.8])

NASION_SOFT = np.array([0.0, -181.5, 1536.4])
INION_Z = 1510.0
EAR_APEX_OFS = (15.0, 30.0)  # (+Y rear, +Z up)
EAR_AXIS = 19.4

phiF = np.degrees(np.arctan2(PORION[1] - ORBITALE[1], PORION[0] - ORBITALE[0]))

sa_r = np.array([PORION_R[0], PORION_R[1] + EAR_APEX_OFS[0], PORION_R[2] + EAR_APEX_OFS[1]])
sa_l = np.array([PORION_L[0], PORION_L[1] + EAR_APEX_OFS[0], PORION_L[2] + EAR_APEX_OFS[1]])
sa_mid = (sa_r + sa_l) / 2.0

ear_rad = np.radians(EAR_AXIS)
ear_dir = np.array([0.0, np.sin(ear_rad), np.cos(ear_rad)])
lobe_r = sa_r - 60.0 * ear_dir
lobe_l = sa_l - 60.0 * ear_dir

def load_mesh(fid):
    p = OBJ / f"{fid}.obj"
    if p.exists():
        return trimesh.load(p, force="mesh", process=False)
    return None

def resample(P, step=0.5):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    S = np.arange(0, s[-1], step)
    Q = np.column_stack([np.interp(S, s, P[:, 0]), np.interp(S, s, P[:, 1])])
    return Q, np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]

def get_midsagittal_skin():
    skin = load_mesh("FJ2810")
    sec = skin.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0])
    pts = np.vstack([e[:, 1:] for e in sec.discrete])
    pts = pts[pts[:, 1] > 1440]
    c = np.array([-90.0, 1535.0])
    ang = np.degrees(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    prof = []
    for a0 in np.arange(240, -60, -0.5):
        a = ((ang - a0 + 180) % 360) - 180
        k = np.abs(a) < 0.25
        if k.any():
            prof.append(pts[k][np.argmax(np.hypot(*(pts[k] - c).T))])
    prof = np.array(prof)
    Q, _ = resample(prof)
    Qs = np.column_stack([gaussian_filter1d(Q[:, i], 4, mode="nearest") for i in (0, 1)])
    return resample(Qs)

# Compute 2D Skin curve and 3D intersection points
P_2d, S_2d = get_midsagittal_skin()
iN = int(np.argmin(np.hypot(P_2d[:, 0] - NASION_SOFT[1], P_2d[:, 1] - NASION_SOFT[2])))
ii = np.where(P_2d[:, 0] > -40)[0]
iI = ii[np.argmin(abs(P_2d[ii, 1] - INION_Z))]
sN, sI = S_2d[iN], S_2d[iI]
s_span = sI - sN

def hit_midline(p0_yz, beta_deg):
    rad = np.radians(phiF - beta_deg)
    d = np.array([-np.sin(rad), np.cos(rad)])
    best = None
    for k in range(len(P_2d) - 1):
        a, b = P_2d[k], P_2d[k + 1]
        M = np.array([d, a - b]).T
        if abs(np.linalg.det(M)) < 1e-9 or a[1] < 1560:
            continue
        t, u = np.linalg.solve(M, a - p0_yz)
        if t > 0 and 0 <= u <= 1 and (best is None or t < best[0]):
            best = (t, a + u * (b - a))
    return best[1] if best else None

hits_3d = {}
for beta in [0.0, 19.4, 22.0, 23.4, 27.8, 30.0, 35.0]:
    pt_yz = hit_midline(sa_mid[1:], beta)
    if pt_yz is not None:
        hits_3d[beta] = np.array([0.0, pt_yz[0], pt_yz[1]])

# 5-cun anchors in 3D
s_hair = sN + 0.601 * s_span
s_glab = sN + 0.639 * s_span
pt_hair_yz = P_2d[np.argmin(abs(S_2d - s_hair))]
pt_glab_yz = P_2d[np.argmin(abs(S_2d - s_glab))]
pt_hair_3d = np.array([0.0, pt_hair_yz[0], pt_hair_yz[1]])
pt_glab_3d = np.array([0.0, pt_glab_yz[0], pt_glab_yz[1]])

s_59 = sN + 0.59 * s_span
s_66 = sN + 0.66 * s_span
idx_band = np.where((S_2d >= s_59) & (S_2d <= s_66))[0]
band_pts_3d = np.array([[0.0, P_2d[k, 0], P_2d[k, 1]] for k in idx_band])

# Midline arc points in 3D
idx_midline = np.where((S_2d >= sN) & (S_2d <= sI))[0]
midline_arc_3d = np.array([[0.0, P_2d[k, 0], P_2d[k, 1]] for k in idx_midline])

# Colors
C_B0 = "#1565C0"       # Vibrant Blue
C_B19 = "#00897B"      # Dark Teal
C_B22 = "#C2185B"      # Central sulcus crimson
C_B23 = "#AD1457"      # Semicircular canal pink
C_B30 = "#EF6C00"      # Clinical amber
C_HAIR = "#212121"     # Black
C_GLAB = "#424242"     # Gray open square

# -------------------------------------------------------------
# 1. GENERATE HIGH-RESOLUTION 3D MESH RENDER IMAGE (PNG)
# -------------------------------------------------------------
def generate_3d_render_image():
    print("Generating 3D mesh multi-view rendering...")
    plt.rcParams["font.sans-serif"] = ["Arial", "Helvetica", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    fig = plt.figure(figsize=(19.5, 7.8), dpi=300, facecolor="white")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.0], wspace=0.10, left=0.02, right=0.98, top=0.92, bottom=0.06)

    # Load 3D meshes and simplify for clean vector/raster rendering
    skin = load_mesh("FJ2810")
    calv = load_mesh("FJ3309")
    pre_r = load_mesh("FJ1801")
    post_r = load_mesh("FJ1798")
    sfg_r = load_mesh("FJ1834")
    spl_r = load_mesh("FJ1836")

    # Crop head skin at z > 1445
    head_skin = skin.slice_plane(plane_origin=[0, 0, 1445], plane_normal=[0, 0, 1])

    # Subsample meshes for efficient and smooth 3D plotting
    def subsample_mesh(m, max_faces=4000):
        if len(m.faces) > max_faces:
            step = int(np.ceil(len(m.faces) / max_faces))
            return m.vertices, m.faces[::step]
        return m.vertices, m.faces

    v_skin_plot, f_skin_plot = subsample_mesh(head_skin, 5000)
    v_calv_plot, f_calv_plot = subsample_mesh(calv, 3000)
    v_pre_plot, f_pre_plot = subsample_mesh(pre_r, 1800)
    v_post_plot, f_post_plot = subsample_mesh(post_r, 1800)
    v_sfg_plot, f_sfg_plot = subsample_mesh(sfg_r, 1500)
    v_spl_plot, f_spl_plot = subsample_mesh(spl_r, 1500)

    # 3D Plot helper function
    def setup_3d_ax(ax, elev, azim, title_code, title_text, view_type="perspective"):
        ax.set_title(f"{title_code}   {title_text}", loc="left", fontsize=12.0, fontweight="bold", pad=12, color="#111111")
        ax.view_init(elev=elev, azim=azim)
        ax.set_box_aspect((1.0, 1.25, 1.35))
        ax.set_axis_off()

        # 1. Skull calvaria (Smooth bone white)
        poly_c = Poly3DCollection(v_calv_plot[f_calv_plot], facecolors="#EAEAEA", edgecolors="none", alpha=0.35, zorder=2)
        ax.add_collection3d(poly_c)

        # 2. Cortex Gyri (Smooth brain regions)
        # SFG (Light Blue)
        poly_sfg = Poly3DCollection(v_sfg_plot[f_sfg_plot], facecolors="#BBDEFB", edgecolors="none", alpha=0.70, zorder=3)
        ax.add_collection3d(poly_sfg)
        # Precentral gyrus (Motor, Rose Pink)
        poly_pre = Poly3DCollection(v_pre_plot[f_pre_plot], facecolors="#F48FB1", edgecolors="none", alpha=0.85, zorder=4)
        ax.add_collection3d(poly_pre)
        # Postcentral gyrus (Sensory, Soft Green)
        poly_post = Poly3DCollection(v_post_plot[f_post_plot], facecolors="#81C784", edgecolors="none", alpha=0.85, zorder=4)
        ax.add_collection3d(poly_post)
        # SPL (Soft Amber)
        poly_spl = Poly3DCollection(v_spl_plot[f_spl_plot], facecolors="#FFE082", edgecolors="none", alpha=0.70, zorder=3)
        ax.add_collection3d(poly_spl)

        # 3. Translucent Smooth Skin Surface
        if view_type == "cut":
            # Right hemisphere + subtle translucent left
            poly_s = Poly3DCollection(v_skin_plot[f_skin_plot], facecolors="#F5EBE1", edgecolors="#D7CCC8", linewidths=0.08, alpha=0.18, zorder=5)
            ax.add_collection3d(poly_s)
        else:
            poly_s = Poly3DCollection(v_skin_plot[f_skin_plot], facecolors="#F5EBE1", edgecolors="none", alpha=0.22, zorder=5)
            ax.add_collection3d(poly_s)

        # 4. Midline Arc (N-I Arc Tube)
        ax.plot(midline_arc_3d[:, 0], midline_arc_3d[:, 1], midline_arc_3d[:, 2], color="#5D4037", lw=2.2, zorder=8)

        # 5. 5-cun Anchor Band (59%–66% ribbon on midline scalp)
        ax.plot(band_pts_3d[:, 0], band_pts_3d[:, 1], band_pts_3d[:, 2], color="#9E9E9E", lw=8.0, alpha=0.6, solid_capstyle="butt", zorder=9)

        # 6. Landmarks & Ear Axis (3D Cylinders / Markers)
        # Biauricular apex axis connecting Left & Right apices
        ax.plot([sa_r[0], sa_l[0]], [sa_r[1], sa_l[1]], [sa_r[2], sa_l[2]], color="#880E4F", lw=2.5, ls="--", zorder=7)
        # Right ear lobe -> apex
        ax.plot([lobe_r[0], sa_r[0]], [lobe_r[1], sa_r[1]], [lobe_r[2], sa_r[2]], color="#880E4F", lw=3.5, solid_capstyle="round", zorder=8)
        # Left ear lobe -> apex
        ax.plot([lobe_l[0], sa_l[0]], [lobe_l[1], sa_l[1]], [lobe_l[2], sa_l[2]], color="#880E4F", lw=3.5, solid_capstyle="round", zorder=8)

        ax.plot(*sa_r, marker="o", color="#880E4F", ms=6, zorder=10)
        ax.plot(*sa_l, marker="o", color="#880E4F", ms=6, zorder=10)
        ax.plot(*sa_mid, marker="o", color="#4A148C", ms=6, zorder=10)

        # Porion & Orbitale
        ax.plot(*PORION_R, marker="o", color="#37474F", ms=5, zorder=8)
        ax.plot(*PORION_L, marker="o", color="#37474F", ms=5, zorder=8)
        ax.plot(*ORBITALE_R, marker="o", color="#37474F", ms=5, zorder=8)
        ax.plot(*ORBITALE_L, marker="o", color="#37474F", ms=5, zorder=8)

        # 7. Projected 3D Rays from Midpoint to Scalp Midline
        ray_defs = [
            (0.0, C_B0, r"$\beta=0^\circ$ (45.7%)"),
            (19.4, C_B19, r"$\beta=19.4^\circ$ (55.6%)"),
            (23.4, C_B23, r"$\beta=23.4^\circ$ (57.7%)"),
            (30.0, C_B30, r"$\beta=30^\circ$ (61.4%)")
        ]
        for b_deg, col, lab in ray_defs:
            if b_deg in hits_3d:
                hp = hits_3d[b_deg]
                # Ray from sa_mid to midline hit
                ax.plot([sa_mid[0], hp[0]], [sa_mid[1], hp[1]], [sa_mid[2], hp[2]], color=col, lw=2.4, zorder=11)
                ax.plot(*hp, marker="o", color=col, ms=7.5, mec="white", mew=1.0, zorder=12)

        # 8. 5-cun Points
        ax.plot(*pt_hair_3d, marker="s", color=C_HAIR, ms=8.0, mec="white", mew=1.0, zorder=13)
        ax.plot(*pt_glab_3d, marker="s", mfc="white", mec=C_GLAB, ms=8.0, mew=2.0, zorder=13)

        # Limits to center the head properly
        ax.set_xlim(-110, 110)
        ax.set_ylim(-210, 80)
        ax.set_zlim(1440, 1680)

    # ---------------------------------------------------------
    # Panel A: 3D Perspective Sagittal-Cut View
    # ---------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0], projection="3d")
    setup_3d_ax(ax1, elev=22, azim=-48, title_code="a",
                title_text="3D Sagittal-Cut Perspective View\n(Translucent Skin, Calvaria, Cortex Gyri & Projected Rays)",
                view_type="cut")

    # Add text annotation on 3D view
    ax1.text2D(0.04, 0.88, "• Right hemisphere: cortex & gyri exposed\n• Left hemisphere: translucent scalp contour\n• Ray origins: binaural apex axis (midline)",
               transform=ax1.transAxes, fontsize=8.2, color="#37474F",
               bbox=dict(boxstyle="round,pad=0.4", fc="#FFFFFF", ec="#CFD8DC", alpha=0.9))

    # ---------------------------------------------------------
    # Panel B: 3D Lateral Orthographic View (Frankfurt Levelled)
    # ---------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1], projection="3d")
    setup_3d_ax(ax2, elev=0, azim=0, title_code="b",
                title_text="3D Right Lateral View\n(Frankfurt-Levelled Profile & Posterior Ray Shift)",
                view_type="lateral")

    # Annotate key anatomical components
    ax2.text2D(0.04, 0.88, "• Precentral gyrus (motor, pink)\n• Postcentral gyrus (sensory, green)\n• Central sulcus: between pink & green\n• 5-cun GV20: ■ hairline (60.1%) / □ glabella (63.9%)",
               transform=ax2.transAxes, fontsize=8.0, color="#37474F",
               bbox=dict(boxstyle="round,pad=0.4", fc="#FFFFFF", ec="#CFD8DC", alpha=0.9))

    # ---------------------------------------------------------
    # Panel C: 3D Superior Cranial View (Top-Down Dorsal)
    # ---------------------------------------------------------
    ax3 = fig.add_subplot(gs[0, 2], projection="3d")
    setup_3d_ax(ax3, elev=88, azim=0, title_code="c",
                title_text="3D Superior Cranial View\n(Biauricular Axis × Midline Meridian Crossing)",
                view_type="top")

    ax3.text2D(0.04, 0.88, "• Transverse dashed line: biauricular apex axis\n• Brown midline: Governor Vessel (Du Meridian)\n• Grey patch: 5-cun anchor range (59–66% N–I)\n• Rays advance posteriorly with increasing β",
               transform=ax3.transAxes, fontsize=8.0, color="#37474F",
               bbox=dict(boxstyle="round,pad=0.4", fc="#FFFFFF", ec="#CFD8DC", alpha=0.9))

    # Shared Legend at bottom
    leg_handles = [
        Line2D([0], [0], marker="o", color=C_B0, label=r"$\beta=0^\circ$ Literal (45.7%)", ms=6.5, lw=2.0),
        Line2D([0], [0], marker="o", color=C_B19, label=r"$\beta=19.4^\circ$ Ear axis (55.6%)", ms=6.5, lw=2.0),
        Line2D([0], [0], marker="o", color=C_B23, label=r"$\beta=23.4^\circ$ Canal (57.7%)", ms=6.5, lw=2.0),
        Line2D([0], [0], marker="o", color=C_B30, label=r"$\beta=30^\circ$ Convention (61.4%)", ms=6.5, lw=2.0),
        Line2D([0], [0], marker="s", color="w", markerfacecolor=C_HAIR, label="5-cun Hairline (60.1%)", ms=7, markeredgecolor="w"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="w", markeredgecolor=C_GLAB, markeredgewidth=1.8, label="5-cun Glabella (63.9%)", ms=7),
        mpatches.Patch(color="#9E9E9E", alpha=0.6, label="5-cun range (59–66%)"),
        mpatches.Patch(color="#F8BBD0", label="Precentral gyrus"),
        mpatches.Patch(color="#C8E6C9", label="Postcentral gyrus")
    ]
    fig.legend(handles=leg_handles, loc="lower center", bbox_to_anchor=(0.5, 0.01),
               ncol=5, fontsize=8.2, frameon=True, facecolor="white", edgecolor="#CFD8DC", framealpha=0.95)

    # Footer note
    fig.text(0.98, 0.01, "BodyParts3D 4.0, © The Database Center for Life Science, CC BY 4.0 | FMA:7163, 52735, 72661, 72665",
             fontsize=7.2, color="#90A4AE", ha="right", va="bottom")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_png = OUT_DIR / "Fig1_GV20_3D_mesh_render.png"
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Successfully saved 3D multi-view render: {out_png} ({os.path.getsize(out_png):,} bytes)")

# -------------------------------------------------------------
# 2. GENERATE INTERACTIVE THREE.JS 3D MODEL HTML
# -------------------------------------------------------------
def generate_interactive_3d_html():
    print("Generating interactive Three.js 3D model HTML...")
    skin = load_mesh("FJ2810")
    calv = load_mesh("FJ3309")
    pre = load_mesh("FJ1801")
    post = load_mesh("FJ1798")
    sfg = load_mesh("FJ1834")
    spl = load_mesh("FJ1836")

    head_skin = skin.slice_plane(plane_origin=[0, 0, 1445], plane_normal=[0, 0, 1])

    def downsample(m, faces=5000):
        return m

    m_skin = downsample(head_skin, 3500)
    m_calv = downsample(calv, 2200)
    m_pre = downsample(pre, 1200)
    m_post = downsample(post, 1200)
    m_sfg = downsample(sfg, 1000)
    m_spl = downsample(spl, 1000)

    # Coordinate transform: BodyParts3D (x, y, z) -> Three.js view (x, z, -y)
    def to_view(v):
        v = np.asarray(v, dtype=float)
        return np.stack([v[..., 0], v[..., 2], -v[..., 1]], axis=-1)

    all_v = np.concatenate([to_view(m.vertices) for m in [m_skin, m_calv, m_pre, m_post]])
    center = (all_v.min(0) + all_v.max(0)) / 2.0
    scale = float((all_v.max(0) - all_v.min(0)).max())

    def pack_mesh(m, name, color, opacity, cat):
        v = to_view(m.vertices) - center
        f = m.faces
        return {
            "name": name,
            "cat": cat,
            "color": color,
            "opacity": opacity,
            "pos": base64.b64encode(np.ascontiguousarray(v, dtype="<f4").tobytes()).decode("ascii"),
            "idx": base64.b64encode(np.ascontiguousarray(f, dtype="<u4").tobytes()).decode("ascii")
        }

    meshes = [
        pack_mesh(m_skin, "Scalp Skin (FMA:7163)", "#F7E8D0", 0.35, "skin"),
        pack_mesh(m_calv, "Skull Calvaria (FMA:52735)", "#E0E0E0", 0.55, "bone"),
        pack_mesh(m_pre, "Precentral Gyrus (Motor, FMA:72661)", "#E91E63", 0.85, "cortex"),
        pack_mesh(m_post, "Postcentral Gyrus (Sensory, FMA:72665)", "#4CAF50", 0.85, "cortex"),
        pack_mesh(m_sfg, "Superior Frontal Gyrus (FMA:72653)", "#2196F3", 0.70, "cortex"),
        pack_mesh(m_spl, "Superior Parietal Lobule (FMA:72671)", "#FF9800", 0.70, "cortex")
    ]

    # Convert paths & points to view coordinates
    def pt_view(p):
        return (to_view(p) - center).round(2).tolist()

    # Rays and lines
    lines = [
        {"name": "Biauricular Axis", "color": "#880E4F", "pts": [pt_view(sa_r), pt_view(sa_l)], "dash": True},
        {"name": "Right Ear Axis (Lobe-Apex)", "color": "#880E4F", "pts": [pt_view(lobe_r), pt_view(sa_r)], "dash": False},
        {"name": "Left Ear Axis (Lobe-Apex)", "color": "#880E4F", "pts": [pt_view(lobe_l), pt_view(sa_l)], "dash": False},
        {"name": "Midline Arc (Governor Vessel)", "color": "#5D4037", "pts": [pt_view(p) for p in midline_arc_3d[::2]], "dash": False},
        {"name": "Ray beta=0 deg (Literal, 45.7%)", "color": C_B0, "pts": [pt_view(sa_mid), pt_view(hits_3d[0.0])], "dash": False},
        {"name": "Ray beta=19.4 deg (Ear Axis, 55.6%)", "color": C_B19, "pts": [pt_view(sa_mid), pt_view(hits_3d[19.4])], "dash": False},
        {"name": "Ray beta=23.4 deg (Canal, 57.7%)", "color": C_B23, "pts": [pt_view(sa_mid), pt_view(hits_3d[23.4])], "dash": False},
        {"name": "Ray beta=30 deg (Convention, 61.4%)", "color": C_B30, "pts": [pt_view(sa_mid), pt_view(hits_3d[30.0])], "dash": False}
    ]

    points = [
        {"name": "Auricular Apex (Right)", "color": "#880E4F", "pos": pt_view(sa_r), "radius": 3.0},
        {"name": "Auricular Apex (Left)", "color": "#880E4F", "pos": pt_view(sa_l), "radius": 3.0},
        {"name": "Apex Midpoint", "color": "#4A148C", "pos": pt_view(sa_mid), "radius": 3.5},
        {"name": "Intersection beta=0 deg (45.7%)", "color": C_B0, "pos": pt_view(hits_3d[0.0]), "radius": 4.0},
        {"name": "Intersection beta=19.4 deg (55.6%)", "color": C_B19, "pos": pt_view(hits_3d[19.4]), "radius": 4.0},
        {"name": "Intersection beta=22.0 deg Central Sulcus (57.0%)", "color": C_B22, "pos": pt_view(hits_3d[22.0]), "radius": 4.5},
        {"name": "Intersection beta=23.4 deg Canal (57.7%)", "color": C_B23, "pos": pt_view(hits_3d[23.4]), "radius": 4.0},
        {"name": "Intersection beta=30 deg Clinical (61.4%)", "color": C_B30, "pos": pt_view(hits_3d[30.0]), "radius": 4.0},
        {"name": "5-cun GV20 (Hairline Anchor, 60.1%)", "color": C_HAIR, "pos": pt_view(pt_hair_3d), "radius": 4.8},
        {"name": "5-cun GV20 (Glabella Anchor, 63.9%)", "color": C_GLAB, "pos": pt_view(pt_glab_3d), "radius": 4.8}
    ]

    payload = json.dumps({"meshes": meshes, "lines": lines, "points": points, "scale": scale}, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GV20 (Baihui) 3D Anatomical Mesh Model — Auricular Apex Projection Geometry</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
  body {{ overflow: hidden; background: #121418; color: #eceff1; }}
  #canvas-container {{ width: 100vw; height: 100vh; position: absolute; top: 0; left: 0; }}
  #ui-panel {{
    position: absolute; top: 16px; left: 16px; width: 340px; max-height: calc(100vh - 32px);
    background: rgba(22, 27, 34, 0.92); backdrop-filter: blur(12px); border: 1px solid #30363d;
    border-radius: 10px; padding: 18px; overflow-y: auto; z-index: 10; box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  }}
  h1 {{ font-size: 15px; font-weight: 700; color: #58a6ff; margin-bottom: 6px; line-height: 1.3; }}
  .sub {{ font-size: 11.5px; color: #8b949e; margin-bottom: 14px; border-bottom: 1px solid #30363d; padding-bottom: 8px; }}
  .section-title {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: #79c0ff; margin: 12px 0 6px 0; letter-spacing: 0.5px; }}
  .item-row {{ display: flex; align-items: center; justify-content: space-between; font-size: 11.5px; margin: 4px 0; padding: 3px 0; }}
  .item-label {{ display: flex; align-items: center; gap: 8px; color: #c9d1d9; }}
  .color-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
  input[type="checkbox"] {{ accent-color: #1f6feb; cursor: pointer; }}
  input[type="range"] {{ width: 70px; accent-color: #1f6feb; cursor: pointer; }}
  .legend-box {{ font-size: 11px; background: rgba(13, 17, 23, 0.7); border: 1px solid #30363d; border-radius: 6px; padding: 10px; margin-top: 14px; line-height: 1.5; color: #8b949e; }}
  .btn-group {{ display: flex; gap: 6px; margin-top: 12px; }}
  button {{ flex: 1; padding: 6px 10px; font-size: 11px; font-weight: 600; background: #21262d; border: 1px solid #363b42; color: #c9d1d9; border-radius: 6px; cursor: pointer; }}
  button:hover {{ background: #30363d; color: #ffffff; }}
  #hud {{ position: absolute; bottom: 16px; right: 16px; font-size: 10px; color: #6e7681; background: rgba(13,17,23,0.8); padding: 6px 12px; border-radius: 6px; }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<div id="canvas-container"></div>
<div id="ui-panel">
  <h1>Baihui (GV20) 3D Geometry Model</h1>
  <div class="sub">BodyParts3D 4.0 Standard Head · Auricular Apex Line & Cortex Projection</div>

  <div class="section-title">Anatomical Layers</div>
  <div id="mesh-controls"></div>

  <div class="section-title">Geometric Rays & Trajectories</div>
  <div id="line-controls"></div>

  <div class="section-title">Acupoints & Landmarks</div>
  <div id="point-controls"></div>

  <div class="btn-group">
    <button onclick="setCamera('sagittal')">Sagittal View</button>
    <button onclick="setCamera('top')">Top View</button>
    <button onclick="setCamera('perspective')">Perspective</button>
  </div>

  <div class="legend-box">
    <strong>Key Geometry Findings:</strong><br>
    • <b>β = 0° (Vertical)</b>: N-I 45.7% (52.8 mm ant. to 5-cun)<br>
    • <b>β = 19.4° (Ear Axis)</b>: N-I 55.6% (Precentral gyrus)<br>
    • <b>β = 22.0°</b>: N-I 57.0% (Upper Central Sulcus)<br>
    • <b>β = 23.4° (Canal CT)</b>: N-I 57.7% (Postcentral gyrus)<br>
    • <b>β = 27.8°</b>: N-I 60.1% (5-cun Hairline Anchor ■)<br>
    • <b>β = 30.0°</b>: N-I 61.4% (Clinical Convention)<br>
    • <b>β = 35.0°</b>: N-I 63.9% (5-cun Glabella Anchor □)
  </div>
</div>
<div id="hud">BodyParts3D, © DBCLS, CC BY 4.0 · Left Click: Rotate | Right Click: Pan | Scroll: Zoom</div>

<script>
const DATA = {payload};

const container = document.getElementById('canvas-container');
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x121418);

const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, 1, 3000);
camera.position.set(-280, 220, 320);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
container.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.target.set(0, 0, 0);

// Lights
const ambLight = new THREE.AmbientLight(0xffffff, 0.7);
scene.add(ambLight);
const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
dirLight1.position.set(300, 400, 300);
scene.add(dirLight1);
const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
dirLight2.position.set(-300, -200, -300);
scene.add(dirLight2);

// Decode base64 float32 / uint32 arrays
function decodeF32(b64) {{
  const bin = atob(b64);
  const buf = new ArrayBuffer(bin.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
  return new Float32Array(buf);
}}
function decodeU32(b64) {{
  const bin = atob(b64);
  const buf = new ArrayBuffer(bin.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < bin.length; i++) view[i] = bin.charCodeAt(i);
  return new Uint32Array(buf);
}}

const meshObjs = [];
const meshControls = document.getElementById('mesh-controls');

DATA.meshes.forEach((m, idx) => {{
  const geom = new THREE.BufferGeometry();
  const vArr = decodeF32(m.pos);
  const iArr = decodeU32(m.idx);
  geom.setAttribute('position', new THREE.BufferAttribute(vArr, 3));
  geom.setIndex(new THREE.BufferAttribute(iArr, 1));
  geom.computeVertexNormals();

  const isTrans = m.opacity < 0.99;
  const mat = new THREE.MeshStandardMaterial({{
    color: parseInt(m.color.replace('#', '0x')),
    roughness: 0.4,
    metalness: 0.1,
    transparent: isTrans,
    opacity: m.opacity,
    side: THREE.DoubleSide,
    depthWrite: !isTrans
  }});
  const mesh = new THREE.Mesh(geom, mat);
  scene.add(mesh);
  meshObjs.push({{ mesh, mat, data: m }});

  // UI row
  const row = document.createElement('div');
  row.className = 'item-row';
  row.innerHTML = `
    <div class="item-label">
      <input type="checkbox" id="mchk_${{idx}}" checked>
      <span class="color-dot" style="background:${{m.color}}"></span>
      <span>${{m.name}}</span>
    </div>
    <input type="range" id="mop_${{idx}}" min="0" max="100" value="${{Math.round(m.opacity*100)}}">
  `;
  meshControls.appendChild(row);

  document.getElementById(`mchk_${{idx}}`).addEventListener('change', (e) => {{
    mesh.visible = e.target.checked;
  }});
  document.getElementById(`mop_${{idx}}`).addEventListener('input', (e) => {{
    const op = e.target.value / 100;
    mat.opacity = op;
    mat.transparent = op < 0.99;
    mat.depthWrite = op >= 0.99;
  }});
}});

// Lines
const lineObjs = [];
const lineControls = document.getElementById('line-controls');
DATA.lines.forEach((l, idx) => {{
  const pts = l.pts.map(p => new THREE.Vector3(p[0], p[1], p[2]));
  const geom = new THREE.BufferGeometry().setFromPoints(pts);
  const mat = new THREE.LineBasicMaterial({{
    color: parseInt(l.color.replace('#', '0x')),
    linewidth: 2.5
  }});
  const line = new THREE.Line(geom, mat);
  scene.add(line);
  lineObjs.push(line);

  const row = document.createElement('div');
  row.className = 'item-row';
  row.innerHTML = `
    <div class="item-label">
      <input type="checkbox" id="lchk_${{idx}}" checked>
      <span class="color-dot" style="background:${{l.color}}"></span>
      <span>${{l.name}}</span>
    </div>
  `;
  lineControls.appendChild(row);
  document.getElementById(`lchk_${{idx}}`).addEventListener('change', (e) => {{
    line.visible = e.target.checked;
  }});
}});

// Points
const pointObjs = [];
const pointControls = document.getElementById('point-controls');
DATA.points.forEach((p, idx) => {{
  const geom = new THREE.SphereGeometry(p.radius, 16, 16);
  const mat = new THREE.MeshStandardMaterial({{
    color: parseInt(p.color.replace('#', '0x')),
    roughness: 0.2,
    metalness: 0.3
  }});
  const mesh = new THREE.Mesh(geom, mat);
  mesh.position.set(p.pos[0], p.pos[1], p.pos[2]);
  scene.add(mesh);
  pointObjs.push(mesh);

  const row = document.createElement('div');
  row.className = 'item-row';
  row.innerHTML = `
    <div class="item-label">
      <input type="checkbox" id="pchk_${{idx}}" checked>
      <span class="color-dot" style="background:${{p.color}}"></span>
      <span>${{p.name}}</span>
    </div>
  `;
  pointControls.appendChild(row);
  document.getElementById(`pchk_${{idx}}`).addEventListener('change', (e) => {{
    mesh.visible = e.target.checked;
  }});
}});

function setCamera(type) {{
  if (type === 'sagittal') {{
    camera.position.set(-420, 0, 0);
    controls.target.set(0, 0, 0);
  }} else if (type === 'top') {{
    camera.position.set(0, 420, 0);
    controls.target.set(0, 0, 0);
  }} else {{
    camera.position.set(-280, 220, 320);
    controls.target.set(0, 0, 0);
  }}
}}

window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});

function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();
</script>
</body>
</html>"""

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_html = OUT_DIR / "Fig1_GV20_3D_interactive_model.html"
    out_html.write_text(html_content, encoding="utf-8")
    print(f"Successfully saved interactive 3D model: {out_html} ({os.path.getsize(out_html):,} bytes)")

if __name__ == "__main__":
    generate_3d_render_image()
    generate_interactive_3d_html()
    print("All 3D mesh outputs generated successfully!")

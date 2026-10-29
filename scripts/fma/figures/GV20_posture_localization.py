# -*- coding: utf-8 -*-
"""GV20 백회 — 두부 굴곡(가쪽반고리관 수평) 최고점 원칙과 귓불–귀끝 연장선 정위의 실측 기하 검증 그림.

BodyParts3D 4.0 표준 모델(단일 성인 남성, CC BY 4.0)의 피부(FMA:7163) 정중 시상 단면 윤곽을 잘라
Frankfurt 수평(porion–orbitale)으로 세운 뒤, 정위 후보점을 같은 Nasion–Inion(N-I) 호 위에서 비교한다.
  A  Frankfurt 자세: 최고점(Vertex) · 直兩耳尖(귀끝 수직선) · Cz(N-I 50%) · Taylor-Haughton 54% · 귓불→귀끝 연장선 · 골도 5촌
  B  가쪽반고리관 수평 자세: Frankfurt 대비 β만큼 숙였을 때의 최고점 (β = 20°·23.4° CT 실측, 30° 임상 관례)
  C  각 N-I 위치를 최고점으로 만드는 데 필요한 굴곡 각도 곡선 + 그 위치 아래 피질 이랑(같은 모델의 뇌 메쉬)
귀끝·귓불은 피부 메쉬에 귓바퀴가 없어 porion 기준 인체계측 가정(위 30mm·뒤 15mm, 장축 19.4°)으로 놓고,
가정 범위(민감도 162조합)를 오차 막대(5–95%)로 그린다. 수치·근거는 GV20 보고서 7.2절.
사용: python GV20_posture_localization.py [출력 폴더]
"""
import itertools
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import trimesh
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fma_common import data_dir  # noqa: E402

plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
REPO = Path(__file__).resolve().parents[3]
OUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "01_경혈별_해부생리_분석보고서" / "GV_독맥" / "GV20_백회"
BP3D = data_dir() / "bodyparts3d"
OBJ = BP3D / "partof_BP3D_4.0_obj_99"

# 모델 기준점 (mm, 모델 좌표: +Z 위, -Y 앞) — 머리뼈 메쉬 광선 깊이맵으로 찾은 값
ORBITALE = np.array([-145.2, 1500.8])        # 눈확 아래 테두리 최저점 (좌우 평균)
PORION = np.array([-83.0, 1505.8])           # 바깥귀길 위끝 (오목 중심 1501.2 + 반지름 추정, 상한 1510.0은 민감도)
NASION_SOFT = np.array([-181.5, 1536.4])     # 연조직 코뿌리점 (이마–코 사이 가장 깊은 점)
INION_Z = 1510.0                             # 뒤통수→목 꺾임점 높이 (민감도 1500–1520)
EAR_APEX_OFS = (15.0, 30.0)                  # Frankfurt 좌표에서 porion 기준 귀끝 (뒤, 위) — 가정
EAR_AXIS = 19.4                              # 귓바퀴 장축 기울기(수직 대비, 남성 평균, PMID 37643081)
TRICHION = 60.0                              # 앞머리털경계까지 N 기준 호 길이 — 가정 (민감도 50–70)
BETAS = (20.0, 23.4, 30.0)                   # 가쪽반고리관 기울기: Reid 대비 19.9°(PMID 16088383), Frankfurt 환산 ≈23.4°, 임상 관례 30°


def load(fid):
    return trimesh.load(OBJ / f"{fid}.obj", force="mesh", process=False)


def resample(P, step=0.5, sig=0):
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    S = np.arange(0, s[-1], step)
    Q = np.column_stack([np.interp(S, s, P[:, 0]), np.interp(S, s, P[:, 1])])
    if sig:
        Q = np.column_stack([gaussian_filter1d(Q[:, i], sig, mode="nearest") for i in (0, 1)])
    return Q, np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]


def midsagittal_profile(mesh, centre=(-90.0, 1535.0), a_range=(240, -60), zmin=1440):
    sec = mesh.section(plane_origin=[0, 0, 0], plane_normal=[1, 0, 0])
    pts = np.vstack([e[:, 1:] for e in sec.discrete])
    pts = pts[pts[:, 1] > zmin]
    c = np.asarray(centre)
    ang = np.degrees(np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0]))
    prof = []
    for a0 in np.arange(a_range[0], a_range[1], -0.5):          # 앞(180°) → 위(90°) → 뒤(0°)
        a = ((ang - a0 + 180) % 360) - 180
        k = np.abs(a) < 0.25
        if k.any():
            prof.append(pts[k][np.argmax(np.hypot(*(pts[k] - c).T))])
    return resample(gaussian_smooth(np.array(prof)))


def gaussian_smooth(P, sig=4):
    Q, _ = resample(P)
    return np.column_stack([gaussian_filter1d(Q[:, i], sig, mode="nearest") for i in (0, 1)])


def rot(Q, th, c=(-85.0, 1540.0)):
    """굴곡 th°(얼굴이 내려가고 뒤통수가 올라감)."""
    t = np.radians(th)
    q = np.atleast_2d(Q) - np.asarray(c)
    return np.column_stack([q[:, 0] * np.cos(t) - q[:, 1] * np.sin(t),
                            q[:, 0] * np.sin(t) + q[:, 1] * np.cos(t)]) + np.asarray(c)


def vrot(v, th):
    return rot(np.asarray(v, float), th, c=(0.0, 0.0))[0]


class Head:
    def __init__(self):
        self.P, self.S = midsagittal_profile(load("FJ2810"))              # 피부 FMA:7163
        Ps, self.Ss = resample(self.P, sig=16)                            # 접선용 약 8mm 평활
        self.tang = np.degrees(np.arctan2(np.gradient(Ps[:, 1]), np.gradient(Ps[:, 0])))
        self.iN = int(np.argmin(np.hypot(*(self.P - NASION_SOFT).T)))

    def s_inion(self, z):
        ii = np.where(self.P[:, 0] > -40)[0]
        return self.S[ii[np.argmin(abs(self.P[ii, 1] - z))]]

    def s_apex(self, flex_fh, phiF):
        top = np.where(self.P[:, 1] > 1580)[0]
        return self.Ss[top[np.argmin(abs(self.tang[top] + (flex_fh - phiF)))]]

    def flex_needed(self, s, phiF):
        return -self.tang[np.argmin(abs(self.Ss - s))] + phiF

    def hit(self, p0, d):
        best = None
        for k in range(len(self.P) - 1):
            a, b = self.P[k], self.P[k + 1]
            M = np.array([d, a - b]).T
            if abs(np.linalg.det(M)) < 1e-9 or a[1] < 1560:
                continue
            t, u = np.linalg.solve(M, a - p0)
            if t > 0 and 0 <= u <= 1 and (best is None or t < best[0]):
                best = (t, self.S[k] + u * (self.S[k + 1] - self.S[k]))
        return best[1]

    def xy(self, s):
        return self.P[np.argmin(abs(self.S - s))]


def candidates(h, z_po=PORION[1], z_in=INION_Z, apex=EAR_APEX_OFS, alpha=EAR_AXIS, tr=TRICHION):
    po = np.array([PORION[0], z_po])
    phiF = np.degrees(np.arctan2(po[1] - ORBITALE[1], po[0] - ORBITALE[0]))
    sN, sI = h.S[h.iN], h.s_inion(z_in)
    sa = po + vrot(apex, phiF)
    up = vrot((np.sin(np.radians(alpha)), np.cos(np.radians(alpha))), phiF)
    c = {"FH_vertex": h.s_apex(0, phiF), "apex_vertical": h.hit(sa, vrot((0, 1), phiF)),
         "Cz": sN + 0.5 * (sI - sN), "TH54": sN + 0.54 * (sI - sN), "lobe_apex": h.hit(sa, up),
         "GV20_5cun": sN + tr + 5 / 9.5 * (sI - sN - tr)}
    for b in BETAS:
        c[f"beta{b:g}"] = h.s_apex(b, phiF)
    return c, dict(phiF=phiF, sN=sN, sI=sI, sa=sa, up=up)


def sensitivity(h):
    rows = []
    for z_po, z_in, ap, al, tr in itertools.product((1505.8, 1510.0), (1500, 1510, 1520),
                                                    ((5, 25), (15, 30), (25, 35)), (14.6, 19.4, 24.2), (50, 60, 70)):
        c, g = candidates(h, z_po, z_in, ap, al, tr)
        rows.append({k: 100 * (v - g["sN"]) / (g["sI"] - g["sN"]) for k, v in c.items()})
    return {k: np.percentile([r[k] for r in rows], [5, 50, 95]) for k in rows[0]}


def cortex_bands(h, g):
    want = {"72653": "SFG", "72654": "SFG", "72661": "PreCG", "72662": "PreCG",
            "72665": "PostCG", "72666": "PostCG", "72671": "SPL", "72672": "SPL"}
    V, lab = [], []
    for line in open(BP3D / "partof_element_parts.txt", encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if c[0][3:] in want:
            m = load(c[2]); V.append(m.vertices); lab += [want[c[0][3:]]] * len(m.vertices)
    tree, lab = cKDTree(np.vstack(V)), np.array(lab)
    out = []
    for pct in np.arange(30, 76, 0.5):
        y, z = h.xy(g["sN"] + pct / 100 * (g["sI"] - g["sN"]))
        _, j = tree.query([0.0, y, z], k=12)
        vals, cnt = np.unique(lab[j], return_counts=True)
        out.append((pct, vals[np.argmax(cnt)]))
    return out


T = {
    "ko": dict(
        sup="백회(百會, GV20) 두부 굴곡 최고점 원칙 · 귓불–귀끝 연장선 정위의 실측 기하 검증 (BodyParts3D 표준 모델 정중 시상 단면)",
        A="A. Frankfurt 수평 자세 — 최고점은 Vertex(N-I %.0f%%), 백회 아님",
        B="B. 가쪽반고리관 수평 자세 — Frankfurt 대비 β만큼 굴곡한 최고점",
        C="C. 각 정중선 위치를 최고점으로 만드는 굴곡 각도와 그 아래 피질",
        FH="Frankfurt 평면", vertex="Vertex(FH 최고점)", apexV="直兩耳尖\n(귀끝 수직선)", Cz="Cz (N-I 50%)",
        TH="T-H 54%", lobe="귓불→귀끝 연장선", gv="골도 5촌 백회", ear="귀끝·귓불(가정)",
        bl="β=%g° 최고점", xl="Nasion–Inion 호 백분율 (%)", yl="Frankfurt 대비 필요한 머리 굴곡 (°)",
        band1="CT 실측 19.9°±7.0° (Reid 기준)", band2="임상 관례 30°",
        foot="근거: BodyParts3D 4.0 (CC BY 4.0) 피부 FMA:7163·머리뼈·대뇌 이랑 메쉬 | 가쪽반고리관 기울기 PMID 16088383 | 귓바퀴 장축 19.4° PMID 37643081 | "
             "귀끝 위치·앞머리털경계는 가정, 오차 막대 = 가정 범위 162조합의 5–95% | 단일 표준 모델, 개인차 미반영(B1 보조)",
        cortex=dict(SFG="위이마이랑", PreCG="중심앞이랑", PostCG="중심뒤이랑", SPL="위마루소엽")),
    "en": dict(
        sup="Baihui (百會, GV20): Measured Geometry of the Flexed-Head Apex Principle and the Earlobe–Apex Line (BodyParts3D midsagittal section)",
        A="A. Frankfurt horizontal — apex is the Vertex (N-I %.0f%%), not GV20",
        B="B. Lateral canal horizontal — apex after flexing the head by β",
        C="C. Flexion needed to make each midline point the apex, and cortex beneath",
        FH="Frankfurt plane", vertex="Vertex (FH apex)", apexV="直兩耳尖\n(ear-apex vertical)", Cz="Cz (N-I 50%)",
        TH="T-H 54%", lobe="Earlobe→apex line", gv="5-cun GV20", ear="Ear apex & lobe (assumed)",
        bl="apex at β=%g°", xl="Nasion–Inion arc (%)", yl="Head flexion from Frankfurt (°)",
        band1="CT 19.9°±7.0° (Reid plane)", band2="Clinical convention 30°",
        foot="Sources: BodyParts3D 4.0 (CC BY 4.0) skin FMA:7163, skull and gyrus meshes | lateral canal tilt PMID 16088383 | ear axis 19.4° PMID 37643081 | "
             "ear apex position and hairline assumed; error bars = 5–95% of 162 assumption sets | single reference model (B1 auxiliary)",
        cortex=dict(SFG="Sup. frontal", PreCG="Precentral", PostCG="Postcentral", SPL="Sup. parietal")),
}
COL = dict(FH_vertex="#1565C0", apex_vertical="#00838F", Cz="#455A64", TH54="#6A1B9A", lobe_apex="#AD1457",
           GV20_5cun="#C62828", beta20="#F9A825", beta23_4="#EF6C00", beta30="#8D6E63")
CORTEX_COL = dict(SFG="#BBDEFB", PreCG="#F8BBD0", PostCG="#C8E6C9", SPL="#FFE0B2")


def render(h, sens, bands, lang, path):
    t = T[lang]
    c, g = candidates(h)
    phiF = g["phiF"]
    pct = {k: 100 * (v - g["sN"]) / (g["sI"] - g["sN"]) for k, v in c.items()}
    fig = plt.figure(figsize=(19, 7.4), dpi=200, facecolor="white")
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.15], wspace=0.12, left=0.02, right=0.985, top=0.86, bottom=0.12)
    lab = dict(FH_vertex=t["vertex"], apex_vertical=t["apexV"], Cz=t["Cz"], TH54=t["TH"], lobe_apex=t["lobe"], GV20_5cun=t["gv"])

    for k_ax, flex in ((0, 0.0), (1, BETAS[1])):
        ax = fig.add_subplot(gs[0, k_ax])
        R = lambda Q: rot(Q, flex - phiF)        # 모델 → Frankfurt(+굴곡) 좌표
        prof = R(h.P)
        ax.fill(prof[:, 0], prof[:, 1], fc="#FBF6EE", ec="#6E5A4F", lw=1.4, zorder=1)
        top = prof[:, 1].max()
        ax.axhline(top, color="#F9A825", lw=2.6, zorder=2)
        po, orb = R(np.array([PORION]))[0], R(np.array([ORBITALE]))[0]
        fh = np.vstack([orb + (orb - po) * 0.6, po + (po - orb) * 1.6])
        ax.plot(fh[:, 0], fh[:, 1], ls="--", color="#546E7A", lw=1.1, zorder=2)
        ax.plot(*po, "o", color="#37474F", ms=4, zorder=4); ax.plot(*orb, "o", color="#37474F", ms=4, zorder=4)
        ax.text(fh[1, 0], fh[1, 1] + 3, t["FH"], fontsize=7.5, color="#546E7A", ha="right")
        sa = R(np.array([g["sa"]]))[0]
        up = vrot(g["up"], flex - phiF)
        lobe = sa - 62 * up
        ax.plot([lobe[0], sa[0]], [lobe[1], sa[1]], color="#AD1457", lw=3, solid_capstyle="round", zorder=4)
        ax.plot(*sa, "o", color="#AD1457", ms=5, zorder=5); ax.plot(*lobe, "o", color="#AD1457", ms=5, zorder=5)
        ax.text(lobe[0] + 4, lobe[1] - 4, t["ear"], fontsize=7, color="#AD1457")
        for key in ("lobe_apex",):
            p = R(np.array([h.xy(c[key])]))[0]
            ax.plot([sa[0], p[0]], [sa[1], p[1]], ls="-", color="#AD1457", lw=1.1, alpha=0.8, zorder=3)
        if flex == 0:
            p = R(np.array([h.xy(c["apex_vertical"])]))[0]
            ax.plot([sa[0], p[0]], [sa[1], p[1]], ls=":", color="#00838F", lw=1.3, zorder=3)
            keys = ["FH_vertex", "apex_vertical", "Cz", "TH54", "lobe_apex", "GV20_5cun"]
        else:
            keys = ["FH_vertex", "Cz", "lobe_apex", "GV20_5cun", "beta20", "beta23.4", "beta30"]
        if flex == 0:
            off = {"FH_vertex": (-58, 26), "apex_vertical": (-34, 50), "Cz": (-6, 32), "TH54": (14, 54),
                   "lobe_apex": (44, 34), "GV20_5cun": (62, 10)}
        else:
            off = {"FH_vertex": (-62, 22), "Cz": (-38, 44), "lobe_apex": (-2, 56), "GV20_5cun": (56, 34),
                   "beta20": (-62, -30), "beta23.4": (-12, -44), "beta30": (44, -30)}
        for k in keys:
            ck = k.replace(".", "_")
            p = R(np.array([h.xy(c[k])]))[0]
            col = COL.get(ck, "#000")
            ax.plot(*p, "o", color=col, ms=7 if k == "GV20_5cun" else 5.5, mec="white", mew=0.8, zorder=6)
            name = lab.get(k, t["bl"] % float(k[4:]) if k.startswith("beta") else k)
            ax.annotate("%s\n%.0f%%" % (name, pct[k]), p, xytext=(p[0] + off[k][0], p[1] + off[k][1]), fontsize=7.2,
                        color=col, fontweight="bold", ha="center",
                        arrowprops=dict(arrowstyle="-", color=col, lw=0.8), zorder=7)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(prof[:, 0].min() - 15, prof[:, 0].max() + 25); ax.set_ylim(prof[:, 1].min() - 5, top + 62)
        ax.set_title(t["A"] % pct["FH_vertex"] if flex == 0 else t["B"] + " (β=%.1f°)" % flex, fontsize=9.6,
                     fontweight="bold", color="#1A237E", pad=6)

    ax = fig.add_subplot(gs[0, 2])
    xs = np.arange(30, 75.5, 0.5)
    ys = [h.flex_needed(g["sN"] + x / 100 * (g["sI"] - g["sN"]), phiF) for x in xs]
    ax.plot(xs, ys, color="#263238", lw=2, zorder=3)
    ax.axhspan(19.9 - 7.0, 19.9 + 7.0, color="#FFF59D", alpha=0.55, zorder=0)
    ax.axhline(19.9, color="#F9A825", lw=1, zorder=1); ax.text(30.5, 20.6, t["band1"], fontsize=7.3, color="#8D6E00")
    ax.axhline(30, color="#8D6E63", lw=1.2, ls="--", zorder=1); ax.text(30.5, 30.6, t["band2"], fontsize=7.3, color="#5D4037")
    y0 = -9
    for (p0, name), (p1, _) in zip(bands, bands[1:] + [(bands[-1][0] + 0.5, None)]):
        ax.add_patch(plt.Rectangle((p0, y0), p1 - p0, 4, fc=CORTEX_COL[name], ec="none", zorder=2))
    seen = {}
    for p, name in bands:
        seen.setdefault(name, []).append(p)
    for name, ps in seen.items():
        ax.text(np.mean(ps), y0 + 2, t["cortex"][name], fontsize=7, ha="center", va="center", zorder=3)
    toff = {"FH_vertex": (0, 2.6, "center"), "apex_vertical": (0, -4.6, "center"), "Cz": (-1.2, 2.2, "right"),
            "TH54": (1.2, -3.6, "left"), "lobe_apex": (-1.0, 3.6, "right"), "GV20_5cun": (-1.0, 2.6, "right")}
    for k in ["FH_vertex", "apex_vertical", "Cz", "TH54", "lobe_apex", "GV20_5cun"]:
        lo, med, hi = sens[k]
        yv = h.flex_needed(c[k], phiF)
        col = COL[k]
        ax.errorbar(med, yv, xerr=[[med - lo], [hi - med]], fmt="o", color=col, ms=6, capsize=3, lw=1.4, zorder=5)
        dx, dy, ha = toff[k]
        ax.text(med + dx, yv + dy, "%s (%d°)" % (lab[k].replace("\n", " "), int(round(yv))), fontsize=7, color=col, ha=ha,
                fontweight="bold", zorder=6, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
    ax.set_xlim(30, 75); ax.set_ylim(-10, 55)
    ax.set_xlabel(t["xl"], fontsize=8.5); ax.set_ylabel(t["yl"], fontsize=8.5); ax.tick_params(labelsize=7.5)
    ax.grid(True, alpha=0.3); ax.set_title(t["C"], fontsize=9.6, fontweight="bold", color="#1A237E", pad=6)

    fig.suptitle(t["sup"], fontsize=12, fontweight="bold", y=0.965)
    fig.text(0.5, 0.025, t["foot"], fontsize=7.2, color="#455A64", ha="center", style="italic", wrap=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print("Saved:", path)
    return pct


if __name__ == "__main__":
    head = Head()
    sens = sensitivity(head)
    _, geo = candidates(head)
    bands = cortex_bands(head, geo)
    p = render(head, sens, bands, "ko", OUT_DIR / "GV20_백회_두부자세_정위원칙_해부모식도.png")
    render(head, sens, bands, "en", OUT_DIR / "GV20_head_posture_localization_diagram_en.png")
    print("baseline N-I %:", {k: round(v, 1) for k, v in p.items()})
    print("sensitivity p5/p50/p95:", {k: [round(x, 1) for x in v] for k, v in sens.items()})
    print("cortex:", [(b[0], b[1]) for b in bands if b[0] % 2 == 0])

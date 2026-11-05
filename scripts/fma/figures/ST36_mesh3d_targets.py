# -*- coding: utf-8 -*-
"""
ST36_mesh3d_targets.py — 족삼리 Tri-Target 정위점을 BodyParts3D 4.0 표준 모델(오른다리)에 골도분촌으로 놓고,
피부에 수직인 직자선을 따라 만나는 구조와 깊이를 잰다. 보고서 4·5·7절 'BodyParts3D 규범 모델 측정(B1 보조)'의 원자료.

정위(오른다리, BodyParts3D 좌표: mm, +X 왼쪽, −Y 앞, +Z 위)
  Y(종향): 슬관절선(정강뼈 가쪽관절융기 위끝) ~ 가쪽복사 끝(종아리뼈 아래끝) = 16寸(WHO 골도). 犊鼻下 3寸
  X(횡향, 같은 높이의 피부 단면 둘레를 따라 정강뼈 앞모서리 위 피부점에서 가쪽으로 잰 호 길이)
    Target 1 (고전 '胫骨之外廉')       : 10 mm (보고서 추정 0.5~1.5 cm의 중앙)
    Target 1≡3 (WHO 앞모서리 외측 1횡지): 17.5 mm (1횡지 1.5~2.0 cm의 중앙, 범위도 계산)
    Target 2 ('两筋(肉分)间')          : 앞정강근 단면의 앞가쪽 모서리(긴발가락폄근과의 근간 중격 입구) 위 피부점,
                                         자입 방향 = 피부점 → 앞정강동맥 단면 중심(중격의 깊은 끝, 신경혈관속)
직자선: 피부점에서 단면 안쪽 법선(피부에 수직, 가로면 안) 방향 60 mm.
판정: 직자선이 각 메쉬를 들어가고 나오는 깊이(광선 교차, 바깥에서 출발 가정), 문헌 깊이에서 침끝이 놓이는 구조,
      침끝과 직자선 전체의 앞정강동·정맥 최근접 거리(깊은종아리신경은 메쉬가 없어 동반 혈관으로 대리).

사용: python ST36_mesh3d_targets.py --out "<보고서 폴더>" [--skin bp3d | smplx:<이름>]
출력: <out>/ST36_족삼리_3D해부_Target별_직자경로.png (실제 메쉬 가로 단면), ST36_족삼리_3D해부_모델.html, ST36_족삼리_3D해부_측정.json
  --skin smplx:<이름>: 정위(골도분촌·정강뼈 앞모서리)는 그대로 두고 피부면만 smplx_skin.py로 골격에 등록한 체형 피부로 바꾼다.
  파일명에 _smplx-<이름>이 붙고, 단면 그림에 BodyParts3D 피부를 점선으로 함께 그린다. 음수 깊이 = 구조가 체형 피부 밖(정합 오차).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mesh3d as M                       # noqa: E402
from mesh3d_viewer import build_html     # noqa: E402
from needle_depth import load as load_nd  # noqa: E402

SIDE = "right"
STRUCT = [  # (FMA, 이름, 색, 역할)
    (22532, "앞정강근", "#d9534f", "근육"), (22534, "긴발가락폄근", "#e8907a", "근육"),
    (35187, "종아리뼈사이막", "#9fb7c9", "막"), (43894, "앞정강동맥", "#e0302b", "혈관"), (44331, "앞정강정맥", "#2f6fd0", "혈관"),
    (24476, "정강뼈", "#efe8d2", "뼈"), (24479, "종아리뼈", "#e3dcc4", "뼈")]
TARGETS = [("Target 1 (胫骨之外廉)", "#6c7a89", 10.0), ("Target 1≡3 (WHO 1횡지)", "#111111", 17.5), ("Target 2 (两筋间)", "#7b3fb5", None)]
LIT = [("《铜人》 卷下 5푼", 11.5), ("고전 4종 평균 9.5푼", 21.9), ("7종 평균 11.86푼", 27.3), ("현대 3종 평균 15푼", 34.5),
       ("현대 상한 2촌", 46.0), ("《窦太师》 25푼", 57.5)]
NEEDLE = 60.0
OFF = 30.0                               # 광선 출발점을 피부 밖 30 mm에 둔다(체형 피부 밖으로 나온 구조도 바깥에서 들어가며 센다)


def loop_at(mesh, z, near):
    """메쉬를 z 가로면으로 자른 닫힌 고리 중 near(xy)에 가장 가까운 것 (N×3, 첫 점 반복 없음)"""
    sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    loops = [np.asarray(d) for d in sec.discrete]
    best = min(loops, key=lambda L: np.linalg.norm(L[:, :2].mean(0) - near[:2]))
    if np.allclose(best[0], best[-1]):
        best = best[:-1]
    return best


def arc_walk(L, i0, direction, dist):
    """고리 L에서 i0부터 direction(+1/−1)으로 호 길이 dist만큼 간 점"""
    n, acc, i = len(L), 0.0, i0
    while True:
        j = (i + direction) % n
        seg = np.linalg.norm(L[j] - L[i])
        if acc + seg >= dist:
            return L[i] + (L[j] - L[i]) * (dist - acc) / seg
        acc, i = acc + seg, j
        if j == i0:
            raise ValueError("arc too long")


def arc_len(L, i0, direction, idx):
    acc, i = 0.0, i0
    while i != idx:
        j = (i + direction) % len(L)
        acc += np.linalg.norm(L[j] - L[i])
        i = j
    return acc


def inward_normal(L, p, center):
    i = int(np.argmin(np.linalg.norm(L - p, axis=1)))
    t = L[(i + 1) % len(L)] - L[i - 1]
    n = np.array([t[1], -t[0], 0.0])
    n /= np.linalg.norm(n)
    return n if np.dot(center - p, n) > 0 else -n


def ray_intervals(mesh, o, d):
    loc, _, _ = mesh.ray.intersects_location([o], [d], multiple_hits=True)
    t = np.sort([float(np.dot(x - o, d)) for x in loc])
    t = t[t > 0]
    return [(float(t[k]), float(t[k + 1]) if k + 1 < len(t) else None) for k in range(0, len(t), 2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--skin", default="bp3d", help="피부면: bp3d(기본) 또는 smplx:<이름>")
    a = ap.parse_args()
    out = Path(a.out)
    np.random.seed(0)
    meshes = {f: M.load_mesh(f, SIDE)[0] for f, *_ in STRUCT}
    skin, sk = M.skin_surface(a.skin)
    bskin = M.load_mesh(M.SKIN_FMA)[0] if sk["signed"] else None
    sfx = sk["suffix"]
    tib, fib = meshes[24476], meshes[24479]
    # 종향: 슬관절선(가쪽관절융기 위끝) ~ 가쪽복사 끝 = 16寸
    tv = tib.vertices
    lateral = tv[tv[:, 0] < np.median(tv[:, 0])]               # 오른다리 가쪽 = −X
    z_knee, z_mall = float(lateral[:, 2].max()), float(fib.vertices[:, 2].min())
    cun = (z_knee - z_mall) / 16
    z = z_knee - 3 * cun
    tl = loop_at(tib, z, tib.centroid)
    center = np.r_[tl[:, :2].mean(0), z]
    skin_loop = loop_at(skin, z, center)
    crest = tl[np.argmin(tl[:, 1])]                               # 정강뼈 앞모서리 = 가장 앞(−Y)
    ic = int(np.argmin(np.linalg.norm(skin_loop - crest, axis=1)))
    # 가쪽(−X)으로 도는 방향 정하기
    step = +1 if skin_loop[(ic + 5) % len(skin_loop), 0] < skin_loop[ic, 0] else -1
    # Target 2: 앞정강근–긴발가락폄근 근간 중격 입구 = 앞정강근 단면의 앞가쪽 모서리(보고서 4절 '앞정강근 가쪽 가장자리').
    # 피부점은 그 모서리에 가장 가까운 피부 단면 점, 자입 방향은 피부점 → 중격 입구(중격을 따라 들어감).
    # 이 모델은 바깥쪽 피부 외피가 크고 종아리근 등은 불러오지 않아, 피부 둘레 거리로 근간 위치를 정하지 않는다.
    trees = {f: M._surface(meshes[f], 40000)[1] for f in (22532, 22534, 43894, 44331)}
    ta_l = loop_at(meshes[22532], z, meshes[22532].centroid)
    edl_l = loop_at(meshes[22534], z, meshes[22534].centroid)
    ant = ta_l[ta_l[:, 1] < ta_l[:, 1].mean()]
    septum = ant[np.argmin(ant[:, 0])]                          # 앞쪽 절반 중 가장 가쪽(−X)
    i2 = int(np.argmin(np.linalg.norm(skin_loop - septum, axis=1)))
    groove_arc = arc_len(skin_loop, ic, step, i2)
    muscle = {"ta_width_ml_mm": round(float(np.ptp(ta_l[:, 0])), 1), "ta_depth_ap_mm": round(float(np.ptp(ta_l[:, 1])), 1),
              "edl_width_ml_mm": round(float(np.ptp(edl_l[:, 0])), 1), "edl_depth_ap_mm": round(float(np.ptp(edl_l[:, 1])), 1),
              "crest_to_septum_entry_mm": round(float(np.linalg.norm((septum - crest)[:2])), 1),
              "crest_to_septum_entry_ml_mm": round(float(crest[0] - septum[0]), 1)}
    res = {"model": "BodyParts3D 4.0 오른다리", "skin": sk["label"], "z_knee_mm": round(z_knee, 1), "z_lateral_malleolus_mm": round(z_mall, 1),
           "cun_mm": round(cun, 2), "level_z_mm": round(z, 1), "crest_skin_mm": skin_loop[ic].round(1).tolist(),
           "skin_to_crest_mm": round(float(np.linalg.norm(skin_loop[ic] - crest)), 1), "targets": []}
    paths, sections = [], []
    for name, color, arc in TARGETS:
        if arc is None:
            # 중격의 깊은 끝 = 종아리뼈사이막 앞 신경혈관속(앞정강동맥 단면 중심) → 피부점에서 그쪽으로 중격을 따라 자입
            p = skin_loop[i2]
            art_c = np.r_[loop_at(meshes[43894], z, meshes[43894].centroid)[:, :2].mean(0), z]
            n = (art_c - p) / np.linalg.norm(art_c - p)
            muscle["path_to_septum_entry_mm"] = round(float(np.linalg.norm(np.cross(septum - p, n))), 1)
        else:
            p = arc_walk(skin_loop, ic, step, arc)
            n = inward_normal(skin_loop, p, center)
        arc_v = groove_arc if arc is None else arc
        o = p - n * OFF
        hits = {}
        for f, nm, *_ in STRUCT:
            iv = ray_intervals(meshes[f], o, n)
            hits[nm] = [(round(s - OFF, 1), None if e is None else round(e - OFF, 1)) for s, e in iv if s - OFF <= NEEDLE]

        def tip_in(dmm):
            inside = [nm for nm, iv in hits.items() if any(s <= dmm and (e is None or dmm <= e) for s, e in iv)]
            return inside or ["근육 밖 연부조직(피하·근막·근간)"]
        seg = np.linspace(0, NEEDLE, 241)
        pts = p[None, :] + seg[:, None] * n[None, :]
        vessel = {nm: trees[f].query(pts)[0] for f, nm in ((43894, "앞정강동맥"), (44331, "앞정강정맥"))}
        lit = []
        for lab, dmm in LIT:
            tip = p + n * dmm
            lit.append({"literature": lab, "depth_mm": dmm, "tip_in": tip_in(dmm),
                        "artery_mm": round(float(trees[43894].query(tip)[0]), 1), "vein_mm": round(float(trees[44331].query(tip)[0]), 1)})
        first = min([iv[0][0] for nm, iv in hits.items() if iv and nm in ("앞정강근", "긴발가락폄근", "정강뼈")] or [None], key=lambda v: v if v is not None else 1e9)
        rec = {"target": name, "arc_from_crest_mm": round(arc_v, 1), "skin_point_mm": p.round(1).tolist(), "direction": n.round(3).tolist(),
               "hits": hits, "subcutaneous_mm": first,
               "closest_artery_on_path": {"mm": round(float(vessel["앞정강동맥"].min()), 1), "at_depth_mm": round(float(seg[vessel["앞정강동맥"].argmin()]), 1)},
               "closest_vein_on_path": {"mm": round(float(vessel["앞정강정맥"].min()), 1), "at_depth_mm": round(float(seg[vessel["앞정강정맥"].argmin()]), 1)},
               "literature_tips": lit}
        if arc is not None and arc == 17.5:
            rec["arc_range_mm"] = {str(x): arc_walk(skin_loop, ic, step, x).round(1).tolist() for x in (15.0, 20.0)}
        res["targets"].append(rec)
        ticks = [{"mm": d, "label": f"{d:g} mm"} for _, d in LIT if d <= NEEDLE and d in (11.5, 27.3, 46.0)]
        paths.append({"label": name, "color": color, "start": p, "end": p + n * NEEDLE, "ticks": ticks})
        sections.append((name, color, p, n))
    t13 = next(t for t in res["targets"] if t["target"].startswith("Target 1≡3"))
    t2 = next(t for t in res["targets"] if t["target"].startswith("Target 2"))
    t1 = res["targets"][0]
    # Δ(X): Target 2 = 앞모서리 → 중격 입구 직선거리(근육 수준), Target 1≡3 = 1횡지 15~20 mm, Target 1 = 5~15 mm
    sx = muscle["crest_to_septum_entry_mm"]
    res["muscle"] = muscle
    res["delta_mm"] = {"T2-T3": round(sx - 17.5, 1), "T2-T3_range": [round(sx - 20, 1), round(sx - 15, 1)],
                       "T1-T3": 7.5, "T1-T3_range": [0.0, 15.0], "T1-T2": round(sx - 10, 1),
                       "note": "Y(犊鼻下 3寸)는 세 Target이 같으므로 Δ는 X(가로) 차이. Target 2는 근육 단면에서 잰 값, 1횡지는 가정값"}
    nd = load_nd()["ST36"]
    res["needle_depth_literature"] = {"all_mean_pun": nd["all"]["mean_pun"], "all_mean_mm": nd["all"]["mean_mm"],
                                      "classic_mm": nd["classic"]["mean_mm"], "modern_mm": nd["modern"]["mean_mm"]}
    res["caveat"] = ("BodyParts3D 단일 표준 성인 모델(개인차·자세·피하지방 미반영) 측정, 규범 해부 형상 참고(B1 보조). "
                     "정위점은 골도분촌과 횡향 거리 가정으로 놓은 것이며 경혈 실측(B2)이 아니다. 깊은종아리신경은 메쉬가 없어 앞정강동정맥으로 대리")
    if sk["signed"]:
        res["caveat"] += (". 피부면은 BodyParts3D 골격 관절 중심에 등록한 SMPL-X 통계 체형 피부이며 근육·지방 층은 BodyParts3D 그대로라 "
                          "체형 차이는 피하층 두께 차이로만 나타나는 근사다. 음수 깊이 = 구조 표면이 체형 피부 밖(정합 오차)")
        res["skin_joint_error_mm"] = sk.get("joint_error_mm")
    attrib = " ".join(x for x in (M.ATTRIB, sk["attribution"]) if x)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"ST36_족삼리_3D해부_측정{sfx}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    draw_section(meshes, skin, z, center, sections, res, out / f"ST36_족삼리_3D해부_Target별_직자경로{sfx}.png", sk, bskin, attrib)
    items = [{"mesh": meshes[f], "fma": f, "label": nm, "category": "근육" if role == "근육" else ("뼈" if role == "뼈" else ("동맥" if "동맥" in nm else "정맥" if "정맥" in nm else "막")),
              "color": c, "opacity": 0.5 if role == "근육" else (0.85 if role in ("뼈", "막") else 1.0), "role": "context" if role == "뼈" else "structure"}
             for f, nm, c, role in STRUCT]
    lo, hi = center - [70, 70, 90], center + [70, 70, 90]
    keep = np.all((skin.triangles_center >= lo) & (skin.triangles_center <= hi), axis=1)
    items.append({"mesh": skin.submesh([np.nonzero(keep)[0]], append=True), "fma": M.SKIN_FMA,
                  "label": "피부" if not sk["signed"] else sk["label"], "category": "피부",
                  "color": "#f0c8a6", "opacity": 0.15, "role": "context"})
    notes = [f"{attrib}.", res["caveat"] + ".",
             f"정위: 슬관절선~가쪽복사 끝 16寸(이 모델 1寸 = {cun:.1f} mm), 犊鼻下 3寸. Target 1 = 정강뼈 앞모서리 위 피부에서 가쪽 10 mm, "
             f"Target 1≡3 = 17.5 mm(1횡지), Target 2 = 앞정강근–긴발가락폄근 근간 중격 입구 위 피부점(앞모서리에서 근육 수준 직선 {sx:.1f} mm), 중격 쪽 자입. "
             "막대 = 자입선 60 mm(Target 1·1≡3은 피부에 수직), 눈금 = 11.5·27.3·46 mm."]
    build_html(items, out / f"ST36_족삼리_3D해부_모델{sfx}.html", "족삼리(ST36) 3D 해부 모델 · Tri-Target 직자 경로",
               f"BodyParts3D 4.0 · 피부: {sk['label']} · FMA 대응 · 오른다리 · 단위 mm · 犊鼻下 3寸 높이", notes, paths=paths)
    print(json.dumps({k: res[k] for k in ("cun_mm", "level_z_mm", "skin_to_crest_mm", "delta_mm", "muscle")}, ensure_ascii=False))
    for t in res["targets"]:
        print(f"\n{t['target']}  호 {t['arc_from_crest_mm']} mm · 피하 {t['subcutaneous_mm']} mm · 동맥 최근접 {t['closest_artery_on_path']}")
        for nm, iv in t["hits"].items():
            if iv:
                print(f"   {nm:8} {iv}")
        for l in t["literature_tips"]:
            print(f"   {l['literature']:16} {l['depth_mm']:5.1f} mm → {', '.join(l['tip_in'])} · 동맥 {l['artery_mm']} · 정맥 {l['vein_mm']}")


def draw_section(meshes, skin, z, center, sections, res, out, skin_info=None, bskin=None, attrib=M.ATTRIB):
    """실제 메쉬를 犊鼻下 3寸 가로면으로 자른 단면 + Target별 직자선과 문헌 깊이 눈금 (위에서 내려다봄, 앞이 위)"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
    fig, ax = plt.subplots(figsize=(11, 9.5), dpi=170)
    # 화면: 가로 = −X(오른다리 가쪽이 오른쪽), 세로 = −Y(앞이 위)
    P = lambda v: np.c_[-(v[:, 0] - center[0]), -(v[:, 1] - center[1])]
    sk = loop_at(skin, z, center)
    ax.add_patch(Polygon(P(sk), closed=True, fc="#f6e3d3", ec="#c9a184", lw=1.2, zorder=1))
    if bskin is not None:            # 체형 피부일 때 BodyParts3D 피부 단면을 점선으로 겹쳐 피하 두께 차이를 보인다
        bl = P(loop_at(bskin, z, center))
        ax.plot(*np.vstack([bl, bl[:1]]).T, color="#8a6a50", lw=1.0, ls="--", zorder=6, label="BodyParts3D 피부")
        ax.legend(loc="lower right", fontsize=8.5, frameon=False)
    order = [(24476, 3), (24479, 3), (22532, 2), (22534, 2), (35187, 4), (43894, 5), (44331, 5)]
    names = {f: (nm, c) for f, nm, c, _ in STRUCT}
    for f, zo in order:
        sec = meshes[f].section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
        if sec is None:
            continue
        nm, c = names[f]
        for k, L in enumerate(sec.discrete):
            L = np.asarray(L)
            if f == 35187 or len(L) < 4:
                ax.plot(*P(L).T, color="#5d7d93", lw=2.2, zorder=zo)
            else:
                ax.add_patch(Polygon(P(L), closed=True, fc=c, ec="#555", lw=.6, alpha=.9 if f in (24476, 24479, 43894, 44331) else .75, zorder=zo))
            if k == 0:
                q = P(L).mean(0)
                off = {24476: (-30, 10), 24479: (30, -4), 22532: (20, 22), 22534: (34, 6), 35187: (-36, -16),
                       43894: (-30, -30), 44331: (30, -24)}[f]
                ax.annotate(nm, q, xytext=(q[0] + off[0], q[1] + off[1]), fontsize=9.5, ha="center", color="#222", zorder=9,
                            arrowprops=dict(arrowstyle="-", color="#777", lw=.6), bbox=dict(boxstyle="round,pad=.15", fc="white", ec="none", alpha=.8))
    for (name, color, p, n), t in zip(sections, res["targets"]):
        a_, b_ = P(p[None]), P((p + n * NEEDLE)[None])
        ax.plot([a_[0, 0], b_[0, 0]], [a_[0, 1], b_[0, 1]], color=color, lw=2.2, zorder=8)
        ax.scatter(*a_.T, s=46, color=color, zorder=9, edgecolor="white", lw=.8)
        for lab, d in LIT:
            if d in (11.5, 27.3, 46.0):
                q = P((p + n * d)[None])[0]
                ax.scatter(*q, s=22, marker="_" if False else "o", color=color, zorder=9, edgecolor="white", lw=.5)
                if name.startswith("Target 1≡3"):
                    ax.annotate(f"{d:g} mm", q, xytext=(q[0] + 4, q[1] + 2.5), fontsize=8, color=color, va="center", ha="left", zorder=9,
                                bbox=dict(boxstyle="round,pad=.1", fc="white", ec="none", alpha=.7))
        k = res["targets"].index(t)
        sub = f"앞모서리에서 {t['arc_from_crest_mm']:.1f} mm" if k < 2 else f"중격 입구: 앞모서리에서 {res['muscle']['crest_to_septum_entry_mm']:.1f} mm"
        ax.annotate(f"{name}\n{sub}", a_[0], xytext=(a_[0, 0] + (-28, 0, 30)[k], a_[0, 1] + (16, 30, 16)[k]),
                    fontsize=9, ha="center", color=color, weight="bold", zorder=10, arrowprops=dict(arrowstyle="-", color=color, lw=.7))
    ax.set_aspect("equal")
    # 앞칸 주변만 보인다(뒤칸 근육은 그리지 않았으므로 피부 단면 뒤쪽은 비어 있다)
    pts = np.vstack([P(np.array([p, p + n * NEEDLE])) for _, _, p, n in sections] +
                    [P(loop_at(meshes[f], z, meshes[f].centroid)) for f in (24476, 24479, 22532, 22534)])
    x0, x1 = pts[:, 0].min() - 45, pts[:, 0].max() + 45
    y0, y1 = pts[:, 1].min() - 22, pts[:, 1].max() + 42
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.axis("off")
    ax.text(0.01, 0.995, "앞(前) ↑", transform=ax.transAxes, va="top", fontsize=10, color="#555")
    ax.text(0.99, 0.5, "가쪽 →", transform=ax.transAxes, ha="right", fontsize=10, color="#555")
    ax.plot([x0 + 4, x0 + 14], [y0 + 6] * 2, color="k", lw=2)
    ax.text(x0 + 9, y0 + 3, "10 mm", ha="center", va="top", fontsize=8.5)
    fig.suptitle("족삼리(ST36) 犊鼻下 3寸 높이 실제 메쉬 가로 단면 · Tri-Target 직자 경로 (BodyParts3D 4.0" + ("" if not skin_info or not skin_info.get("signed") else f" · 피부 {skin_info['label']}") + ", 오른다리, 위에서 내려다봄)",
                 x=0.01, ha="left", fontsize=12, weight="bold")
    fig.text(0.01, 0.01, f"{attrib}. 단일 표준 성인 모델 — 개인차·자세·피하지방 미반영, 경혈 위치 실측 아님. "
             "Target 1·1≡3 자입선 = 피부에 수직, Target 2 = 근간 중격을 따라 신경혈관속 방향. 점 = 깊이 11.5·27.3·46 mm. "
             "깊은종아리신경은 메쉬가 없어 그리지 않았다(앞정강동정맥과 함께 종아리뼈사이막 앞을 지난다)", fontsize=7.6, color="#444", wrap=True)
    fig.savefig(out, facecolor="white", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
mesh3d.py — FMA 기반 3D 형상·메쉬 DB 연동 (BodyParts3D · Open Anatomy Project) — 공간 좌표·부피·표면적·거리·간섭·렌더링

데이터:
  BodyParts3D 4.0 (DBCLS, CC BY 4.0) — FMA 개념 ID별 전신 3D 폴리곤(.obj, 단위 mm, 좌우 별도 메쉬)
      표기: "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International"
  Open Anatomy Project (SPL/NAC, 3D Slicer License 섹션 B) — 부위별 아틀라스(무릎·두경부·복부·뇌·내이·간) .vtk 모델 + MRML/JSON
원본 위치(PC별, Drive 밖): FMA_DATA_DIR(기본 %LOCALAPPDATA%\\acupoint_fma)\\bodyparts3d, \\oap
색인·결과(Drive 공유): 02_Master_Datasets/FMA/BodyParts3D/, 02_Master_Datasets/FMA/OpenAnatomy/

사용 (프로젝트 루트에서):
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py fetch bp3d
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py fetch oap knee-2016-09        # oap-list로 아틀라스 목록
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py index                         # 색인 + 경혈별 메쉬 보유 현황
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py measure 22532 --side right    # 부피·표면적·경계상자·무게중심
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py distance 44771 22532 --side right   # 최소 거리·간섭(겹침)
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py render 22532 22534 44771 --side right --out a.png
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py acupoint ST36 --side right --out <폴더>   # 경혈 구조 일괄
  python .claude/skills/acupoint-anatomy/scripts/fma/mesh3d.py oap measure head-neck-2016-09 "left trapezius muscle"

해석 원칙: BodyParts3D는 한 사람 표준 모델이라 개인차를 반영하지 않는다. 메쉬 다수가 완전히 닫혀 있지 않으므로(watertight=False)
부피는 근사(부호 있는 체적 합)이며 결과에 watertight 여부를 함께 적는다. 경혈 위치 자체는 메쉬에 없다 — 경혈 특이 실측(B2)이 아니다.
"""
import argparse
import csv
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

from fma_common import INDEX_PATH, MAPPING_JSON, ROOT, data_dir, norm

BP3D_URL = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/"
BP3D_FILES = ["partof_element_parts.txt", "partof_inclusion_relation_list.txt", "partof_parts_list_e.txt",
              "isa_element_parts.txt", "isa_inclusion_relation_list.txt", "isa_parts_list_e.txt",
              "partof_BP3D_4.0_obj_99.zip", "isa_BP3D_4.0_obj_99.zip"]
OAP_URL = "https://www.openanatomy.org/atlases/nac/{}.zip"
OAP_ATLASES = {"knee-2016-09": "무릎(MRI)", "head-neck-2016-09": "두경부(CT)", "abdomen-2016-09": "복부(CT)",
               "brain-2017-01": "뇌(MRI)", "inner-ear-2018-02": "내이(μCT)", "liver-2014-02-20": "간(CT)"}
BP3D_DIR = data_dir() / "bodyparts3d"
OAP_DIR = data_dir() / "oap"
SHARE_BP3D = ROOT / "02_Master_Datasets" / "FMA" / "BodyParts3D"
SHARE_OAP = ROOT / "02_Master_Datasets" / "FMA" / "OpenAnatomy"
ATTRIB = "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International"


# ---------------------------------------------------------------- fetch
def _get(url, out):
    if out.exists() and out.stat().st_size > 0:
        print(f"   [skip] {out.name}")
        return
    print(f"   [get ] {url}")
    part = out.with_name(out.name + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(part, "wb") as w:
        shutil.copyfileobj(r, w, length=1 << 20)
    part.replace(out)


def cmd_fetch(a):
    if a.what == "bp3d":
        BP3D_DIR.mkdir(parents=True, exist_ok=True)
        for f in BP3D_FILES:
            _get(BP3D_URL + f, BP3D_DIR / f)
        for z in ("partof_BP3D_4.0_obj_99.zip", "isa_BP3D_4.0_obj_99.zip"):
            if not (BP3D_DIR / z.replace(".zip", "")).exists():
                zipfile.ZipFile(BP3D_DIR / z).extractall(BP3D_DIR)
                print(f"   [unzip] {z}")
    else:
        if a.atlas not in OAP_ATLASES:
            sys.exit(f"[oap] 알 수 없는 아틀라스: {a.atlas}. 목록: {', '.join(OAP_ATLASES)}")
        OAP_DIR.mkdir(parents=True, exist_ok=True)
        z = OAP_DIR / f"{a.atlas}.zip"
        _get(OAP_URL.format(a.atlas), z)
        if not (OAP_DIR / a.atlas).exists():
            zipfile.ZipFile(z).extractall(OAP_DIR)
            print(f"   [unzip] {z.name}")


# ---------------------------------------------------------------- index
def _tsv(name):
    with io.open(BP3D_DIR / name, encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t")
        next(r)
        return [row for row in r if row]


def _fid(s):
    m = re.match(r"FMA(\d+)", s or "")
    return int(m.group(1)) if m else None


def oap_structures(atlas):
    root = OAP_DIR / atlas
    j = json.loads((root / "atlasStructure.json").read_text(encoding="utf-8"))
    ds = {d["@id"]: d.get("source") for d in j if d.get("@type") == "DataSource"}
    out = []
    for d in j:
        if d.get("@type") != "Structure":
            continue
        name = (d.get("annotation") or {}).get("name") or d["@id"].strip("#").replace("_", " ")
        files = [ds.get(s.get("dataSource")) for s in d.get("sourceSelector", []) if "GeometrySelector" in str(s.get("@type"))]
        files = [f for f in files if f]
        if files:
            out.append({"name": name, "file": files[0].replace("%20", " "), "color": (d.get("renderOption") or {}).get("color")})
    return out


ORD_WORD = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
OAP_ALIASES = [(r"\bscalenius\b", "scalenus"), (r"\bperoneus nerve\b", "common fibular nerve"),
               (r"\b(lateral|medial) head gastrocnemius muscle\b", r"\1 head of gastrocnemius"),
               (r"\bmuscular branches tibialis nerve\b", "muscular branch of tibial nerve"),
               (r"\btibialis nerve\b", "tibial nerve"), (r"\bzygomatic muscle\b", "zygomaticus major"),
               (r"\b(external|internal|common) carotid$", r"\1 carotid artery"), (r"\bsternocleidomastoideus muscle\b", "sternocleidomastoid"),
               (r"^hyoid$", "hyoid bone"), (r"\bpatellar cartilage\b", "articular cartilage of patella"),
               (r"\binfrapatellar fat body\b", "infrapatellar fat pad")]


def oap_name(name):
    """OAP 구조명(밑줄·약식 표기)을 FMA 대조용 영문으로 바꾼다. 예: cervical3 → third cervical vertebra"""
    n = name.replace("_", " ").strip()
    n = re.sub(r"\b(cervical|thoracic|lumbar)\s?(\d{1,2})\b",
               lambda m: f"{ORD_WORD[int(m.group(2)) - 1]} {m.group(1)} vertebra" if 0 < int(m.group(2)) <= 12 else m.group(0), n, flags=re.I)
    n = re.sub(r"\brib\s?(\d{1,2})\b", lambda m: f"{ORD_WORD[int(m.group(1)) - 1]} rib" if 0 < int(m.group(1)) <= 12 else m.group(0), n, flags=re.I)
    for pat, rep in OAP_ALIASES:
        n = re.sub(pat, rep, n, flags=re.I)
    return n


def cmd_index(a):
    if not (BP3D_DIR / "partof_element_parts.txt").exists():
        sys.exit("[index] BodyParts3D가 없습니다. 먼저: mesh3d.py fetch bp3d")
    SHARE_BP3D.mkdir(parents=True, exist_ok=True)
    for f in BP3D_FILES[:6]:
        shutil.copy2(BP3D_DIR / f, SHARE_BP3D / f)
    idx = {}
    for tree in ("partof", "isa"):
        for cid, name, el in _tsv(f"{tree}_element_parts.txt"):
            fid = _fid(cid)
            if fid is None:
                continue
            e = idx.setdefault(fid, {"name": name, "partof": [], "isa": []})
            e[tree].append(el)
    payload = {"_metadata": {"source": "BodyParts3D 4.0 (dbarchive.biosciencedbc.jp/en/bodyparts3d)", "license": "CC BY 4.0",
                             "attribution": ATTRIB, "units": "mm", "concepts": len(idx),
                             "note": "partof/isa 트리별 구성 요소 obj(FJxxxx) 목록. 좌우는 별도 요소 — measure --side로 X 부호(+X=왼쪽, 메쉬 좌표 기준)"},
               "concepts": {str(k): v for k, v in sorted(idx.items())}}
    (SHARE_BP3D / "bp3d_fma_index.json").write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"[index] BodyParts3D FMA 개념 {len(idx):,}개 → {SHARE_BP3D / 'bp3d_fma_index.json'}")

    # OAP 아틀라스: 구조 이름 → FMA ID (fma_build.Matcher)
    sys.path.insert(0, str(Path(__file__).parent))
    from fma_build import Matcher
    con = sqlite3.connect(str(INDEX_PATH))
    mt = Matcher(con)
    SHARE_OAP.mkdir(parents=True, exist_ok=True)
    oap_all = {}
    for atlas in sorted(p.name for p in OAP_DIR.glob("*") if p.is_dir() and (p / "atlasStructure.json").exists()):
        rows = []
        for s in oap_structures(atlas):
            hit = mt.match(oap_name(s["name"]))
            h = hit[0] if hit else {}
            rows.append({**s, "fma_id": h.get("fma_id"), "fma_label": h.get("fma_label"), "match": h.get("match", "none")})
        oap_all[atlas] = rows
        ok = sum(1 for r in rows if r["fma_id"] and r["match"].startswith("exact"))
        print(f"[index] OAP {atlas}: 구조 {len(rows)} · FMA 정확 대응 {ok}")
    (SHARE_OAP / "oap_fma_index.json").write_text(json.dumps({"_metadata": {"license": "3D Slicer License section B (SPL/NAC atlases)",
                                                                             "source": "https://www.openanatomy.org/atlas-pages/"},
                                                              "atlases": oap_all}, ensure_ascii=False, indent=0), encoding="utf-8")

    # 경혈별 메쉬 보유 현황 (교재 구조 → BodyParts3D 개념 직접 일치, 없으면 FMA 상위(is_a·part_of) 1~3단계에서 찾음)
    rows = json.loads(MAPPING_JSON.read_text(encoding="utf-8"))["rows"]
    up = {}
    # 상위 대체는 부분-전체 관계로만(분류 관계 is_a는 'Set of organ regions' 같은 일반 개념으로 새므로 제외), 2단계까지
    for s_, rel, d_ in con.execute("SELECT src, rel, dst FROM edge WHERE rel IN ('regional_part_of','constitutional_part_of','branch_of','tributary_of')"):
        up.setdefault(s_, []).append(d_)
    lab = dict(con.execute("SELECT fma_id, label FROM entity"))

    def find_mesh(fid):
        seen, frontier = {fid}, [fid]
        for depth in range(3):
            for f in frontier:
                if f in idx and not (lab.get(f) or "").lower().startswith("set of"):
                    return f, depth
            frontier = [p for f in frontier for p in up.get(f, []) if p not in seen and not seen.add(p)]
        return None, None

    cov = {}
    for r in rows:
        if not r["fma_id"] or r["match"].startswith(("fuzzy", "none")) or "검토" in r["match"]:
            continue
        mf, depth = find_mesh(r["fma_id"])
        e = cov.setdefault(r["code"], {})
        e[str(r["fma_id"])] = {"label": r["fma_label"], "category": r["category"], "mesh_fma": mf,
                              "mesh_label": lab.get(mf), "level": None if mf is None else ("exact" if depth == 0 else f"ancestor+{depth}")}
    (SHARE_BP3D / "acupoint_mesh_coverage.json").write_text(json.dumps(cov, ensure_ascii=False, indent=0), encoding="utf-8")
    tot = sum(len(v) for v in cov.values())
    ex = sum(1 for v in cov.values() for x in v.values() if x["level"] == "exact")
    an = sum(1 for v in cov.values() for x in v.values() if x["level"] and x["level"] != "exact")
    print(f"[index] 경혈 {len(cov)}개 · 교재 구조 {tot:,}건 중 메쉬 직접 보유 {ex:,} · 상위 구조 메쉬 {an:,} · 없음 {tot - ex - an:,}")


# ---------------------------------------------------------------- mesh load / measure
def _bp3d_index():
    p = SHARE_BP3D / "bp3d_fma_index.json"
    if not p.exists():
        sys.exit("[mesh] 색인이 없습니다. 먼저: mesh3d.py index")
    return json.loads(p.read_text(encoding="utf-8"))["concepts"]


def resolve(q):
    m = re.fullmatch(r"(?:fma:?)?(\d+)", str(q).strip(), re.I)
    if m:
        return int(m.group(1))
    con = sqlite3.connect(str(INDEX_PATH))
    r = con.execute("SELECT fma_id FROM term WHERE term_norm=? LIMIT 1", (norm(q),)).fetchone()
    if not r:
        sys.exit(f"[mesh] '{q}'를 FMA에서 찾지 못했습니다")
    return r[0]


def load_mesh(fid, side=None, tree=None):
    import trimesh
    idx = _bp3d_index()
    e = idx.get(str(fid))
    if not e:
        return None, None
    tree = tree or ("partof" if e["partof"] else "isa")
    els = e[tree] or e["isa"] or e["partof"]
    d = BP3D_DIR / f"{tree if e[tree] else ('isa' if e['isa'] else 'partof')}_BP3D_4.0_obj_99"
    parts = []
    for el in els:
        p = d / f"{el}.obj"
        if not p.exists():
            continue
        m = trimesh.load(str(p), force="mesh", process=False)
        cx = m.bounds.mean(axis=0)[0]
        if side == "left" and cx < 0 or side == "right" and cx > 0:
            continue
        parts.append(m)
    if not parts:
        return None, e
    return trimesh.util.concatenate(parts), {**e, "elements_used": len(parts), "tree": tree}


def metrics(m):
    hull = m.convex_hull
    return {"volume_cm3": round(abs(m.volume) / 1000, 2), "surface_area_cm2": round(m.area / 100, 2),
            "watertight": bool(m.is_watertight), "convex_hull_volume_cm3": round(hull.volume / 1000, 2),
            "bbox_min_mm": m.bounds[0].round(1).tolist(), "bbox_max_mm": m.bounds[1].round(1).tolist(),
            "extent_mm": m.extents.round(1).tolist(), "centroid_mm": m.centroid.round(1).tolist(),
            "vertices": int(len(m.vertices)), "faces": int(len(m.faces))}


def _label(fid):
    con = sqlite3.connect(str(INDEX_PATH))
    r = con.execute("SELECT label FROM entity WHERE fma_id=?", (fid,)).fetchone()
    return r[0] if r else str(fid)


def cmd_measure(a):
    out = []
    for q in a.targets:
        fid = resolve(q)
        m, info = load_mesh(fid, a.side, a.tree)
        if m is None:
            print(f"FMA:{fid} {_label(fid)} — BodyParts3D 메쉬 없음")
            continue
        r = {"fma_id": fid, "label": _label(fid), "side": a.side or "both", "tree": info["tree"], **metrics(m)}
        out.append(r)
        print(json.dumps(r, ensure_ascii=False))
    return out


def min_distance(ma, mb, n=20000):
    """A 표면 표본점 → B 표면 최근접 거리(open3d KD-tree). 간섭: B가 닫힌 메쉬면 A 표본점 중 B 내부 비율."""
    import open3d as o3d
    pa = ma.sample(n)
    pb = mb.sample(n)
    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pb))
    tree = o3d.geometry.KDTreeFlann(pcd)
    d = np.array([np.sqrt(tree.search_knn_vector_3d(p, 1)[2][0]) for p in pa])
    i = int(d.argmin())
    inside = None
    if mb.is_watertight:
        inside = float(mb.contains(pa[:5000]).mean())
    return {"min_distance_mm": round(float(d.min()), 2), "p05_distance_mm": round(float(np.percentile(d, 5)), 2),
            "closest_point_A_mm": pa[i].round(1).tolist(), "A_points_inside_B_ratio": inside}


def cmd_distance(a):
    fa, fb = resolve(a.a), resolve(a.b)
    ma, _ = load_mesh(fa, a.side)
    mb, _ = load_mesh(fb, a.side)
    if ma is None or mb is None:
        sys.exit("[distance] 둘 중 메쉬가 없는 구조가 있습니다")
    r = {"A": f"FMA:{fa} {_label(fa)}", "B": f"FMA:{fb} {_label(fb)}", "side": a.side or "both", **min_distance(ma, mb)}
    if ma.is_watertight and mb.is_watertight:
        try:
            inter = ma.intersection(mb, engine="manifold")
            r["intersection_volume_cm3"] = round(abs(inter.volume) / 1000, 3)
        except Exception as ex:   # noqa: BLE001
            r["intersection_volume_cm3"] = f"계산 불가({type(ex).__name__})"
    else:
        r["intersection_volume_cm3"] = "닫히지 않은 메쉬 — 표본점 거리로만 판정"
    print(json.dumps(r, ensure_ascii=False))
    return r


PALETTE = {"근육": "#d9534f", "신경": "#f2c230", "혈관": "#e0302b", "뼈": "#efe8d2"}


def _scene_pyvista(items, view):
    import pyvista as pv
    pv.OFF_SCREEN = True
    pl = pv.Plotter(off_screen=True, window_size=(1400, 1600))
    pl.set_background("white")
    for m, color, label, opacity in items:
        pl.add_mesh(pv.wrap(m), color=color, opacity=opacity, smooth_shading=True)
    if view == "iso":
        pl.view_xz()
        pl.camera.azimuth = -35
        pl.camera.elevation = 15
    else:
        {"xz": pl.view_xz, "yz": pl.view_yz, "xy": pl.view_xy}[view]()
    pl.camera.zoom(1.2)
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


def _scene_matplotlib(items, view):
    """VTK 없이 그리는 대체 경로(Windows 애플리케이션 제어가 VTK DLL을 막는 PC). 면 단위 램버트 음영 + 깊이 정렬."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    # pyvista 시점과 맞춤: xz = 앞(−Y)에서, yz = 옆(+X)에서, xy = 위에서, iso = 앞에서 왼쪽으로 35°·위 15°
    elev, azim = {"xz": (0, -90), "yz": (0, 0), "xy": (90, -90), "iso": (15, -125)}[view]
    e, az = np.radians(elev), np.radians(azim)
    eye = np.array([np.cos(e) * np.cos(az), np.cos(e) * np.sin(az), np.sin(e)])
    light = eye + np.array([0.3, 0.2, 0.6])
    light /= np.linalg.norm(light)
    fig = plt.figure(figsize=(7, 8), dpi=200)
    ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    polys, cols, depth = [], [], []
    for m, color, label, opacity in items:
        tri = m.vertices[m.faces]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12
        shade = 0.35 + 0.65 * np.abs(nrm @ light)
        rgb = np.clip(np.array(to_rgb(color))[None, :] * shade[:, None], 0, 1)
        polys.append(tri)
        cols.append(np.c_[rgb, np.full(len(tri), opacity)])
        depth.append(tri.mean(1) @ eye)
    tri, col, dep = np.concatenate(polys), np.concatenate(cols), np.concatenate(depth)
    order = np.argsort(dep)                       # 먼 면부터
    ax.add_collection3d(Poly3DCollection(tri[order], facecolors=col[order], edgecolors="none", linewidths=0))
    allv = tri.reshape(-1, 3)
    lo, hi = allv.min(0), allv.max(0)
    ax.set_xlim(lo[0], hi[0]); ax.set_ylim(lo[1], hi[1]); ax.set_zlim(lo[2], hi[2])
    ax.set_box_aspect(hi - lo)
    ax.view_init(elev=elev, azim=azim)
    ax.set_proj_type("ortho")
    ax.axis("off")
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return img


def render(items, out, title="", view="xz", note=""):
    """3D 장면을 찍고(pyvista, 안 되면 matplotlib 대체), 범례·제목·주석은 matplotlib으로 얹는다(한글 글꼴 사용)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    try:
        img = _scene_pyvista(items, view)
    except Exception as ex:   # noqa: BLE001 — VTK DLL 차단·OpenGL 없음 등
        print(f"   [render] pyvista 사용 불가({type(ex).__name__}) → matplotlib 대체 렌더러")
        img = _scene_matplotlib(items, view)
    plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei"]
    fig = plt.figure(figsize=(12, 11), dpi=150)
    ax = fig.add_axes([0.0, 0.06, 0.62, 0.88]); ax.imshow(img); ax.axis("off")
    lg = fig.add_axes([0.6, 0.06, 0.4, 0.88]); lg.axis("off")
    lg.legend(handles=[Patch(fc=c, ec="#555", alpha=max(o, 0.6), label=l) for _, c, l, o in items], loc="upper left",
              fontsize=10.5, frameon=False, title="구조 (BodyParts3D 메쉬)", title_fontsize=11.5)
    fig.suptitle(title, x=0.01, ha="left", fontsize=14, weight="bold")
    fig.text(0.01, 0.012, note or ATTRIB, fontsize=8.2, color="#444", va="bottom", wrap=True)
    fig.savefig(out, facecolor="white")
    plt.close(fig)


def cmd_render(a):
    items = []
    colors = ["#d9534f", "#e57f6c", "#f2c230", "#e0302b", "#2f5fb3", "#7d6f4f", "#2a9d8f", "#8f4a2a"]
    for i, q in enumerate(a.targets):
        fid = resolve(q)
        m, _ = load_mesh(fid, a.side)
        if m is not None:
            items.append((m, colors[i % len(colors)], f"FMA:{fid} {_label(fid)}", 1.0 if i else 0.85))
    render(items, a.out, a.title or "", a.view)
    print(f"[render] → {a.out}")


def cmd_acupoint(a):
    cov = json.loads((SHARE_BP3D / "acupoint_mesh_coverage.json").read_text(encoding="utf-8"))
    m_ = re.fullmatch(r"([A-Za-z]+)-?(\d+)", a.code.strip())
    code = f"{m_.group(1).upper()}{int(m_.group(2)):02d}" if m_ else a.code
    rows = cov.get(code)
    if not rows:
        sys.exit(f"[acupoint] {code}의 메쉬 현황이 없습니다(index 먼저)")
    outdir = Path(a.out) if a.out else data_dir() / "mesh_results"
    outdir.mkdir(parents=True, exist_ok=True)
    loaded, table = {}, []
    for fid, r in rows.items():
        mf = r["mesh_fma"]
        if mf is None:
            table.append({"fma_id": int(fid), "label": r["label"], "category": r["category"],
                          "mesh": "없음 (BodyParts3D 미수록 — 말초 피부신경·가지 다수가 없음)"})
            continue
        if mf not in loaded:
            m, _ = load_mesh(mf, a.side)
            loaded[mf] = m
        m = loaded[mf]
        if m is None:
            table.append({"fma_id": int(fid), "label": r["label"], "category": r["category"], "mesh": f"FMA:{mf} {a.side} 측 없음"})
            continue
        table.append({"fma_id": int(fid), "label": r["label"], "category": r["category"], "mesh": f"FMA:{mf} {r['mesh_label']}",
                      "level": r["level"], **metrics(m)})
    # 신경·혈관 ↔ 근육 최소 거리 (직접 보유 메쉬만)
    pairs = []
    exact = [t for t in table if t.get("level") == "exact"]
    for t1 in exact:
        for t2 in exact:
            if t1["category"] in ("신경", "혈관") and t2["category"] == "근육":
                r = min_distance(loaded[int(t1["mesh"].split()[0][4:])], loaded[int(t2["mesh"].split()[0][4:])], n=8000)
                pairs.append({"A": t1["label"], "B": t2["label"], **r})
    res = {"code": code, "side": a.side, "structures": table, "nerve_vessel_to_muscle": pairs,
           "attribution": ATTRIB, "caveat": "BodyParts3D 단일 표준 모델, 경혈 위치 정보 없음, 비폐쇄 메쉬 부피는 근사"}
    (outdir / f"{code}_mesh3d.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    items = []
    for t in table:
        if "level" in t:
            fid = int(t["mesh"].split()[0][4:])
            color = PALETTE.get(t["category"], "#888888")
            if t["category"] == "혈관" and "vein" in t["label"].lower():
                color = "#2f5fb3"
            if t["category"] == "근육":
                color = ["#d9534f", "#e57f6c", "#c96b5a", "#b56b5a"][len([i for i in items if i[1].startswith(("#d9", "#e5", "#c9", "#b5"))]) % 4]
            items.append((loaded[fid], color, f"[{t['category']}] {t['label']} — FMA:{fid}", 0.55 if t["category"] == "근육" else 1.0))
    for cq in [c for c in (a.context or "").split(",") if c.strip()]:
        cf = resolve(cq.strip())
        cm, _ = load_mesh(cf, a.side)
        if cm is not None:
            items.append((cm, "#efe8d2", f"{_label(cf)} FMA:{cf} (위치 참고)", 0.35))
    if items:
        side_kr = {"right": "오른쪽", "left": "왼쪽"}.get(a.side, "양쪽")
        mesh_miss = [t["label"] for t in table if "level" not in t]
        note = (f"{ATTRIB}. 단일 표준 성인 모델(개인차 미반영), 경혈 위치 정보 없음, 단위 mm.\n"
                f"BodyParts3D 메쉬가 없어 그림에 빠진 교재 구조: {', '.join(mesh_miss) if mesh_miss else '없음'}")
        render(items, outdir / f"{code}_mesh3d_render.png", f"{code} 교재 구조 3D 메쉬 — {side_kr} (FMA ↔ BodyParts3D)", a.view, note)
    print(json.dumps({"code": code, "structures": len(table), "with_mesh": sum(1 for t in table if "level" in t),
                      "pairs": len(pairs)}, ensure_ascii=False))
    print(f"[acupoint] → {outdir}")


# ---------------------------------------------------------------- depth (교재 구조 목록 기준 경혈 위치·깊이 추정)
SKIN_FMA = 7163
PUN_MM = 2.3                        # 1푼 = 2.3 mm (스킬 3절 환산)
CAT_COLOR = {"근육": ["#d9534f", "#e57f6c", "#c96b5a", "#b5574a", "#e0907a"], "신경": "#f2c230", "동맥": "#e0302b",
             "정맥": "#2f6fd0", "뼈": "#efe8d2", "피부": "#f0c8a6"}


def _code(s):
    m_ = re.fullmatch(r"([A-Za-z]+)-?(\d+)", s.strip())
    return f"{m_.group(1).upper()}{int(m_.group(2)):02d}" if m_ else s.strip()


def _surface(m, n):
    from scipy.spatial import cKDTree
    pts = np.asarray(m.sample(n))
    return pts, cKDTree(pts)


def _textbook_structures(code, source, side):
    """대응표(교재 xlsx → FMA)에서 source 교재 행만 골라 BodyParts3D 메쉬를 불러온다."""
    rows = [r for r in json.loads(MAPPING_JSON.read_text(encoding="utf-8"))["rows"] if r["code"] == code and r["source"] == source]
    if not rows:
        sys.exit(f"[depth] 대응표에 {code}({source}) 행이 없습니다")
    cov = json.loads((SHARE_BP3D / "acupoint_mesh_coverage.json").read_text(encoding="utf-8")).get(code, {})
    out, missing, seen, cache = [], [], set(), {}
    for r in rows:
        name = f"{r['term_kr']} ({r['variant']})"
        if not r["fma_id"] or r["match"].startswith(("fuzzy", "none")) or "검토" in r["match"]:
            missing.append(f"{name} — FMA 대응 {r['match']}")
            continue
        c = cov.get(str(r["fma_id"])) or {}
        mf = c.get("mesh_fma")
        if mf is None:
            missing.append(f"{name} — BodyParts3D 메쉬 없음")
            continue
        if mf in seen:
            continue
        seen.add(mf)
        if mf not in cache:
            cache[mf] = load_mesh(mf, side)[0]
        if cache[mf] is None:
            missing.append(f"{name} — {side} 측 메쉬 없음")
            continue
        cat = r["category"]
        if cat == "혈관":
            cat = "정맥" if "vein" in (c.get("mesh_label") or r["fma_label"]).lower() else "동맥"
        level = c.get("level")
        if r["match"].startswith("parent"):
            level = f"{level} · 상위 구조 대응"
        out.append({"mesh": cache[mf], "fma": mf, "label": f"{r['term_kr']} · {c.get('mesh_label') or r['fma_label']}",
                    "term": r["term_kr"], "category": cat, "level": level, "match": r["match"]})
    return out, missing


def cmd_depth(a):
    """교재가 경혈 아래에 둔 근육들이 함께 놓이는 피부 영역을 후보 위치로 삼고, 그 영역에서 구조별 깊이(피부→구조 표면 최소 거리)를 잰다."""
    from mesh3d_viewer import build_html
    np.random.seed(0)                # 표면 표본점 고정 → 같은 입력이면 같은 깊이
    code = _code(a.code)
    structs, missing = _textbook_structures(code, a.source, a.side)
    if not structs:
        sys.exit(f"[depth] {code}: 메쉬가 있는 교재 구조가 없습니다. 없는 구조: {missing}")
    anchors = [s for s in structs if s["category"] == "근육"] or structs
    print(f"[depth] {code} ({a.source} 교재) · 메쉬 구조 {len(structs)} · 위치 기준 {', '.join(s['term'] for s in anchors)}")
    # 1) 피부 후보 영역: 기준 근육들의 경계상자(+30 mm) 안 피부 표면 표본점
    skin = load_mesh(SKIN_FMA)[0]
    if skin is None:
        sys.exit("[depth] BodyParts3D 피부(FMA:7163) 메쉬가 없습니다")
    lo = np.min([s["mesh"].bounds[0] for s in anchors], 0) - 30
    hi = np.max([s["mesh"].bounds[1] for s in anchors], 0) + 30
    keep = np.all((skin.triangles_center >= lo) & (skin.triangles_center <= hi), axis=1)
    patch = skin.submesh([np.nonzero(keep)[0]], append=True)
    cand = np.asarray(patch.sample(max(4000, int(patch.area / 4))))           # 약 2 mm 간격
    trees = {id(s): _surface(s["mesh"], 30000)[1] for s in structs}
    dist = {id(s): trees[id(s)].query(cand)[0] for s in structs}
    if a.point:
        p = np.array([float(v) for v in a.point.split(",")])
        near = np.linalg.norm(cand - p, axis=1) <= a.radius
        if not near.any():
            sys.exit(f"[depth] --point 반경 {a.radius} mm 안에 피부 표본점이 없습니다(피부면 위 좌표를 주세요)")
        region, how = near, f"지정 좌표 반경 {a.radius:g} mm 피부 영역"
        best = cand[np.argmin(np.linalg.norm(cand - p, axis=1))]
    else:
        # 기준 근육 모두에 가장 가까운 피부점: score = max_k d_k. 최솟값 + tol 이내를 후보 영역으로 둔다.
        score = np.max([dist[id(s)] for s in anchors], 0)
        region = score <= score.min() + a.tol
        best = cand[np.argmin(score)]
        how = f"기준 근육 모두에 가장 가까운 피부점(최대 거리 최솟값 {score.min():.1f} mm) + {a.tol:g} mm 이내"
    rp = cand[region]
    span = rp.max(0) - rp.min(0) if len(rp) > 1 else np.zeros(3)
    # 2) 구조별 깊이
    rows = []
    for s in structs:
        d = dist[id(s)][region]
        db = float(trees[id(s)].query(best)[0])
        rows.append({"structure": s["label"], "category": s["category"], "fma_id": s["fma"], "mesh_level": s["level"],
                     "depth_mm_at_point": round(db, 1), "depth_pun_at_point": round(db / PUN_MM, 1),
                     "depth_mm_median": round(float(np.median(d)), 1), "depth_mm_p10": round(float(np.percentile(d, 10)), 1),
                     "depth_mm_p90": round(float(np.percentile(d, 90)), 1)})
    rows.sort(key=lambda r: r["depth_mm_at_point"])
    # 문헌 자입 깊이 평균(needle_depth.py, 푼 × 2.3 mm)과 대조: 대표점에서 그 깊이 안에 표면이 있는 구조
    from needle_depth import load as load_needle_depth, summary_line
    lit = load_needle_depth().get(code)
    lit_res = None
    if lit and lit["all"]["n"]:
        mm = lit["all"]["mean_mm"]
        for r in rows:
            r["within_literature_mean"] = r["depth_mm_at_point"] <= mm
        lit_res = {"summary": summary_line(lit), "mean_pun": lit["all"]["mean_pun"], "mean_mm": mm,
                   "classic_mm": lit["classic"]["mean_mm"], "modern_mm": lit["modern"]["mean_mm"],
                   "modern_range_mm": lit["modern"].get("range_mm"), "forbidden_sources": lit["forbidden_sources"],
                   "reached_at_point": [r["structure"] for r in rows if r["within_literature_mean"]]}
    elif lit:
        lit_res = {"summary": summary_line(lit), "mean_mm": None, "forbidden_sources": lit["forbidden_sources"]}
    res = {"code": code, "source": a.source, "side": a.side, "method": how, "candidate_points": int(region.sum()),
           "candidate_extent_mm": span.round(1).tolist(), "point_mm": best.round(1).tolist(), "depths": rows,
           "literature_depth": lit_res, "missing_structures": missing, "attribution": ATTRIB,
           "caveat": ("BodyParts3D 단일 표준 성인 모델(개인차·자세·피하지방 미반영). 경혈 위치는 교재 구조 목록에서 정한 후보 영역이며 "
                      "정위 실측(B2)이 아니다. 깊이는 피부점에서 구조 표면까지의 최소 직선거리로, 자침 방향 깊이와 다를 수 있다.")}
    outdir = Path(a.out) if a.out else data_dir() / "mesh_results"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{code}_depth.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    side_kr = {"right": "오른쪽", "left": "왼쪽"}[a.side]
    md = [f"### {code} 경혈 위치 기준 깊이 추정 ({a.source} 교재 구조 · BodyParts3D, {side_kr})", "",
          f"- 위치 기준: {how} · 후보 피부점 {int(region.sum()):,}개, 후보 영역 크기(X·Y·Z) {' × '.join(f'{v:.0f}' for v in span)} mm",
          "- 깊이 = 피부점 → 구조 표면 최소 직선거리(mm). 푼 = mm ÷ 2.3"]
    if lit_res:
        md.append(f"- 문헌 자입 깊이(침구문헌별 자침깊이 정리, 1푼 = 2.3 mm): {lit_res['summary']}")
    if lit_res and lit_res.get("mean_mm"):
        md.append(f"- 대표점에서 문헌 평균 깊이({lit_res['mean_mm']} mm) 안에 표면이 있는 구조: "
                  + (", ".join(lit_res["reached_at_point"]) or "없음"))
    md += ["", "| 구조 | 구분 | FMA | 대표점 깊이 mm (푼) | 후보 영역 중앙값 mm (10–90%) | 문헌 평균 깊이 이내 |",
           "| :--- | :--- | :--- | ---: | ---: | :---: |"]
    md += [f"| {r['structure']} | {r['category']} | FMA:{r['fma_id']} | {r['depth_mm_at_point']} ({r['depth_pun_at_point']}) | "
           f"{r['depth_mm_median']} ({r['depth_mm_p10']}–{r['depth_mm_p90']}) | "
           f"{'예' if r.get('within_literature_mean') else ('아니오' if 'within_literature_mean' in r else '–')} |" for r in rows]
    if missing:
        md += ["", "메쉬가 없어 깊이를 재지 못한 교재 구조: " + "; ".join(missing)]
    md += ["", f"> {res['caveat']} {ATTRIB}"]
    (outdir / f"{code}_depth.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    # 3) 상호작용 3D 모델: 교재 구조 + 피부 조각 + 후보 영역 대표점과 깊이 선
    items, k = [], 0
    for s in structs:
        col = CAT_COLOR.get(s["category"], "#999999")
        if isinstance(col, list):
            col, k = col[k % len(col)], k + 1
        items.append({**s, "color": col, "opacity": 0.55 if s["category"] == "근육" else 1.0})
    for cq in [c for c in (a.context or "").split(",") if c.strip()]:
        cf = resolve(cq.strip())
        cm, _ = load_mesh(cf, a.side)
        if cm is not None:
            items.append({"mesh": cm, "fma": cf, "label": _label(cf), "category": "뼈", "color": CAT_COLOR["뼈"], "opacity": 0.9, "role": "context"})
    items.append({"mesh": patch, "fma": SKIN_FMA, "label": "피부(후보 영역 주변)", "category": "피부", "color": CAT_COLOR["피부"],
                  "opacity": 0.18, "role": "context"})
    dlist = [{"label": s["label"], "mm": float(trees[id(s)].query(best)[0]), "closest": trees[id(s)].data[trees[id(s)].query(best)[1]].tolist()}
             for s in structs]
    dlist.sort(key=lambda d: d["mm"])
    notes = [f"{ATTRIB}.", res["caveat"], f"위치 기준: {how}. 후보 영역 크기(X·Y·Z) {' × '.join(f'{v:.0f}' for v in span)} mm.",
             (f"문헌 자입 깊이: {lit_res['summary']}. 분홍 구는 대표점에서 문헌 평균 깊이까지의 직선거리 반경입니다." if lit_res else ""),
             ("메쉬가 없어 빠진 교재 구조: " + "; ".join(missing)) if missing else ""]
    reach = {"mm": lit_res["mean_mm"], "label": f"문헌 평균 {lit_res['mean_pun']}푼 = {lit_res['mean_mm']} mm"} if lit_res and lit_res.get("mean_mm") else None
    html_out = build_html(items, outdir / f"{code}_mesh3d_model.html", f"{code} 경혈 해부 3D 모델 · {a.source} 교재 구조",
                          f"BodyParts3D 4.0 · FMA 대응 · {side_kr} · 단위 mm · 분홍 점 = 교재 구조로 추정한 대표 피부점", notes,
                          point=best, distances=dlist, reach=reach)
    if lit_res:
        print(f"[depth] 문헌: {lit_res['summary']}")
    for r in rows:
        print(f"  {r['depth_mm_at_point']:6.1f} mm ({r['depth_pun_at_point']:4.1f}푼)  중앙 {r['depth_mm_median']:5.1f} "
              f"[{r['depth_mm_p10']}–{r['depth_mm_p90']}]  {r['category']} {r['structure']}")
    print(f"[depth] 후보 영역 {int(region.sum())}점 · 크기 {span.round(0).tolist()} mm · 대표점 {best.round(1).tolist()}")
    print(f"[depth] → {outdir / f'{code}_depth.md'} · {html_out}")
    return res


def cmd_oap(a):
    if a.action == "list":
        for k, v in OAP_ATLASES.items():
            print(f"{k:22} {v:10} {'받음' if (OAP_DIR / k).exists() else '-'}")
        return
    import pyvista as pv
    sts = oap_structures(a.atlas)
    hit = [s for s in sts if norm(a.structure) in norm(s["name"])]
    if not hit:
        sys.exit(f"[oap] '{a.structure}' 없음. 예: {[s['name'] for s in sts[:8]]}")
    for s in hit[:5]:
        m = pv.read(str(OAP_DIR / a.atlas / s["file"])).extract_surface(algorithm="dataset_surface").triangulate()
        import trimesh
        tm = trimesh.Trimesh(m.points, m.faces.reshape(-1, 4)[:, 1:], process=False)
        print(json.dumps({"atlas": a.atlas, "structure": s["name"], **metrics(tm)}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description="FMA 기반 3D 메쉬(BodyParts3D·OAP) 기하·공간 분석")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("fetch"); s.add_argument("what", choices=["bp3d", "oap"]); s.add_argument("atlas", nargs="?")
    sub.add_parser("index")
    for name in ("measure", "render"):
        s = sub.add_parser(name); s.add_argument("targets", nargs="+"); s.add_argument("--side", choices=["left", "right"])
        if name == "measure":
            s.add_argument("--tree", choices=["partof", "isa"])
        else:
            s.add_argument("--out", required=True); s.add_argument("--title"); s.add_argument("--view", default="xz", choices=["xz", "yz", "xy", "iso"])
    s = sub.add_parser("distance"); s.add_argument("a"); s.add_argument("b"); s.add_argument("--side", choices=["left", "right"])
    s = sub.add_parser("acupoint"); s.add_argument("code"); s.add_argument("--side", choices=["left", "right"], default="right")
    s.add_argument("--out"); s.add_argument("--view", default="iso", choices=["xz", "yz", "xy", "iso"])
    s.add_argument("--context", help="위치 참고용 주변 구조 FMA ID/이름, 쉼표 구분 (예: 24476,24479 = 정강뼈·종아리뼈)")
    s = sub.add_parser("depth", help="교재 구조 목록으로 경혈 위치(피부 후보 영역)를 정하고 구조별 깊이를 잰다 + 3D 모델 HTML")
    s.add_argument("code"); s.add_argument("--side", choices=["left", "right"], default="right")
    s.add_argument("--source", default="김재효", choices=["김재효", "공통교재"], help="대응표의 교재 (기본: 김재효 수업 데이터셋)")
    s.add_argument("--point", help="경혈 추정 피부 좌표 x,y,z (BodyParts3D mm). 주면 이 점 주변으로 위치를 고정")
    s.add_argument("--radius", type=float, default=5.0, help="--point 주변 후보 반경 mm (기본 5)")
    s.add_argument("--tol", type=float, default=5.0, help="후보 영역 허용 폭 mm (기본 5)")
    s.add_argument("--context", help="위치 참고용 주변 구조 FMA ID/이름, 쉼표 구분 (예: 24476,24479 = 정강뼈·종아리뼈)")
    s.add_argument("--out")
    s = sub.add_parser("oap"); s.add_argument("action", choices=["list", "measure"]); s.add_argument("atlas", nargs="?"); s.add_argument("structure", nargs="?")
    a = ap.parse_args()
    {"fetch": cmd_fetch, "index": cmd_index, "measure": cmd_measure, "render": cmd_render, "distance": cmd_distance,
     "acupoint": cmd_acupoint, "depth": cmd_depth, "oap": cmd_oap}[a.cmd](a)


if __name__ == "__main__":
    main()

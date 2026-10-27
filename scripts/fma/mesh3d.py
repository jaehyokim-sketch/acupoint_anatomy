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


def render(items, out, title="", view="xz", note=""):
    """pyvista로 3D 장면만 찍고(오프스크린), 범례·제목·주석은 matplotlib으로 얹는다(한글 글꼴 사용)."""
    import pyvista as pv
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
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
    s = sub.add_parser("oap"); s.add_argument("action", choices=["list", "measure"]); s.add_argument("atlas", nargs="?"); s.add_argument("structure", nargs="?")
    a = ap.parse_args()
    {"fetch": cmd_fetch, "index": cmd_index, "measure": cmd_measure, "render": cmd_render, "distance": cmd_distance,
     "acupoint": cmd_acupoint, "oap": cmd_oap}[a.cmd](a)


if __name__ == "__main__":
    main()

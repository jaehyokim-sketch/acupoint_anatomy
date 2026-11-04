# -*- coding: utf-8 -*-
"""
smplx_skin.py — SMPL-X 체형 피부를 BodyParts3D 해부 메쉬의 골격에 맞춰 등록한다(해부 분석·3D 이미지용 피부면).

왜 골격 기준인가: BodyParts3D 피부(FMA:7163)는 생체보다 피하가 두껍다(ST36 정강뼈 앞모서리 위 8.7 mm, WHO점 피부–앞정강동맥
  37.7 mm vs 초음파 24 mm). SMPL-X 피부를 BodyParts3D 피부에 맞추면 이 편향을 그대로 옮긴다. 그래서 BodyParts3D 뼈에서 구한
  관절 중심(엉덩·무릎·발목·어깨·팔꿈치·손목)에 SMPL-X 관절이 오도록 자세·위치·크기를 맞추고, 피부 겉모양은 약하게만 쓴다.
  같은 골격 위에 체형(키·BMI)만 바꾼 피부를 얹어 체형별 피부→구조 깊이를 비교할 수 있다.

자료: SMPL-X v1.1 모델(SMPLX_NEUTRAL/MALE/FEMALE.npz) — SMPL-X Model License(비상업 연구·교육, 재배포 금지).
  PC마다 사용자가 등록·동의 후 받아 %LOCALAPPDATA%\\acupoint_smplx\\models 에 둔다(환경변수 SMPLX_MODEL_DIR).
  등록한 피부 메쉬는 SMPL-X Body License(CC BY 4.0)로 공유할 수 있다 → 02_Master_Datasets/FMA/SMPLX/ (편집 PC가 쓴다).

사용 (어느 폴더에서나):
  python smplx_skin.py check
  python smplx_skin.py register --name male_bmi24 --gender male --bmi 24          # 키는 기본 BodyParts3D 신장(1.719 m)
  python smplx_skin.py register --name male_bmi30 --gender male --bmi 30
  python smplx_skin.py list
그 뒤: python mesh3d.py depth ST36 --skin smplx:male_bmi24 …   ·   figures/ST36_mesh3d_targets.py --skin smplx:male_bmi24
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fma_common import ROOT, data_dir   # noqa: E402

MODEL_DIR = Path(os.environ.get("SMPLX_MODEL_DIR") or Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "acupoint_smplx" / "models")
BODY_DIR = data_dir() / "smplx_bodies"
SHARE = ROOT / "02_Master_Datasets" / "FMA" / "SMPLX"
ATTRIB = ("Body surface generated with SMPL-X (Pavlakos et al., CVPR 2019), © Max Planck Institute for Intelligent Systems, "
          "SMPL-X Body License CC BY 4.0 (https://smpl-x.is.tue.mpg.de/bodylicense.html). Changes: shape set to target stature/BMI, "
          "posed and registered to BodyParts3D 4.0 joint centres")
# SMPL-X 관절 번호 (왼쪽, 오른쪽). SMPL-X의 +X = 몸의 왼쪽 = BodyParts3D +X
JOINTS = {"hip": (1, 2), "knee": (4, 5), "ankle": (7, 8), "shoulder": (16, 17), "elbow": (18, 19), "wrist": (20, 21)}
FREE = [1, 2, 3, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]   # 최적화하는 관절 회전
BONES = {"femur": 9611, "tibia": 24476, "fibula": 24479, "humerus": 13303, "radius": 23463, "ulna": 23466}


# ---------------------------------------------------------------- SMPL-X (numpy)
def load_model(gender):
    hits = list(MODEL_DIR.rglob(f"SMPLX_{gender.upper()}.npz")) if MODEL_DIR.exists() else []
    if not hits:
        sys.exit(f"[smplx] 모델이 없습니다: {MODEL_DIR}\\SMPLX_{gender.upper()}.npz — smpl-x.is.tue.mpg.de 등록 후 "
                 "'SMPL-X v1.1 (NPZ+PKL)'을 받아 .npz를 이 폴더에 두세요")
    d = np.load(hits[0], allow_pickle=True)
    m = {k: np.asarray(d[k]) for k in ("v_template", "f", "shapedirs", "posedirs", "J_regressor", "weights", "kintree_table")}
    m["f"] = m["f"].astype(np.int64)
    m["parents"] = m["kintree_table"][0].astype(np.int64)
    m["parents"][0] = -1
    return m


def rodrigues(r):
    th = np.linalg.norm(r)
    if th < 1e-9:
        return np.eye(3)
    k = r / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


def shaped(m, betas):
    v = m["v_template"] + np.einsum("vck,k->vc", m["shapedirs"][:, :, :len(betas)], betas)
    return v, m["J_regressor"] @ v


def pose_lbs(m, v, J, pose, correctives=True):
    nj = J.shape[0]
    R = np.stack([rodrigues(p) for p in pose])
    if correctives:
        v = v + np.einsum("vck,k->vc", m["posedirs"], (R[1:] - np.eye(3)).reshape(-1))
    G = np.zeros((nj, 4, 4))
    for i in range(nj):
        T = np.eye(4)
        T[:3, :3] = R[i]
        p = m["parents"][i]
        T[:3, 3] = J[i] - (J[p] if p >= 0 else 0)
        G[i] = T if p < 0 else G[p] @ T
    Jp = G[:, :3, 3].copy()
    A = G.copy()
    A[:, :3, 3] -= np.einsum("jab,jb->ja", G[:, :3, :3], J)
    W = np.einsum("vj,jab->vab", m["weights"], A)
    return np.einsum("vab,vb->va", W[:, :3, :3], v) + W[:, :3, 3], Jp


def stature(v):
    return float(v[:, 1].max() - v[:, 1].min())


def mass(v, f, density=1000.0):
    import trimesh
    return float(abs(trimesh.Trimesh(v, f, process=False).volume) * density)


# 마디 길이(m): SMPL-X 관절 쌍. 엉덩 너비는 SMPL 엉덩관절이 해부학적 넙다리뼈머리 중심보다 안쪽에 정의되므로 약하게만 맞춘다
SEGMENTS = {"thigh": ((1, 4), (2, 5), 1.0), "shank": ((4, 7), (5, 8), 1.0), "upper_arm": ((16, 18), (17, 19), 1.0),
            "forearm": ((18, 20), (19, 21), 1.0), "hip_width": ((1, 2), None, 0.2), "shoulder_width": ((16, 17), None, 0.5)}


def seg_lengths(J):
    out = {}
    for k, (a, b, _) in SEGMENTS.items():
        ls = [np.linalg.norm(J[a[0]] - J[a[1]])] + ([np.linalg.norm(J[b[0]] - J[b[1]])] if b else [])
        out[k] = float(np.mean(ls))
    return out


def bp3d_segments(joints):
    """BodyParts3D 관절 중심에서 마디 길이(m)"""
    L = lambda a, b: float(np.linalg.norm(joints[a] - joints[b])) / 1000.0
    avg = lambda k1, k2: (L((k1, "left"), (k2, "left")) + L((k1, "right"), (k2, "right"))) / 2
    return {"thigh": avg("hip", "knee"), "shank": avg("knee", "ankle"), "upper_arm": avg("shoulder", "elbow"),
            "forearm": avg("elbow", "wrist"), "hip_width": L(("hip", "left"), ("hip", "right")),
            "shoulder_width": L(("shoulder", "left"), ("shoulder", "right"))}


def fit_betas(m, height, weight, nb=16, reg=0.3, segments=None):
    """키·체중(+선택: BodyParts3D 마디 길이)에 맞춰 앞쪽 betas nb개를 찾는다"""
    from scipy.optimize import minimize
    zero = np.zeros((m["J_regressor"].shape[0], 3))

    def loss(b):
        v, J = shaped(m, b)
        e = ((stature(pose_lbs(m, v, J, zero, False)[0]) - height) / 0.005) ** 2
        if weight is not None:
            e += ((mass(v, m["f"]) - weight) / 0.5) ** 2
        if segments:
            sl = seg_lengths(J)
            e += sum(SEGMENTS[k][2] * ((sl[k] - segments[k]) / 0.005) ** 2 for k in segments)
        return e + reg * float(b @ b)
    return minimize(loss, np.zeros(nb), method="Powell", options={"maxiter": 8000, "xtol": 1e-3, "ftol": 1e-4}).x


# ---------------------------------------------------------------- BodyParts3D 관절 중심
def _sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]
    c = np.linalg.lstsq(A, (P ** 2).sum(1), rcond=None)[0]
    return c[:3]


def _end(v, frac, top):
    z = v[:, 2]
    q = np.quantile(z, 1 - frac if top else frac)
    return v[z >= q] if top else v[z <= q]


def bp3d_joints():
    """BodyParts3D 뼈 메쉬에서 관절 중심(mm, BodyParts3D 좌표)을 구한다. 반환: {('hip','left'): xyz, …}"""
    import mesh3d as M
    out = {}
    for side, sg in (("left", 1), ("right", -1)):
        b = {k: M.load_mesh(f, side)[0].vertices for k, f in BONES.items()}
        head = _end(b["femur"], 0.12, True)
        head = head[sg * head[:, 0] <= np.median(sg * head[:, 0])]               # 넙다리뼈머리 = 위끝의 안쪽 절반
        out[("hip", side)] = _sphere(head)
        out[("knee", side)] = (_end(b["femur"], 0.03, False).mean(0) + _end(b["tibia"], 0.03, True).mean(0)) / 2
        out[("ankle", side)] = (_end(b["tibia"], 0.02, False).mean(0) + _end(b["fibula"], 0.02, False).mean(0)) / 2
        hh = _end(b["humerus"], 0.10, True)
        hh = hh[sg * hh[:, 0] <= np.median(sg * hh[:, 0])]                        # 위팔뼈머리 = 위끝의 안쪽 절반
        out[("shoulder", side)] = _sphere(hh)
        out[("elbow", side)] = (_end(b["humerus"], 0.04, False).mean(0) + _end(b["ulna"], 0.04, True).mean(0)) / 2
        out[("wrist", side)] = (_end(b["radius"], 0.03, False).mean(0) + _end(b["ulna"], 0.03, False).mean(0)) / 2
    return out


# ---------------------------------------------------------------- 등록
def to_bp3d(v, rg, t, s):
    """SMPL-X(m, +Y 위, +Z 앞) → 전역 회전 rg → BodyParts3D(mm, +X 왼쪽, −Y 앞, +Z 위) × s + t"""
    w = v @ rodrigues(rg).T
    return np.c_[w[:, 0], -w[:, 2], w[:, 1]] * 1000.0 * s + t


def register(m, betas, joints, skin_tree, verbose=True):
    from scipy.optimize import least_squares
    v0, J0 = shaped(m, betas)
    nj = J0.shape[0]
    tgt = np.array([joints[(k, sd)] for k in JOINTS for sd in ("left", "right")])
    jid = [JOINTS[k][0 if sd == "left" else 1] for k in JOINTS for sd in ("left", "right")]
    rng = np.random.default_rng(0)
    sub = rng.choice(len(v0), 1500, replace=False)

    def unpack(x):
        pose = np.zeros((nj, 3))
        pose[FREE] = x[7:].reshape(-1, 3)
        return x[:3], x[3:6], np.exp(x[6]), pose

    def resid(x):
        rg, t, s, pose = unpack(x)
        v, Jp = pose_lbs(m, v0, J0, pose, False)
        jr = (to_bp3d(Jp[jid], rg, t, s) - tgt).ravel()
        # 피부 잔차는 25 mm에서 잘라(체형 차이로 생기는 큰 간격이 관절 정합을 끌지 않게) 약하게 둔다
        d = np.minimum(skin_tree.query(to_bp3d(v[sub], rg, t, s))[0], 25.0)
        return np.r_[3.0 * jr, 0.15 * d, 5.0 * x[7:]]

    x0 = np.zeros(7 + 3 * len(FREE))
    x0[7 + 3 * FREE.index(16) + 2] = -1.3                                       # 팔을 내린 상태에서 시작
    x0[7 + 3 * FREE.index(17) + 2] = 1.3
    _, J00 = pose_lbs(m, v0, J0, unpack(x0)[3], False)
    pelvis_t = np.mean([joints[("hip", "left")], joints[("hip", "right")]], 0)
    x0[3:6] = pelvis_t - to_bp3d(J00[[1, 2]].mean(0, keepdims=True), np.zeros(3), np.zeros(3), 1.0)[0]
    r = least_squares(resid, x0, loss="linear", x_scale="jac", max_nfev=120 * len(x0), verbose=0)
    rg, t, s, pose = unpack(r.x)
    v, Jp = pose_lbs(m, v0, J0, pose, True)
    vb, Jb = to_bp3d(v, rg, t, s), to_bp3d(Jp[jid], rg, t, s)
    err = {f"{k}_{sd}": round(float(np.linalg.norm(Jb[i] - tgt[i])), 1) for i, (k, sd) in enumerate((k, sd) for k in JOINTS for sd in ("left", "right"))}
    return vb, {"global_rot": r.x[:3].round(5).tolist(), "translation_mm": t.round(2).tolist(), "scale": round(float(s), 4),
                "pose": pose.round(5).tolist(), "joint_error_mm": err, "cost": float(r.cost), "nfev": int(r.nfev)}


# ---------------------------------------------------------------- 명령
def cmd_check(a):
    print(f"[smplx] 모델 폴더: {MODEL_DIR}")
    for g in ("neutral", "male", "female"):
        ok = bool(list(MODEL_DIR.rglob(f"SMPLX_{g.upper()}.npz"))) if MODEL_DIR.exists() else False
        print(f"  {g:7} {'있음' if ok else '없음'}")
    print(f"[smplx] 등록 피부: {BODY_DIR} · 공유: {SHARE}")
    for n in body_names():
        print(f"  {n}")


def body_names():
    names = set()
    for d in (BODY_DIR, SHARE):
        if d.exists():
            names |= {p.stem for p in d.glob("*.obj")}
    return sorted(names)


def cmd_register(a):
    import trimesh
    from scipy.spatial import cKDTree
    import mesh3d as M
    np.random.seed(0)
    m = load_model(a.gender)
    skin = M.load_mesh(M.SKIN_FMA)[0]
    h_bp = float(np.ptp(skin.vertices[:, 2])) / 1000.0
    height = a.height or h_bp
    joints = bp3d_joints()
    segs = bp3d_segments(joints)
    if a.betas:
        betas, how = np.array([float(x) for x in a.betas.split(",")]), "betas 직접 지정"
    else:
        weight = a.weight if a.weight else (a.bmi * height ** 2 if a.bmi else None)
        betas = fit_betas(m, height, weight, segments=segs)
        how = f"키 {height:.3f} m" + (f"·체중 {weight:.1f} kg" if weight else "") + "·BodyParts3D 마디 길이에 맞춘 betas 16개"
    v0, J0 = shaped(m, betas)
    vz, _ = pose_lbs(m, v0, J0, np.zeros((J0.shape[0], 3)), False)
    h, w = stature(vz), mass(vz, m["f"])
    print(f"[smplx] {a.name}: {how} → 키 {h:.3f} m · 체중 {w:.1f} kg · BMI {w / h ** 2:.1f}")
    sl = seg_lengths(J0)
    seg_cmp = {k: [round(sl[k] * 1000, 1), round(segs[k] * 1000, 1)] for k in segs}
    print(f"[smplx] 마디 길이 mm (SMPL-X, BodyParts3D): {seg_cmp}")
    tree = cKDTree(np.asarray(skin.sample(150000)))
    vb, info = register(m, betas, joints, tree)
    d = tree.query(vb)[0]
    body = trimesh.Trimesh(vb, m["f"], process=False)
    meta = {"name": a.name, "generated_at": datetime.now().isoformat(timespec="seconds"), "gender": a.gender, "shape_method": how,
            "betas": [round(float(b), 5) for b in betas], "stature_m": round(h, 4), "mass_kg": round(w, 2), "bmi": round(w / h ** 2, 2),
            "bp3d_stature_m": round(h_bp, 4), "segment_mm_smplx_vs_bp3d": seg_cmp, **info,
            "skin_offset_vs_bp3d_mm": {"median": round(float(np.median(d)), 1), "p90": round(float(np.percentile(d, 90)), 1)},
            "frame": "BodyParts3D 4.0 (mm, +X left, -Y anterior, +Z up)", "attribution": ATTRIB,
            "caveat": "골격(관절 중심)에 맞춘 통계 체형 피부. 근육·지방 층은 BodyParts3D 그대로이므로 체형 차이는 피하층 두께 차이로만 나타나는 근사다"}
    for d_ in [BODY_DIR] + ([SHARE] if a.share else []):
        d_.mkdir(parents=True, exist_ok=True)
        body.export(d_ / f"{a.name}.obj")
        (d_ / f"{a.name}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[smplx] 관절 오차(mm): {info['joint_error_mm']}")
    print(f"[smplx] 크기 {info['scale']} · BodyParts3D 피부와의 거리 중앙 {meta['skin_offset_vs_bp3d_mm']['median']} mm · 90% {meta['skin_offset_vs_bp3d_mm']['p90']} mm")
    print(f"[smplx] → {BODY_DIR / (a.name + '.obj')}" + (f" · 공유 {SHARE}" if a.share else ""))


def load_body(name):
    """등록 피부 메쉬(trimesh, BodyParts3D 좌표) — 이 PC 사본 우선, 없으면 Drive 공유본"""
    import trimesh
    for d in (BODY_DIR, SHARE):
        p = d / f"{name}.obj"
        if p.exists():
            meta = json.loads((d / f"{name}.json").read_text(encoding="utf-8")) if (d / f"{name}.json").exists() else {}
            return trimesh.load(p, force="mesh", process=False), meta
    sys.exit(f"[smplx] 등록 피부 '{name}'이 없습니다. 먼저: smplx_skin.py register --name {name} …  (있는 것: {body_names()})")


def main():
    ap = argparse.ArgumentParser(description="SMPL-X 체형 피부를 BodyParts3D 골격에 등록")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("list")
    s = sub.add_parser("register")
    s.add_argument("--name", required=True)
    s.add_argument("--gender", default="male", choices=["neutral", "male", "female"])
    s.add_argument("--height", type=float, help="키(m). 기본 = BodyParts3D 피부 신장")
    s.add_argument("--weight", type=float)
    s.add_argument("--bmi", type=float)
    s.add_argument("--betas")
    s.add_argument("--no-share", dest="share", action="store_false", help="Drive 공유 폴더에 쓰지 않음(미러 PC)")
    a = ap.parse_args()
    if a.cmd == "list":
        print("\n".join(body_names()) or "(없음)")
        return
    {"check": cmd_check, "register": cmd_register}[a.cmd](a)


if __name__ == "__main__":
    main()

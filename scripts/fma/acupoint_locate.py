#!/usr/bin/env python3
"""BodyParts3D 4.0 오른쪽(정중선 경혈은 정중선) 모델에서 골도분촌·뼈 기준점으로 경혈 피부 좌표를 정한다.

사용:
  python acupoint_locate.py <코드> [<코드> …]        # 좌표·정위 근거 출력
  python acupoint_locate.py --json <코드> …           # JSON 출력
  mesh3d.py depth <코드> --point "$(python acupoint_locate.py --xyz <코드>)"

좌표계: BodyParts3D mm, +X = 왼쪽(오른쪽 구조는 X < 0), −Y = 앞, +Z = 위. 모델은 해부학적 자세(팔을 내리고 손바닥이 앞).
정위는 WHO 표준 경혈 위치(2008)의 골도분촌 기준을 뼈 메쉬 기준점(관절선·뼈끝·돌기)으로 근사한 것이다.
피부신경·힘줄·피부 주름은 메쉬가 없으므로 뼈 기준점 + 방향으로 대신한다. 규범 해부 형상 참고(B1 보조)이며 경혈 실측(B2)이 아니다.
"""
import json
import sys
from functools import lru_cache

import numpy as np

import mesh3d as M

R = "right"
NOTE = []                                                         # 정위 중 근사·예외 기록(locate 결과 note)


@lru_cache(None)
def bone(fid, side=R):
    m, _ = M.load_mesh(fid, side)
    if m is None:
        sys.exit(f"[locate] FMA:{fid} 메쉬 없음")
    return m


@lru_cache(None)
def skin():
    return M.load_mesh(M.SKIN_FMA)[0]


def V(fid, side=R):
    return np.asarray(bone(fid, side).vertices)


def extreme(fid, axis, sign, side=R, sel=None):
    v = V(fid, side)
    if sel is not None:
        v = v[sel(v)]
    return v[np.argmax(sign * v[:, axis])]


def center_at(fid, z, side=R, band=3.0):
    """뼈 메쉬를 높이 z에서 자른 단면 윤곽의 중심(단면이 없으면 ±band 정점 평균)"""
    sec = bone(fid, side).section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if sec is not None and len(sec.vertices):
        return np.asarray(sec.vertices).mean(0)
    v = V(fid, side)
    s = v[np.abs(v[:, 2] - z) <= band]
    if len(s) < 3:
        sys.exit(f"[locate] FMA:{fid} z={z:.1f} 단면이 없습니다")
    return s.mean(0)


def skin_ray(origin, direction):
    """origin(몸 안)에서 direction으로 쏜 광선이 피부를 나가는 점. BodyParts3D 피부는 두 겹(약 2 mm)이라 첫 교차 묶음의 바깥면을 쓴다"""
    d = np.asarray(direction, float)
    d /= np.linalg.norm(d)
    o = np.asarray(origin, float)
    loc, _, _ = skin().ray.intersects_location(o[None], d[None])
    if not len(loc):
        sys.exit(f"[locate] 광선이 피부와 만나지 않습니다: {o.round(1)} → {d.round(2)}")
    t = np.sort((loc - o) @ d)
    t = t[t > 0]
    first = t[t <= t[0] + 6.0]
    return o + d * first.max()


def skin_nearest(p):
    from scipy.spatial import cKDTree
    pts = _skin_pts()
    return pts[cKDTree(pts).query(np.asarray(p))[1]]


@lru_cache(None)
def _skin_pts():
    import trimesh
    return np.asarray(trimesh.sample.sample_surface(skin(), 400000, seed=0)[0])


# ---------------------------------------------------------------- 기준점·골도
def leg():
    tib, fib = V(24476), V(24479)
    z_knee = float(tib[tib[:, 0] < np.median(tib[:, 0])][:, 2].max())       # 정강뼈 가쪽관절융기 위끝(슬관절선)
    z_lm = float(fib[:, 2].min())                                            # 가쪽복사 끝
    mm = tib[tib[:, 2] < tib[:, 2].min() + 15]
    medial_mall = mm[np.argmax(mm[:, 0])]                                    # 안쪽복사(오른쪽 → X 최대 쪽)
    z_mm = float(tib[(tib[:, 0] > medial_mall[0] - 8)][:, 2].min())
    return {"z_knee": z_knee, "z_lat_mall": z_lm, "z_med_mall": z_mm, "medial_mall": medial_mall,
            "cun": (z_knee - z_lm) / 16, "basis": "슬관절선(정강뼈 가쪽관절융기 위끝)~가쪽복사 끝 = 16寸"}


def forearm():
    rad, hum = V(23463), V(13303)
    z_w = float(rad[:, 2].min())                     # 노뼈 붓돌기 끝 ≈ 손목 앞 가로주름 높이
    z_e = float(hum[:, 2].min())                     # 위팔뼈 아래끝(도르래) ≈ 팔오금 가로주름 높이
    return {"z_wrist": z_w, "z_elbow": z_e, "cun": (z_e - z_w) / 12,
            "basis": "팔오금 가로주름(위팔뼈 아래끝 높이)~손목 앞 가로주름(노뼈 붓돌기 끝 높이) = 12寸"}


def _fold_z(fid, side=None):
    """겨드랑이 주름 높이: 근육(큰가슴근 = 앞주름, 큰원근 = 뒤주름)의 가쪽 30 mm 부분의 아래끝"""
    v = V(fid, side)
    lat = v[v[:, 0] < v[:, 0].min() + 30]
    return float(lat[:, 2].min())


def upper_arm():
    hum = V(13303)
    z_e = float(hum[:, 2].min())
    z_ax = _fold_z(13373)                                          # 오른쪽 큰가슴근
    z_post = _fold_z(32549, R)                                      # 오른쪽 큰원근
    return {"z_axilla": z_ax, "z_post_axilla": z_post, "z_elbow": z_e, "cun": (z_ax - z_e) / 9,
            "basis": "겨드랑이 앞주름(큰가슴근 가쪽 아래끝)~팔오금 가로주름(위팔뼈 아래끝) = 9寸"}


def limb_point(fid, z, direction_xy, side=R, extra=None):
    c = center_at(fid, z, side)
    if extra is not None:
        c = (c + center_at(extra, z, side)) / 2
    d = np.array([direction_xy[0], direction_xy[1], 0.0])
    return skin_ray(c, d)


# ---------------------------------------------------------------- 경혈별 정위
def loc_PC06():
    f = forearm()
    z = f["z_wrist"] + 2 * f["cun"]
    p = limb_point(23463, z, (0.0, -1.0), extra=23466)
    return p, f, f"손목 앞 가로주름 위 2寸(z = {z:.1f}), 노뼈·자뼈 단면 중심에서 앞쪽 정중(긴손바닥근힘줄–노쪽손목굽힘근힘줄 사이 근사)"


def loc_LU09():
    f = forearm()
    z = f["z_wrist"] + 4.0
    p = limb_point(23463, z, (-0.35, -1.0))
    return p, f, f"손목 앞 가로주름(노뼈 붓돌기 끝 + 4 mm, z = {z:.1f}) 노쪽, 노뼈 단면 중심에서 앞·약간 가쪽(노동맥 박동처 근사)"


def loc_LU06():
    f = forearm()
    z = f["z_wrist"] + 7 * f["cun"]
    p = limb_point(23463, z, (-0.35, -1.0))
    return p, f, f"태연(손목 앞 가로주름) 위 7寸(z = {z:.1f}), 척택–태연 선 위: 노뼈 단면 중심에서 앞·약간 가쪽"


def loc_LI04():
    mc = V(23900)
    zc = float((mc[:, 2].max() + mc[:, 2].min()) / 2)
    c = center_at(23900, zc)
    p = skin_ray(c, (-0.75, 0.66, 0.0))
    return p, {"cun": None, "basis": "둘째 손허리뼈 길이 중점"}, f"손등, 둘째 손허리뼈 노쪽 중점(z = {zc:.1f}): 뼈 단면 중심에서 가쪽·손등 쪽"


def loc_PC09():
    dp = V(23947)
    tip = dp[np.argmin(dp[:, 2])]
    p = skin_ray(tip + np.array([0, 0, 3.0]), (0.0, 0.0, -1.0))
    return p, {"cun": None, "basis": "가운데손가락 끝마디뼈 끝"}, "가운데손가락 끝 중앙: 끝마디뼈 끝에서 손가락 축 방향(아래)"


def _lu_upper(n):
    f = upper_arm()
    z = f["z_axilla"] - n * f["cun"]
    p = limb_point(13303, z, (-0.45, -1.0))
    return p, f, f"겨드랑이 앞주름 아래 {n}寸(z = {z:.1f}), 위팔두갈래근 가쪽 모서리: 위팔뼈 단면 중심에서 앞·가쪽"


def loc_LU03():
    return _lu_upper(3)


def loc_LU04():
    return _lu_upper(4)


def loc_SP06():
    g = leg()
    z = g["z_med_mall"] + 3 * g["cun"]
    p = limb_point(24476, z, (1.0, 0.45))
    return p, g, f"안쪽복사 끝 위 3寸(z = {z:.1f}), 정강뼈 안쪽 모서리 뒤: 정강뼈 단면 중심에서 안쪽·약간 뒤쪽"


def loc_GB39():
    g = leg()
    z = g["z_lat_mall"] + 3 * g["cun"]
    p = limb_point(24479, z, (-0.55, -1.0))
    return p, g, f"가쪽복사 끝 위 3寸(z = {z:.1f}), 종아리뼈 앞모서리: 종아리뼈 단면 중심에서 앞·가쪽"


def loc_SP05():
    g = leg()
    nav = V(24499)
    tub = nav[np.argmax(nav[:, 0])]
    m = g["medial_mall"]
    mid = (m + tub) / 2
    p = skin_nearest(mid)
    return p, {"cun": None, "basis": "안쪽복사 끝·발배뼈거친면"}, "안쪽복사 앞아래 오목: 안쪽복사 끝과 발배뼈거친면을 잇는 선의 중점에서 가장 가까운 피부점"


def loc_GB21():
    c7 = V(12525, None)
    sp = c7[np.argmax(c7[:, 1])]                                  # 극돌기 끝(가장 뒤)
    sc = V(13394)
    top = sc[sc[:, 2] > sc[:, 2].max() - 40]
    acr = top[np.argmin(top[:, 0])]                               # 봉우리 가쪽 끝
    mid = (sp + acr) / 2
    p = skin_ray(mid + np.array([0, 0, -10.0]), (0, 0, 1.0))
    return p, {"cun": None, "basis": "제7목뼈 극돌기 끝·봉우리 가쪽 끝"}, "대추(제7목뼈 극돌기)와 견봉 끝을 잇는 선의 중점에서 위쪽 피부(등세모근 위)"


def loc_TE13():
    hum = V(13303)
    sc = V(13394)
    top = sc[sc[:, 2] > sc[:, 2].max() - 40]
    acr = top[np.argmin(top[:, 0])]
    f = upper_arm()
    z = acr[2] - 3 * f["cun"]
    p = limb_point(13303, z, (-0.6, 0.8))
    return p, f, f"견료(봉우리 뒤아래) 아래 3寸(z = {z:.1f}), 어깨세모근 뒤아래 모서리: 위팔뼈 단면 중심에서 뒤·가쪽"


def loc_GV20():
    tb = V(52737)
    y0 = float(tb[:, 1].mean())                                   # 바깥귀길 앞뒤 위치 근사(관자뼈 중심)
    p = skin_ray(np.array([0.0, y0, 1500.0]), (0, 0, 1.0))
    return p, {"cun": None, "basis": "정중선 × 양 귀끝 연결선(관자뼈 중심 앞뒤 위치로 근사)"}, f"정수리 정중선, 양 귀끝 연결선 높이(y = {y0:.1f}): 위쪽 피부"


def loc_BL02():
    fr = V(52734, None)
    s = fr[(fr[:, 0] > -22) & (fr[:, 0] < -14) & (fr[:, 1] < fr[:, 1].min() + 12)]
    rim = s[np.argmin(s[:, 2])]                                   # 눈확위모서리 안쪽(이마패임 근사)
    p = skin_ray(rim + np.array([0, 8.0, 0]), (0, -1.0, 0.15))
    return p, {"cun": None, "basis": "이마뼈 눈확위모서리 안쪽"}, "눈썹 안쪽 끝 오목(이마패임): 이마뼈 눈확위모서리 안쪽 끝에서 앞쪽 피부"


def _anterior_midline(z):
    return skin_ray(np.array([0.0, -60.0, z]), (0, -1.0, 0))


def _umbilicus():
    """앞 정중선 피부 윤곽(z 900~1100)에서 가장 깊이 들어간 점(배꼽)"""
    zs = np.arange(900.0, 1101.0, 2.0)
    ys = np.array([_anterior_midline(z)[1] for z in zs])
    k = int(np.argmax(ys))                                        # 앞(−Y)으로 덜 나온 곳 = 오목
    return float(zs[k]), ys


def loc_CV12():
    xi = V(7488, None)
    z_x = float(xi[:, 2].max())                                   # 가슴뼈몸통–칼돌기 결합
    z_u, _ = _umbilicus()
    cun = (z_x - z_u) / 8
    z = z_u + 4 * cun
    p = _anterior_midline(z)
    return p, {"cun": cun, "z_xiphisternal": z_x, "z_umbilicus": z_u, "basis": "칼돌기결합~배꼽 = 8寸"}, f"앞 정중선, 배꼽 위 4寸(z = {z:.1f})"


def loc_CV15():
    xi = V(7488, None)
    z_x = float(xi[:, 2].max())
    z_u, _ = _umbilicus()
    cun = (z_x - z_u) / 8
    z = z_x - 1 * cun
    return _anterior_midline(z), {"cun": cun, "basis": "칼돌기결합~배꼽 = 8寸"}, f"앞 정중선, 칼돌기결합 아래 1寸(z = {z:.1f})"


def loc_CV14():
    xi = V(7488, None)
    z_x = float(xi[:, 2].max())
    z_u, _ = _umbilicus()
    cun = (z_x - z_u) / 8
    z = z_u + 6 * cun
    return _anterior_midline(z), {"cun": cun, "basis": "칼돌기결합~배꼽 = 8寸"}, f"앞 정중선, 배꼽 위 6寸(z = {z:.1f})"


RIBS = {"right": {2: 7882, 3: 7909, 4: 7957, 5: 8066, 6: 8175}, "left": {2: 8012, 3: 8039, 4: 8148, 5: 8093, 6: 8202}}
CARTILAGE = {"right": {2: 7886, 3: 7913, 4: 7976, 5: 8070, 6: 8194}, "left": {2: 8031, 3: 8058, 4: 8167, 5: 8112, 6: 8221}}


def _anterior_rib(n, side, x):
    """n번 갈비뼈 + 늑연골의 앞쪽 조각에서 x 근처 정점(뒤쪽 갈비뼈머리를 집지 않도록 가장 앞쪽 35 mm 안만)"""
    v = np.vstack([V(RIBS[side][n], side), V(CARTILAGE[side][n], side)])
    for band in (4, 8, 12, 16):
        s = v[np.abs(v[:, 0] - x) <= band]
        if len(s) >= 3:
            s = s[s[:, 1] <= s[:, 1].min() + 35]
            if len(s) >= 3:
                return s
    return np.empty((0, 3))


def _intercostal_z(n, x, side="right"):
    """n번째 갈비사이공간 높이: x에서 n번 갈비뼈(늑연골) 앞쪽 조각 아래끝과 n+1번 위끝의 중간(흉부경혈 보고서 4-1절과 같은 방법)"""
    sa, sb = _anterior_rib(n, side, x), _anterior_rib(n + 1, side, x)
    if len(sb) >= 3 and len(sa) < 3:
        NOTE.append(f"제{n}갈비뼈 앞쪽 조각이 x = {x:.0f} mm까지 오지 않아 제{n + 1}갈비뼈 위끝 + 8 mm로 근사")
        return float(sb[:, 2].max() + 8.0)
    if len(sa) < 3 or len(sb) < 3:
        sys.exit(f"[locate] x = {x:.1f}에서 제{n}·{n + 1}갈비뼈 앞쪽 정점이 없습니다")
    return float((sa[:, 2].min() + sb[:, 2].max()) / 2)


def loc_CV17():
    z = _intercostal_z(4, -30)
    return _anterior_midline(z), {"cun": None, "basis": "제4갈비사이공간 높이(정중선 옆 늑연골)"}, f"앞 정중선, 제4갈비사이공간 높이(z = {z:.1f})"


def chest_cun(side="right"):
    cl = V(13321, side)
    x_mcl = float((cl[:, 0].min() + cl[:, 0].max()) / 2)          # 빗장뼈 중간선(젖꼭지선)
    return abs(x_mcl) / 4


def _chest_lateral(n, cun_lat=6, side="right"):
    """정중선 가쪽 cun_lat寸: 가슴 골도 = 양 젖꼭지 사이 8寸 → 빗장뼈 중간선(젖꼭지선)을 4寸으로 둔다"""
    cun = chest_cun(side)
    sgn = -1 if side == "right" else 1
    x = sgn * cun_lat * cun
    z = _intercostal_z(n, x, side)
    p = skin_ray(np.array([x, -60.0, z]), (0, -1.0, 0))           # 정면 방향 → 피부점의 X = 정중선 가쪽 거리
    return p, {"cun": cun, "basis": "정중선~빗장뼈 중간선(젖꼭지선) = 4寸"},         f"{'왼' if side == 'left' else '오른'}쪽 제{n}갈비사이공간(z = {z:.1f}), 정중선 가쪽 {cun_lat}寸(x = {x:.1f})"


def loc_SP17(side="right"):
    return _chest_lateral(5, 6, side)


def loc_SP18(side="right"):
    return _chest_lateral(4, 6, side)


def loc_SP19(side="right"):
    return _chest_lateral(3, 6, side)


def loc_SP20(side="right"):
    return _chest_lateral(2, 6, side)


def loc_KI22(side="left"):
    return _chest_lateral(5, 2, side)


def loc_KI23(side="left"):
    return _chest_lateral(4, 2, side)


def loc_KI24(side="left"):
    return _chest_lateral(3, 2, side)


def loc_ST18(side="left"):
    return _chest_lateral(5, 4, side)


# ---------------------------------------------------------------- 어깨
def _acromion():
    sc = V(13394)
    top = sc[sc[:, 2] > sc[:, 2].max() - 40]
    return top[np.argmin(top[:, 0])]                               # 봉우리 가쪽 끝


def _humeral_head():
    h = V(13303)
    return h[h[:, 2] > h[:, 2].max() - 50].mean(0)


def loc_LI15():
    a, hh = _acromion(), _humeral_head()
    o = np.array([a[0] + 12, hh[1], a[2] - 12])
    return skin_ray(o, (-0.55, -0.83, -0.1)), {"cun": None, "basis": "봉우리 가쪽 끝·위팔뼈머리"},         "봉우리 앞아래 오목(팔을 내린 자세): 봉우리 가쪽 끝 아래·앞쪽 피부"


def loc_TE14():
    a, hh = _acromion(), _humeral_head()
    o = np.array([a[0] + 12, hh[1], a[2] - 12])
    return skin_ray(o, (-0.55, 0.83, -0.1)), {"cun": None, "basis": "봉우리 가쪽 끝·위팔뼈머리"},         "봉우리 뒤아래 오목: 봉우리 가쪽 끝 아래·뒤쪽 피부"


def _posterior_axillary_z():
    f = upper_arm()
    return f["z_post_axilla"], f


def loc_SI09():
    z_ax, f = _posterior_axillary_z()
    z = z_ax + 1 * f["cun"]
    c = center_at(13303, z)
    return skin_ray(c, (0.0, 1.0, 0)), f, f"겨드랑이 뒤주름 끝 위 1寸(z = {z:.1f}): 위팔뼈 단면 중심에서 바로 뒤쪽(팔을 내린 자세)"


def _spine_of_scapula():
    sc = V(13394)
    post = sc[sc[:, 1] > np.percentile(sc[:, 1], 85)]              # 등쪽 돌출(어깨뼈가시)
    return post


def loc_SI10():
    p9, f, _ = loc_SI09()
    sp = _spine_of_scapula()
    near = sp[np.abs(sp[:, 0] - p9[0]) <= 15]
    z = float(near[:, 2].min()) - 4 if len(near) else p9[2] + 40
    o = np.array([p9[0], p9[1] - 25, z])
    return skin_ray(o, (0, 1.0, 0)), f, f"노수: 견정(SI9) 바로 위, 어깨뼈가시 아래 오목(z = {z:.1f})"


def loc_SI11():
    sc = V(13394)
    sp = _spine_of_scapula()
    mid_spine = sp[np.argsort(np.abs(sp[:, 0] - np.median(sp[:, 0])))[:30]].mean(0)
    inf = sc[np.argmin(sc[:, 2])]                                   # 아래각
    q = mid_spine + (inf - mid_spine) / 3
    return skin_ray(q + np.array([0, -15.0, 0]), (0, 1.0, 0)), {"cun": None, "basis": "어깨뼈가시 중점·아래각"},         "가시아래오목: 어깨뼈가시 중점과 아래각을 잇는 선의 위 1/3 지점의 뒤쪽 피부"


def loc_LU02():
    cun = chest_cun("right")
    x = -6 * cun
    cl = V(13321)
    s = cl[np.abs(cl[:, 0] - x) <= 5]
    z = float(s[:, 2].min()) - 8
    return skin_ray(np.array([x, -80.0, z]), (0, -1.0, 0)), {"cun": cun, "basis": "정중선~빗장뼈 중간선 = 4寸"},         f"빗장뼈 아래 오목(z = {z:.1f}), 정중선 가쪽 6寸(x = {x:.1f})"


def loc_LI16():
    cl = V(13321)
    lat = cl[np.argmin(cl[:, 0])]
    sp = _spine_of_scapula()
    sp_lat = sp[sp[:, 0] < lat[0] + 30]
    q = (lat + sp_lat.mean(0)) / 2 if len(sp_lat) else lat + np.array([10, 30, 0])
    return skin_ray(q + np.array([0, 0, -15.0]), (0, 0, 1.0)), {"cun": None, "basis": "빗장뼈 가쪽 끝·어깨뼈가시"},         "빗장뼈 가쪽 끝과 어깨뼈가시 사이 오목: 두 기준점 중간의 위쪽 피부"


LOCATORS = {k[4:]: v for k, v in globals().items() if k.startswith("loc_")}


def locate(code, side=None):
    import inspect
    code = M._code(code)
    if code not in LOCATORS:
        sys.exit(f"[locate] {code}: 정위 규칙이 없습니다. 있는 코드: {', '.join(sorted(LOCATORS))}")
    fn = LOCATORS[code]
    if "side" in inspect.signature(fn).parameters:
        side = side or inspect.signature(fn).parameters["side"].default
        p, basis, how = fn(side=side)
    else:
        if side not in (None, "right") and code not in ("GV20", "CV12", "CV14", "CV15", "CV17"):
            sys.exit(f"[locate] {code}: 오른쪽만 정위 규칙이 있습니다")
        side = "right"
        p, basis, how = fn()
    cun = basis.get("cun")
    if NOTE:
        how += " · " + "; ".join(NOTE)
        NOTE.clear()
    return {"code": code, "side": side, "point_mm": [round(float(v), 1) for v in p], "method": how, "basis": basis.get("basis"),
            "cun_mm": round(float(cun), 2) if cun else None, "frame": "BodyParts3D 4.0 (mm, +X left, -Y anterior, +Z up)",
            "caveat": "WHO 표준 위치의 골도분촌을 BodyParts3D 뼈 기준점으로 근사한 좌표(규범 해부 형상 참고, B1 보조). 경혈 실측(B2)이 아니다"}


def main():
    args = sys.argv[1:]
    side = None
    if "--side" in args:
        k = args.index("--side"); side = args[k + 1]; args = args[:k] + args[k + 2:]
    mode = "text"
    if args and args[0] in ("--json", "--xyz"):
        mode, args = args[0][2:], args[1:]
    if not args:
        print(__doc__)
        print("코드:", " ".join(sorted(LOCATORS)))
        return
    res = [locate(c, side) for c in args]
    if mode == "json":
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif mode == "xyz":
        print(" ".join(",".join(str(v) for v in r["point_mm"]) for r in res))
    else:
        for r in res:
            print(f"{r['code']}: {r['point_mm']} · {r['method']}" + (f" · 1寸 = {r['cun_mm']} mm ({r['basis']})" if r["cun_mm"] else f" · 기준: {r['basis']}"))


if __name__ == "__main__":
    main()

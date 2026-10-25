# -*- coding: utf-8 -*-
"""[경혈해부] 중분류 군집별 공유 해부 구조 3D 렌더링(BodyParts3D 4.0, mesh3d.py 공용 함수 호출).

사용: python render3d.py <출력 폴더> [ko|en]
군집마다 구성혈 절반 이상(최소 2혈)이 공유하는 FMA 구조 중 메쉬가 있는 것을 최대 7개, 뼈대를 반투명 배경으로 그린다.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster

HERE = Path(__file__).resolve().parent
MESH = Path(r"G:\내 드라이브\도서 번역\.claude\skills\acupoint-anatomy\scripts\fma")
sys.path.insert(0, str(MESH))
import mesh3d  # noqa: E402

OUT = Path(sys.argv[1])
LANG = sys.argv[2] if len(sys.argv) > 2 else "ko"
D = json.loads((HERE / "clusters.json").read_text(encoding="utf-8"))
codes, Z, FEAT = D["codes"], np.array(D["linkage"]), D["features"]
def groups_at(k):
    g = {}
    for c, l in zip(codes, fcluster(Z, k, "maxclust")):
        g.setdefault(int(l), []).append(c)
    return g


GROUP_K = {"ST12": 8}  # B2는 중분류 8군 단계(天突·璇璣·人迎·缺盆)로 묶는다

BONE = "#d8cfb8"
SETS = [  # (식별 혈, 파일 키, 제목 ko, 제목 en, 뼈대 FMA, 시점, 측)
    ("LU9", "A1_상지", "A1 상지(수태음 본경·손목·손가락) — 공유 구조",
     "A1 Upper limb (Lung-meridian trunk, wrist, digits) — shared structures", [23130, 23464, 23467, 9713], "xz", "right"),
    ("SP18", "A2a_앞가슴벽", "A2a 앞가슴벽 2~5늑간(늑간신경 + 가슴근신경) — 공유 구조",
     "A2a Anterior chest wall, 2nd–5th intercostal spaces (intercostal + pectoral nn.) — shared structures", [7480, 7485, 13322], "xz", "right"),
    ("ST12", "B2_목앞_빗장위", "B2 목 앞·빗장위(목신경얼기 C1–C4) — 공유 구조",
     "B2 Anterior neck & supraclavicular fossa (cervical plexus C1–C4) — shared structures", [24138, 7485, 13322, 7857], "xz", None),
    ("BL13", "B1_등_흉추옆", "B1 등 흉추 옆·어깨 위(등쪽어깨신경·후지) — 공유 구조",
     "B1 Paravertebral back & shoulder (dorsal scapular n., posterior rami) — shared structures", [9140, 7480, 13395], "iso", "right"),
]
COLORS = ["#c0392b", "#e67e22", "#f1c40f", "#2980b9", "#8e44ad", "#16a085", "#d35400"]


def label(fid):
    return mesh3d._label(fid)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for key, fname, t_ko, t_en, bones, view, side in SETS:
        mem = next(v for v in groups_at(GROUP_K.get(key, 12)).values() if key in v)
        cnt = Counter(s for c in mem for s in FEAT[c]["S"])
        need = max(2, (len(mem) + 1) // 2)
        cand = [f for f, n in cnt.most_common() if n >= need] + [f for f, n in cnt.most_common() if 2 <= n < need]
        items, used = [], []
        for f in cand:
            if len(items) >= 7:
                break
            m, _ = mesh3d.load_mesh(f, side)
            if m is None:
                continue
            who = [c for c in mem if f in FEAT[c]["S"]]
            op = 0.45 if label(f) in ("Platysma", "Pectoralis major", "Trapezius") else 1.0
            items.append((m, COLORS[len(items) % len(COLORS)], f"FMA:{f} {label(f)} — {len(who)}/{len(mem)}", op))
            used.append({"fma_id": f, "label": label(f), "points": who})
        for b in bones:
            m, _ = mesh3d.load_mesh(b, side if b not in (7485, 24138, 9140, 7480) else None)
            if m is not None:
                items.append((m, BONE, f"FMA:{b} {label(b)} ({'뼈대' if LANG == 'ko' else 'skeleton'})", 0.28))
        note = ("BodyParts3D 4.0 (DBCLS, CC BY 4.0) 표준 모델 — 개인차·경혈 위치 미반영, 규범 해부 형상 참고(B1 보조). "
                f"구성혈: {', '.join(mem)}. 숫자 = 공유 혈 수/군집 혈 수." if LANG == "ko" else
                "BodyParts3D 4.0 (DBCLS, CC BY 4.0) reference model — no individual variation or point positions; normative shape only (B1 supplementary). "
                f"Members: {', '.join(mem)}. Numbers = points sharing the structure / points in the group.")
        out = OUT / f"Fig4_{fname}_3D_{LANG}.png"
        mesh3d.render(items, str(out), t_ko if LANG == "ko" else t_en, view, note)
        report[fname] = {"members": mem, "structures": used, "view": view, "side": side}
        print("[3D]", out.name, len(used), "structures")
    (HERE / f"render3d_{LANG}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

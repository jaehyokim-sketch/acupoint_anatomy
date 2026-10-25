# -*- coding: utf-8 -*-
"""[경혈해부] 두통 鍼灸法 군집별 공유 구조 3D(BodyParts3D 4.0, mesh3d.py 공용 함수).

사용: python hd_render3d.py <출력 폴더> [ko|en]
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, r"G:\내 드라이브\도서 번역\.claude\skills\acupoint-anatomy\scripts\fma")
import mesh3d  # noqa: E402

OUT = Path(sys.argv[1])
LANG = sys.argv[2] if len(sys.argv) > 2 else "ko"
D = json.loads((HERE / "hd_clusters.json").read_text(encoding="utf-8"))
FEAT = D["features"]
BONE = "#d8cfb8"
SETS = [
    ("Ha_이마정수리", ["GV20", "GV21", "GV22", "GV23", "GV24", "GV29", "BL2"], "Ha 이마·정수리 정중(V1) — 공유 구조",
     "Ha Forehead & vertex midline (V1) — shared structures", [46565], "iso", None),
    ("Hc_뒤통수밑_등", ["GB20", "BL12"], "Hc·Hd 뒤통수밑·등 위(風池·風門) — 구조",
     "Hc/Hd Suboccipital & upper back (GB20, BL12) — structures", [46565, 24138], "iso", "right"),
    ("L_종아리발목", ["ST36", "ST40", "ST41"], "L 종아리·발목(足三里·豊隆·解谿) — 공유 구조",
     "L Leg & ankle (ST36, ST40, ST41) — shared structures", [24477, 24480, 11343], "xz", "right"),
]
COLORS = ["#c0392b", "#e67e22", "#f1c40f", "#2980b9", "#8e44ad", "#16a085", "#d35400"]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for key, mem, t_ko, t_en, bones, view, side in SETS:
        cnt = Counter(s for c in mem for s in FEAT[c]["S"])
        need = 1 if len(mem) <= 2 else 2
        items, used = [], []
        for f, n in cnt.most_common():
            if n < need or len(items) >= 7:
                continue
            m, _ = mesh3d.load_mesh(f, side)
            if m is None:
                continue
            who = [c for c in mem if f in FEAT[c]["S"]]
            lab = mesh3d._label(f)
            op = 0.45 if lab in ("Trapezius", "Platysma", "Occipitofrontalis", "Temporalis") else 1.0
            items.append((m, COLORS[len(items) % len(COLORS)], f"FMA:{f} {lab} — {len(who)}/{len(mem)}", op))
            used.append({"fma_id": f, "label": lab, "points": who})
        for b in bones:
            m, _ = mesh3d.load_mesh(b, side if b not in (46565, 24138) else None)
            if m is not None:
                items.append((m, BONE, f"FMA:{b} {mesh3d._label(b)} ({'뼈대' if LANG == 'ko' else 'skeleton'})", 0.25))
        note = ("BodyParts3D 4.0 (DBCLS, CC BY 4.0) 표준 모델 — 개인차·경혈 위치 미반영, 규범 해부 형상 참고(B1 보조). "
                f"구성혈: {', '.join(mem)}. 숫자 = 공유 혈 수/군집 혈 수." if LANG == "ko" else
                "BodyParts3D 4.0 (DBCLS, CC BY 4.0) reference model — no individual variation or point positions; normative shape only (B1 supplementary). "
                f"Members: {', '.join(mem)}. Numbers = points sharing the structure / points in the group.")
        out = OUT / f"Fig5_{key}_3D_{LANG}.png"
        mesh3d.render(items, str(out), t_ko if LANG == "ko" else t_en, view, note)
        rep[key] = {"members": mem, "structures": used}
        print("[3D]", out.name, len(used), [u["label"] for u in used])
    (HERE / f"hd_render3d_{LANG}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

# -*- coding: utf-8 -*-
"""
needle_depth.py — 「침구문헌별 자침깊이 정리_AI 분석용.xlsx」로 경혈별 자입 깊이 평균을 추정한다.

원자료: 02_Master_Datasets/침구문헌별 자침깊이 정리_AI 분석용.xlsx (시트1, 361혈, 단위 푼(分))
  표기: 숫자 = 푼 · 0 = 금침혈 · 빈칸 = 깊이 기술 없음 · '.'/'x' 등 숫자가 아닌 값 = 값 없음
깊이 문헌 7종 (열 이름은 원자료 그대로):
  고전 단일값 4종 — 황제명당경(황룡상 감수편찬) · 침구갑을경 · 침구경험방 · 동의보감
  현대 범위 3종  — 경락수혈학 공통교재 · 침구의학 공통교재 · 《침구수혈통고》 (최소~최대 → 중앙값을 대표값으로)
  깊이가 아닌 열(갑을경 분류·배열순서, 동의보감 인용 문헌, 선호되는 자침법)은 쓰지 않는다.
추정: 문헌마다 대표값 1개(같은 가중치) → 고전 평균 · 현대 평균 · 전체 평균·중앙값·표준편차·범위. 금침(0)은 평균에서 빼고 따로 센다.
환산: 1푼 = 2.3 mm (스킬 3절).
해석: 《명당경》과 《갑을경》은 같은 계통 기재가 많아 서로 독립된 표본이 아니다. 평균은 문헌 기재의 요약이며 안전 깊이가 아니다.

Usage (어느 폴더에서나):
  python needle_depth.py show ST36                 # 한 혈의 문헌별 값과 평균
  python needle_depth.py build [--out <폴더>]       # 361혈 표 → <폴더>/자입깊이_문헌평균_추정.xlsx·.json (기본 02_Master_Datasets, 편집 PC에서만)
"""
import argparse
import json
import re
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

from fma_common import ROOT

SRC = ROOT / "02_Master_Datasets" / "침구문헌별 자침깊이 정리_AI 분석용.xlsx"
PUN_MM = 2.3
# (짧은 이름, 원자료 열 이름(단일값) 또는 (최소 열, 최대 열), 구분)
SOURCES = [("명당경", "황제명당경_황룡상 감수편찬", "고전"), ("갑을경", "침구갑을경", "고전"),
           ("경험방", "침구경험방", "고전"), ("동의보감", "동의보감", "고전"),
           ("경락수혈학", ("경락수혈학 공통교재(자입깊이 최소값)", "경락수혈학 공통교재(자입깊이 최대값)"), "현대"),
           ("침구의학", ("침구의학 공통교재(자입깊이 최소값)", "침구의학 공통교재(자입깊이 최대값)"), "현대"),
           ("수혈통고", ("<<침구수혈통고>>(자입깊이 최소값)", "<<침구수혈통고>>(자입깊이 최대값)"), "현대")]


def _num(v):
    if v is None or str(v).strip() == "":
        return None, "blank"
    s = str(v).strip()
    if re.fullmatch(r"\d+(\.\d+)?", s):
        return float(s), "ok"
    return None, "invalid"


def _code(s):
    m = re.fullmatch(r"([A-Za-z]+)-?(\d+)", str(s).strip())
    return f"{m.group(1).upper()}{int(m.group(2)):02d}" if m else str(s).strip()


def _stats(vals):
    if not vals:
        return {"n": 0, "mean_pun": None, "mean_mm": None}
    m = st.mean(vals)
    return {"n": len(vals), "mean_pun": round(m, 2), "mean_mm": round(m * PUN_MM, 1)}


def load(path=SRC):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and "경혈부호" in [str(x).strip() for x in r if x])
    head = [str(x).strip() if x is not None else "" for x in rows[hi]]
    col = {h: i for i, h in enumerate(head) if h}
    for _, c, _ in SOURCES:
        for h in (c if isinstance(c, tuple) else (c,)):
            if h not in col:
                sys.exit(f"[needle_depth] 원자료에 열이 없습니다: {h}")
    out = {}
    for r in rows[hi + 1:]:
        if not r or not r[col["경혈부호"]]:
            continue
        code = _code(r[col["경혈부호"]])
        per, flags = [], []
        for name, c, kind in SOURCES:
            if isinstance(c, tuple):
                (lo, s1), (hi_, s2) = _num(r[col[c[0]]]), _num(r[col[c[1]]])
                if lo is None or hi_ is None:
                    per.append({"source": name, "kind": kind, "status": s1 if lo is None else s2})
                    continue
                lo, hi_ = min(lo, hi_), max(lo, hi_)
                status = "금침" if hi_ == 0 else "ok"
                per.append({"source": name, "kind": kind, "status": status, "min": lo, "max": hi_, "value": (lo + hi_) / 2})
            else:
                v, s = _num(r[col[c]])
                per.append({"source": name, "kind": kind, "status": "금침" if v == 0 else s, **({"value": v} if v is not None else {})})
        ok = [p for p in per if p["status"] == "ok"]
        vals = [p["value"] for p in ok]
        rec = {"code": code, "name": str(r[col.get("경혈명", 2)] or "").strip(), "sources": per,
               "classic": _stats([p["value"] for p in ok if p["kind"] == "고전"]),
               "modern": _stats([p["value"] for p in ok if p["kind"] == "현대"]),
               "all": {**_stats(vals), "median_pun": round(st.median(vals), 2) if vals else None,
                       "sd_pun": round(st.stdev(vals), 2) if len(vals) > 1 else None,
                       "min_pun": min(vals) if vals else None, "max_pun": max(vals) if vals else None},
               "forbidden_sources": [p["source"] for p in per if p["status"] == "금침"],
               "missing_sources": [p["source"] for p in per if p["status"] in ("blank", "invalid")]}
        if ok:
            mins = [p.get("min", p["value"]) for p in ok if p["kind"] == "현대"]
            maxs = [p.get("max", p["value"]) for p in ok if p["kind"] == "현대"]
            if mins:
                rec["modern"]["range_pun"] = [round(st.mean(mins), 2), round(st.mean(maxs), 2)]
                rec["modern"]["range_mm"] = [round(st.mean(mins) * PUN_MM, 1), round(st.mean(maxs) * PUN_MM, 1)]
        out[code] = rec
    return out


def summary_line(rec):
    a, c, m = rec["all"], rec["classic"], rec["modern"]
    if not a["n"]:
        return f"{rec['code']} {rec['name']}: 깊이 기재 없음" + (f" (금침: {', '.join(rec['forbidden_sources'])})" if rec["forbidden_sources"] else "")
    s = (f"{rec['code']} {rec['name']}: 7종 평균 {a['mean_pun']}푼 = {a['mean_mm']} mm (n={a['n']}, 중앙값 {a['median_pun']}푼, "
         f"범위 {a['min_pun']:g}–{a['max_pun']:g}푼) · 고전 {c['mean_pun']}푼(n={c['n']}) · 현대 {m['mean_pun']}푼(n={m['n']})")
    if rec["forbidden_sources"]:
        s += f" · 금침 기재: {', '.join(rec['forbidden_sources'])}"
    return s


def cmd_show(a):
    rec = load().get(_code(a.code))
    if not rec:
        sys.exit(f"[needle_depth] {a.code} 없음")
    for p in rec["sources"]:
        v = f"{p['min']:g}–{p['max']:g}푼(중앙 {p['value']:g})" if "min" in p else (f"{p['value']:g}푼" if "value" in p else "")
        print(f"  {p['kind']} {p['source']:6} {p['status']:7} {v}")
    print(summary_line(rec))


def cmd_build(a):
    data = load()
    outdir = Path(a.out) if a.out else ROOT / "02_Master_Datasets"
    meta = {"generated_at": datetime.now().isoformat(timespec="seconds"), "source": SRC.name, "unit": "푼(分), 1푼 = 2.3 mm",
            "method": "문헌별 대표값 1개(범위는 중앙값), 같은 가중치 평균. 금침(0)은 평균에서 제외하고 forbidden_sources에 기록",
            "sources": [{"name": n, "kind": k} for n, _, k in SOURCES],
            "caveat": "명당경·갑을경은 같은 계통 기재라 독립 표본이 아님. 문헌 기재의 요약이며 안전 자침 깊이가 아님"}
    (outdir / "자입깊이_문헌평균_추정.json").write_text(json.dumps({"_metadata": meta, "points": data}, ensure_ascii=False, indent=0), encoding="utf-8")
    import openpyxl
    from openpyxl.styles import Font
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "자입깊이_문헌평균"
    head = ["경혈부호", "경혈명"] + [f"{n}(푼)" for n, _, _ in SOURCES] + \
           ["7종 평균(푼)", "7종 평균(mm)", "n", "중앙값(푼)", "표준편차(푼)", "최소(푼)", "최대(푼)",
            "고전 평균(푼)", "고전 n", "현대 평균(푼)", "현대 n", "현대 범위 평균(mm)", "금침 기재 문헌", "기재 없음"]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True)
    for code, r in data.items():
        cells = []
        for p in r["sources"]:
            cells.append(p.get("value") if p["status"] == "ok" else ("금침" if p["status"] == "금침" else None))
        a_, c_, m_ = r["all"], r["classic"], r["modern"]
        ws.append([code, r["name"], *cells, a_["mean_pun"], a_["mean_mm"], a_["n"], a_["median_pun"], a_["sd_pun"], a_["min_pun"], a_["max_pun"],
                   c_["mean_pun"], c_["n"], m_["mean_pun"], m_["n"], "–".join(f"{v:g}" for v in m_.get("range_mm", [])) or None,
                   ", ".join(r["forbidden_sources"]) or None, ", ".join(r["missing_sources"]) or None])
    ws.freeze_panes = "C2"
    note = wb.create_sheet("방법")
    for k, v in meta.items():
        note.append([k, json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v])
    wb.save(outdir / "자입깊이_문헌평균_추정.xlsx")
    n_ok = sum(1 for r in data.values() if r["all"]["n"])
    print(f"[needle_depth] {len(data)}혈 · 평균 산출 {n_ok} · 금침 기재 있는 혈 {sum(1 for r in data.values() if r['forbidden_sources'])}")
    print(f"[needle_depth] → {outdir / '자입깊이_문헌평균_추정.xlsx'} · .json")


def main():
    ap = argparse.ArgumentParser(description="침구 문헌별 자입 깊이 → 경혈별 평균 추정")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show"); s.add_argument("code")
    s = sub.add_parser("build"); s.add_argument("--out")
    a = ap.parse_args()
    {"show": cmd_show, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    main()

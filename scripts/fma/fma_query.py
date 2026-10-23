# -*- coding: utf-8 -*-
"""
fma_query.py — FMA 로컬 색인 질의·경혈 해부 프로파일 (Claude Code 전용)

사용 (프로젝트 루트에서):
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_query.py search "deep fibular nerve"
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_query.py entity 9626            # 또는 entity "Trapezius"
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_query.py ancestors 44822 --rel branch_of,regional_part_of
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_query.py path "Deep fibular nerve" "Sciatic nerve"
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_query.py profile ST36 [--md] [--json]
  python .claude/skills/acupoint-anatomy/scripts/fma/fma_query.py sparql "SELECT ?l WHERE { fma:fma9626 rdfs:label ?l }"

profile 출력은 보고서 근거로 그대로 쓸 수 있도록 FMA ID(FMA:9626)를 붙이며, 대응 수준(exact/parent/fuzzy)을 함께 표시한다.
"""
import argparse
import io
import json
import re
import sys
from collections import deque

from fma_common import (FMA_NS, KEY_RELATIONS, MAPPING_JSON, QUADSTORE_PATH, norm, open_index)

SPINAL_RE = re.compile(r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth) "
                       r"(cervical|thoracic|lumbar|sacral|coccygeal) (spinal )?nerve\b", re.I)
SEG_LABEL_RE = re.compile(r"^([CTLS])(\d{1,2})$")
ORD = {w: i + 1 for i, w in enumerate("first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split())}
UP_RELS = ("branch_of", "regional_part_of", "constitutional_part_of", "tributary_of")
BRANCH_CLASS_RE = re.compile(r"^((?:[\w-]+ )*?(?:branch|tributary|ramus)) of (.+)$", re.I)


class FMA:
    def __init__(self):
        self.con = open_index()

    def label(self, fid):
        r = self.con.execute("SELECT label FROM entity WHERE fma_id=?", (fid,)).fetchone()
        return r[0] if r else None

    def resolve(self, q):
        """FMA ID(숫자·'FMA:123'·'fma123') 또는 이름 → fma_id."""
        m = re.fullmatch(r"(?:fma:?)?(\d+)", str(q).strip(), re.I)
        if m:
            return int(m.group(1))
        hits = self.search(q, limit=1)
        if not hits:
            sys.exit(f"[fma] '{q}'에 해당하는 FMA 실체가 없습니다. search로 후보를 확인하세요.")
        return hits[0]["fma_id"]

    def search(self, text, limit=20):
        n = norm(text)
        rows = self.con.execute("""SELECT DISTINCT e.fma_id, e.label, t.kind, t.term FROM term t JOIN entity e USING(fma_id)
                                   WHERE t.term_norm = ? LIMIT ?""", (n, limit)).fetchall()
        if len(rows) < limit:
            like = self.con.execute("""SELECT DISTINCT e.fma_id, e.label, t.kind, t.term FROM term t JOIN entity e USING(fma_id)
                                       WHERE t.term_norm LIKE ? ORDER BY length(t.term_norm) LIMIT ?""",
                                    (f"%{n}%", limit * 3)).fetchall()
            seen = {r["fma_id"] for r in rows}
            rows = list(rows) + [r for r in like if r["fma_id"] not in seen and not seen.add(r["fma_id"])]
        return [dict(r) for r in rows[:limit]]

    def edges(self, fid, rels=None, inverse=False):
        col_a, col_b = ("dst", "src") if inverse else ("src", "dst")
        sql = f"SELECT rel, {col_b} AS other FROM edge WHERE {col_a}=?"
        args = [fid]
        if rels:
            sql += f" AND rel IN ({','.join('?' * len(rels))})"
            args += list(rels)
        return [(r["rel"], r["other"]) for r in self.con.execute(sql, args)]

    def ancestors(self, fid, rels=UP_RELS, depth=10):
        """상향 순회 (BFS). [(depth, rel, fma_id, label)]"""
        out, seen, dq = [], {fid}, deque([(fid, 0)])
        while dq:
            cur, d = dq.popleft()
            if d >= depth:
                continue
            for rel, nxt in self.edges(cur, rels):
                if nxt not in seen:
                    seen.add(nxt)
                    out.append((d + 1, rel, nxt, self.label(nxt)))
                    dq.append((nxt, d + 1))
        return out

    def trunk_chain(self, fid, depth=8):
        """가지·지류 → 줄기 순회. FMA에 branch_of가 없으면 is_a 클래스명('Branch of X', 'Tributary of X')으로 상위를 찾는다."""
        chain, cur, seen = [], fid, {fid}
        for _ in range(depth):
            nxt = [(r, o) for r, o in self.edges(cur, ("branch_of", "tributary_of")) if o not in seen]
            if not nxt:
                for _, cls in self.edges(cur, ("is_a",)):
                    m = BRANCH_CLASS_RE.match(self.label(cls) or "")
                    if m:
                        hit = self.con.execute("SELECT fma_id FROM term WHERE term_norm=? AND kind IN ('label','preferred') LIMIT 1",
                                               (norm(m.group(2)),)).fetchone()
                        if hit and hit[0] not in seen:
                            nxt = [("is_a:" + m.group(1).lower(), hit[0])]
                            break
            if not nxt:
                break
            rel, cur = nxt[0]
            seen.add(cur)
            chain.append((rel, cur, self.label(cur)))
        return chain

    def path(self, a, b, rels=None, depth=12):
        # 1차: 두 실체의 줄기(상향) 사슬에서 공통 지점을 찾는다 — 해부학적으로 읽기 쉬운 경로
        if rels is None:
            up_a = [(None, a, self.label(a))] + self.trunk_chain(a, 15) + [(r, o, l) for _, r, o, l in self.ancestors(a, UP_RELS, 6)]
            up_b = [(None, b, self.label(b))] + self.trunk_chain(b, 15)
            ids_b = [o for _, o, _ in up_b]
            for i, (_, o, _) in enumerate(up_a):
                if o in ids_b:
                    j = ids_b.index(o)
                    fwd = [(up_a[k - 1][1], up_a[k][0], up_a[k][1]) for k in range(1, i + 1)]
                    back = [(up_b[k][1], "↑" + str(up_b[k][0]), up_b[k - 1][1]) for k in range(j, 0, -1)]
                    return fwd + back
        rels = rels or ("branch_of", "branch", "regional_part_of", "regional_part", "constitutional_part_of",
                        "constitutional_part", "continuous_with", "continuous_proximally_with", "continuous_distally_with",
                        "tributary_of", "tributary", "is_a")
        prev, dq = {a: None}, deque([(a, 0)])
        while dq:
            cur, d = dq.popleft()
            if cur == b:
                break
            if d >= depth:
                continue
            for rel, nxt in self.edges(cur, rels):
                if nxt not in prev:
                    prev[nxt] = (cur, rel)
                    dq.append((nxt, d + 1))
        if b not in prev:
            return None
        chain, cur = [], b
        while prev[cur]:
            p, rel = prev[cur]
            chain.append((p, rel, cur))
            cur = p
        return list(reversed(chain))

    def segments(self, fid):
        """척수 분절: 직접 segmental_supply(근육 등) + 상향 순회에서 만나는 척수신경 이름(신경)."""
        direct = {}
        for rel, s in self.edges(fid, ("segmental_supply", "primary_segmental_supply", "secondary_segmental_supply")):
            lab = self.label(s)
            direct.setdefault(lab, set()).add(rel.replace("_segmental_supply", "").replace("segmental_supply", "segmental"))
        inferred = set()
        for _, _, a, lab in [(0, None, fid, self.label(fid))] + self.ancestors(fid, depth=12):
            m = SPINAL_RE.search(lab or "")
            if m:
                inferred.add(f"{m.group(2)[0].upper()}{ORD[m.group(1).lower()]}")
        return {"direct": {k: sorted(v) for k, v in direct.items()}, "inferred_from_nerve_chain": sorted(inferred)}


# ---------------------------------------------------------------- commands
def cmd_search(f, a):
    for r in f.search(a.text, a.limit):
        print(f"FMA:{r['fma_id']:<7} {r['label']}   [{r['kind']}: {r['term']}]")


def cmd_entity(f, a):
    fid = f.resolve(a.query)
    e = f.con.execute("SELECT * FROM entity WHERE fma_id=?", (fid,)).fetchone()
    if not e:
        sys.exit(f"FMA:{fid} 없음")
    print(f"FMA:{fid}  {e['label']}" + (f"   TA {e['ta_id']}" if e["ta_id"] else ""))
    terms = f.con.execute("SELECT kind, term FROM term WHERE fma_id=? AND kind IN ('synonym','latin')", (fid,)).fetchall()
    for t in terms:
        print(f"   {t['kind']:8} {t['term']}")
    if e["definition"]:
        print(f"   정의: {e['definition']}")
    groups = {}
    for rel, o in f.edges(fid):
        groups.setdefault(rel, []).append(o)
    order = ["is_a"] + KEY_RELATIONS + sorted(set(groups) - set(KEY_RELATIONS) - {"is_a"})
    for rel in order:
        if rel in groups:
            ids = groups[rel]
            shown = ids if a.all or len(ids) <= 12 else ids[:12]
            print(f"  {rel} ({len(ids)})")
            for o in shown:
                print(f"     → FMA:{o:<7} {f.label(o)}")
            if len(shown) < len(ids):
                print(f"     … {len(ids) - len(shown)}개 더 (--all)")


def cmd_ancestors(f, a):
    fid = f.resolve(a.query)
    rels = tuple(a.rel.split(",")) if a.rel else UP_RELS
    print(f"FMA:{fid} {f.label(fid)}")
    for d, rel, o, lab in f.ancestors(fid, rels, a.depth):
        print(f"{'  ' * d}└ {rel} → FMA:{o} {lab}")


def cmd_path(f, a):
    s, t = f.resolve(a.source), f.resolve(a.target)
    chain = f.path(s, t)
    if chain is None:
        print(f"경로 없음: FMA:{s} {f.label(s)} ↛ FMA:{t} {f.label(t)}")
        return
    print(f"FMA:{s} {f.label(s)}")
    for _, rel, o in chain:
        print(f"  ─[{rel}]→ FMA:{o} {f.label(o)}")


def build_profile(f, code):
    if not MAPPING_JSON.exists():
        sys.exit("[fma] 경혈 대응표가 없습니다. 먼저: python .claude/skills/acupoint-anatomy/scripts/fma/fma_build.py map")
    m = re.fullmatch(r"([A-Za-z]+)-?(\d+)", code.strip())
    if m:   # LI4 · LI-4 · LI04 모두 허용 (교재 표기는 LI04)
        code = f"{m.group(1).upper()}{int(m.group(2)):02d}"
    rows = [r for r in json.loads(io.open(MAPPING_JSON, encoding="utf-8").read())["rows"] if r["code"] == code.upper()]
    if not rows:
        sys.exit(f"[fma] 대응표에 {code} 행이 없습니다.")
    structs = {}
    for r in rows:
        key = r["fma_id"] or f"none:{r['term_en']}"
        s = structs.setdefault(key, {"fma_id": r["fma_id"], "fma_label": r["fma_label"], "category": r["category"],
                                     "terms": set(), "sources": set(), "match": set()})
        s["terms"].add(f"{r['term_kr']} ({r['term_en']})")
        s["sources"].add(r["source"])
        s["match"].add(r["match"])
    seg_union = {}
    for s in structs.values():
        fid = s["fma_id"]
        if not fid:
            continue
        rel = {k: [(o, f.label(o)) for _, o in f.edges(fid, (k,))] for k in
               ("nerve_supply", "arterial_supply", "venous_drainage", "drains_into", "has_origin", "has_insertion",
                "attaches_to", "contained_in")}
        s["relations"] = {k: v for k, v in rel.items() if v}
        s["branch_chain"] = [(o, lab) for _, o, lab in f.trunk_chain(fid)]
        s["nerve_trunks"] = {nid: [(o, lab) for _, o, lab in f.trunk_chain(nid)] for nid, _ in rel.get("nerve_supply", [])}
        s["is_a"] = [(o, f.label(o)) for _, o in f.edges(fid, ("is_a",))]
        s["segments"] = f.segments(fid)
        # 근육의 지배신경 자체에서도 분절을 추론
        for nid, _ in s["relations"].get("nerve_supply", []):
            s["segments"]["inferred_from_nerve_chain"] = sorted(set(s["segments"]["inferred_from_nerve_chain"]) |
                                                                set(f.segments(nid)["inferred_from_nerve_chain"]))
        for lab in s["segments"]["direct"]:
            seg_union.setdefault(lab, set()).add(s["fma_label"])
        for lab in s["segments"]["inferred_from_nerve_chain"]:
            seg_union.setdefault(lab, set()).add(s["fma_label"])
    # 두 교재 비교 (10대 구성 요소 ⑥)
    by_src = {}
    for s in structs.values():
        if s["fma_id"]:
            for src in s["sources"]:
                by_src.setdefault(src, set()).add(s["fma_id"])
    common = set.intersection(*by_src.values()) if len(by_src) == 2 else set()
    return {"code": code.upper(), "name_kr": rows[0]["name_kr"], "structures": list(structs.values()),
            "segment_union": {k: sorted(v) for k, v in sorted(seg_union.items(), key=lambda x: (x[0][0], int(x[0][1:]) if x[0][1:].isdigit() else 0))},
            "textbook_compare": {"common": sorted(common), **{f"only_{k}": sorted(v - common) for k, v in by_src.items()}}}


def _fmt(items, n=4):
    return "; ".join(f"FMA:{o} {lab}" for o, lab in items[:n]) + (f" 외 {len(items) - n}" if len(items) > n else "")


def cmd_profile(f, a):
    p = build_profile(f, a.code)
    if a.json:
        def conv(o):
            return sorted(o) if isinstance(o, set) else o
        print(json.dumps(p, ensure_ascii=False, indent=1, default=conv))
        return
    cat_order = {"근육": 0, "신경": 1, "혈관": 2}
    structs = sorted(p["structures"], key=lambda s: (cat_order.get(s["category"], 9), s["fma_label"] or "~"))
    if a.md:
        print(f"#### FMA 해부 실체 프로파일 — {p['code']} {p['name_kr']} (FMA 5.1.0, 로컬 색인)\n")
        print("| 구분 | 교재 용어 | FMA 실체 | 대응 | 출처 | 신경 지배 / 상위 줄기 | 척수 분절 |")
        print("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for s in structs:
            if not s["fma_id"]:
                print(f"| {s['category']} | {'<br>'.join(sorted(s['terms']))} | — | none | {'·'.join(sorted(s['sources']))} | — | — |")
                continue
            rel = s.get("relations", {})
            if rel.get("nerve_supply"):
                nerve = "<br>".join(f"FMA:{nid} {lab}" + (" → " + " → ".join(f"{l2}" for _, l2 in s["nerve_trunks"].get(nid, [])[:3]) if s["nerve_trunks"].get(nid) else "")
                                    for nid, lab in rel["nerve_supply"][:3])
            else:
                nerve = " → ".join(f"FMA:{o} {lab}" for o, lab in s["branch_chain"][:4]) or "—"
            seg = s["segments"]
            segtxt = ", ".join(f"{k}({'/'.join(v)})" for k, v in seg["direct"].items()) or \
                (", ".join(seg["inferred_from_nerve_chain"]) + " (신경 경로 추론)" if seg["inferred_from_nerve_chain"] else "—")
            print(f"| {s['category']} | {'<br>'.join(sorted(s['terms']))} | FMA:{s['fma_id']} {s['fma_label']} | "
                  f"{'/'.join(sorted(s['match']))} | {'·'.join(sorted(s['sources']))} | {nerve} | {segtxt} |")
        print(f"\n- 분절 합집합(B-Check ② 입력): " + (", ".join(f"{k}" for k in p["segment_union"]) or "FMA 기재 없음"))
        tc = p["textbook_compare"]
        print(f"- 두 교재 공통 FMA 실체 {len(tc.get('common', []))}개 · 공통교재 단독 {len(tc.get('only_공통교재', []))}개 · "
              f"김재효 단독 {len(tc.get('only_김재효', []))}개")
        print("- 대응 수준: exact=정확 일치 / parent=상위 구조 대응(가지 미등재) / fuzzy=오탈자 근사(검토 필요) / none=FMA 미대응")
        return
    print(f"== {p['code']} {p['name_kr']} — FMA 해부 프로파일")
    for s in structs:
        if not s["fma_id"]:
            print(f"\n[{s['category']}] {', '.join(sorted(s['terms']))}  → FMA 미대응")
            continue
        print(f"\n[{s['category']}] FMA:{s['fma_id']} {s['fma_label']}   ({'/'.join(sorted(s['match']))}; {'·'.join(sorted(s['sources']))})")
        print(f"   교재: {', '.join(sorted(s['terms']))}")
        if s["is_a"]:
            print(f"   is_a: {_fmt(s['is_a'], 2)}")
        for k, v in s.get("relations", {}).items():
            print(f"   {k}: {_fmt(v)}")
        for nid, tr in s.get("nerve_trunks", {}).items():
            if tr:
                print(f"     └ FMA:{nid} 줄기: {' → '.join(f'FMA:{o} {lab}' for o, lab in tr[:5])}")
        if s["branch_chain"]:
            print(f"   상위 줄기: {' → '.join(f'FMA:{o} {lab}' for o, lab in s['branch_chain'][:6])}")
        seg = s["segments"]
        if seg["direct"] or seg["inferred_from_nerve_chain"]:
            print(f"   분절: 직접 {seg['direct'] or '—'} / 신경 경로 추론 {seg['inferred_from_nerve_chain'] or '—'}")
    print(f"\n분절 합집합: {p['segment_union'] or 'FMA 기재 없음'}")
    print("교재 비교(FMA 실체 수): " + ", ".join(f"{k} {len(v)}" for k, v in p["textbook_compare"].items()))


def cmd_sparql(f, a):
    """owlready2 영속 저장소 위에서 SPARQL 실행. 기본 rdflib 엔진, --engine owlready로 owlready2 네이티브 엔진."""
    import owlready2
    if not QUADSTORE_PATH.exists():
        sys.exit("[fma] owlready2 저장소가 없습니다. 먼저: fma_build.py load")
    owlready2.default_world.set_backend(filename=str(QUADSTORE_PATH), exclusive=False)
    prefixes = (f"PREFIX fma: <{FMA_NS}>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n")
    q = a.query if a.query.lstrip().upper().startswith("PREFIX") else prefixes + a.query
    if a.engine == "owlready":
        res = owlready2.default_world.sparql(q)
    else:
        res = owlready2.default_world.as_rdflib_graph().query(q)
    for i, row in enumerate(res):
        if i >= a.limit:
            print(f"… (--limit {a.limit})")
            break
        print("\t".join(str(x) for x in row))


def main():
    ap = argparse.ArgumentParser(description="FMA 로컬 질의 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("text"); s.add_argument("--limit", type=int, default=20)
    s = sub.add_parser("entity"); s.add_argument("query"); s.add_argument("--all", action="store_true")
    s = sub.add_parser("ancestors"); s.add_argument("query"); s.add_argument("--rel"); s.add_argument("--depth", type=int, default=10)
    s = sub.add_parser("path"); s.add_argument("source"); s.add_argument("target")
    s = sub.add_parser("profile"); s.add_argument("code"); s.add_argument("--md", action="store_true"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("sparql"); s.add_argument("query"); s.add_argument("--engine", choices=["rdflib", "owlready"], default="rdflib")
    s.add_argument("--limit", type=int, default=200)
    a = ap.parse_args()
    f = FMA()
    {"search": cmd_search, "entity": cmd_entity, "ancestors": cmd_ancestors, "path": cmd_path,
     "profile": cmd_profile, "sparql": cmd_sparql}[a.cmd](f, a)


if __name__ == "__main__":
    main()

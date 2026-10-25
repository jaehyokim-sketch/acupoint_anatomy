# -*- coding: utf-8 -*-
"""구판 『동의보감』 두통 매트릭스(2026-10 이전) 감사: 원전 인용문 실재 여부 + 경혈·유형 대조.

인용 형식 《書名》 "인용문" 을 구판 xlsx 2종·HTML 2종에서 뽑아, 3대 원전 + 『동의보감』 정제 마크다운(간체로 정규화)에서 찾는다.
판정: 일치(정규화 전문 일치) / 부분(4자 단위 조각의 60% 이상 일치) / 미검출
"""
import html
import json
import re
import sys
from pathlib import Path

import openpyxl
from opencc import OpenCC

t2s = OpenCC("t2s").convert
OLD = Path(r"C:\workspace\acupoint_anatomy\04_번역원고_및_임상매트릭스\동의보감_두통_침구해부_매트릭스\_구판_20261024")
SRC = Path(r"G:\내 드라이브\도서 번역\01_도서_번역_및_원전")
HERE = Path(__file__).resolve().parent
PUNCT = re.compile(r"[\s，。、；：！？“”‘’「」『』（）()《》〈〉\[\]【】…·,.;:!?\"'—\-]")


def norm(s):
    return PUNCT.sub("", t2s(s))


def corpus():
    parts = {}
    for d in ("중국침구혈위통감(中国针灸穴位通鉴)", "중국침구증치통감(中国针灸证治通鉴)", "침구수혈통고(针灸腧穴通考)", "동의보감"):
        txt = "".join(p.read_text(encoding="utf-8") for p in sorted((SRC / d).glob("*.md")) if "한글번역" not in p.name)
        parts[d] = norm(txt)
    return parts


def quotes():
    out = []
    pat = re.compile(r"《([^》]{2,30})》\s*[\"“]([^\"”]{3,80})[\"”]")
    for f in sorted(OLD.glob("*.xlsx")):
        wb = openpyxl.load_workbook(f, read_only=True)
        for ws in wb:
            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if isinstance(v, str):
                        out += [(f.name, ws.title, b, q) for b, q in pat.findall(v)]
    for f in sorted(OLD.glob("Donguibogam_Headache_*Report.html")):
        t = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", f.read_text(encoding="utf-8"), flags=re.S)))
        out += [(f.name, "html", b, q) for b, q in pat.findall(t)]
    seen, uniq = set(), []
    for x in out:
        k = (x[2], x[3])
        if k not in seen:
            seen.add(k)
            uniq.append(x)
    return uniq


def judge(q, C):
    nq = norm(q)
    for name, txt in C.items():
        if nq and nq in txt:
            return "일치", name
    grams = [nq[i:i + 4] for i in range(0, max(1, len(nq) - 3))]
    best, where = 0.0, ""
    for name, txt in C.items():
        r = sum(1 for g in grams if g in txt) / len(grams)
        if r > best:
            best, where = r, name
    return ("부분" if best >= 0.6 else "미검출"), f"{where} ({best:.0%})"


def main():
    C = corpus()
    Q = quotes()
    res = []
    for f, sh, b, q in Q:
        j, w = judge(q, C)
        res.append({"file": f, "sheet": sh, "book": b, "quote": q, "verdict": j, "where": w})
    (HERE / "audit_quotes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    print(len(res), Counter(r["verdict"] for r in res))
    for r in res:
        print(r["verdict"], "|", r["book"], "|", r["quote"], "|", r["where"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

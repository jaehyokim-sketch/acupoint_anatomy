# -*- coding: utf-8 -*-
"""[경혈해부] 『동의보감』 두통 침구해부 매트릭스 xlsx (11시트) + 보고서용 데이터(hd_report_data.json).

사용: python hd_matrix.py <출력 xlsx>
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from scipy.cluster.hierarchy import fcluster

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from hd_similarity import NAMES, RX, REGION  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else None
DBGM = Path(r"G:\내 드라이브\도서 번역\01_도서_번역_및_원전\동의보감\동의보감_030_外形篇一_頭.md")
HP = json.loads((HERE / "headache_points.json").read_text(encoding="utf-8"))
CL = json.loads((HERE / "hd_clusters.json").read_text(encoding="utf-8"))
AUD = json.loads((HERE / "audit_quotes.json").read_text(encoding="utf-8"))
codes, Z, FEAT = CL["codes"], np.array(CL["linkage"]), CL["features"]
M = np.loadtxt(HERE / "hd_similarity.csv", delimiter=",", skiprows=1)
LA = {r["code"]: r for r in csv.DictReader(open(HERE / "hd_layerA.csv", encoding="utf-8-sig"))}

SECTIONS = [("1.7", "頭風證"), ("1.10", "正頭痛"), ("1.11", "偏頭痛"), ("1.12", "風寒頭痛"), ("1.13", "濕熱頭痛"), ("1.14", "厥逆頭痛"),
            ("1.15", "痰厥頭痛"), ("1.16", "氣厥頭痛"), ("1.17", "熱厥頭痛"), ("1.18", "濕厥頭痛"), ("1.19", "眞頭痛 / 醉後頭痛"),
            ("1.21", "頭痛當分六經"), ("1.22", "腦風證"), ("1.23", "首風證"), ("1.24", "眉稜骨痛"), ("1.25", "頭痛不治難治證")]
SEC_RX = {"1.7": "R6", "1.10": "R2 (+R1)", "1.11": "R1 (+阿是穴)", "1.14": "R3 腎厥 · R4 齒亦痛", "1.15": "R5", "1.19": "R9 (醉後)",
          "1.22": "R7", "1.24": "R8"}
OLD_TYPES = [("풍두통 風頭痛", "해당 절 없음 — 1.7 頭風證·1.12 風寒頭痛에 흩어짐"), ("편두통 偏頭痛", "1.11 일치"),
             ("뇌역두통 腦逆頭痛", "1.14 厥逆頭痛 안의 기술('腦逆故令頭痛') — 별도 유형 아님"), ("궐역두통 厥逆頭痛", "1.14 일치(정의는 '大寒內至骨髓…頭痛齒亦痛'; 구판의 '손발 冷' 서술은 1.14에 없음)"),
             ("담궐두통 痰厥頭痛", "1.15 일치"), ("기궐두통 氣厥頭痛", "1.16 일치(氣虛·血虛·氣血俱虛 포함)"),
             ("혈궐두통 血厥頭痛", "해당 절 없음 — 1.16 안의 血虛頭痛"), ("신궐두통 腎厥頭痛", "1.14 안의 腎厥(玉眞丸·關元 灸) — 별도 절 아님"),
             ("진두통 眞頭痛", "1.25 일치"), ("취포두통 醉飽頭痛", "1.19 醉後頭痛(內傷門 참조) — '飽' 표기는 원문에 없음"),
             ("기허두통 氣虛頭痛", "1.16 안의 하위 기술"), ("혈허두통 血虛頭痛", "1.16 안의 하위 기술"), ("습열두통 濕熱頭痛", "1.13 일치"),
             ("열두통 熱頭痛", "원문 절은 1.17 熱厥頭痛"), ("습두통 濕頭痛", "원문 절은 1.18 濕厥頭痛"), ("두풍증 頭風證", "1.7 일치"),
             ("(누락)", "1.10 正頭痛 · 1.21 六經 · 1.22 腦風 · 1.23 首風 · 1.24 眉稜骨痛 — 구판에 없음")]
OLD_POINTS = ['GV20', 'LI4', 'GB20', 'EX-HN5', 'TE23', 'BL2', 'GV16', 'KI1', 'ST40', 'ST36', 'CV12', 'LR3', 'BL23', 'GV26', 'EX-UE11', 'GB8',
              'TE20', 'GB5', 'GB6', 'ST8', 'BL7', 'BL10', 'BL60', 'CV6', 'CV4', 'BL17', 'SP6', 'SP10', 'ST44', 'LI11', 'SP9', 'GV14', 'CV9',
              'GV21', 'GV23', 'PC6', 'TE5', 'GV4', 'BL20', 'BL21', 'GB39']
L4, L9, L12 = (fcluster(Z, k, "maxclust") for k in (4, 9, 12))
GN = {"H": "H 머리·목", "U": "U 손", "L": "L 하지", "T": "T 체간"}


def name_l(level, c):
    lab = {4: L4, 9: L9, 12: L12}[level]
    mem = {x for x, l in zip(codes, lab) if l == lab[codes.index(c)]}
    if level == 4:
        return "H 머리·목" if "GV20" in mem else "U 손(合谷)" if "LI4" in mem else "L 하지(足三里·豊隆·解谿)" if "ST36" in mem else "T 체간 정중"
    if level == 9:
        return ("Ha 이마·정수리 정중(V1)" if "GV20" in mem else "Hb 관자(V3·VII)" if "TE23" in mem else "Hc 뒤통수밑(風池)" if "GB20" in mem
                else "Hd 등 위(風門)" if "BL12" in mem else "U 손(合谷)" if "LI4" in mem else "L 하지" if "ST36" in mem else f"T {NAMES[c][0]}")
    nm = {"GV20": "Ha1 정수리(百會·前頂)", "GV23": "Ha2 앞머리 정중(上星·神庭·顖會)", "GV29": "Ha3 미간·눈썹(印堂·攢竹)",
          "TE23": "Hb1 관자(太陽·絲竹空·曲鬢)"}
    for k, v in nm.items():
        if k in mem:
            return v
    return f"{NAMES[c][0]} 단독" if len(mem) == 1 else "L 하지(足三里·豊隆·解谿)"


def sec_text():
    L = DBGM.read_text(encoding="utf-8").split("\n")
    out = {}
    for sec, _ in SECTIONS:
        i = next(k for k, l in enumerate(L) if l.startswith(f"### {sec} "))
        j = i + 1
        while j < len(L) and not L[j].strip():
            j += 1
        out[sec] = (i + 1, j + 1, re.sub(r"〔[^〕]*〕", "", L[j])[:160])
    return out


def main():
    wb = Workbook()
    wb.remove(wb.active)
    hdr, fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="1F6FB2")

    def sheet(title, head, rows, widths):
        ws = wb.create_sheet(title)
        ws.append(head)
        for c in ws[1]:
            c.font, c.fill = hdr, fill
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for r in rows:
            ws.append(r)
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w
        ws.freeze_panes = "B2"

    ST = sec_text()
    sheet("1_동의보감_두통유형", ["절", "유형", "정의 원문(첫 행)", "동의보감 행", "鍼灸法 처방"],
          [[s, t, ST[s][2], f"L{ST[s][1]}", SEC_RX.get(s, "없음(약물·吐法·下法만)")] for s, t in SECTIONS], [6, 22, 90, 10, 22])
    rows = [[r["id"], r["type"], r["method"], " ".join(f"{NAMES[p][0]}({p})" for p in r["points"]), r["tag"], r["trace"],
             r["cohesion"], f"{r['tcc_n']}/{r['n']}", f"{r['tier1_n']}/{r['n']}"] for r in CL["rx"]]
    rows += [["R10", "久患頭痛(手足 血絡 紫黑)", "刺出血 → 刺受病之經", "—", "綱目", "3대 원전 미검출", None, "", ""],
             ["R11", "偏頭痛·正頭痛", "阿是穴 鍼", "—", "—", "—", None, "", ""],
             ["(眩暈1)", "眩暈", "取", "神庭 上星 顖會 前頂 後頂 腦空 風池 陽谷 大都 至陰 金門 申脉 足三里", "綱目", "두통 처방 아님 — 참고", None, "", ""],
             ["(眩暈2)", "眩暈 怕寒", "取", "百會 上星 風池 豊隆", "綱目", "두통 처방 아님 — 참고", None, "", ""]]
    sheet("2_鍼灸法_처방", ["ID", "대상", "방법", "경혈", "출전 표기", "3대 원전 추적(《证治通鉴》)", "처방 내 해부 응집도", "TCC 포함", "단독 주치 1층"],
          rows, [8, 22, 22, 46, 8, 70, 12, 10, 12])
    rows = []
    for c in codes:
        d = HP[c]
        ev = [it for it in d["items"] if it["groups"]][:3]
        rows.append([c, NAMES[c][0], NAMES[c][1], d["tier"], "·".join(g[:2] for g in d["groups_han"]) or "—",
                     "·".join(g[:2] for g in d["groups_later"]) or "—",
                     " / ".join(f"L{it['line']} {it['source'][:16]} “{'/'.join(it['hits'])}”" for it in ev), d["file"]])
    sheet("3_경혈_단독주치층", ["코드", "혈명", "한글", "층", "한대 단독(H1~H5)", "후대 단독", "대표 근거", "《通考》 파일"], rows, [8, 8, 8, 5, 16, 16, 90, 34])
    rows = []
    for c in codes:
        for it in HP[c]["items"]:
            rows.append([c, NAMES[c][0], it["line"], it["era"], it["source"], " ".join(it["groups"]), " ".join(it["groups_combo"]),
                         it["flag"], " / ".join(it["hits"]), it["text"]])
    sheet("4_두통_근거조문", ["코드", "혈명", "행", "시기", "출전", "단독 증상군", "배오 구절 증상군", "Rank 4 표지", "적중어", "조문"], rows,
          [8, 8, 6, 11, 26, 26, 18, 10, 20, 90])
    rows = [[c, NAMES[c][0], REGION[c], ",".join(FEAT[c]["cranial"]), ",".join(FEAT[c]["tcc"]), ",".join(FEAT[c]["G"]),
             "; ".join(FEAT[c]["N"]), len(FEAT[c]["S"]), "; ".join(FEAT[c]["multiseg"]),
             "B1 수작업(교재 미수록)" if c == "GV29" else "瞳子髎(GB1) 대리 — Rank 3" if c == "EX-HN5" else "fma_query profile"] for c in codes]
    sheet("5_해부특징_FMA", ["코드", "혈명", "부위", "뇌신경 분지", "TCC(V+C1–C3)", "분절·분지", "신경 영역", "FMA 구조 수", "다분절 제외", "출처"], rows,
          [8, 8, 14, 12, 14, 30, 80, 8, 24, 22])
    ws = wb.create_sheet("6_유사도행렬")
    ws.append([""] + codes)
    for i, c in enumerate(codes):
        ws.append([c] + [round(float(x), 3) for x in M[i]])
    rows = [[c, NAMES[c][0], HP[c]["tier"], name_l(4, c), name_l(9, c), name_l(12, c),
             "; ".join(f"{codes[k]}({M[i, k]:.2f})" for k in np.argsort(-M[i])[1:4])] for i, c in enumerate(codes)]
    sheet("7_층위", ["코드", "혈명", "주치 층", "대분류(4군)", "중분류(9군)", "소분류(12군)", "가장 가까운 3혈"], rows, [8, 8, 6, 24, 26, 30, 40])
    rows = [[c, NAMES[c][0], LA[c]["n_active"], LA[c]["n_headache"], LA[c]["ids"]] for c in codes]
    rows += [["(DB 미병합)", "Cochrane 2016 편두통 예방", "", "", "PMID 27351677 · DOI 10.1002/14651858.CD001218.pub3 — 22 RCT, 가짜침 대비 SMD −0.18"],
             ["(DB 미병합)", "Cochrane 2016 긴장형 두통", "", "", "PMID 27092807 · DOI 10.1002/14651858.CD007587.pub2 — 12 RCT, 가짜침 대비 반응률 51% vs 43%"]]
    sheet("8_LayerA", ["코드", "혈명", "DB 연결(active)", "두통 관련", "papers.id / 비고"], rows, [12, 24, 12, 10, 90])
    sheet("9_구판감사_인용", ["파일", "시트", "서명", "인용문", "판정", "최고 일치 문헌"],
          [[a["file"], a["sheet"], a["book"], a["quote"], a["verdict"], a["where"]] for a in AUD], [36, 20, 18, 46, 8, 40])
    norm = lambda c: re.sub(r"([A-Z]+)0*(\d+)", r"\1\2", c.replace("EX-HN05", "EX-HN5"))
    oldn = [norm(c) for c in OLD_POINTS]
    rows = [[t, v] for t, v in OLD_TYPES]
    rows += [["경혈 — 구판·신판 공통", ", ".join(sorted(set(oldn) & set(codes)))],
             ["경혈 — 구판에만(원문 鍼灸法에 없음)", ", ".join(sorted(set(oldn) - set(codes)))],
             ["경혈 — 신판에만(구판 누락)", ", ".join(sorted(set(codes) - set(oldn)))]]
    sheet("10_구판감사_유형·경혈", ["구판 항목", "원문 대조 결과"], rows, [34, 110])
    rows = [["가중치(잠정)", json.dumps(CL["weights"])], ["군집법", "UPGMA, 거리 = 1 − 유사도"], ["코페네틱 상관", CL["cophenetic"]],
            ["등가중치 ARI", CL["ari"]], ["실루엣 최적 k", CL["k"]],
            ["분지 대응", "V1(눈신경·이마·눈확위·도르래위·도르래아래), V2(광대관자 등), V3(아래턱·귓바퀴관자), VII, XI; C1 뒤통수밑, C2 큰뒤통수, C2–C3 작은뒤통수 (B1-01·B1-02)"],
            ["TCC", "삼차신경 V1–V3 + C1–C3 상부 경수 — 삼차-경수 복합체 수렴(B1-02 규범 신경해부)"],
            ["印堂", "2대 교재 데이터셋 미수록 → B1 수작업 대응(눈살근·눈썹주름근·도르래위/아래신경·도르래위동정맥·코등동맥)"],
            ["太陽", "《通考》 太阳(EX-HN5) 名實考: 원·명초 문헌에서 瞳子髎와 동일시 → 해부는 GB1 프로파일 대리"],
            ["3D", "BodyParts3D 4.0 — 관자 연부조직(관자근·얕은관자동맥 등) 메쉬 없음 → Hb 3D 생략"]]
    sheet("11_방법·감사", ["항목", "값"], rows, [20, 120])
    wb.save(OUT)
    (HERE / "hd_report_data.json").write_text(json.dumps({"sections": {s: ST[s] for s, _ in SECTIONS}}, ensure_ascii=False), encoding="utf-8")
    print("[xlsx]", OUT)
    for r in rows:
        pass
    for i, c in enumerate(codes):
        print(c, name_l(4, c), "|", name_l(9, c), "|", name_l(12, c))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()

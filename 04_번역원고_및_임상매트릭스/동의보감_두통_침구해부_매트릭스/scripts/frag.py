import json,csv,sys,re
sys.path.insert(0,'.')
from hd_similarity import NAMES, REGION
import hd_matrix as HM
HP=json.load(open('headache_points.json',encoding='utf-8')); CL=json.load(open('hd_clusters.json',encoding='utf-8'))
AUD=json.load(open('audit_quotes.json',encoding='utf-8')); RD=json.load(open('hd_report_data.json',encoding='utf-8'))['sections']
codes=CL['codes']; F=CL['features']
T={'I':'1층','II':'2층','III':'3층'}
o=[]
o.append('<!--TYPES-->')
o.append('| 절 | 유형 | 정의 원문(첫 문장, `동의보감_030` 행) | 鍼灸法 |\n| :-- | :-- | :-- | :-- |')
for s,t in HM.SECTIONS:
    txt=RD[s][2]; first=re.split(r'(?<=\))',txt)[0][:70]
    o.append(f"| {s} | {t} | {first}… (L{RD[s][1]}) | {HM.SEC_RX.get(s,'없음(약물·吐下法만)')} |")
o.append('<!--RX-->')
o.append('| ID | 대상 | 방법 | 경혈 | 표기 | 3대 원전 추적 | 응집도 | TCC | 1층 |\n| :-- | :-- | :-- | :-- | :-: | :-- | :-: | :-: | :-: |')
for r in CL['rx']:
    o.append(f"| {r['id']} | {r['type']} | {r['method']} | {'·'.join(NAMES[p][0] for p in r['points'])} | {r['tag']} | {r['trace']} | {r['cohesion'] if r['cohesion'] is not None else '—'} | {r['tcc_n']}/{r['n']} | {r['tier1_n']}/{r['n']} |")
o.append('<!--TIER-->')
o.append('| 층 | 코드 | 혈명 | 한대 단독 | 후대 단독 | 대표 근거(《通考》 행·출전·적중어) |\n| :-: | :-- | :-- | :-- | :-- | :-- |')
for t in ('I','II','III'):
    for c in [x for x in codes if HP[x]['tier']==t]:
        d=HP[c]; ev=[it for it in d['items'] if it['groups']]
        ev=[it for it in ev if it['era']=='1_先秦两汉'][:1]+[it for it in ev if it['era']!='1_先秦两汉'][:1]
        evs='; '.join(f"L{it['line']} {it['source'].split('、')[0][:18]} “{'/'.join(it['hits'])}”" for it in ev) or '두통 조문 없음'
        o.append(f"| {T[t]} | {c} | {NAMES[c][1]} {NAMES[c][0]} | {'·'.join(g[:2] for g in d['groups_han']) or '—'} | {'·'.join(g[:2] for g in d['groups_later']) or '—'} | {evs} |")
o.append('<!--HIER-->')
o.append('| 코드 | 혈명 | 주치 층 | 대분류(4) | 중분류(9) | 소분류(12) | 뇌신경 분지 | TCC | 분절 | 가장 가까운 3혈 |\n| :-- | :-- | :-: | :-- | :-- | :-- | :-- | :-- | :-- | :-- |')
import numpy as np
M=np.loadtxt('hd_similarity.csv',delimiter=',',skiprows=1)
order=json.load(open('hd_order.json',encoding='utf-8'))
for c in order:
    i=codes.index(c); nn='; '.join(f"{codes[k]}({M[i,k]:.2f})" for k in np.argsort(-M[i])[1:4])
    segs=','.join(g for g in F[c]['G'] if not g.startswith(('V','X'))) or '—'
    o.append(f"| {c} | {NAMES[c][0]} | {T[HP[c]['tier']]} | {HM.name_l(4,c)} | {HM.name_l(9,c)} | {HM.name_l(12,c)} | {','.join(F[c]['cranial']) or '—'} | {','.join(F[c]['tcc']) or '—'} | {segs} | {nn} |")
o.append('<!--AUD-->')
o.append('| 판정 | 서명 | 구판 인용문 | 최고 일치 문헌(4자 조각 일치율) |\n| :-: | :-- | :-- | :-- |')
for a in sorted(AUD,key=lambda a:{'일치':0,'부분':1,'미검출':2}[a['verdict']]):
    o.append(f"| {a['verdict']} | 《{a['book']}》 | {a['quote']} | {a['where'] or '—'} |")
open('hd_frag_ko.md','w',encoding='utf-8').write('\n'.join(o)+'\n')
print(len(o))

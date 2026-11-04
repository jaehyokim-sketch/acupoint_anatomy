# -*- coding: utf-8 -*-
"""
mesh3d_viewer.py — BodyParts3D 메쉬를 단일 HTML 상호작용 3D 모델로 묶는다 (mesh3d.py model이 부른다).

- three.js(r160)·OrbitControls를 한 번 내려받아 FMA_DATA_DIR/web에 두고, HTML 안에 data URI로 넣는다 → 인터넷 없이 열린다.
- 좌표: BodyParts3D(mm, +X 왼쪽, −Y 앞, +Z 위) → 화면(x, z, −y): 위가 머리 쪽, 정면 보기에서 화면 오른쪽이 환자 왼쪽.
- 보고서 비노출 규정(스킬 7절)에 맞춰 로컬 경로·원본 파일명·확장자를 HTML에 쓰지 않는다.
"""
import base64
import html
import json
import urllib.request

import numpy as np

from fma_common import data_dir

THREE_VER = "0.160.0"
THREE_FILES = {"three": f"https://cdn.jsdelivr.net/npm/three@{THREE_VER}/build/three.module.min.js",
               "orbit": f"https://cdn.jsdelivr.net/npm/three@{THREE_VER}/examples/jsm/controls/OrbitControls.js"}


def _lib(name):
    p = data_dir() / "web" / f"{name}-{THREE_VER}.js"
    if not p.exists() or p.stat().st_size == 0:
        p.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(THREE_FILES[name], timeout=120) as r:
            p.write_bytes(r.read())
    return "data:text/javascript;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def to_view(v):
    """BodyParts3D 좌표 → 화면 좌표 (x, z, −y)"""
    v = np.asarray(v, dtype=float)
    return np.stack([v[..., 0], v[..., 2], -v[..., 1]], axis=-1)


def _b64(a, dtype):
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode("ascii")


def build_html(items, out, title, subtitle, notes, point=None, distances=None, reach=None):
    """items: [{mesh, color, label, category, fma, level, opacity, role}] · point: BodyParts3D 좌표 [x,y,z] · distances: [{label, mm, closest}]
    reach: {mm, label} — 대표점 중심의 깊이 반경 구(문헌 평균 자입 깊이)"""
    allv = np.concatenate([to_view(it["mesh"].vertices) for it in items])
    center = (allv.min(0) + allv.max(0)) / 2
    size = float((allv.max(0) - allv.min(0)).max())
    objs = []
    for it in items:
        m = it["mesh"]
        v = to_view(m.vertices) - center
        anchor = v[np.argmin(np.linalg.norm(v - v.mean(0), axis=1))]      # 무게중심에 가장 가까운 표면 꼭짓점
        objs.append({"label": it["label"], "cat": it["category"], "fma": it.get("fma"), "level": it.get("level") or "",
                     "role": it.get("role", "structure"), "color": it["color"], "opacity": it["opacity"],
                     "pos": _b64(v, "<f4"), "idx": _b64(m.faces, "<u4"), "anchor": anchor.round(2).tolist()})
    data = {"objs": objs, "size": round(size, 1), "point": None, "distances": distances or [], "reach": reach}
    if point is not None:
        data["point"] = (to_view(point) - center).round(2).tolist()
        for d in data["distances"]:
            d["closest"] = (to_view(d["closest"]) - center).round(2).tolist()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    page = (TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__SUBTITLE__", html.escape(subtitle))
            .replace("__NOTES__", "".join(f"<p>{html.escape(n)}</p>" for n in notes if n))
            .replace("__THREE__", _lib("three")).replace("__ORBIT__", _lib("orbit")).replace("__DATA__", payload))
    out.write_text(page, encoding="utf-8")
    return out


TEMPLATE = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#0b1722;--panel:#112433;--line:#2c4458;--text:#e8f0f5;--muted:#9fb4c3;--accent:#8dd8bd}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 "Malgun Gothic","Noto Sans KR",system-ui,sans-serif}
header{padding:14px 18px 10px;border-bottom:1px solid var(--line)}h1{font-size:19px;margin:0 0 3px}header p{margin:0;color:var(--muted);font-size:12.5px}
main{display:grid;grid-template-columns:minmax(0,1fr) 360px;height:calc(100vh - 140px);min-height:520px}
#stage{position:relative;overflow:hidden}#stage canvas{display:block;width:100%;height:100%;touch-action:none}
.lbl{position:absolute;transform:translate(-50%,-120%);padding:2px 7px;border-radius:5px;background:rgba(8,20,30,.82);border:1px solid;font-size:11.5px;white-space:nowrap;pointer-events:none}
.dist{border-style:dashed}
aside{border-left:1px solid var(--line);background:var(--panel);overflow:auto;padding:12px 14px}
aside h2{font-size:13px;margin:12px 0 6px;color:#bfe3d6}
.views{display:flex;flex-wrap:wrap;gap:5px}button{background:#173246;color:var(--text);border:1px solid #33546b;border-radius:6px;padding:5px 9px;font:inherit;font-size:12px;cursor:pointer}
button[aria-pressed="true"]{background:var(--accent);color:#0b1722;border-color:var(--accent)}
.item{display:grid;grid-template-columns:auto 14px 1fr;gap:6px;align-items:start;padding:5px 0;border-top:1px solid #20384a;font-size:12.5px}
.item.sel{background:#183a4c}.sw{width:14px;height:14px;border-radius:3px;margin-top:3px}.item small{color:var(--muted);display:block}
label.row{display:flex;align-items:center;gap:8px;font-size:12.5px;margin:6px 0}input[type=range]{flex:1}
table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-top:1px solid #20384a;padding:4px 3px;text-align:left}td.n{text-align:right;font-variant-numeric:tabular-nums}
footer{padding:8px 18px;border-top:1px solid var(--line);color:var(--muted);font-size:11.5px;height:70px;overflow:auto}footer p{margin:2px 0}
@media (max-width:860px){main{grid-template-columns:1fr;height:auto}#stage{height:70vh}aside{border-left:0;border-top:1px solid var(--line)}}
</style>
<script type="importmap">{"imports":{"three":"__THREE__","three/addons/controls/OrbitControls.js":"__ORBIT__"}}</script>
</head><body>
<header><h1>__TITLE__</h1><p>__SUBTITLE__</p></header>
<main><div id="stage"></div>
<aside>
 <h2>보기</h2><div class="views" id="views"></div>
 <label class="row"><input type="checkbox" id="show-labels" checked> 구조 라벨</label>
 <label class="row">근육 불투명도 <input type="range" id="muscle-op" min="5" max="100" value="55"><output id="muscle-op-o">55%</output></label>
 <div id="dist-box" hidden><h2>경혈 추정점 → 구조 표면 최소 거리</h2><table id="dist"></table><p style="color:var(--muted);font-size:11.5px">교재 구조 목록(또는 지정 좌표)으로 정한 대표 피부점 기준의 최소 직선거리입니다. 경혈 위치 실측(B2)이 아니며 자침 방향 깊이와 다를 수 있습니다.</p></div>
 <h2>구조 (클릭: 강조 · 체크: 표시)</h2><div id="legend"></div>
</aside></main>
<footer>__NOTES__</footer>
<script id="model-data" type="application/json">__DATA__</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const D=JSON.parse(document.getElementById('model-data').textContent),stage=document.getElementById('stage');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(2,devicePixelRatio||1));renderer.setClearColor(0x0b1722);stage.appendChild(renderer.domElement);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(30,1,1,D.size*20),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
scene.add(new THREE.HemisphereLight(0xeaf4ff,0x40464c,1.6));for(const [p,i] of [[[1,1.2,1.5],1.6],[[-1.2,.4,-1],1],[[0,-1,.6],.6]]){const l=new THREE.DirectionalLight(0xffffff,i);l.position.set(...p);scene.add(l)}
const dec=(s,T)=>{const b=atob(s),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return new T(u.buffer)};
const objs=D.objs.map((o,i)=>{const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(dec(o.pos,Float32Array),3));g.setIndex(new THREE.BufferAttribute(dec(o.idx,Uint32Array),1));g.computeVertexNormals();
 const mat=new THREE.MeshStandardMaterial({color:o.color,roughness:.62,metalness:0,transparent:o.opacity<1,opacity:o.opacity,depthWrite:o.opacity>=1,side:THREE.DoubleSide});
 const mesh=new THREE.Mesh(g,mat);mesh.renderOrder=o.opacity<1?2:1;mesh.userData.i=i;scene.add(mesh);
 const el=document.createElement('span');el.className='lbl';el.textContent=o.label;el.style.color=el.style.borderColor=o.color;stage.appendChild(el);
 return {...o,mesh,el,anchor:new THREE.Vector3(...o.anchor),base:o.opacity}});
const extra=[];
if(D.point){const P=new THREE.Vector3(...D.point);const s=new THREE.Mesh(new THREE.SphereGeometry(D.size*.008+1.2,20,14),new THREE.MeshBasicMaterial({color:0xff4fd8,depthTest:false}));s.position.copy(P);s.renderOrder=5;scene.add(s);
 const pl=document.createElement('span');pl.className='lbl';pl.textContent='경혈 추정점';pl.style.color=pl.style.borderColor='#ff8fe6';stage.appendChild(pl);extra.push({el:pl,v:P});
 const rows=[];for(const d of D.distances){const C=new THREE.Vector3(...d.closest),g=new THREE.BufferGeometry().setFromPoints([P,C]);const ln=new THREE.Line(g,new THREE.LineDashedMaterial({color:0xff8fe6,dashSize:1.5,gapSize:1,depthTest:false}));ln.computeLineDistances();ln.renderOrder=5;scene.add(ln);
  rows.push(`<tr><td>${d.label.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</td><td class="n">${d.mm.toFixed(1)} mm</td></tr>`)}
 if(D.reach){const g=new THREE.Mesh(new THREE.SphereGeometry(D.reach.mm,32,20),new THREE.MeshBasicMaterial({color:0xff8fe6,wireframe:true,transparent:true,opacity:.22,depthWrite:false}));g.position.copy(P);scene.add(g);
  rows.unshift(`<tr><td><b>${D.reach.label}</b></td><td class="n">반경 구</td></tr>`)}
 document.getElementById('dist').innerHTML='<tr><th>구조</th><th>최소 거리</th></tr>'+rows.join('');document.getElementById('dist-box').hidden=false}
// 보기
const R=D.size*2.1,VIEWS={'정면':[0,0,1],'뒤':[0,0,-1],'환자 오른쪽':[-1,0,0],'환자 왼쪽':[1,0,0],'위':[0,1,.001],'아래':[0,-1,.001],'사위':[-.7,.35,.75]};
function view(name){const d=new THREE.Vector3(...VIEWS[name]).normalize();controls.target.set(0,0,0);camera.position.copy(d.multiplyScalar(R));camera.up.set(0,1,0);controls.update();document.querySelectorAll('#views button').forEach(b=>b.setAttribute('aria-pressed',b.textContent===name))}
for(const k of Object.keys(VIEWS)){const b=document.createElement('button');b.textContent=k;b.onclick=()=>view(k);document.getElementById('views').appendChild(b)}
// 범례
let selected=-1;const legend=document.getElementById('legend');
function select(i){selected=selected===i?-1:i;objs.forEach((o,j)=>{o.mesh.material.emissive.setHex(j===selected?0x3a3a10:0);legend.children[j].classList.toggle('sel',j===selected)})}
objs.forEach((o,i)=>{const row=document.createElement('div');row.className='item';const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;cb.onchange=()=>{o.mesh.visible=cb.checked};
 const sw=document.createElement('span');sw.className='sw';sw.style.background=o.color;const t=document.createElement('div');t.innerHTML=`<b></b><small></small>`;t.querySelector('b').textContent=o.label;
 t.querySelector('small').textContent=[o.cat,o.fma?'FMA:'+o.fma:'',o.level&&o.level!=='exact'?'메쉬: '+o.level:'',o.role==='context'?'위치 참고':''].filter(Boolean).join(' · ');t.style.cursor='pointer';t.onclick=()=>select(i);row.append(cb,sw,t);legend.appendChild(row)});
const op=document.getElementById('muscle-op');op.oninput=()=>{const v=op.value/100;document.getElementById('muscle-op-o').textContent=op.value+'%';for(const o of objs)if(o.cat==='근육'){o.mesh.material.opacity=v;o.mesh.material.transparent=v<1;o.mesh.material.depthWrite=v>=1;o.mesh.material.needsUpdate=true}};
// 클릭 선택
const ray=new THREE.Raycaster(),ptr=new THREE.Vector2();let down=null;
renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY]});
renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4)return;const r=renderer.domElement.getBoundingClientRect();ptr.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(ptr,camera);
 const hit=ray.intersectObjects(objs.filter(o=>o.mesh.visible).map(o=>o.mesh))[0];if(hit)select(hit.object.userData.i)});
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(resize).observe(stage);resize();view('사위');
const showLabels=document.getElementById('show-labels');
function place(el,v,ok){const p=v.clone().project(camera);const vis=ok&&p.z<1&&Math.abs(p.x)<1&&Math.abs(p.y)<1;el.style.display=vis?'block':'none';if(vis){el.style.left=(p.x*.5+.5)*stage.clientWidth+'px';el.style.top=(-p.y*.5+.5)*stage.clientHeight+'px'}}
(function loop(){requestAnimationFrame(loop);controls.update();for(const o of objs)place(o.el,o.anchor,showLabels.checked&&o.mesh.visible&&(o.role!=='context'||selected===objs.indexOf(o)));for(const x of extra)place(x.el,x.v,true);renderer.render(scene,camera)})();
window.Mesh3DModel={scene,camera,objs};
</script></body></html>
'''

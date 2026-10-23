# -*- coding: utf-8 -*-
"""
fma_visualizer.py — FMA 온톨로지(v5.1.0) 및 Neo4j 그래프 기반 경혈 신경해부 지식 그래프 및 도식 이미지 자동 생성기
(Claude Code ↔ Antigravity 공용 도구)

기능:
  1. graph: Neo4j Cypher 쿼리를 통해 경혈-해부실체-신경지배-상위줄기-척수분절 네트워크 그래프 이미지(PNG/SVG) 생성
  2. cross-section: 혈위별 횡단면 해부 모식도 생성 (figures/ 전용 스크립트 또는 표준 5층차 심도 렌더러)
  3. all: 두 이미지 일괄 생성 및 보고서 디렉토리 저장

사용:
  python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py graph ST36
  python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py graph SP05 --out figures/SP05_fma_network.png
  python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py cross-section ST36
  python .agents/skills/acupoint-anatomy/scripts/fma/fma_visualizer.py all ST36 --dir "acupoint_anatomy/01_경혈별_해부생리_분석보고서/ST_족양명위경/ST36_족삼리"
"""
import argparse
import os
import sys
import subprocess
from pathlib import Path

# Matplotlib headless backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Hangul font fallback
plt.rcParams["font.family"] = ["Malgun Gothic", "Microsoft YaHei", "NanumGothic", "Arial"]
plt.rcParams["axes.unicode_minus"] = False

# Import local FMA modules
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from fma_common import find_project_root, MAPPING_JSON
    from fma_neo4j import conn_params, Runner
except ImportError:
    from fma_common import find_project_root, MAPPING_JSON
    from fma_neo4j import conn_params, Runner


COLOR_MAP = {
    "acupoint": "#D97706",          # 경혈 (골드/호박색)
    "근육": "#DC2626",              # 근육 (코랄 레드)
    "신경": "#F59E0B",              # 신경 (앰버 옐로우)
    "혈관": "#2563EB",              # 혈관 (로열 블루)
    "trunk": "#B45309",             # 상위 줄기 신경/혈관 (딥 앰버)
    "nerve_innervation": "#059669", # 신경 지배 경로 (에메랄드 그린)
    "segment": "#7C3AED",           # 척수 분절 (바이올렛)
    "골막/관절": "#4B5563",          # 골막/인대/기타 (슬레이트 그레이)
    "기타": "#6B7280"
}


def build_network_graph(code: str, runner: Runner):
    """Neo4j에서 특정 경혈의 해부학적 지식 하위 그래프를 질의하여 NetworkX 그래프 객체로 변환."""
    import networkx as nx
    
    cypher = """
    MATCH (a:Acupoint {code:$code})-[h:HAS_STRUCTURE]->(s:Anatomy)
    OPTIONAL MATCH (s)-[:NERVE_SUPPLY]->(n:Anatomy)
    OPTIONAL MATCH p=(s)-[:BRANCH_OF|BRANCH_OF_INFERRED*1..4]->(trunk:Anatomy)
    OPTIONAL MATCH (s)-[r:SEGMENTAL_SUPPLY|PRIMARY_SEGMENTAL_SUPPLY|SECONDARY_SEGMENTAL_SUPPLY]->(seg:Anatomy)
    RETURN a.code AS code, a.nameKr AS nameKr,
           h.category AS category, s.fmaId AS fmaId, s.label AS label,
           n.fmaId AS nerveFma, n.label AS nerveLabel,
           [node IN nodes(p) | {fma: node.fmaId, label: node.label}] AS trunkChain,
           type(r) AS segRel, seg.label AS segLabel
    """
    records = runner.run(cypher, code=code)
    if not records:
        return None, None
        
    name_kr = records[0].get("nameKr") or code
    
    G = nx.DiGraph()
    root_node = f"{code}\n({name_kr})"
    G.add_node(root_node, ntype="acupoint", label=root_node, category="acupoint")
    
    added_nodes = set([root_node])
    
    for r in records:
        s_label = r["label"]
        cat = r.get("category") or "기타"
        s_id = f"{s_label}\n[FMA:{r['fmaId']}]"
        
        if s_id not in added_nodes:
            G.add_node(s_id, ntype="structure", label=s_label, fma=r["fmaId"], category=cat)
            added_nodes.add(s_id)
        G.add_edge(root_node, s_id, rel="HAS_STRUCTURE")
        
        # 신경 지배
        if r.get("nerveLabel"):
            n_id = f"{r['nerveLabel']}\n[FMA:{r['nerveFma']}]"
            if n_id not in added_nodes:
                G.add_node(n_id, ntype="nerve_innervation", label=r["nerveLabel"], fma=r["nerveFma"], category="nerve_innervation")
                added_nodes.add(n_id)
            G.add_edge(s_id, n_id, rel="NERVE_SUPPLY")
            
        # 상위 줄기 사슬
        trunks = r.get("trunkChain")
        if trunks and len(trunks) > 1:
            for i in range(len(trunks) - 1):
                u_info = trunks[i]
                v_info = trunks[i+1]
                u_id = f"{u_info['label']}\n[FMA:{u_info['fma']}]"
                v_id = f"{v_info['label']}\n[FMA:{v_info['fma']}]"
                if v_id not in added_nodes:
                    G.add_node(v_id, ntype="trunk", label=v_info["label"], fma=v_info["fma"], category="trunk")
                    added_nodes.add(v_id)
                G.add_edge(u_id, v_id, rel="BRANCH_OF")
                
        # 척수 분절
        if r.get("segLabel"):
            seg_id = f"Segment {r['segLabel']}"
            if seg_id not in added_nodes:
                G.add_node(seg_id, ntype="segment", label=r["segLabel"], category="segment")
                added_nodes.add(seg_id)
            G.add_edge(s_id, seg_id, rel="SEGMENTAL_SUPPLY")

    return G, name_kr


def render_graph_image(G, code: str, name_kr: str, out_path: Path, dpi: int = 200) -> bool:
    """NetworkX 그래프를 고해상도 시각화 이미지로 렌더링하여 저장."""
    import networkx as nx

    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 노드 색상 및 크기 설정
    node_colors = []
    node_sizes = []
    for n, data in G.nodes(data=True):
        ntype = data.get("ntype")
        cat = data.get("category")
        if ntype == "acupoint":
            node_colors.append(COLOR_MAP["acupoint"])
            node_sizes.append(3000)
        elif ntype == "segment":
            node_colors.append(COLOR_MAP["segment"])
            node_sizes.append(1800)
        elif cat in COLOR_MAP:
            node_colors.append(COLOR_MAP[cat])
            node_sizes.append(1500)
        elif ntype in COLOR_MAP:
            node_colors.append(COLOR_MAP[ntype])
            node_sizes.append(1400)
        else:
            node_colors.append(COLOR_MAP["기타"])
            node_sizes.append(1200)

    fig, ax = plt.subplots(figsize=(16, 12), dpi=dpi)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFAFA")
    
    # Layout 알고리즘 (spring layout with tuning)
    pos = nx.spring_layout(G, k=1.9, iterations=120, seed=42)
    
    # 엣지 렌더링
    edge_styles = {
        "HAS_STRUCTURE": {"color": "#64748B", "style": "solid", "width": 1.8, "alpha": 0.8},
        "NERVE_SUPPLY": {"color": "#059669", "style": "dashed", "width": 2.0, "alpha": 0.9},
        "BRANCH_OF": {"color": "#B45309", "style": "dotted", "width": 1.7, "alpha": 0.85},
        "SEGMENTAL_SUPPLY": {"color": "#7C3AED", "style": "dashdot", "width": 2.2, "alpha": 0.9}
    }
    
    for rel_type, style in edge_styles.items():
        edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("rel") == rel_type]
        if edges:
            nx.draw_networkx_edges(
                G, pos, edgelist=edges, ax=ax,
                edge_color=style["color"],
                style=style["style"],
                width=style["width"],
                alpha=style["alpha"],
                arrows=True,
                arrowsize=14,
                connectionstyle="arc3,rad=0.08"
            )

    # 노드 렌더링
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.94,
        edgecolors="#FFFFFF",
        linewidths=1.8
    )
    
    # 라벨 렌더링
    labels = {n: n for n in G.nodes()}
    nx.draw_networkx_labels(
        G, pos, labels=labels, ax=ax,
        font_size=8.5,
        font_family="Malgun Gothic",
        font_weight="bold",
        font_color="#0F172A"
    )
    
    # 타이틀
    ax.set_title(
        f"[FMA 5.1.0] FMA 해부 온톨로지 신경회로망 & 해부 구조 지식 그래프 — {code} {name_kr}",
        fontsize=16, fontweight="bold", pad=22, color="#0F172A"
    )
    
    # 범례
    legend_elements = [
        mpatches.Patch(color=COLOR_MAP["acupoint"], label="중심 경혈 (Acupoint)"),
        mpatches.Patch(color=COLOR_MAP["근육"], label="근육 실체 (Muscle)"),
        mpatches.Patch(color=COLOR_MAP["신경"], label="신경 실체 (Nerve)"),
        mpatches.Patch(color=COLOR_MAP["nerve_innervation"], label="지배신경 (Innervation)"),
        mpatches.Patch(color=COLOR_MAP["trunk"], label="상위 줄기 신경 (Trunk Chain)"),
        mpatches.Patch(color=COLOR_MAP["혈관"], label="혈관 실체 (Vessel)"),
        mpatches.Patch(color=COLOR_MAP["segment"], label="척수 분절 (Spinal Segment)")
    ]
    ax.legend(
        handles=legend_elements, loc="upper right", frameon=True,
        facecolor="#F8FAFC", edgecolor="#CBD5E1", fontsize=9.5, framealpha=0.95
    )
    
    # 하단 메타데이터
    n_structures = sum(1 for _, d in G.nodes(data=True) if d.get("ntype") == "structure")
    n_segments = sum(1 for _, d in G.nodes(data=True) if d.get("ntype") == "segment")
    meta_text = f"• 총 노드: {G.number_of_nodes()}개 | 해부 구조: {n_structures}개 | 척수 분절: {n_segments}개 | 관계: {G.number_of_edges()}개 | 출처: FMA v5.1.0 (Neo4j)"
    plt.figtext(0.08, 0.02, meta_text, fontsize=9, color="#64748B", family="Malgun Gothic")
    
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=dpi, bbox_inches="tight")
    plt.close()
    return True


def generate_cross_section_diagram(code: str, out_path: Path) -> bool:
    """혈위별 횡단면 모식도 생성 (전용 figures 스크립트 실행 또는 표준 층차 심도 다이어그램 생성)."""
    fig_script = SCRIPT_DIR / "figures" / f"{code}_cross_section.py"
    if fig_script.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run([sys.executable, str(fig_script), str(out_path)], capture_output=True, text=True)
        if res.returncode == 0:
            return True
            
    # 표준 5층차 심도 다이어그램 폴백 생성
    fig, ax = plt.subplots(figsize=(10, 8), dpi=180)
    ax.set_xlim(0, 10)
    ax.set_ylim(-30, 5)
    
    # 5개 층차 밴드
    layers = [
        ("Layer 1: 표피 및 피하 결합조직 (0 ~ 2.5mm)", 0, -2.5, "#FDE68A"),
        ("Layer 2: 표층 근막 및 천층 건막 (2.5 ~ 6.5mm)", -2.5, -6.5, "#FED7AA"),
        ("Layer 3: 심층 근육 및 건막 간극 (6.5 ~ 16.5mm)", -6.5, -16.5, "#FECACA"),
        ("Layer 4: 신경혈관속 및 자율신경총 (16.5 ~ 22.0mm)", -16.5, -22.0, "#BFDBFE"),
        ("Layer 5: 골막 및 관절낭 기저면 (22.0mm 이상)", -22.0, -30.0, "#E2E8F0")
    ]
    
    for name, top, bottom, color in layers:
        ax.axhspan(bottom, top, facecolor=color, alpha=0.7, edgecolor="#94A3B8", lw=0.8)
        ax.text(0.3, (top + bottom)/2, name, va="center", ha="left", fontsize=9.5, fontweight="bold", color="#1E293B")
        
    # 자침 침체 표시
    ax.arrow(8.0, 4.0, 0, -20.0, head_width=0.25, head_length=1.5, fc="#DC2626", ec="#991B1B", lw=2.0)
    ax.text(8.0, 4.5, f"{code} 자침선\n(직자 15~20mm)", ha="center", va="bottom", fontsize=9, fontweight="bold", color="#DC2626")
    
    ax.set_title(f"[경혈해부] {code} 5층차(Layer 1~5) 표준 자침 심도 모식도", fontsize=13, fontweight="bold", pad=15)
    ax.set_ylabel("자침 깊이 (mm)", fontsize=10, fontweight="bold")
    ax.set_xticks([])
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(str(out_path), dpi=180, bbox_inches="tight")
    plt.close()
    return True


def cmd_graph(code: str, out_file: str = None, dpi: int = 200) -> str:
    """그래프 이미지 단독 생성 CLI 핸들러."""
    runner = Runner()
    G, name_kr = build_network_graph(code, runner)
    runner.close()
    
    if not G:
        print(f"[visualizer] 경혈 {code}의 Neo4j 지식 그래프 데이터가 없습니다.")
        return None
        
    if not out_file:
        out_path = SCRIPT_DIR / "figures" / f"{code}_fma_network.png"
    else:
        out_path = Path(out_file)
        
    render_graph_image(G, code, name_kr, out_path, dpi=dpi)
    print(f"[visualizer] ✅ FMA 지식 그래프 이미지 생성 완료: {out_path}")
    return str(out_path)


def cmd_cross_section(code: str, out_file: str = None) -> str:
    """횡단면 모식도 생성 CLI 핸들러."""
    if not out_file:
        out_path = SCRIPT_DIR / "figures" / f"{code}_cross_section.png"
    else:
        out_path = Path(out_file)
        
    generate_cross_section_diagram(code, out_path)
    print(f"[visualizer] ✅ 횡단면 해부 모식도 생성 완료: {out_path}")
    return str(out_path)


def cmd_all(code: str, target_dir: str = None) -> dict:
    """두 가지 시각화 이미지 일괄 생성."""
    if target_dir:
        td = Path(target_dir)
    else:
        td = SCRIPT_DIR / "figures"
        
    td.mkdir(parents=True, exist_ok=True)
    graph_out = td / f"{code}_fma_network.png"
    cross_out = td / f"{code}_cross_section.png"
    
    g_res = cmd_graph(code, str(graph_out))
    c_res = cmd_cross_section(code, str(cross_out))
    
    return {"graph": g_res, "cross_section": c_res}


def main():
    parser = argparse.ArgumentParser(description="FMA 온톨로지(v5.1.0) 및 Neo4j 기반 경혈 지식 그래프 & 도식 이미지 생성기")
    sub = parser.add_subparsers(dest="command")
    
    p_graph = sub.add_parser("graph", help="FMA 신경해부 지식 그래프 이미지 생성")
    p_graph.add_argument("code", help="경혈 코드 (예: ST36, SP05)")
    p_graph.add_argument("--out", help="출력 이미지 파일 경로")
    p_graph.add_argument("--dpi", type=int, default=200, help="해상도 DPI (기본 200)")
    
    p_cross = sub.add_parser("cross-section", help="경혈 횡단면 해부 모식도 생성")
    p_cross.add_argument("code", help="경혈 코드 (예: ST36, SP05)")
    p_cross.add_argument("--out", help="출력 이미지 파일 경로")
    
    p_all = sub.add_parser("all", help="지식 그래프 및 횡단면 모식도 일괄 생성")
    p_all.add_argument("code", help="경혈 코드 (예: ST36, SP05)")
    p_all.add_argument("--dir", help="출력 디렉토리 경로")
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    if args.command == "graph":
        cmd_graph(args.code.upper(), args.out, dpi=args.dpi)
    elif args.command == "cross-section":
        cmd_cross_section(args.code.upper(), args.out)
    elif args.command == "all":
        cmd_all(args.code.upper(), args.dir)


if __name__ == "__main__":
    main()

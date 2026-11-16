"""경혈학 핸드북 포털(한국어판) 생성기.

data/master_361_acupoints_dataset.json(SSOT) → tools/acupoint-handbook.html
이어서 영문판(scripts/handbook_portal_en/build_handbook_portal_en.py)을 다시 만들고,
강의 폴더(Drive `강의/경혈학 교재 편찬`)가 있으면 두 포털을 복사한다.

- 원본: Antigravity 작업 폴더의 generate_handbook_portal_v3.py (2026-11-13)
- 2026-11-15: '핸드북 자구법'(handbook.puncture_method) 표시·검색·자침법 필터 제거.
  마스터 JSON에는 필드가 남아 있으나(PDF 서식 틀만 남은 깨진 추출 텍스트) 포털에는 넣지 않는다.
- 2026-11-15: 헤더 영문판 전환 링크, 출처에 최수빈(KMD) 추가
- 2026-11-15: 헤더 hits.sh 조회수 배지(커밋 5d67590) 반영

사용: python scripts/generate_handbook_portal.py [--no-en] [--no-lecture-copy]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_JSON = os.path.join(REPO, "data", "master_361_acupoints_dataset.json")
DEST_HTML = os.path.join(REPO, "tools", "acupoint-handbook.html")
DEST_EN_HTML = os.path.join(REPO, "tools", "acupoint-handbook-en.html")
EN_BUILDER = os.path.join(REPO, "scripts", "handbook_portal_en", "build_handbook_portal_en.py")
LECTURE_DIR = os.environ.get("ACUPOINT_LECTURE_DIR", r"G:\내 드라이브\강의\경혈학 교재 편찬")
LECTURE_COPIES = {DEST_HTML: "경혈학_핸드북_포털.html", DEST_EN_HTML: "경혈학_핸드북_포털_영문판.html"}

# 포털에 넣지 않는 handbook 필드
DROP_HANDBOOK_FIELDS = ("puncture_method",)

with open(SRC_JSON, "r", encoding="utf-8") as f:
    points = json.load(f)
for p in points:
    for k in DROP_HANDBOOK_FIELDS:
        p.get("handbook", {}).pop(k, None)

print(f"Loaded {len(points)} points from master dataset.")

# Meridian metadata
meridians = [
    {"code": "LU", "name": "수태음폐경", "en": "Lung Meridian (LU)", "count": 11, "color": "#2563eb"},
    {"code": "LI", "name": "수양명대장경", "en": "Large Intestine Meridian (LI)", "count": 20, "color": "#d97706"},
    {"code": "ST", "name": "족양명위경", "en": "Stomach Meridian (ST)", "count": 45, "color": "#ea580c"},
    {"code": "SP", "name": "족태음비경", "en": "Spleen Meridian (SP)", "count": 21, "color": "#ca8a04"},
    {"code": "HT", "name": "수소음심경", "en": "Heart Meridian (HT)", "count": 9, "color": "#dc2626"},
    {"code": "SI", "name": "수태양소장경", "en": "Small Intestine Meridian (SI)", "count": 19, "color": "#e11d48"},
    {"code": "BL", "name": "족태양방광경", "en": "Bladder Meridian (BL)", "count": 67, "color": "#0284c7"},
    {"code": "KI", "name": "족소음신경", "en": "Kidney Meridian (KI)", "count": 27, "color": "#4f46e5"},
    {"code": "PC", "name": "수궐음심포경", "en": "Pericardium Meridian (PC)", "count": 9, "color": "#9333ea"},
    {"code": "TE", "name": "수소양삼초경", "en": "Triple Energizer Meridian (TE)", "count": 23, "color": "#c026d3"},
    {"code": "GB", "name": "족소양담경", "en": "Gallbladder Meridian (GB)", "count": 44, "color": "#16a34a"},
    {"code": "LR", "name": "족궐음간경", "en": "Liver Meridian (LR)", "count": 14, "color": "#059669"},
    {"code": "CV", "name": "임맥", "en": "Conception Vessel (CV)", "count": 24, "color": "#0891b2"},
    {"code": "GV", "name": "독맥", "en": "Governor Vessel (GV)", "count": 28, "color": "#7c3aed"}
]

# Total homonym matches count
homonym_pts_count = sum(1 for p in points if p.get("homonym_matches") and len(p["homonym_matches"]) > 0)
total_pairs_count = sum(len(p.get("homonym_matches", [])) for p in points)
print(f"Points with homonym matches: {homonym_pts_count} (Total pairs: {total_pairs_count})")

html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>원광대학교 한의과대학 경혈학 핸드북 포털 (Wonkwang Univ. College of Korean Med. Acupoint Handbook Portal) — 14경맥 361경혈 표준 정본</title>
  <meta name="description" content="14경맥 361종 경혈 핸드북 포털: 김재효 수업자료 및 경혈학 공통교재 해부구조 데이터셋, 문헌별 자침깊이(명당경·갑을경·경험방·동의보감·공통교재·통고), 황룡상 고증 침구법, 표준 KCD 질병코드 연계, KJH 경혈명 비교정리 및 본명-이명 혼동주의 경보">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&family=Noto+Serif+KR:wght@500;700;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #1e3a8a;
      --primary-light: #3b82f6;
      --primary-dark: #172554;
      --secondary: #0d9488;
      --accent: #b45309;
      --bg-main: #f8fafc;
      --bg-card: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --kcd-badge-bg: #ecfdf5;
      --kcd-badge-text: #065f46;
      --kcd-badge-border: #a7f3d0;
      --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
      --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
      --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
      --radius: 12px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html {
      scroll-behavior: smooth;
      -webkit-text-size-adjust: 100%;
    }
    body {
      font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
      touch-action: pan-y;
      -webkit-overflow-scrolling: touch;
    }

    header {
      background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0369a1 100%);
      color: #ffffff;
      padding: 2.25rem 1.5rem 1.75rem;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: var(--shadow-md);
    }
    .header-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .header-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .title-area h1 {
      font-size: 1.85rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .title-area p {
      font-size: 0.92rem;
      color: #93c5fd;
      margin-top: 0.35rem;
    }
    .header-badges {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .badge {
      font-size: 0.75rem;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-weight: 600;
      letter-spacing: 0.02em;
      background: rgba(255, 255, 255, 0.15);
      border: 1px solid rgba(255, 255, 255, 0.25);
      color: #ffffff;
    }
    .badge.gold {
      background: rgba(245, 158, 11, 0.25);
      border-color: rgba(245, 158, 11, 0.6);
      color: #fef08a;
    }
    .badge.rose {
      background: rgba(244, 63, 94, 0.25);
      border-color: rgba(244, 63, 94, 0.6);
      color: #ffe4e6;
    }

    /* Search & Filter Bar */
    .search-filter-bar {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr 1fr;
      gap: 0.75rem;
      background: rgba(255, 255, 255, 0.12);
      backdrop-filter: blur(8px);
      padding: 0.75rem;
      border-radius: var(--radius);
      border: 1px solid rgba(255, 255, 255, 0.18);
    }
    .search-box {
      position: relative;
    }
    .search-box input {
      width: 100%;
      height: 42px;
      padding: 0 1rem 0 2.5rem;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.25);
      background: #ffffff;
      color: var(--text-main);
      font-size: 0.95rem;
      outline: none;
      transition: all 0.2s;
    }
    .search-box input:focus {
      border-color: var(--primary-light);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
    }
    .search-box svg {
      position: absolute;
      left: 0.85rem;
      top: 50%;
      transform: translateY(-50%);
      width: 18px;
      height: 18px;
      color: #94a3b8;
    }
    .filter-select {
      height: 42px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.25);
      background: #ffffff;
      color: var(--text-main);
      font-size: 0.9rem;
      padding: 0 0.75rem;
      outline: none;
      font-weight: 500;
      cursor: pointer;
    }

    .container {
      max-width: 1400px;
      margin: 1.5rem auto 3rem;
      padding: 0 1.5rem;
    }

    /* Stats Strip */
    .stats-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .stat-card {
      background: var(--bg-card);
      padding: 1rem 1.25rem;
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
    }
    .stat-card .label {
      font-size: 0.8rem;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .stat-card .value {
      font-size: 1.5rem;
      font-weight: 800;
      color: var(--primary);
      margin-top: 0.25rem;
      font-family: 'JetBrains Mono', monospace;
    }

    /* Meridian Pills */
    .meridian-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      margin-bottom: 1.75rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid var(--border);
    }
    .meridian-pill {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 9999px;
      padding: 0.35rem 0.85rem;
      font-size: 0.82rem;
      font-weight: 600;
      color: #475569;
      cursor: pointer;
      transition: all 0.15s ease;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .meridian-pill:hover {
      border-color: var(--primary-light);
      color: var(--primary);
      background: #eff6ff;
    }
    .meridian-pill.active {
      background: var(--primary);
      color: #ffffff;
      border-color: var(--primary);
      box-shadow: 0 2px 4px rgba(30, 58, 138, 0.25);
    }
    .meridian-pill .pill-count {
      font-size: 0.72rem;
      background: rgba(0, 0, 0, 0.08);
      padding: 0.05rem 0.4rem;
      border-radius: 9999px;
    }
    .meridian-pill.active .pill-count {
      background: rgba(255, 255, 255, 0.25);
    }

    /* Points Grid */
    .points-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
      gap: 1.5rem;
    }

    /* Point Card */
    .point-card {
      background: var(--bg-card);
      border-radius: var(--radius);
      border: 1px solid var(--border);
      box-shadow: var(--shadow-sm);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    }
    .point-card:hover {
      transform: translateY(-2px);
      box-shadow: var(--shadow-md);
      border-color: #cbd5e1;
    }

    /* Card Header */
    .card-header {
      padding: 1.1rem 1.25rem 0.9rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.75rem;
      background: #fafafa;
    }
    .card-title-group {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .card-title-top {
      display: flex;
      align-items: baseline;
      gap: 0.6rem;
      flex-wrap: wrap;
    }
    .point-code {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 800;
      font-size: 1.2rem;
      color: var(--primary);
    }
    .point-name {
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--text-main);
    }
    .point-hanja {
      font-family: 'Noto Serif KR', serif;
      font-size: 1.15rem;
      color: #64748b;
      font-weight: 700;
    }
    .slide-hanja-badge {
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      background: #f1f5f9;
      color: #475569;
      border: 1px solid #cbd5e1;
      padding: 0.1rem 0.4rem;
      border-radius: 4px;
      font-weight: 600;
    }
    .aliases-row {
      font-size: 0.8rem;
      color: #64748b;
      display: flex;
      align-items: center;
      gap: 0.35rem;
      flex-wrap: wrap;
    }
    .aliases-row strong {
      color: #475569;
    }
    .meridian-tag {
      font-size: 0.75rem;
      font-weight: 700;
      color: #ffffff;
      padding: 0.2rem 0.6rem;
      border-radius: 6px;
      white-space: nowrap;
      flex-shrink: 0;
    }

    /* Homonym Alert Box */
    .homonym-alert-box {
      margin: 0.75rem 1.25rem 0;
      background: #fff1f2;
      border: 1px solid #fecdd3;
      border-left: 4px solid #e11d48;
      border-radius: 6px;
      padding: 0.6rem 0.85rem;
      font-size: 0.82rem;
      color: #9f1239;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }
    .homonym-header {
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      color: #be123c;
    }
    .homonym-header svg {
      width: 15px;
      height: 15px;
      flex-shrink: 0;
    }
    .homonym-pair-list {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      padding-left: 0.25rem;
    }
    .homonym-pair-item {
      line-height: 1.45;
      color: #881337;
    }
    .homonym-target-badge {
      display: inline-block;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 0.78rem;
      background: #ffe4e6;
      border: 1px solid #fda4af;
      color: #9f1239;
      padding: 0.05rem 0.4rem;
      border-radius: 4px;
      margin-left: 0.25rem;
      cursor: pointer;
      text-decoration: underline;
    }
    .homonym-target-badge:hover {
      background: #f43f5e;
      color: #ffffff;
    }

    /* Card Body */
    .card-body {
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1.15rem;
      flex: 1;
    }

    .section-block {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .section-label {
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .section-label svg { width: 14px; height: 14px; color: var(--primary-light); }
    .section-content {
      font-size: 0.92rem;
      color: #1e293b;
      line-height: 1.55;
    }

    /* Puncture & Moxa Specifications */
    .puncture-summary {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 0.85rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .puncture-row-top {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
      font-size: 0.88rem;
    }
    .puncture-val-badge {
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      color: var(--primary-dark);
      background: #ffffff;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      border: 1px solid #cbd5e1;
    }

    /* Literature Depth Comparison Table */
    .depth-table-wrapper {
      margin-top: 0.35rem;
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      touch-action: pan-x pan-y;
    }
    .depth-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.8rem;
      text-align: center;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      overflow: hidden;
    }
    .depth-table th {
      background: #f1f5f9;
      color: #334155;
      font-weight: 700;
      padding: 0.4rem 0.5rem;
      border-bottom: 1px solid #cbd5e1;
      border-right: 1px solid #e2e8f0;
      white-space: nowrap;
    }
    .depth-table td {
      padding: 0.45rem 0.5rem;
      border-bottom: 1px solid #f1f5f9;
      border-right: 1px solid #f1f5f9;
      color: #1e293b;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 600;
      white-space: nowrap;
    }
    .depth-table tr:last-child td { border-bottom: none; }
    .depth-table td:last-child, .depth-table th:last-child { border-right: none; }
    .method-tag {
      font-family: 'Pretendard', sans-serif;
      font-size: 0.72rem;
      color: #b45309;
      background: #fef3c7;
      padding: 0.1rem 0.35rem;
      border-radius: 3px;
      margin-left: 0.25rem;
      font-weight: 600;
    }

    /* Caution box */
    .caution-box {
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-left: 4px solid #f59e0b;
      padding: 0.6rem 0.85rem;
      border-radius: 6px;
      font-size: 0.85rem;
      color: #92400e;
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
    }
    .caution-box svg { flex-shrink: 0; width: 16px; height: 16px; margin-top: 2px; }

    /* Anatomy Box */
    .anatomy-box {
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #fafafa;
      overflow: hidden;
    }
    .anatomy-header {
      padding: 0.6rem 0.85rem;
      background: #f1f5f9;
      font-size: 0.82rem;
      font-weight: 700;
      color: #334155;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
    }
    .anatomy-body {
      padding: 0.85rem;
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
      font-size: 0.86rem;
      background: #ffffff;
    }
    .anatomy-group-title {
      font-weight: 700;
      color: var(--primary);
      font-size: 0.78rem;
      text-transform: uppercase;
      margin-bottom: 0.2rem;
      border-bottom: 1px dashed #e2e8f0;
      padding-bottom: 0.2rem;
    }
    .anatomy-items {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      padding-left: 0.25rem;
    }
    .anat-item {
      color: #334155;
      line-height: 1.45;
    }

    /* Indications & KCD pills */
    .indication-group {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .cat-title {
      font-size: 0.8rem;
      font-weight: 700;
      color: #475569;
      background: #f1f5f9;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      display: inline-block;
      align-self: flex-start;
    }
    .ind-pill-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .ind-pill {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      padding: 0.25rem 0.6rem;
      border-radius: 6px;
      font-size: 0.84rem;
      color: #1e293b;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .kcd-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      font-weight: 700;
      background: var(--kcd-badge-bg);
      color: var(--kcd-badge-text);
      border: 1px solid var(--kcd-badge-border);
      padding: 0.05rem 0.35rem;
      border-radius: 4px;
      letter-spacing: -0.01em;
    }

    /* Floating Back-to-Top Button */
    .btn-top {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: var(--primary);
      color: #ffffff;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: var(--shadow-lg);
      cursor: pointer;
      border: none;
      transition: all 0.2s;
      z-index: 99;
    }
    .btn-top:hover {
      background: var(--primary-light);
      transform: translateY(-3px);
    }

    footer {
      background: #0f172a;
      color: #94a3b8;
      padding: 2.5rem 1.5rem;
      text-align: center;
      font-size: 0.85rem;
      border-top: 1px solid #1e293b;
      line-height: 1.7;
    }
    footer strong { color: #f1f5f9; }

    @media (max-width: 900px) {
      header {
        position: relative;
        top: auto;
        padding: 1.25rem 1rem 1rem;
        box-shadow: none;
      }
      .header-content {
        gap: 0.85rem;
      }
      .title-area h1 {
        font-size: 1.35rem;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.25rem;
      }
      .title-area h1 span:last-child {
        font-size: 0.82rem;
        opacity: 0.85;
      }
      .title-area p {
        font-size: 0.8rem;
        line-height: 1.45;
        margin-top: 0.25rem;
      }
      .header-badges {
        gap: 0.35rem;
      }
      .badge {
        font-size: 0.72rem;
        padding: 0.2rem 0.55rem;
      }
      .search-filter-bar {
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
        padding: 0.6rem;
      }
      .search-box {
        grid-column: 1 / -1;
      }
      .search-box input {
        height: 38px;
        font-size: 0.88rem;
        touch-action: pan-y;
      }
      .filter-select {
        height: 38px;
        font-size: 0.82rem;
        padding: 0 0.5rem;
        touch-action: pan-y;
      }
      #specialFilter {
        grid-column: 1 / -1;
      }
      .container {
        padding: 0 0.85rem;
        margin: 1rem auto 2.5rem;
        width: 100%;
      }
      .stats-strip {
        grid-template-columns: repeat(2, 1fr);
        gap: 0.6rem;
        margin-bottom: 1rem;
      }
      .stat-card {
        padding: 0.75rem 0.85rem;
      }
      .stat-card .label {
        font-size: 0.72rem;
      }
      .stat-card .value {
        font-size: 1.25rem;
      }
      .meridian-tabs {
        gap: 0.35rem;
        margin-bottom: 1.25rem;
        padding-bottom: 0.5rem;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
      }
      .meridian-pill {
        font-size: 0.75rem;
        padding: 0.3rem 0.65rem;
        flex-shrink: 0;
      }
      .points-grid {
        grid-template-columns: 1fr;
        gap: 1rem;
        width: 100%;
        min-width: 0;
      }
      .point-card {
        width: 100%;
        min-width: 0;
      }
      .card-header {
        padding: 0.85rem 1rem;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      .card-body {
        padding: 1rem;
        gap: 1rem;
      }
      .btn-top {
        bottom: 1.25rem;
        right: 1.25rem;
        width: 44px;
        height: 44px;
        z-index: 1000;
      }
    }

    @media (max-width: 480px) {
      .header-content {
        gap: 0.75rem;
      }
      .title-area h1 {
        font-size: 1.2rem;
      }
      .search-filter-bar {
        grid-template-columns: 1fr;
      }
      .search-box, #specialFilter {
        grid-column: auto;
      }
      .stats-strip {
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-content">
      <div class="header-top">
        <div class="title-area">
          <h1>
            <span>원광대학교 한의과대학 경혈학 핸드북 포털</span>
            <span style="font-size: 1rem; font-weight: 500; opacity: 0.8;">Wonkwang Univ. College of Korean Med. Acupoint Handbook Portal</span>
          </h1>
          <p>14경맥 361종 표준 경혈 정본: 원광대 한의과대학 핸드북 · 7대 문헌군 자침깊이 · 황룡상 고증 침구법 · KCD-8 질병코드 · KJH 경혈명 및 이명 대조</p>
        </div>
        <div class="header-badges">
          <span class="page-view-counter" style="display:inline-flex;align-items:center;margin:0 4px;vertical-align:middle;" title="Views 열람 횟수"><a href="https://hits.sh/jaehyokim-sketch.github.io/acupoint_anatomy/tools/acupoint-handbook.html/" target="_blank" rel="noopener noreferrer" style="text-decoration:none;display:inline-flex;align-items:center;"><img src="https://hits.sh/jaehyokim-sketch.github.io/acupoint_anatomy/tools/acupoint-handbook.html.svg?style=flat-square&label=%EC%A1%B0%ED%9A%8C%EC%88%98&color=2563eb&labelColor=0f172a" alt="Views" style="height:20px;vertical-align:middle;border-radius:3px;" /></a></span>
          <span class="badge gold">14경맥 361혈 전수 완비</span>
          <span class="badge">7대 문헌군 자침깊이</span>
          <span class="badge">황룡상 침구법 &amp; KCD-8</span>
          <span class="badge rose">⚠️ 본명-이명 혼동주의 35쌍 경보</span>
          <a class="badge lang-switch" style="text-decoration: none; color: inherit;" href="acupoint-handbook-en.html" title="English edition">🌐 English</a>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="search-filter-bar">
        <div class="search-box">
          <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input type="text" id="searchInput" placeholder="경혈코드, 국문명, 한자, 이명, 위치, 근육, 신경, 혈관, 주치증, KCD 검색...">
        </div>
        <select class="filter-select" id="meridianFilter">
          <option value="ALL">전체 경맥 (All Meridians)</option>
        </select>
        <select class="filter-select" id="methodFilter">
          <option value="ALL">전체 자침법 (All Methods)</option>
          <option value="직자">직자 (Perpendicular)</option>
          <option value="사자">사자 (Oblique)</option>
          <option value="횡자">횡자 / 연피자 (Transverse)</option>
        </select>
        <select class="filter-select" id="specialFilter">
          <option value="ALL">전체 혈위 (모든 항목)</option>
          <option value="homonym">⚠️ 본명-이명 혼동주의 (34혈)</option>
          <option value="muscle">근육(Muscles) 포함</option>
          <option value="nerve">신경(Nerves) 포함</option>
          <option value="vessel">혈관(Vessels) 포함</option>
        </select>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="stats-strip">
      <div class="stat-card">
        <span class="label">수록 경맥</span>
        <span class="value">14 Meridians</span>
      </div>
      <div class="stat-card">
        <span class="label">표준 경혈수</span>
        <span class="value">361 Acupoints</span>
      </div>
      <div class="stat-card">
        <span class="label">검색된 경혈</span>
        <span class="value" id="filteredCount">361</span>
      </div>
      <div class="stat-card">
        <span class="label">본명-이명 혼동주의</span>
        <span class="value" style="color: #e11d48;">35 Pairs (34혈)</span>
      </div>
    </div>

    <!-- Meridian Pills -->
    <div class="meridian-tabs" id="meridianTabs">
      <button class="meridian-pill active" data-meridian="ALL">전체 <span class="pill-count">361</span></button>
    </div>

    <!-- Points Grid -->
    <div class="points-grid" id="pointsGrid">
    </div>
  </div>

  <button class="btn-top" onclick="window.scrollTo({top: 0, behavior: 'smooth'})" title="맨 위로">
    <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/></svg>
  </button>

  <footer>
    <p><strong>원광대학교 한의과대학 경혈학 핸드북 포털 (Wonkwang Univ. College of Korean Med. Acupoint Handbook Portal) v1.2</strong></p>
    <p>학술 고증 및 데이터 출처: 《핸드북(한 영) 한글판》 (원광대학교 한의과대학 경혈학교실 &amp; 최수빈(KMD)) · 《침구문헌별 자침깊이 정리_AI 분석용》 (황제명당경·침구갑을경·침구경험방·동의보감·경락수혈학·침구의학·침구수혈통고) · 《김재효 수업_경혈_해부구조_데이터셋》 · 《경혈학공통교재 해부구조 데이터셋》 · 《경혈별 주치증 정리 V2》 (황룡상 교수 고증 침구법 &amp; KCD-8 질병코드 연계) · 《경혈명_비교_정리_KJH》 (표준 한자명·이명 및 본명-이명 일치 Case A 경보)</p>
    <p style="margin-top: 0.5rem;">© 2026 Jae-Hyo Kim. All Rights Reserved. Hosted via GitHub Pages.</p>
  </footer>

  <script>
    const POINTS_DATA = %%POINTS_DATA%%;
    const MERIDIANS = %%MERIDIANS%%;

    const pointsGrid = document.getElementById('pointsGrid');
    const searchInput = document.getElementById('searchInput');
    const meridianFilter = document.getElementById('meridianFilter');
    const methodFilter = document.getElementById('methodFilter');
    const specialFilter = document.getElementById('specialFilter');
    const filteredCount = document.getElementById('filteredCount');
    const meridianTabs = document.getElementById('meridianTabs');

    // Populate Meridian options & tabs
    MERIDIANS.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.code;
      opt.textContent = `${m.name} (${m.code}) - ${m.count}혈`;
      meridianFilter.appendChild(opt);

      const pill = document.createElement('button');
      pill.className = 'meridian-pill';
      pill.dataset.meridian = m.code;
      pill.innerHTML = `${m.name} <span class="pill-count">${m.count}</span>`;
      pill.addEventListener('click', () => {
        setMeridianFilter(m.code);
      });
      meridianTabs.appendChild(pill);
    });

    function setMeridianFilter(code) {
      meridianFilter.value = code;
      document.querySelectorAll('.meridian-pill').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.meridian === code);
      });
      renderPoints();
    }

    meridianFilter.addEventListener('change', (e) => setMeridianFilter(e.target.value));
    methodFilter.addEventListener('change', renderPoints);
    specialFilter.addEventListener('change', renderPoints);
    searchInput.addEventListener('input', renderPoints);

    function jumpToPoint(code) {
      searchInput.value = code;
      meridianFilter.value = 'ALL';
      methodFilter.value = 'ALL';
      specialFilter.value = 'ALL';
      document.querySelectorAll('.meridian-pill').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.meridian === 'ALL');
      });
      renderPoints();
      window.scrollTo({top: 180, behavior: 'smooth'});
    }

    function renderPoints() {
      const q = searchInput.value.trim().toLowerCase();
      const selectedMeridian = meridianFilter.value;
      const selectedMethod = methodFilter.value;
      const selectedSpecial = specialFilter.value;

      const filtered = POINTS_DATA.filter(p => {
        if (selectedMeridian !== 'ALL' && p.meridian_ab !== selectedMeridian) return false;

        // Method filter
        if (selectedMethod !== 'ALL') {
          const methods = (p.depth_literature.common_method + ' ' + p.depth_literature.tongkao_method).toLowerCase();
          if (!methods.includes(selectedMethod.toLowerCase())) return false;
        }

        // Special filter
        if (selectedSpecial === 'homonym') {
          if (!p.homonym_matches || p.homonym_matches.length === 0) return false;
        } else if (selectedSpecial === 'muscle') {
          if (!p.anatomy.kjh.muscle_ko || p.anatomy.kjh.muscle_ko.length === 0) return false;
        } else if (selectedSpecial === 'nerve') {
          if (!p.anatomy.kjh.nerve_ko || p.anatomy.kjh.nerve_ko.length === 0) return false;
        } else if (selectedSpecial === 'vessel') {
          if (!p.anatomy.kjh.vessel_ko || p.anatomy.kjh.vessel_ko.length === 0) return false;
        }

        if (!q) return true;

        const matchCode = p.code.toLowerCase().includes(q);
        const matchName = p.name.toLowerCase().includes(q);
        const matchHanja = p.hanja.includes(q);
        const slideHanja = (p.kjh_naming && p.kjh_naming.slide_hanja) ? p.kjh_naming.slide_hanja : '';
        const matchSlideHanja = slideHanja.includes(q);
        const matchAliases = (p.aliases || '').toLowerCase().includes(q);
        const matchLoc = (p.handbook.location || '').toLowerCase().includes(q);
        const matchFind = (p.handbook.find_method || '').toLowerCase().includes(q);

        const matchAnatKjh = (p.anatomy.kjh.muscle_bilingual + ' ' + p.anatomy.kjh.nerve_bilingual + ' ' + p.anatomy.kjh.vessel_bilingual).toLowerCase().includes(q);

        // match literature depths
        const dl = p.depth_literature;
        const matchDepth = (dl.common_method + ' ' + dl.tongkao_method + ' ' + dl.dongui_source).toLowerCase().includes(q);

        // match homonym matches
        let matchHomonym = false;
        if (p.homonym_matches && p.homonym_matches.length > 0) {
          for (const hm of p.homonym_matches) {
            if ((hm.match_alias && hm.match_alias.includes(q)) ||
                (hm.match_pronunciation && hm.match_pronunciation.toLowerCase().includes(q)) ||
                (hm.target_code && hm.target_code.toLowerCase().includes(q)) ||
                (hm.target_name && hm.target_name.toLowerCase().includes(q)) ||
                (hm.target_hanja && hm.target_hanja.includes(q))) {
              matchHomonym = true;
              break;
            }
          }
        }

        // match indications & kcd
        let matchInd = false;
        if (p.indications && p.indications.categories) {
          for (const cat of p.indications.categories) {
            if (cat.category.toLowerCase().includes(q)) { matchInd = true; break; }
            for (const item of cat.items) {
              if (item.ind.toLowerCase().includes(q) || item.kcd.toLowerCase().includes(q)) {
                matchInd = true;
                break;
              }
            }
            if (matchInd) break;
          }
        }

        return matchCode || matchName || matchHanja || matchSlideHanja || matchAliases || matchHomonym || matchLoc || matchFind || matchAnatKjh || matchDepth || matchInd;
      });

      filteredCount.textContent = filtered.length;
      pointsGrid.innerHTML = '';

      if (filtered.length === 0) {
        pointsGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: #64748b; font-size: 1.1rem;">검색 조건과 일치하는 경혈이 없습니다.</div>';
        return;
      }

      filtered.forEach(p => {
        const card = document.createElement('div');
        card.className = 'point-card';
        card.id = `point-${p.code}`;

        const mInfo = MERIDIANS.find(m => m.code === p.meridian_ab) || { color: '#1e3a8a' };

        // Indications HTML
        let indicationsHtml = '';
        if (p.indications && p.indications.categories && p.indications.categories.length > 0) {
          indicationsHtml = p.indications.categories.map(cat => `
            <div class="indication-group">
              <span class="cat-title">${escapeHtml(cat.category)}</span>
              <div class="ind-pill-list">
                ${cat.items.map(it => `
                  <span class="ind-pill">
                    <span>${escapeHtml(it.ind)}</span>
                    ${it.kcd ? `<span class="kcd-tag">${escapeHtml(it.kcd)}</span>` : ''}
                  </span>
                `).join('')}
              </div>
            </div>
          `).join('');
        } else {
          indicationsHtml = '<span style="color: #94a3b8; font-size: 0.85rem;">주치증 데이터 없음</span>';
        }

        // Anatomy
        const kjhMuscles = p.anatomy.kjh.muscle_bilingual ? p.anatomy.kjh.muscle_bilingual.split('\\n') : [];
        const kjhNerves = p.anatomy.kjh.nerve_bilingual ? p.anatomy.kjh.nerve_bilingual.split('\\n') : [];
        const kjhVessels = p.anatomy.kjh.vessel_bilingual ? p.anatomy.kjh.vessel_bilingual.split('\\n') : [];

        const comMuscles = p.anatomy.common.muscle_ko || [];
        const comNerves = p.anatomy.common.nerve_ko || [];
        const comVessels = p.anatomy.common.vessel_ko || [];

        const dl = p.depth_literature;

        // Slide hanja & Aliases
        const slideHanja = (p.kjh_naming && p.kjh_naming.slide_hanja) ? p.kjh_naming.slide_hanja : '';
        const aliasesText = p.aliases || (p.kjh_naming && p.kjh_naming.aliases_hanja) || '';

        // Homonym matches alert HTML
        let homonymAlertHtml = '';
        if (p.homonym_matches && p.homonym_matches.length > 0) {
          homonymAlertHtml = `
            <div class="homonym-alert-box">
              <div class="homonym-header">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                <span>⚠️ 본명-이명 혼동주의 (Case A: 타 경혈 정명과 일치)</span>
              </div>
              <div class="homonym-pair-list">
                ${p.homonym_matches.map(hm => `
                  <div class="homonym-pair-item">
                    • 이명 <strong>「${escapeHtml(hm.match_alias)}」</strong>(${escapeHtml(hm.match_pronunciation || '')})은
                    <span class="homonym-target-badge" onclick="jumpToPoint('${escapeHtml(hm.target_code)}')">
                      ${escapeHtml(hm.target_code)} ${escapeHtml(hm.target_name)}(${escapeHtml(hm.target_hanja)})
                    </span>
                    의 본명(정명)과 일치함
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="card-header">
            <div class="card-title-group">
              <div class="card-title-top">
                <span class="point-code">${p.code}</span>
                <span class="point-name">${p.name}</span>
                <span class="point-hanja">${p.hanja}</span>
                ${slideHanja && slideHanja !== p.hanja ? `<span class="slide-hanja-badge" title="강의슬라이드 표기 한자">교재: ${escapeHtml(slideHanja)}</span>` : ''}
              </div>
              ${aliasesText ? `
                <div class="aliases-row">
                  <strong>[이명]</strong> <span>${escapeHtml(aliasesText)}</span>
                </div>
              ` : ''}
            </div>
            <span class="meridian-tag" style="background-color: ${mInfo.color};">${p.meridian_ko}</span>
          </div>

          ${homonymAlertHtml}

          <div class="card-body">
            <!-- Location & Find Method -->
            <div class="section-block">
              <span class="section-label">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                위치 및 취혈 (Location & Method)
              </span>
              <div class="section-content">
                <strong>[부위]</strong> ${escapeHtml(p.handbook.location || '위치 기술 준비 중')}<br>
                ${p.handbook.find_method ? `<strong>[취혈]</strong> ${escapeHtml(p.handbook.find_method)}` : ''}
              </div>
            </div>

            <!-- Puncture & Moxa with Literature Table -->
            <div class="puncture-summary">
              <div class="puncture-row-top">
                <span><strong>황제명당경:</strong> <span class="puncture-val-badge">${dl.mingtang}</span></span>
                <span><strong>뜸법:</strong> <span class="puncture-val-badge">${p.indications.moxa_huanglongxiang ? p.indications.moxa_huanglongxiang + ' 장' : '-'}</span></span>
                ${dl.common_method ? `<span><strong>자침법:</strong> <span class="method-tag">${escapeHtml(dl.common_method)}</span></span>` : ''}
                ${dl.tongkao_method && dl.tongkao_method !== dl.common_method ? `<span><strong>통고 자침법:</strong> <span class="method-tag">${escapeHtml(dl.tongkao_method)}</span></span>` : ''}
              </div>

              <!-- Literature Depth Comparison Table -->
              <div class="depth-table-wrapper">
                <table class="depth-table">
                  <thead>
                    <tr>
                      <th>침구갑을경</th>
                      <th>침구경험방</th>
                      <th>동의보감</th>
                      <th>경락수혈학</th>
                      <th>침구의학</th>
                      <th>침구수혈통고</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>${dl.jiayijing}</td>
                      <td>${dl.jingyanfang}</td>
                      <td>${dl.donguibogam} ${dl.dongui_source ? `<span style="font-size:0.7rem; color:#64748b;">(${escapeHtml(dl.dongui_source)})</span>` : ''}</td>
                      <td>${dl.common_range}</td>
                      <td>${dl.acupuncture_range}</td>
                      <td>${dl.tongkao_range}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Caution if present -->
            ${p.handbook.caution ? `
              <div class="caution-box">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                <div><strong>Caution:</strong> ${escapeHtml(p.handbook.caution)}</div>
              </div>
            ` : ''}

            <!-- Anatomy Dataset -->
            <div class="anatomy-box">
              <div class="anatomy-header" onclick="toggleAccordion(this)">
                <span>해부학적 구조 (Anatomical Structures)</span>
                <span style="font-size: 0.75rem; color: var(--primary);">상세보기 ▼</span>
              </div>
              <div class="anatomy-body" style="display: none;">
                <div>
                  <div class="anatomy-group-title">근육 (Muscles) - 김재효 수업자료</div>
                  <div class="anatomy-items">
                    ${kjhMuscles.length > 0 ? kjhMuscles.map(m => `<div class="anat-item">• ${escapeHtml(m)}</div>`).join('') : '<div style="color: #94a3b8;">-</div>'}
                  </div>
                  ${comMuscles.length > 0 ? `
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.25rem;">
                      <strong>공통교재 대조:</strong> ${escapeHtml(comMuscles.join(', '))}
                    </div>
                  ` : ''}
                </div>

                <div>
                  <div class="anatomy-group-title">신경 (Nerves) - 김재효 수업자료</div>
                  <div class="anatomy-items">
                    ${kjhNerves.length > 0 ? kjhNerves.map(n => `<div class="anat-item">• ${escapeHtml(n)}</div>`).join('') : '<div style="color: #94a3b8;">-</div>'}
                  </div>
                  ${comNerves.length > 0 ? `
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.25rem;">
                      <strong>공통교재 대조:</strong> ${escapeHtml(comNerves.join(', '))}
                    </div>
                  ` : ''}
                </div>

                <div>
                  <div class="anatomy-group-title">혈관 (Vessels) - 김재효 수업자료</div>
                  <div class="anatomy-items">
                    ${kjhVessels.length > 0 ? kjhVessels.map(v => `<div class="anat-item">• ${escapeHtml(v)}</div>`).join('') : '<div style="color: #94a3b8;">-</div>'}
                  </div>
                  ${comVessels.length > 0 ? `
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.25rem;">
                      <strong>공통교재 대조:</strong> ${escapeHtml(comVessels.join(', '))}
                    </div>
                  ` : ''}
                </div>
              </div>
            </div>

            <!-- Indications with KCD -->
            <div class="section-block">
              <span class="section-label">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                주치증 및 표준 KCD 질병분류 (Indications &amp; KCD-8)
              </span>
              <div class="section-content">
                ${indicationsHtml}
              </div>
            </div>

          </div>
        `;
        pointsGrid.appendChild(card);
      });
    }

    function toggleAccordion(el) {
      const body = el.nextElementSibling;
      const arrow = el.querySelector('span:last-child');
      if (body.style.display === 'none') {
        body.style.display = 'flex';
        arrow.textContent = '상세보기 ▲';
      } else {
        body.style.display = 'none';
        arrow.textContent = '상세보기 ▼';
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    renderPoints();
  </script>
</body>
</html>
"""

final_html = html_template.replace("%%POINTS_DATA%%", json.dumps(points, ensure_ascii=False))
final_html = final_html.replace("%%MERIDIANS%%", json.dumps(meridians, ensure_ascii=False))



def main():
    ap = argparse.ArgumentParser(description="경혈학 핸드북 포털(한국어판) 생성기")
    ap.add_argument("--no-en", action="store_true", help="영문판을 다시 만들지 않음")
    ap.add_argument("--no-lecture-copy", action="store_true", help="강의 폴더에 복사하지 않음")
    args = ap.parse_args()

    with open(DEST_HTML, "w", encoding="utf-8") as f:  # Windows 텍스트 모드 → CRLF (기존 파일과 동일)
        f.write(final_html)
    print(f"Saved {DEST_HTML} ({os.path.getsize(DEST_HTML):,} bytes)")

    if not args.no_en:
        r = subprocess.run([sys.executable, EN_BUILDER])
        if r.returncode != 0:
            sys.exit("[ERROR] 영문판 생성 실패 - translations_en.json·indications_en.json에 새 항목 번역을 추가할 것")

    if args.no_lecture_copy:
        return
    if not os.path.isdir(LECTURE_DIR):
        print(f"[SKIP] 강의 폴더 없음: {LECTURE_DIR} (환경변수 ACUPOINT_LECTURE_DIR로 지정 가능)")
        return
    for src_path, name in LECTURE_COPIES.items():
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(LECTURE_DIR, name))
            print(f"Copied -> {os.path.join(LECTURE_DIR, name)}")


if __name__ == "__main__":
    main()

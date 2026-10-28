import urllib.parse, sys
from pathlib import Path
from bilingual_data import BILINGUAL_CARDS

sys.stdout.reconfigure(encoding='utf-8')
repo_root = Path(r'C:\workspace\acupoint_anatomy')

# 1. 디스크 상의 모든 HTML 파일 맵 구축
all_htmls = {}
for p in repo_root.rglob('*.html'):
    if '_archive' in p.parts:
        continue
    rel = p.relative_to(repo_root).as_posix()
    encoded_parts = [urllib.parse.quote(part) for part in rel.split('/')]
    encoded_rel = '/'.join(encoded_parts)
    all_htmls[p.name] = (rel, encoded_rel)

# 2. 각 카드의 링크를 실제 디스크 파일 기준으로 자동 정정
for c in BILINGUAL_CARDS:
    if c.get('btn_ko'):
        old_fn = urllib.parse.unquote(c['btn_ko']).split('/')[-1]
        for fn in all_htmls:
            if fn == old_fn or (old_fn.replace('쵔', '최').replace('관쓰', '관원') == fn):
                c['btn_ko'] = all_htmls[fn][1]
                break
    if c.get('btn_en'):
        old_fn = urllib.parse.unquote(c['btn_en']).split('/')[-1]
        for fn in all_htmls:
            if fn == old_fn or (old_fn.replace('쵔', '최').replace('관쓰', '관원') == fn):
                c['btn_en'] = all_htmls[fn][1]
                break

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko" data-lang-mode="both">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>경혈 해부생리학 & 침구 임상 분석 포털 | Acupoint Anatomy & Clinical Acupuncture Archive</title>
  <meta name="description" content="경락, 경혈 및 침구의학 문헌 통감 전수 고증, 한대(漢代) 도량형 실측 심도 및 Layer B 4계층 참조 등록부·생의학 DB 기반 경혈 및 침구 임상 해부생리 분석 포털"/>
  <meta property="og:title" content="Acupoint Anatomy & Clinical Acupuncture Archive | 경혈 해부생리학 포털"/>
  <meta property="og:description" content="경락, 경혈 및 침구의학 문헌 통감 전수 고증 및 신경해부학 실체 판명 디지털 아카이브"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&family=Noto+Sans+KR:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800;900&display=swap" rel="stylesheet"/>
  
  <style>
    :root {
      --bg-dark: #050811;
      --bg-surface: #0a0f1d;
      --bg-card: rgba(13, 20, 36, 0.72);
      --bg-card-hover: rgba(20, 31, 56, 0.85);
      --primary-cyan: #06B6D4;
      --primary-blue: #3B82F6;
      --accent-indigo: #6366F1;
      --accent-amber: #F59E0B;
      --accent-emerald: #10B981;
      --accent-rose: #F43F5E;
      --text-white: #FFFFFF;
      --text-primary: #F1F5F9;
      --text-secondary: #94A3B8;
      --text-muted: #64748B;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-highlight: rgba(6, 182, 212, 0.35);
      --glass-blur: blur(16px);
      --transition-smooth: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Noto Sans KR', 'Inter', -apple-system, sans-serif;
      background: var(--bg-dark);
      color: var(--text-primary);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background-image: 
        radial-gradient(circle at 12% 18%, rgba(6, 182, 212, 0.12), transparent 38%),
        radial-gradient(circle at 88% 22%, rgba(99, 102, 241, 0.14), transparent 42%),
        radial-gradient(circle at 50% 65%, rgba(59, 130, 246, 0.07), transparent 55%),
        radial-gradient(circle at 80% 85%, rgba(245, 158, 11, 0.06), transparent 40%);
      background-attachment: fixed;
      overflow-x: hidden;
    }

    /* Header & Navigation */
    header {
      background: rgba(8, 13, 24, 0.82);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border-bottom: 1px solid var(--border-subtle);
      position: sticky;
      top: 0;
      z-index: 100;
      transition: var(--transition-smooth);
    }

    .nav-container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
      text-decoration: none;
    }

    .brand-icon {
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px rgba(6, 182, 212, 0.45);
      flex-shrink: 0;
    }

    .brand-text h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 1.18rem;
      font-weight: 800;
      color: var(--text-white);
      letter-spacing: -0.3px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-text h1 .badge-ver {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      font-weight: 700;
      color: var(--primary-cyan);
      background: rgba(6, 182, 212, 0.15);
      padding: 2px 7px;
      border-radius: 6px;
      border: 1px solid rgba(6, 182, 212, 0.3);
    }

    .brand-text p {
      font-size: 0.78rem;
      color: var(--text-secondary);
      font-weight: 400;
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    /* Language Switcher */
    .lang-switcher {
      display: flex;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--border-subtle);
      border-radius: 30px;
      padding: 3px;
      gap: 2px;
    }

    .lang-btn {
      background: transparent;
      border: none;
      color: var(--text-secondary);
      font-family: 'Outfit', 'Noto Sans KR', sans-serif;
      font-size: 0.76rem;
      font-weight: 700;
      padding: 5px 12px;
      border-radius: 20px;
      cursor: pointer;
      transition: var(--transition-smooth);
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .lang-btn:hover {
      color: var(--text-white);
    }

    .lang-btn.active {
      background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
      color: var(--text-white);
      box-shadow: 0 0 12px rgba(6, 182, 212, 0.4);
    }

    .live-badge {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34D399;
      font-size: 0.76rem;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 30px;
    }

    .live-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #10B981;
      box-shadow: 0 0 8px #10B981;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    /* Hero Section */
    .hero {
      max-width: 1400px;
      margin: 0 auto;
      padding: 56px 28px 24px 28px;
      text-align: center;
    }

    .hero-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      font-weight: 700;
      color: var(--primary-cyan);
      background: rgba(6, 182, 212, 0.09);
      padding: 6px 16px;
      border-radius: 30px;
      border: 1px solid rgba(6, 182, 212, 0.25);
      margin-bottom: 20px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .hero h2 {
      font-family: 'Outfit', 'Noto Sans KR', sans-serif;
      font-size: 2.75rem;
      font-weight: 900;
      color: var(--text-white);
      line-height: 1.25;
      margin-bottom: 14px;
      letter-spacing: -0.8px;
    }

    .hero h2 span.gradient-text {
      background: linear-gradient(135deg, #38BDF8 10%, #818CF8 50%, #F472B6 90%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .hero h2 .hero-en-sub {
      display: block;
      font-size: 1.28rem;
      font-weight: 600;
      color: #94A3B8;
      margin-top: 6px;
      letter-spacing: -0.2px;
    }

    .hero-descriptions {
      max-width: 920px;
      margin: 0 auto 36px auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .hero-desc-ko {
      font-size: 1.02rem;
      color: #CBD5E1;
      line-height: 1.7;
    }

    .hero-desc-en {
      font-size: 0.92rem;
      color: #94A3B8;
      line-height: 1.6;
      font-family: 'Inter', sans-serif;
      padding-top: 4px;
      border-top: 1px dashed rgba(255, 255, 255, 0.08);
    }

    /* Stats Bar */
    .stats-bar {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      max-width: 1100px;
      margin: 0 auto 40px auto;
    }

    .stat-card {
      background: var(--bg-card);
      backdrop-filter: var(--glass-blur);
      border: 1px solid var(--border-subtle);
      border-radius: 14px;
      padding: 18px 20px;
      text-align: center;
      transition: var(--transition-smooth);
      position: relative;
      overflow: hidden;
    }

    .stat-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--primary-cyan), transparent);
      opacity: 0;
      transition: var(--transition-smooth);
    }

    .stat-card:hover {
      border-color: var(--border-highlight);
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }

    .stat-card:hover::before {
      opacity: 1;
    }

    .stat-num {
      font-family: 'Outfit', sans-serif;
      font-size: 1.85rem;
      font-weight: 800;
      color: #38BDF8;
      display: block;
      line-height: 1.2;
    }

    .stat-label-ko {
      font-size: 0.84rem;
      font-weight: 600;
      color: var(--text-primary);
      margin-top: 4px;
    }

    .stat-label-en {
      font-size: 0.72rem;
      color: var(--text-muted);
      font-family: 'Inter', sans-serif;
      display: block;
    }

    /* Controls: Search & Filter */
    .controls {
      max-width: 1400px;
      margin: 0 auto 28px auto;
      padding: 0 28px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .search-row {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 12px;
      max-width: 800px;
      margin: 0 auto;
      width: 100%;
    }

    .search-box {
      position: relative;
      flex: 1;
      width: 100%;
    }

    .search-icon {
      position: absolute;
      left: 18px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
      transition: color 0.2s;
    }

    .search-input {
      width: 100%;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--border-subtle);
      color: var(--text-white);
      padding: 14px 44px 14px 48px;
      border-radius: 14px;
      font-size: 0.96rem;
      outline: none;
      transition: var(--transition-smooth);
    }

    .search-input:focus {
      border-color: var(--primary-cyan);
      box-shadow: 0 0 24px rgba(6, 182, 212, 0.3);
      background: rgba(15, 23, 42, 0.98);
    }

    .search-input:focus + .search-icon {
      color: var(--primary-cyan);
    }

    .search-clear {
      position: absolute;
      right: 14px;
      top: 50%;
      transform: translateY(-50%);
      background: rgba(255, 255, 255, 0.1);
      border: none;
      color: var(--text-muted);
      width: 22px;
      height: 22px;
      border-radius: 50%;
      cursor: pointer;
      display: none;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      line-height: 1;
    }

    .search-clear:hover {
      background: rgba(255, 255, 255, 0.2);
      color: var(--text-white);
    }

    .results-count-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--primary-cyan);
      background: rgba(6, 182, 212, 0.1);
      border: 1px solid rgba(6, 182, 212, 0.25);
      padding: 12px 16px;
      border-radius: 12px;
      white-space: nowrap;
    }

    .filter-tabs {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 10px;
    }

    .tab-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      padding: 8px 18px;
      border-radius: 30px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: var(--transition-smooth);
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .tab-btn:hover {
      background: rgba(255, 255, 255, 0.09);
      color: var(--text-white);
      transform: translateY(-1px);
    }

    .tab-btn.active {
      background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
      color: var(--text-white);
      border-color: transparent;
      box-shadow: 0 0 18px rgba(6, 182, 212, 0.4);
    }

    .tab-count {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      opacity: 0.85;
      background: rgba(0, 0, 0, 0.25);
      padding: 1px 6px;
      border-radius: 10px;
    }

    /* Grid Section */
    .grid-section {
      max-width: 1400px;
      margin: 0 auto;
      padding: 0 28px 70px 28px;
      flex: 1;
    }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 24px;
    }

    /* Card Component */
    .card {
      background: var(--bg-card);
      backdrop-filter: var(--glass-blur);
      -webkit-backdrop-filter: var(--glass-blur);
      border: 1px solid var(--border-subtle);
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      transition: transform 0.25s, box-shadow 0.25s, border-color 0.25s;
      position: relative;
      overflow: hidden;
    }

    .card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--primary-cyan), var(--primary-blue), var(--accent-indigo));
      opacity: 0;
      transition: opacity 0.25s;
    }

    .card:hover {
      transform: translateY(-5px);
      background: var(--bg-card-hover);
      border-color: var(--border-highlight);
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.45), 0 0 24px rgba(6, 182, 212, 0.16);
    }

    .card:hover::before {
      opacity: 1;
    }

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      gap: 8px;
    }

    .code-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 7px;
      letter-spacing: 0.3px;
      white-space: nowrap;
    }

    .status-badge {
      font-size: 0.74rem;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 12px;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
      max-width: 65%;
    }

    .card-title-group {
      margin-bottom: 12px;
    }

    .card-title-ko {
      font-family: 'Outfit', 'Noto Sans KR', sans-serif;
      font-size: 1.28rem;
      font-weight: 800;
      color: var(--text-white);
      line-height: 1.35;
      letter-spacing: -0.3px;
    }

    .card-title-en {
      font-family: 'Inter', sans-serif;
      font-size: 0.90rem;
      font-weight: 600;
      color: #93C5FD;
      margin-top: 3px;
      line-height: 1.35;
    }

    .card-subtitle {
      font-size: 0.82rem;
      color: var(--text-muted);
      margin-top: 4px;
      line-height: 1.45;
    }

    .card-subtitle .sub-ko {
      display: block;
      color: #94A3B8;
      font-weight: 500;
    }

    .card-subtitle .sub-en {
      display: block;
      color: #64748B;
      font-family: 'Inter', sans-serif;
      font-size: 0.77rem;
    }

    .card-desc {
      font-size: 0.88rem;
      line-height: 1.65;
      margin-bottom: 18px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .desc-ko {
      color: #E2E8F0;
    }

    .desc-en {
      color: #94A3B8;
      font-family: 'Inter', sans-serif;
      font-size: 0.83rem;
      padding-top: 8px;
      border-top: 1px dashed rgba(255, 255, 255, 0.07);
    }

    /* Language Display Modes */
    [data-lang-mode="ko"] .card-title-en,
    [data-lang-mode="ko"] .hero-desc-en,
    [data-lang-mode="ko"] .hero-en-sub,
    [data-lang-mode="ko"] .stat-label-en,
    [data-lang-mode="ko"] .sub-en,
    [data-lang-mode="ko"] .desc-en {
      display: none !important;
    }

    [data-lang-mode="en"] .card-title-ko,
    [data-lang-mode="en"] .hero-desc-ko,
    [data-lang-mode="en"] .stat-label-ko,
    [data-lang-mode="en"] .sub-ko,
    [data-lang-mode="en"] .desc-ko {
      display: none !important;
    }

    [data-lang-mode="en"] .card-title-en {
      font-size: 1.24rem;
      color: var(--text-white);
    }

    .tags-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 18px;
    }

    .tag {
      font-size: 0.72rem;
      background: rgba(255, 255, 255, 0.04);
      color: #94A3B8;
      padding: 2px 8px;
      border-radius: 5px;
      border: 1px solid rgba(255, 255, 255, 0.06);
      transition: var(--transition-smooth);
    }

    .tag:hover {
      background: rgba(255, 255, 255, 0.08);
      color: #E2E8F0;
      border-color: rgba(255, 255, 255, 0.14);
    }

    .card-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 14px;
      border-top: 1px solid var(--border-subtle);
      gap: 10px;
    }

    .category-indicator {
      font-size: 0.77rem;
      color: var(--text-muted);
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 5px;
    }

    .btn-group {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      flex-wrap: wrap;
    }

    .btn-open {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.79rem;
      font-weight: 700;
      padding: 6px 13px;
      border-radius: 8px;
      text-decoration: none;
      transition: var(--transition-smooth);
      line-height: 1.2;
    }

    .lang-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem;
      font-weight: 800;
      padding: 1px 4px;
      border-radius: 4px;
      letter-spacing: 0.4px;
    }

    .btn-ko {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.16), rgba(59, 130, 246, 0.22));
      border: 1px solid rgba(6, 182, 212, 0.42);
      color: #38BDF8;
    }

    .btn-ko .lang-pill {
      background: rgba(6, 182, 212, 0.32);
      color: #E0F2FE;
    }

    .btn-ko:hover {
      background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
      color: #FFFFFF;
      border-color: transparent;
      transform: translateY(-2px);
      box-shadow: 0 4px 14px rgba(6, 182, 212, 0.4);
    }

    .btn-en {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.22));
      border: 1px solid rgba(245, 158, 11, 0.42);
      color: #FBBF24;
    }

    .btn-en .lang-pill {
      background: rgba(245, 158, 11, 0.30);
      color: #FEF3C7;
    }

    .btn-en:hover {
      background: linear-gradient(135deg, #F59E0B, #D97706);
      color: #FFFFFF;
      border-color: transparent;
      transform: translateY(-2px);
      box-shadow: 0 4px 14px rgba(245, 158, 11, 0.4);
    }

    .btn-open svg {
      transition: transform 0.2s;
    }

    .btn-open:hover svg {
      transform: translateX(2px);
    }

    /* No results message */
    .no-results {
      text-align: center;
      padding: 80px 20px;
      color: var(--text-muted);
      font-size: 1.15rem;
      display: none;
      grid-column: 1 / -1;
    }

    .no-results svg {
      margin-bottom: 14px;
      color: var(--text-muted);
      opacity: 0.6;
    }

    /* Scroll to Top Floating Button */
    .scroll-top-btn {
      position: fixed;
      bottom: 28px;
      right: 28px;
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: var(--glass-blur);
      border: 1px solid var(--border-subtle);
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      opacity: 0;
      pointer-events: none;
      transition: var(--transition-smooth);
      z-index: 90;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
    }

    .scroll-top-btn.visible {
      opacity: 1;
      pointer-events: auto;
    }

    .scroll-top-btn:hover {
      background: linear-gradient(135deg, var(--primary-cyan), var(--primary-blue));
      color: var(--text-white);
      border-color: transparent;
      transform: translateY(-3px);
      box-shadow: 0 10px 26px rgba(6, 182, 212, 0.4);
    }

    /* Footer */
    footer {
      background: rgba(8, 13, 24, 0.92);
      border-top: 1px solid var(--border-subtle);
      padding: 36px 28px;
      margin-top: auto;
    }

    .footer-content {
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.84rem;
      color: var(--text-muted);
      gap: 16px;
    }

    .footer-left p {
      margin-bottom: 4px;
    }

    .footer-badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .f-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      background: rgba(255, 255, 255, 0.04);
      padding: 2px 8px;
      border-radius: 5px;
      border: 1px solid var(--border-subtle);
    }

    /* Responsive */
    @media (max-width: 900px) {
      .hero h2 { font-size: 2.15rem; }
      .hero h2 .hero-en-sub { font-size: 1.05rem; }
      .stats-bar { grid-template-columns: repeat(2, 1fr); }
      .cards-grid { grid-template-columns: 1fr; }
      .footer-content { flex-direction: column; text-align: center; }
    }

    @media (max-width: 580px) {
      .nav-container { padding: 12px 18px; }
      .brand-text p { display: none; }
      .hero { padding: 40px 18px 20px 18px; }
      .hero h2 { font-size: 1.85rem; }
      .stats-bar { grid-template-columns: 1fr; }
      .search-row { flex-direction: column; }
      .results-count-badge { width: 100%; text-align: center; }
      .card-footer { flex-direction: column; align-items: flex-start; gap: 12px; }
      .btn-group { width: 100%; justify-content: flex-start; }
    }
  </style>
</head>
<body>

  <!-- Navigation Header -->
  <header>
    <div class="nav-container">
      <a class="brand" href="index.html">
        <div class="brand-icon">
          <svg fill="none" height="24" stroke="#FFFFFF" stroke-width="2.2" viewBox="0 0 24 24" width="24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path>
          </svg>
        </div>
        <div class="brand-text">
          <h1>ACUPOINT ANATOMY PORTAL <span class="badge-ver">v2.7</span></h1>
          <p>경혈 해부생리학 실체 판명 &amp; 침구 임상 분석 아카이브</p>
        </div>
      </a>
      <div class="nav-actions">
        <!-- Language Switcher -->
        <div class="lang-switcher" id="langSwitcher">
          <button class="lang-btn active" data-lang="both" title="한글과 영어 모두 표시 (Bilingual Display)">
            <span>🌐</span> Both
          </button>
          <button class="lang-btn" data-lang="ko" title="한국어만 표시 (Korean Only)">
            <span>🇰🇷</span> 한국어
          </button>
          <button class="lang-btn" data-lang="en" title="English Only">
            <span>🇺🇸</span> English
          </button>
        </div>
        <span class="live-badge">
          <span class="live-dot"></span>Online • Framework v2.7 • ARI v3.0
        </span>
      </div>
    </div>
  </header>

  <!-- Hero Section -->
  <section class="hero">
    <span class="hero-pill">Acupoint Reality Index &amp; Clinical Matrix</span>
    <h2>
      신경해부학적 실체 판명과 <span class="gradient-text">침구 임상 고증 아카이브</span>
      <span class="hero-en-sub">Anatomical Substrate Identification &amp; Clinical Monograph Portal</span>
    </h2>
    <div class="hero-descriptions">
      <p class="hero-desc-ko">
        경락, 경혈 및 침구의학 문헌 통감(혈위통감·증치통감·수혈통고 등)을 전수 고증하고 한대(漢代) 도량형 실측 심도(1푼=2.3mm) 및 Layer B 4계층 참조 등록부와 통합 생의학 DB(PubMed·Crossref)에 기반하고, 독립 2인 이중 채점(ARI v3.0)으로 판정한 경혈 및 침구의학 임상에 대한 해부생리 분석 결과를 공유하는 포털입니다.
      </p>
      <p class="hero-desc-en">
        A dedicated research portal sharing anatomical and physiological analysis of acupoints and acupuncture clinical practice—grounded in comprehensive textual criticism of meridian, acupoint, and acupuncture canons (*Tongjian*, *Zhengzhi Tongjian*, *Tongkao*, etc.), ancient Han dynasty measured needling depth (1 fen = 2.3 mm), the Layer B 4-tier reference registry, and integrated biomedical databases (PubMed·Crossref), evaluated by dual-assessor independent scoring (ARI v3.0).
      </p>
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-card">
        <span class="stat-num">27편 (54종)</span>
        <span class="stat-label-ko">한·영 듀얼 전문 리포트</span>
        <span class="stat-label-en">27 Dual-Language Monographs</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">14개소</span>
        <span class="stat-label-ko">핵심 경혈 Layer 1~5 실체</span>
        <span class="stat-label-en">14 Key Points Layer 1~5 Verified</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">15+38군</span>
        <span class="stat-label-ko">임상 증상·시동병 해부 매트릭스</span>
        <span class="stat-label-en">Clinical Symptom &amp; Shidong Matrix</span>
      </div>
      <div class="stat-card">
        <span class="stat-num">2인 독립</span>
        <span class="stat-label-ko">ARI v3.0 이중 채점 &amp; B-Check</span>
        <span class="stat-label-en">Dual Scoring &amp; Sensitivity Testing</span>
      </div>
    </div>
  </section>

  <!-- Controls: Search & Category Filter -->
  <section class="controls">
    <div class="search-row">
      <div class="search-box">
        <input class="search-input" id="searchInput" placeholder="검색 / Search code (ST36, LU06, GV14), point name, nerve, indication..." type="text"/>
        <svg class="search-icon" fill="none" height="19" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24" width="19"><circle cx="11" cy="11" r="8"></circle><path d="M21 21l-4.35-4.35"></path></svg>
        <button class="search-clear" id="searchClear" title="검색어 지우기">✕</button>
      </div>
      <div class="results-count-badge" id="resultsCount">
        Showing 28 / 28
      </div>
    </div>

    <div class="filter-tabs">
      <button class="tab-btn active" data-filter="all">
        <span>전체 · All</span> <span class="tab-count">28</span>
      </button>
      <button class="tab-btn" data-filter="acupoint">
        <span>경혈 해부생리 · Acupoints</span> <span class="tab-count">13</span>
      </button>
      <button class="tab-btn" data-filter="classics">
        <span>고전문헌 비교 · Classics</span> <span class="tab-count">4</span>
      </button>
      <button class="tab-btn" data-filter="topic">
        <span>주제별 고증 · Thematic</span> <span class="tab-count">7</span>
      </button>
      <button class="tab-btn" data-filter="matrix">
        <span>임상 매트릭스 · Matrix</span> <span class="tab-count">3</span>
      </button>
      <button class="tab-btn" data-filter="policy">
        <span>의료법제 정책 · Policy</span> <span class="tab-count">1</span>
      </button>
    </div>
  </section>

  <!-- Grid Section -->
  <main class="grid-section">
    <div class="cards-grid" id="cardsGrid">
{CARDS_HTML}
      <div class="no-results" id="noResults">
        <svg fill="none" height="42" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" width="42">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="M21 21l-4.35-4.35M8 11h6"></path>
        </svg>
        <p>검색 조건과 일치하는 보고서가 없습니다.<br><span style="font-size:0.9rem; color:var(--text-muted);">No reports match your search criteria.</span></p>
      </div>
    </div>
  </main>

  <!-- Scroll to Top Button -->
  <button class="scroll-top-btn" id="scrollTopBtn" title="맨 위로 스크롤 (Scroll to top)">
    <svg fill="none" height="20" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24" width="20">
      <path d="M18 15l-6-6-6 6"></path>
    </svg>
  </button>

  <!-- Footer -->
  <footer>
    <div class="footer-content">
      <div class="footer-left">
        <p><strong>Acupoint Anatomy &amp; Substrate Identification Portal</strong> · Framework v2.7 &amp; ARI v3.0</p>
        <p>고전 원전 고증과 현대 신경해부학·생의학 실증의 융합 학술 아카이브</p>
      </div>
      <div class="footer-badges">
        <span class="f-badge">Layer B 4-Tier Registry</span>
        <span class="f-badge">Dual-Layer B-Check</span>
        <span class="f-badge">1 Fen = 2.3mm</span>
        <span class="f-badge">Digital Archive &amp; MCP</span>
      </div>
    </div>
  </footer>

  <!-- Interactive Logic -->
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      const searchInput = document.getElementById('searchInput');
      const searchClear = document.getElementById('searchClear');
      const resultsCount = document.getElementById('resultsCount');
      const filterTabs = document.querySelectorAll('.tab-btn');
      const cards = document.querySelectorAll('.card');
      const noResults = document.getElementById('noResults');
      const langSwitcher = document.getElementById('langSwitcher');
      const scrollTopBtn = document.getElementById('scrollTopBtn');

      let currentFilter = 'all';
      let currentQuery = '';

      // Language Switcher Handler
      langSwitcher.addEventListener('click', (e) => {
        const btn = e.target.closest('.lang-btn');
        if (!btn) return;
        const lang = btn.dataset.lang;
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.documentElement.setAttribute('data-lang-mode', lang);
        localStorage.setItem('acupoint_lang_mode', lang);
      });

      // Restore saved language mode
      const savedLang = localStorage.getItem('acupoint_lang_mode');
      if (savedLang) {
        const targetBtn = document.querySelector(`.lang-btn[data-lang="${savedLang}"]`);
        if (targetBtn) targetBtn.click();
      }

      // Filter and Search Engine
      function applyFilterAndSearch() {
        let visibleCount = 0;
        const q = currentQuery.toLowerCase().trim();

        cards.forEach(card => {
          const category = card.dataset.category;
          const searchData = (card.dataset.search || '').toLowerCase();
          const cardText = card.textContent.toLowerCase();

          const matchesCategory = (currentFilter === 'all') || (category === currentFilter) || (currentFilter === 'matrix' && (category === 'matrix' || category === 'headache'));
          const matchesQuery = !q || searchData.includes(q) || cardText.includes(q);

          if (matchesCategory && matchesQuery) {
            card.style.display = 'flex';
            visibleCount++;
          } else {
            card.style.display = 'none';
          }
        });

        resultsCount.textContent = `Showing ${visibleCount} / ${cards.length}`;
        noResults.style.display = (visibleCount === 0) ? 'block' : 'none';
        searchClear.style.display = q ? 'flex' : 'none';
      }

      // Tab Click
      filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
          filterTabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');
          currentFilter = tab.dataset.filter;
          applyFilterAndSearch();
        });
      });

      // Search Input
      searchInput.addEventListener('input', (e) => {
        currentQuery = e.target.value;
        applyFilterAndSearch();
      });

      searchClear.addEventListener('click', () => {
        searchInput.value = '';
        currentQuery = '';
        applyFilterAndSearch();
        searchInput.focus();
      });

      // Hotkey: '/' to focus search, 'Escape' to clear
      document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== searchInput) {
          e.preventDefault();
          searchInput.focus();
        } else if (e.key === 'Escape' && document.activeElement === searchInput) {
          searchInput.value = '';
          currentQuery = '';
          applyFilterAndSearch();
          searchInput.blur();
        }
      });

      // Scroll to Top
      window.addEventListener('scroll', () => {
        if (window.scrollY > 400) {
          scrollTopBtn.classList.add('visible');
        } else {
          scrollTopBtn.classList.remove('visible');
        }
      });

      scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  </script>
</body>
</html>
"""

def generate_card_html(c):
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in c["tags"])
    
    btns = []
    if c.get("btn_ko"):
        btns.append(f'''<a class="btn-open btn-ko" href="{c['btn_ko']}" target="_blank" title="한국어 정본 학술 보고서 열람">
            <span class="lang-pill">KO</span>
            <span>한국어 전문</span>
          </a>''')
    if c.get("btn_en"):
        btns.append(f'''<a class="btn-open btn-en" href="{c['btn_en']}" target="_blank" title="English Monograph with Traditional Chinese Collation">
            <span class="lang-pill">EN</span>
            <span>English Monograph</span>
            <svg fill="none" height="12" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24" width="12"><path d="M5 12h14M12 5l7 7-7 7"></path></svg>
          </a>''')
    btns_html = "".join(btns)

    return f"""      <!-- Card: {c['code_badge']} -->
      <div class="card" data-category="{c['category']}" data-search="{c['search']}">
        <div class="card-header">
          <span class="code-badge" style="{c['code_style']}">{c['code_badge']}</span>
          <span class="status-badge" style="{c['status_style']}">{c['status_badge']}</span>
        </div>
        <div class="card-title-group">
          <h3 class="card-title-ko">{c['title_ko']}</h3>
          <div class="card-title-en">{c['title_en']}</div>
          <div class="card-subtitle">
            <span class="sub-ko">{c['subtitle_ko']}</span>
            <span class="sub-en">{c['subtitle_en']}</span>
          </div>
        </div>
        <p class="card-desc">
          <span class="desc-ko">{c['desc_ko']}</span>
          <span class="desc-en">{c['desc_en']}</span>
        </p>
        <div class="tags-container">{tags_html}</div>
        <div class="card-footer">
          <span class="category-indicator">
            <svg fill="none" height="12" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="12"><path d="M4 6h16M4 12h16M4 18h7"></path></svg>
            <span>{c['cat_label_ko']} · {c['cat_label_en']}</span>
          </span>
          <div class="btn-group">
            {btns_html}
          </div>
        </div>
      </div>
"""

def main():
    cards_html = "\n".join(generate_card_html(c) for c in BILINGUAL_CARDS)
    full_html = HTML_TEMPLATE.replace("{CARDS_HTML}", cards_html)

    # 탭 개수·결과 수는 카드 데이터에서 계산 (headache 카드는 matrix 탭에 합산)
    import re
    counts = {"all": len(BILINGUAL_CARDS)}
    for c in BILINGUAL_CARDS:
        cat = "matrix" if c["category"] == "headache" else c["category"]
        counts[cat] = counts.get(cat, 0) + 1
    for f, n in counts.items():
        full_html = re.sub(r'(data-filter="%s">\s*<span>[^<]*</span> <span class="tab-count">)\d+' % f, r"\g<1>%d" % n, full_html)
    full_html = re.sub(r"Showing \d+ / \d+", "Showing %d / %d" % (counts["all"], counts["all"]), full_html)

    dual_count = sum(1 for c in BILINGUAL_CARDS if c.get('btn_ko') and c.get('btn_en'))
    full_html = re.sub(r'<span class="stat-num">\d+편 \(\d+종\)</span>', f'<span class="stat-num">{dual_count}편 ({dual_count*2}종)</span>', full_html)
    full_html = re.sub(r'<span class="stat-label-en">\d+ Dual-Language Monographs</span>', f'<span class="stat-label-en">{dual_count} Dual-Language Monographs</span>', full_html)

    out_path = repo_root / "index.html"
    out_path.write_text(full_html, encoding="utf-8")
    print(f"Successfully generated bilingual refined index.html ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    main()

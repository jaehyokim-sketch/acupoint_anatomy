import json, urllib.parse, sys
from pathlib import Path

repo_root = Path(r'C:\workspace\acupoint_anatomy')
sys.path.insert(0, str(repo_root / 'scripts'))
from bilingual_data import BILINGUAL_CARDS

sys.stdout.reconfigure(encoding='utf-8')
repo_root = Path(r'C:\workspace\acupoint_anatomy')
gdrive_root = r'g:\내 드라이브\도서 번역\acupoint_anatomy'

manifest = []
for i, c in enumerate(BILINGUAL_CARDS):
    rel_html = c.get('btn_ko') or c.get('btn_en') or ''
    unquoted = urllib.parse.unquote(rel_html) if rel_html else ''
    
    html_exists = (repo_root / unquoted).exists() if unquoted else False
    
    # Check md file
    md_rel = unquoted.replace('.html', '.md') if unquoted else ''
    md_exists = (repo_root / md_rel).exists() if md_rel else False
    
    base_name = unquoted.replace('.html', '').replace('_en', '') if unquoted else ''
    clean_parts = base_name.split('/')
    base_path = gdrive_root + '\\' + '\\'.join(clean_parts) if clean_parts else ''
    
    manifest.append({
        'index': i + 1,
        'badge': c.get('code_badge'),
        'title': c.get('title_ko'),
        'rel_html': rel_html,
        'html_exists': html_exists,
        'md_exists': md_exists,
        'base_path': base_path
    })

out_file = repo_root / 'reports_manifest.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

print(f'Successfully updated {out_file.name} with {len(manifest)} reports.')
for m in manifest[-5:]:
    print(m['index'], m['badge'], m['title'], 'html:', m['html_exists'], 'md:', m['md_exists'])

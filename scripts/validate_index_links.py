import urllib.parse, re
from pathlib import Path

repo = Path(r'C:\workspace\acupoint_anatomy')
html = (repo / 'index.html').read_text(encoding='utf-8')

links = re.findall(r'href="([^"]+\.html)"', html)
print(f'Total HTML links in index.html: {len(links)}')

broken = []
for link in links:
    if link == 'index.html':
        continue
    unescaped = urllib.parse.unquote(link)
    target = repo / unescaped
    if not target.exists():
        broken.append((link, unescaped))

print(f'Broken links: {len(broken)}')
for b, u in broken:
    print('  BROKEN:', b, '->', u)
if not broken:
    print('ALL LINKS VERIFIED AND 100% VALID!')

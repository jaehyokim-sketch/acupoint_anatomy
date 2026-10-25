import sys
import subprocess
from pathlib import Path

# Set stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

# Run git ls-tree on origin/main
proc = subprocess.run(['git', 'ls-tree', '-r', '--name-only', 'origin/main'], capture_output=True, check=True)
remote_files = set()
for raw_line in proc.stdout.splitlines():
    try:
        line = raw_line.decode('utf-8').strip('"')
    except UnicodeDecodeError:
        line = raw_line.decode('cp949', errors='ignore').strip('"')
    if line.endswith('.html'):
        remote_files.add(line)

# Local files
local_files = set()
for p in Path('.').rglob('*.html'):
    parts = p.parts
    if any(x in parts for x in ['.git', 'venv', '_archive', '.gemini', 'tmp']):
        continue
    local_files.add(p.as_posix())

print(f"=== 1. HTML 전체 파일 수량 비교 ===")
print(f"GitHub origin/main 게시(추적) HTML 파일 수: {len(remote_files)}개")
print(f"로컬 C:\\workspace\\acupoint_anatomy HTML 파일 수: {len(local_files)}개")

diff_local_only = local_files - remote_files
diff_remote_only = remote_files - local_files
common = local_files & remote_files

print(f"\n=== 2. 신규/차이 파일 현황 ===")
print(f"로컬에만 존재하는 파일 ({len(diff_local_only)}개):")
for f in sorted(diff_local_only):
    print(f"  + [로컬 전용] {f}")

print(f"\nGitHub에만 존재하는 파일 ({len(diff_remote_only)}개):")
for f in sorted(diff_remote_only):
    print(f"  - [GitHub 전용] {f}")

# Modified status
status_proc = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, check=True)
modified_html = []
modified_other = []
for raw_line in status_proc.stdout.splitlines():
    line = raw_line.decode('utf-8')
    st = line[:2]
    fname = line[3:].strip('"')
    if fname.endswith('.html'):
        modified_html.append((st, fname))
    else:
        modified_other.append((st, fname))

print(f"\n=== 3. 로컬 수정(Uncommitted/Unsynced) HTML 파일 현황 ({len(modified_html)}개) ===")
for st, f in sorted(modified_html):
    print(f"  [{st.strip()}] {f}")

print(f"\n=== 4. 기타 연관 수정 파일 ({len(modified_other)}개) ===")
for st, f in sorted(modified_other):
    print(f"  [{st.strip()}] {f}")

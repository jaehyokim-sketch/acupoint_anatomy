# -*- coding: utf-8 -*-
"""
deploy_workspace_outputs.py — C:\\workspace에서 만든 결과물을 Google Drive에 자동 배포한다 (Claude Code Stop hook용)

원칙(2026-10-26 사용자 결정): 김재효연구실 PC ⇄ Google Drive 정본 → GOYANGSOON PC 로컬 미러.
규칙·정본은 Drive가 정본이지만, 어느 PC에서든 워크스페이스에서 생성된 결과물(보고서·코드)은 Drive에 동기화한다.

동작
  - C:\\workspace 아래 deploy_to_gdrive.py가 있는 저장소마다 파일 목록(경로·크기·수정 시각)의 지문을 만들고,
    지난 배포 뒤 바뀐 저장소만 그 저장소의 `python -u deploy_to_gdrive.py`를 실행한다(--prune은 쓰지 않는다).
  - 각 deploy_to_gdrive.py는 지침 파일을 올리지 않고(정본은 Drive), Drive 쪽이 더 새로운 파일은 덮어쓰지 않으며,
    내용이 같으면(줄바꿈 차이 포함) 복사하지 않는다.
  - Google Drive가 연결되어 있지 않으면 아무것도 하지 않는다(다음 실행 때 다시 시도).
  - 복사가 있었거나 Drive 쪽이 더 새로운 파일이 있으면 hook JSON(systemMessage)으로 알린다.

사용
  python scripts/deploy_workspace_outputs.py              # 바뀐 저장소만 배포(Stop hook)
  python scripts/deploy_workspace_outputs.py --all        # 모든 저장소 배포
  python scripts/deploy_workspace_outputs.py --dry-run    # 배포 대상만 표시
  python scripts/deploy_workspace_outputs.py --repo acupoint_anatomy
상태 파일: <WORKSPACE>/.claude/.deploy_outputs_state.json (PC별)
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE = Path(__file__).resolve().parents[2]
STATE_PATH = WORKSPACE / ".claude" / ".deploy_outputs_state.json"
MY_DRIVE = Path(os.environ.get("ACUPOINT_DRIVE_ROOT", r"G:\내 드라이브\도서 번역")).parent
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv", "venv", ".idea", ".vscode"}
COPIED_RE = re.compile(r"Copied/Updated\s*:\s*(\d+)|(\d+)\s+files copied")
NEWER_RE = re.compile(r"\[DRIVE NEWER\]\s*(.+)")


def fingerprint(repo: Path) -> str:
    h = hashlib.sha1()
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            try:
                st = os.stat(os.path.join(root, f))
            except OSError:
                continue
            h.update(f"{os.path.relpath(os.path.join(root, f), repo)}|{st.st_size}|{int(st.st_mtime)}\n".encode("utf-8"))
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="워크스페이스 결과물 → Google Drive 자동 배포")
    ap.add_argument("--all", action="store_true", help="바뀌지 않은 저장소도 배포")
    ap.add_argument("--dry-run", action="store_true", help="배포할 저장소만 표시")
    ap.add_argument("--repo", action="append", help="이 저장소만(여러 번 지정 가능)")
    args = ap.parse_args()

    if not MY_DRIVE.is_dir():
        return   # Drive 미연결: 다음에 다시 시도
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    repos = [p for p in sorted(WORKSPACE.iterdir()) if p.is_dir() and (p / "deploy_to_gdrive.py").exists()]
    if args.repo:
        repos = [p for p in repos if p.name in args.repo]

    report, newer_all, failed = [], [], []
    for repo in repos:
        fp = fingerprint(repo)
        if not args.all and state.get(repo.name, {}).get("fingerprint") == fp:
            continue
        if args.dry_run:
            print(f"[배포 대상] {repo.name}")
            continue
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        try:
            r = subprocess.run([sys.executable, "-u", "deploy_to_gdrive.py"], cwd=repo, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=900, env=env)
        except subprocess.TimeoutExpired:
            failed.append(f"{repo.name}(시간 초과)")
            continue
        out = (r.stdout or "") + (r.stderr or "")
        if r.returncode != 0 or "Error:" in out or "[ERROR]" in out:
            failed.append(f"{repo.name}(종료 {r.returncode})")
            continue
        copied = sum(int(a or b) for a, b in COPIED_RE.findall(out))
        newer = [m.strip() for m in NEWER_RE.findall(out)]
        if copied:
            report.append(f"{repo.name} {copied}개")
        newer_all += [f"{repo.name}/{p}" for p in newer]
        # 배포 스크립트가 같은 내용 파일의 로컬 수정 시각을 맞추므로 지문은 배포 뒤에 다시 잰다
        state[repo.name] = {"fingerprint": fingerprint(repo), "deployed_at": datetime.now().isoformat(timespec="seconds"),
                            "copied": copied}

    if not args.dry_run:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    msg = []
    if report:
        msg.append("[Drive 배포] " + " · ".join(report))
    if newer_all:
        msg.append(f"[Drive 배포] Drive 쪽이 더 새로워 덮어쓰지 않은 파일 {len(newer_all)}개: " + ", ".join(newer_all[:8]))
    if failed:
        msg.append("[Drive 배포] 실패: " + ", ".join(failed))
    if msg:
        print(json.dumps({"systemMessage": "\n".join(msg)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

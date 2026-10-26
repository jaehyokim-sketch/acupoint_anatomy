# -*- coding: utf-8 -*-
"""
sync_claude_skill.py — Claude Code용 acupoint-anatomy 스킬을 Google Drive 프로젝트와 로컬 워크스페이스 사이에서 동기화

  Drive  : <DRIVE_ROOT>/.claude/skills/acupoint-anatomy      (정본, 기본 G:/내 드라이브/도서 번역)
  로컬   : <WORKSPACE>/.claude/skills/acupoint-anatomy       (기본: 이 저장소의 상위 폴더, 예 C:/workspace)

동기화 규칙 (지난 동기화 때의 파일 해시를 기준으로 판정)
  - 한쪽만 바뀐 파일은 바뀐 쪽 내용으로 맞춘다(Drive→로컬 또는 로컬→Drive). 수정 시각은 원본 그대로 보존한다.
  - 양쪽이 모두 바뀌었으면 '충돌'로 보고하고 건드리지 않는다(--prefer drive|local로 한쪽을 택할 수 있음).
  - 한쪽에서 지워진 파일은 기본적으로 보고만 한다(--delete를 주면 다른 쪽에서도 지움).
  - 첫 동기화(기록 없음)에서 양쪽 내용이 다르면 충돌로 본다.
  - __pycache__·*.pyc는 제외한다.

사용:
  python scripts/sync_claude_skill.py --dry-run      # 무엇이 바뀔지 확인만
  python scripts/sync_claude_skill.py                # 동기화
  python scripts/sync_claude_skill.py --prefer drive # 충돌 시 Drive 쪽을 택함
  옵션: --drive-root <경로> (또는 환경변수 ACUPOINT_DRIVE_ROOT), --workspace <경로>, --delete
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SKILL_REL = Path(".claude") / "skills" / "acupoint-anatomy"
STATE_NAME = ".acupoint_skill_sync_state.json"  # <WORKSPACE>/.claude/ 아래에 둔다
EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}


def file_map(root: Path) -> dict:
    out = {}
    if not root.is_dir():
        return out
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix in EXCLUDE_SUFFIXES or EXCLUDE_DIRS & set(p.parts):
            continue
        out[p.relative_to(root).as_posix()] = hashlib.sha1(p.read_bytes()).hexdigest()
    return out


def copy(src: Path, dst: Path, dry: bool):
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser(description="acupoint-anatomy Claude Code 스킬 Drive ↔ 로컬 동기화")
    ap.add_argument("--drive-root", default=os.environ.get("ACUPOINT_DRIVE_ROOT", r"G:\내 드라이브\도서 번역"))
    ap.add_argument("--workspace", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--delete", action="store_true", help="한쪽에서 지워진 파일을 다른 쪽에서도 지운다")
    ap.add_argument("--prefer", choices=["drive", "local"], help="충돌 시 택할 쪽")
    args = ap.parse_args()

    drive = Path(args.drive_root) / SKILL_REL
    local = Path(args.workspace) / SKILL_REL
    state_path = Path(args.workspace) / ".claude" / STATE_NAME
    if not drive.is_dir():
        sys.exit(f"[중단] Drive 스킬 폴더가 없습니다: {drive}")

    base = {}
    if state_path.exists():
        base = json.loads(state_path.read_text(encoding="utf-8")).get("files", {})

    d_map, l_map = file_map(drive), file_map(local)
    new_state, actions, conflicts, pending_delete = {}, [], [], []

    for rel in sorted(set(d_map) | set(l_map) | set(base)):
        d, l, b = d_map.get(rel), l_map.get(rel), base.get(rel)
        if d == l:
            if d:
                new_state[rel] = d
            continue
        d_changed, l_changed = d != b, l != b
        if b is None and d and l:  # 첫 동기화에서 양쪽이 다름
            d_changed = l_changed = True
        if d_changed and l_changed:
            if args.prefer == "drive" and d:
                actions.append(("Drive→로컬", rel)); copy(drive / rel, local / rel, args.dry_run); new_state[rel] = d
            elif args.prefer == "local" and l:
                actions.append(("로컬→Drive", rel)); copy(local / rel, drive / rel, args.dry_run); new_state[rel] = l
            else:
                conflicts.append(rel)
                if b:
                    new_state[rel] = b
            continue
        if d_changed:  # Drive 쪽만 바뀜
            if d:
                actions.append(("Drive→로컬", rel)); copy(drive / rel, local / rel, args.dry_run); new_state[rel] = d
            elif args.delete:
                actions.append(("로컬 삭제", rel))
                if not args.dry_run:
                    (local / rel).unlink()
            else:
                pending_delete.append(("Drive에서 삭제됨", rel)); new_state[rel] = b
        else:  # 로컬 쪽만 바뀜
            if l:
                actions.append(("로컬→Drive", rel)); copy(local / rel, drive / rel, args.dry_run); new_state[rel] = l
            elif args.delete:
                actions.append(("Drive 삭제", rel))
                if not args.dry_run:
                    (drive / rel).unlink()
            else:
                pending_delete.append(("로컬에서 삭제됨", rel)); new_state[rel] = b

    mode = "[DRY-RUN] " if args.dry_run else ""
    print(f"{mode}Drive : {drive}\n{mode}로컬  : {local}")
    for kind, rel in actions:
        print(f"  {kind:10s} {rel}")
    for kind, rel in pending_delete:
        print(f"  {kind:10s} {rel}  (보고만 함 — --delete로 반영)")
    for rel in conflicts:
        print(f"  충돌        {rel}  (양쪽 모두 변경 — 확인 후 --prefer drive|local)")
    print(f"{mode}변경 {len(actions)}건 · 삭제 대기 {len(pending_delete)}건 · 충돌 {len(conflicts)}건 · 동일 {len(new_state) - len(actions)}건")

    if not args.dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"drive": str(drive), "local": str(local), "files": new_state},
                                         ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if conflicts else 0)


if __name__ == "__main__":
    main()

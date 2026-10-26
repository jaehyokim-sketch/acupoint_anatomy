# -*- coding: utf-8 -*-
"""
sync_claude_skill.py — [경혈해부] 스킬 규칙을 Google Drive 정본 기준으로 로컬에 미러링한다 (Drive → 로컬, 단방향)

각 PC(GOYANGSOON, 김재효연구실 등)는 Drive 정본만 스킬 규칙으로 쓰고, 로컬 사본은 읽기 전용 미러로 둔다.

  Drive 정본 (<DRIVE>=G:/내 드라이브/도서 번역)                    → 로컬 미러
  <DRIVE>/.claude/skills/acupoint-anatomy/**                       → <WORKSPACE>/.claude/skills/acupoint-anatomy/   (전체 미러)
  <DRIVE>/01_Framework/{정본·등록부·DB 설계}.md                     → <REPO>/framework/
  <DRIVE>/.agents/skills/acupoint-anatomy/SKILL.md                 → <REPO>/skill/SKILL.md
  <DRIVE>/02_Master_Datasets/layer_b_reference_registry.json       → <REPO>/data/layer_b_reference_registry.json

규칙
  - 로컬 사본이 Drive와 다르면 Drive 내용으로 덮어쓴다. 수정 시각도 Drive와 같게 둔다.
  - 지난 동기화 이후 로컬에서 고친 파일은 덮어쓰기 전에 <WORKSPACE>/.claude/skill_sync_backup/<시각>/에 보관하고 알린다
    (규칙은 Drive 정본에서 고친다).
  - Drive에 없는 로컬 스킬 파일은 같은 곳에 보관한 뒤 지운다(미러).
  - 저장소 사본은 줄바꿈(CRLF/LF)만 다르면 같은 것으로 본다(git이 정규화). 바뀌면 커밋이 필요하다고 알린다.
  - Drive를 읽을 수 없으면(드라이브 미연결 등) 아무것도 바꾸지 않는다.
  - __pycache__·*.pyc는 제외한다.

사용:
  python scripts/sync_claude_skill.py            # 동기화
  python scripts/sync_claude_skill.py --check    # 확인만 (다르면 종료코드 1)
  python scripts/sync_claude_skill.py --quiet    # 바뀐 것이 없으면 아무것도 출력하지 않음(세션 시작 hook용)
  옵션: --drive-root <경로> (또는 환경변수 ACUPOINT_DRIVE_ROOT), --workspace <경로>
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SKILL_REL = Path(".claude") / "skills" / "acupoint-anatomy"
STATE_NAME = ".acupoint_skill_sync_state.json"
EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_SUFFIXES = {".pyc"}
REPO_FILES = [  # (Drive 기준 상대경로, 저장소 기준 상대경로)
    ("01_Framework/acupoint_anatomical_logic_framework.md", "framework/acupoint_anatomical_logic_framework.md"),
    ("01_Framework/layer_b_reference_registry.md", "framework/layer_b_reference_registry.md"),
    ("01_Framework/biomedical_master_db_sync_design.md", "framework/biomedical_master_db_sync_design.md"),
    (".agents/skills/acupoint-anatomy/SKILL.md", "skill/SKILL.md"),
    ("02_Master_Datasets/layer_b_reference_registry.json", "data/layer_b_reference_registry.json"),
]
WORKSPACE_FILES = [  # (Drive 기준 상대경로, 워크스페이스 기준 상대경로)
    (".claude/workspace_CLAUDE.md", "CLAUDE.md"),
]


def sha(path: Path, normalize=False) -> str:
    data = path.read_bytes()
    if normalize:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(data).hexdigest()


def skill_files(root: Path) -> dict:
    out = {}
    if root.is_dir():
        for p in root.rglob("*"):
            if p.is_file() and p.suffix not in EXCLUDE_SUFFIXES and not (EXCLUDE_DIRS & set(p.parts)):
                out[p.relative_to(root).as_posix()] = p
    return out


def main():
    ap = argparse.ArgumentParser(description="[경혈해부] 스킬 규칙 Drive 정본 → 로컬 미러")
    ap.add_argument("--drive-root", default=os.environ.get("ACUPOINT_DRIVE_ROOT", r"G:\내 드라이브\도서 번역"))
    ap.add_argument("--workspace", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--check", action="store_true", help="확인만 한다(다르면 종료코드 1)")
    ap.add_argument("--quiet", action="store_true", help="바뀐 것이 없으면 출력하지 않는다")
    ap.add_argument("--dry-run", action="store_true", help="--check와 같음(호환용)")
    args = ap.parse_args()
    check = args.check or args.dry_run

    drive = Path(args.drive_root)
    ws = Path(args.workspace)
    repo = Path(__file__).resolve().parents[1]
    d_skill, l_skill = drive / SKILL_REL, ws / SKILL_REL
    state_path = ws / ".claude" / STATE_NAME
    if not (d_skill / "SKILL.md").exists():
        print(f"[스킬 동기화] ⚠ Drive 정본을 읽을 수 없어 건너뜀: {d_skill} (Google Drive 연결 확인)")
        sys.exit(0 if args.quiet else 2)

    state = {}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8")).get("files", {})
        except Exception:
            state = {}
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = ws / ".claude" / "skill_sync_backup" / stamp
    actions, local_edits, new_state = [], [], {}

    def backup(src: Path, label: str):
        dst = backup_root / label
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # 1) Claude Code 스킬 폴더: 전체 미러
    d_map, l_map = skill_files(d_skill), skill_files(l_skill)
    for rel, src in sorted(d_map.items()):
        key = f"skill:{rel}"
        h = sha(src)
        new_state[key] = h
        dst = l_skill / rel
        if rel in l_map:
            lh = sha(dst)
            if lh == h:
                continue
            if state.get(key) and lh != state[key]:
                local_edits.append(f"스킬 {rel}")
                if not check:
                    backup(dst, f"skill/{rel}")
        actions.append(("Drive→로컬", f"스킬 {rel}"))
        if not check:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for rel, dst in sorted(l_map.items()):
        if rel not in d_map:
            actions.append(("로컬 삭제(Drive에 없음)", f"스킬 {rel}"))
            if not check:
                backup(dst, f"skill/{rel}")
                dst.unlink()

    # 2) 저장소 안의 규칙 사본 · 워크스페이스 지침(CLAUDE.md)
    repo_changed = []
    targets = [(drive / d, repo / r, f"repo:{r}", f"저장소 {r}", f"repo/{r}") for d, r in REPO_FILES] + \
              [(drive / d, ws / w, f"ws:{w}", f"워크스페이스 {w}", f"workspace/{w}") for d, w in WORKSPACE_FILES]
    for src, dst, key, label, blabel in targets:
        if not src.exists():
            continue
        h = sha(src, normalize=True)
        new_state[key] = h
        if dst.exists():
            lh = sha(dst, normalize=True)
            if lh == h:
                continue
            if state.get(key) and lh != state[key]:
                local_edits.append(label)
                if not check:
                    backup(dst, blabel)
        actions.append(("Drive→로컬", label))
        if key.startswith("repo:"):
            repo_changed.append(label)
        if not check:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    if not check:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"mode": "drive-authoritative", "drive": str(drive), "workspace": str(ws),
                                          "synced_at": datetime.now().isoformat(timespec="seconds"), "files": new_state},
                                         ensure_ascii=False, indent=1), encoding="utf-8")

    if args.quiet and not actions:
        return
    head = "[스킬 동기화 확인]" if check else "[스킬 동기화]"
    print(f"{head} Drive 정본 기준: {drive}")
    for kind, what in actions:
        print(f"  {kind:22s} {what}")
    if local_edits:
        print((f"  ⚠ 로컬에서 고친 파일 {len(local_edits)}건을 보관한 뒤 Drive 정본으로 덮어썼습니다 (보관: {backup_root})"
               if not check else f"  ⚠ 로컬에서 고친 파일 {len(local_edits)}건이 있습니다 (동기화하면 보관한 뒤 Drive 정본으로 덮어씀)")
              + ". 규칙 수정은 Drive 정본에서 하세요: " + ", ".join(local_edits))
    if repo_changed and not check:
        print(f"  저장소 규칙 사본 {len(repo_changed)}건 갱신 → acupoint_anatomy 저장소 커밋 필요")
    print(f"  {'차이' if check else '반영'} {len(actions)}건" + ("" if actions else " — Drive 정본과 일치"))
    if check and actions:
        sys.exit(1)


if __name__ == "__main__":
    main()

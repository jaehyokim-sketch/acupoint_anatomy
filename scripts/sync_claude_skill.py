# -*- coding: utf-8 -*-
"""
sync_claude_skill.py — C:\\workspace 작업을 Google Drive 정본 기준으로 로컬에 미러링한다 (Drive → 로컬, 단방향)

원칙(2026-10-26 사용자 결정): 김재효연구실 PC ⇄ Google Drive 정본 → GOYANGSOON PC 로컬 미러.
정책 파일 <DRIVE>/.claude/drive_canonical_policy.json 의 editor_host만 정본을 고치고, 다른 PC는 이 미러만 받는다.

  Drive 정본 (<DRIVE>=G:/내 드라이브/도서 번역)                    → 로컬 미러
  ① 스킬 규칙·지침
  <DRIVE>/.claude/skills/acupoint-anatomy/**                       → <WORKSPACE>/.claude/skills/acupoint-anatomy/   (전체 미러)
  <DRIVE>/.claude/workspace_CLAUDE.md                              → <WORKSPACE>/CLAUDE.md
  <DRIVE>/01_Framework/{정본·등록부·DB 설계}.md                     → <REPO>/framework/
  <DRIVE>/.agents/skills/acupoint-anatomy/SKILL.md                 → <REPO>/skill/SKILL.md
  ② 다른 저장소의 지침 파일 — 각 저장소 deploy_to_gdrive.py의 Drive 배포 폴더가 정본 위치
  <배포 폴더>/{CLAUDE,AGENTS,GEMINI}.md · .claude/settings.json · .claude/{skills,commands}/** · .agents/{rules,skills}/**
                                                                   → <WORKSPACE>/<저장소>/ 같은 경로
  ③ [경혈해부] 데이터 정본
  <DRIVE>/02_Master_Datasets/<DATA_FILES>                          → <REPO>/data/   (바이트 단위)
  ([황룡상] 스킬 규칙은 huanglongxiang-scholar/scripts/sync_skill_copies.py가 맞춘다)

규칙
  - 로컬 사본이 Drive와 다르면 Drive 내용으로 덮어쓴다. 수정 시각도 Drive와 같게 둔다.
  - 지난 동기화 이후 로컬에서 고친 파일은 덮어쓰기 전에 <WORKSPACE>/.claude/skill_sync_backup/<시각>/에 보관하고 알린다.
  - Drive에 없는 로컬 스킬 파일(①의 스킬 폴더)은 보관한 뒤 지운다. ②에서 Drive에 없는 로컬 지침 파일은 알리기만 한다.
  - 텍스트 사본은 줄바꿈(CRLF/LF)만 다르면 같은 것으로 본다(git이 정규화). 데이터는 바이트 단위로 비교한다.
  - 교재·자침 깊이 xlsx가 바뀌면 MCP 참조 데이터(data/mcp_reference_data.json)를 다시 만든다.
  - 저장소 사본이 바뀌면 커밋이 필요하다고 알린다. Drive를 읽을 수 없으면 아무것도 바꾸지 않는다.

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
import re
import shutil
import subprocess
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
DATA_FILES = [  # (Drive 02_Master_Datasets 기준, 저장소 data/ 기준) — 바이트 단위 미러
    ("경혈_생의학_신경반사_마스터DB.json", "경혈_생의학_신경반사_마스터DB.json"),
    ("경혈_생의학_신경반사_마스터DB.xlsx", "경혈_생의학_신경반사_마스터DB.xlsx"),
    ("경혈명_비교_정리_KJH.xlsx", "경혈명_비교_정리_KJH.xlsx"),
    ("361_Acupoints_Refined_Master_DB_v2.csv", "361_Acupoints_Refined_Master_DB_v2.csv"),
    ("All_361_Acupoints_ARI_Master_Dataset.xlsx", "All_361_Acupoints_ARI_Master_Dataset.xlsx"),
    ("경혈의 해부학적 실체를 판명하기 위한 로직(logic) 원칙.xlsx", "경혈의 해부학적 실체를 판명하기 위한 로직(logic) 원칙.xlsx"),
    ("경혈학공통교재 경혈_해부구조_데이터셋_refine.xlsx", "경혈학공통교재 경혈_해부구조_데이터셋_refine.xlsx"),
    ("김재효 수업_경혈_해부구조_데이터셋.xlsx", "김재효 수업_경혈_해부구조_데이터셋.xlsx"),
    ("침구문헌별 자침깊이 정리_AI 분석용.xlsx", "침구문헌별 자침깊이 정리_AI 분석용.xlsx"),
    ("FMA/acupoint_fma_mapping.json", "acupoint_fma_mapping.json"),
]
MCP_REF_INPUTS = {"경혈학공통교재 경혈_해부구조_데이터셋_refine.xlsx", "김재효 수업_경혈_해부구조_데이터셋.xlsx",
                  "침구문헌별 자침깊이 정리_AI 분석용.xlsx"}
# ② 다른 저장소: 자기 규칙을 따로 미러하는 저장소는 제외
OWN_SYNC_REPOS = {"acupoint_anatomy", "huanglongxiang-scholar"}
RULE_FILES = ["CLAUDE.md", "AGENTS.md", "GEMINI.md", ".claude/settings.json"]
RULE_TREES = [".claude/skills", ".claude/commands", ".agents/rules", ".agents/skills"]
DEST_RE = re.compile(r"^\s*(?:GDRIVE_DEST|DEFAULT_DEST)\s*=\s*r?[\"']([^\"']+)[\"']", re.M)
MY_DRIVE_PREFIX = "G:\\내 드라이브"


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


def repo_rule_targets(ws: Path, drive: Path):
    """② 다른 저장소의 (Drive 지침 파일, 로컬 경로, 저장소 이름) 목록과 Drive에 없는 로컬 지침 파일 목록."""
    my_drive = drive.parent
    pairs, local_only = [], []
    for repo in sorted(p for p in ws.iterdir() if p.is_dir() and (p / "deploy_to_gdrive.py").exists()):
        if repo.name in OWN_SYNC_REPOS:
            continue
        m = DEST_RE.search((repo / "deploy_to_gdrive.py").read_text(encoding="utf-8", errors="replace"))
        if not m:
            continue
        dest = m.group(1)
        if dest.startswith(MY_DRIVE_PREFIX):
            dest = str(my_drive) + dest[len(MY_DRIVE_PREFIX):]
        dfold = Path(dest)
        if not dfold.is_dir():
            continue
        rels = [r for r in RULE_FILES if (dfold / r).is_file()]
        for tree in RULE_TREES:
            rels += [p.relative_to(dfold).as_posix() for p in (dfold / tree).rglob("*")
                     if p.is_file() and not (EXCLUDE_DIRS & set(p.parts)) and p.suffix not in EXCLUDE_SUFFIXES]
        pairs += [(dfold / r, repo / r, repo.name, r) for r in rels]
        local = [r for r in RULE_FILES if (repo / r).is_file()]
        for tree in RULE_TREES:
            local += [p.relative_to(repo).as_posix() for p in (repo / tree).rglob("*") if p.is_file()]
        local_only += [f"{repo.name}/{r}" for r in local if r not in rels]
    return pairs, local_only


def host_role(drive: Path) -> str:
    try:
        pol = json.loads((drive / ".claude" / "drive_canonical_policy.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    me = os.environ.get("COMPUTERNAME", "")
    return "편집 PC" if me.casefold() == pol.get("editor_host", "").casefold() else f"미러 PC (편집 PC: {pol.get('editor_host')})"


def main():
    ap = argparse.ArgumentParser(description="C:\\workspace Drive 정본 → 로컬 미러")
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

    # 2) 저장소 규칙·데이터 사본 · 워크스페이스 지침 · 다른 저장소 지침
    #    (src, dst, 상태 키, 표시 이름, 보관 경로, 커밋할 저장소 이름 또는 None, 바이트 비교 여부)
    repo_changed, data_changed = [], []
    targets = [(drive / d, repo / r, f"repo:{r}", f"저장소 {r}", f"repo/{r}", repo.name, False) for d, r in REPO_FILES]
    targets += [(drive / "02_Master_Datasets" / d, repo / "data" / r, f"data:{r}", f"데이터 data/{r}",
                 f"repo/data/{r}", repo.name, True) for d, r in DATA_FILES]
    targets += [(drive / d, ws / w, f"ws:{w}", f"워크스페이스 {w}", f"workspace/{w}", None, False) for d, w in WORKSPACE_FILES]
    rule_pairs, rule_local_only = repo_rule_targets(ws, drive)
    targets += [(s, d, f"rules:{name}/{r}", f"{name} {r}", f"repos/{name}/{r}", name, False) for s, d, name, r in rule_pairs]
    for src, dst, key, label, blabel, commit_repo, binary in targets:
        if not src.exists():
            continue
        if binary and dst.exists():
            ss, ds = src.stat(), dst.stat()
            if ss.st_size == ds.st_size and abs(ss.st_mtime - ds.st_mtime) < 2:   # copy2로 맞춘 뒤 그대로면 해시 생략
                new_state[key] = state.get(key) or sha(dst)
                continue
        h = sha(src, normalize=not binary)
        new_state[key] = h
        if dst.exists():
            lh = sha(dst, normalize=not binary)
            if lh == h:
                if binary and not check:
                    shutil.copystat(src, dst)   # 다음부터 크기·시각으로 빨리 확인
                continue
            if state.get(key) and lh != state[key]:
                local_edits.append(label)
                if not check:
                    backup(dst, blabel)
        actions.append(("Drive→로컬", label))
        if commit_repo:
            repo_changed.append(commit_repo)
        if key.startswith("data:"):
            data_changed.append(dst.name)
        if not check:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    if not check:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"mode": "drive-authoritative", "drive": str(drive), "workspace": str(ws),
                                          "synced_at": datetime.now().isoformat(timespec="seconds"), "files": new_state},
                                         ensure_ascii=False, indent=1), encoding="utf-8")

    rebuilt = ""
    if not check and MCP_REF_INPUTS & set(data_changed):
        r = subprocess.run([sys.executable, str(repo / "scripts" / "build_mcp_reference_data.py")],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        rebuilt = "  MCP 참조 데이터(data/mcp_reference_data.json) 재생성 " + ("완료" if r.returncode == 0 else f"실패: {(r.stderr or r.stdout)[-300:]}")

    if args.quiet and not actions and not rule_local_only:
        return
    head = "[스킬 동기화 확인]" if check else "[스킬 동기화]"
    role = host_role(drive)
    print(f"{head} Drive 정본 기준: {drive}" + (f" · 이 PC = {role}" if role else ""))
    for kind, what in actions:
        print(f"  {kind:22s} {what}")
    if local_edits:
        print((f"  ⚠ 로컬에서 고친 파일 {len(local_edits)}건을 보관한 뒤 Drive 정본으로 덮어썼습니다 (보관: {backup_root})"
               if not check else f"  ⚠ 로컬에서 고친 파일 {len(local_edits)}건이 있습니다 (동기화하면 보관한 뒤 Drive 정본으로 덮어씀)")
              + ". 규칙 수정은 Drive 정본에서 하세요: " + ", ".join(local_edits))
    if rule_local_only:
        print("  ℹ Drive 정본에 없는 로컬 지침 파일(편집 PC에서 Drive에 등록해야 정본이 됨): " + ", ".join(rule_local_only))
    if rebuilt:
        print(rebuilt)
    if repo_changed and not check:
        print("  저장소 사본 갱신 → 커밋 필요: " + ", ".join(sorted(set(repo_changed))))
    print(f"  {'차이' if check else '반영'} {len(actions)}건" + ("" if actions else " — Drive 정본과 일치"))
    if check and actions:
        sys.exit(1)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
workspace_sync.py — C:\\workspace 통합 관리: 로컬 Git 저장소 + Google Drive 정본 동기화 (모든 PC 공용)

원칙(2026-10-26 결정, 2026-11-04 미러 PC 확대)
  - 김재효연구실 PC(편집·정본 PC) ⇄ Google Drive 정본 → 그 밖의 모든 PC(GOYANGSOON·김재효삼성노트 등) 로컬 미러.
  - Git 저장소(.git)는 C:\\workspace\\<저장소>에만 둔다. Google Drive 폴더에는 .git을 두지 않는다.
  - PC 역할은 Drive 정책 파일(<DRIVE>/.claude/drive_canonical_policy.json)의 editor_host와 %COMPUTERNAME%으로 정하고,
    IDE를 열 때 할 일은 같은 파일의 workspace_sync.on_ide_open.<editor|mirror> 단계 목록을 따른다.
  - 저장소 목록·원격·Drive 배포 폴더·Git 사용자는 workspace_repos.json(이 스크립트 옆)에 있다.

명령
  python workspace_sync.py open             IDE 시작 시(VS Code·Antigravity folderOpen 작업): 정책 단계 실행
  python workspace_sync.py deploy [...]     결과물 → Drive 배포(deploy_workspace_outputs.py에 인수 전달)
  python workspace_sync.py status           PC 역할·저장소 상태·Drive .git 점검 표
  python workspace_sync.py install          이 PC에 IDE 자동 실행 등록(.vscode/tasks.json, 자동 작업 허용) + 저장소 Git 설정
  python workspace_sync.py bootstrap        등록부에 있는데 이 PC에 없는 저장소를 clone(원격) 또는 Drive 복사 + git init(로컬 전용)

open 단계(정책 파일 on_ide_open에서 고른다)
  drive_mirror       Drive 정본 → 로컬 미러(sync_claude_skill.py, huanglongxiang sync_skill_copies.py --apply)
  agents_rules       Drive .agents/rules/의 지정 규칙 → C:\\workspace\\.agents\\rules\\ (Antigravity 워크스페이스 규칙)
  global_skills      Drive 스킬 → ~/.gemini·~/.claude 전역 스킬 사본(Drive 쪽이 더 새로운 파일만)
  git_pull           각 저장소 git fetch 후 fast-forward만(로컬 커밋과 갈라졌거나 충돌하면 알리기만)
  drive_git_check    Drive 배포 폴더에 .git이 생겼는지 점검(삭제하지 않고 알림)
  drive_newer_report Drive 배포 폴더에서 로컬보다 새로운 산출물 목록(복사하지 않음). 스트리밍 Drive에서는 느리므로 편집 PC 기본
  role_notice        미러 PC 안내(정본 수정 금지)
Drive가 연결되지 않으면 Drive 단계는 건너뛰고 git_pull만 한다. 실행 기록: <WORKSPACE>/.claude/workspace_sync.log
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPTS = Path(__file__).resolve().parent
WORKSPACE = SCRIPTS.parents[1]
REGISTRY = SCRIPTS / "workspace_repos.json"
LOG_PATH = WORKSPACE / ".claude" / "workspace_sync.log"
LOCK_PATH = WORKSPACE / ".claude" / ".workspace_sync.lock"
BACKUP_ROOT = WORKSPACE / ".claude" / "skill_sync_backup"
HOME = Path.home()

DEFAULT_SYNC = {
    "on_ide_open": {
        "editor": ["drive_mirror", "agents_rules", "global_skills", "git_pull", "drive_git_check", "drive_newer_report"],
        "mirror": ["role_notice", "drive_mirror", "agents_rules", "global_skills", "git_pull", "drive_git_check"],
    },
    "agents_rules_to_workspace": ["drive-canonical-policy.md", "fma-integration.md"],
    "global_skills": [
        {"from": "도서 번역/.agents/skills/acupoint-anatomy", "items": ["SKILL.md", "references"],
         "to": ["~/.gemini/config/skills/acupoint-anatomy"]},
        {"from": "강의/04_평가 및 학습활동 자료/학습일지 평가",
         "items": ["SKILL.md", "학습일지_평가지침.md", "scripts", "references"],
         "to": ["~/.claude/skills/study-log-eval", "~/.gemini/config/skills/study-log-eval"]},
    ],
}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "node_modules", ".venv", "venv", ".idea", ".vscode",
             ".claude", ".agents"}
SKIP_FILES = {"desktop.ini", "Thumbs.db", ".DS_Store", "CLAUDE.md", "AGENTS.md", "GEMINI.md"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".tmp", ".lock", ".swp", ".bak", ".gdoc", ".gsheet", ".gslides"}

OUT = []


def say(msg=""):
    print(msg, flush=True)
    OUT.append(msg)


# ── 경로·정책 ─────────────────────────────────────────────────────────────
def project_root() -> Path:
    """Drive의 '도서 번역' 폴더. ACUPOINT_DRIVE_ROOT → G:\\내 드라이브\\도서 번역 → D:\\도서 번역 순."""
    cands = [os.environ.get("ACUPOINT_DRIVE_ROOT"), r"G:\내 드라이브\도서 번역", r"D:\도서 번역"]
    for c in cands:
        if c and Path(c).is_dir():
            return Path(c)
    return Path(cands[0] or cands[1])


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def role(policy: dict) -> str:
    editor = (policy or {}).get("editor_host", "")
    return "editor" if editor and os.environ.get("COMPUTERNAME", "").casefold() == editor.casefold() else "mirror"


def registry() -> list:
    return (load_json(REGISTRY, {}) or {}).get("repos", [])


def workspace_repos() -> list:
    """등록부 저장소 + 등록부에 없지만 .git이 있는 워크스페이스 폴더."""
    reg = {r["name"]: r for r in registry()}
    extra = [{"name": p.name, "remote": None, "drive": None, "unregistered": True}
             for p in sorted(WORKSPACE.iterdir()) if (p / ".git").is_dir() and p.name not in reg]
    return list(reg.values()) + extra


def git(repo: Path, *args, timeout=120):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return 124, "", "시간 초과"
    except OSError as e:
        return 127, "", str(e)


def same_text_or_bytes(a: Path, b: Path) -> bool:
    try:
        x, y = a.read_bytes(), b.read_bytes()
    except OSError:
        return False
    return x == y or x.replace(b"\r\n", b"\n") == y.replace(b"\r\n", b"\n")


def backup(path: Path, label: str, stamp: str):
    dest = BACKUP_ROOT / stamp / label
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)


# ── open 단계 ────────────────────────────────────────────────────────────
def run_py(script: Path, *args, timeout=600):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    try:
        r = subprocess.run([sys.executable, "-u", str(script), *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env, cwd=str(WORKSPACE))
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return 124, "시간 초과"


def step_drive_mirror(ctx):
    jobs = [("[경혈해부]·지침·데이터", SCRIPTS / "sync_claude_skill.py", ["--quiet"]),
            ("[황룡상]", WORKSPACE / "huanglongxiang-scholar" / "scripts" / "sync_skill_copies.py", ["--apply", "--quiet"])]
    for label, script, args in jobs:
        if not script.exists():
            ctx["warn"].append(f"{label} 미러 스크립트 없음: {script}")
            continue
        code, out = run_py(script, *args)
        if out:
            say(f"  {label}: " + out.replace("\n", "\n    "))
        if code not in (0,):
            ctx["warn"].append(f"{label} 미러 종료 코드 {code}")
    say("  Drive 정본 → 로컬 미러 확인 완료")


def step_agents_rules(ctx):
    src_dir, dst_dir = ctx["project"] / ".agents" / "rules", WORKSPACE / ".agents" / "rules"
    changed = []
    for name in ctx["sync"].get("agents_rules_to_workspace", []):
        src, dst = src_dir / name, dst_dir / name
        if not src.is_file():
            continue
        if dst.is_file() and same_text_or_bytes(src, dst):
            continue
        if dst.is_file():
            backup(dst, f"workspace_agents_rules/{name}", ctx["stamp"])
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        changed.append(name)
    say(f"  .agents/rules 미러: {'갱신 ' + ', '.join(changed) if changed else '변경 없음'}")


def iter_items(base: Path, items):
    for item in items:
        p = base / item
        if p.is_file():
            yield p, Path(item)
        elif p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    if Path(f).suffix.lower() in SKIP_SUFFIXES or f in {"desktop.ini", "Thumbs.db"}:
                        continue
                    fp = Path(root) / f
                    yield fp, fp.relative_to(base)


def step_global_skills(ctx):
    for spec in ctx["sync"].get("global_skills", []):
        base = ctx["my_drive"] / spec["from"]
        if not base.is_dir():
            ctx["warn"].append(f"전역 스킬 원본 없음: {base}")
            continue
        for target in spec["to"]:
            tdir = Path(os.path.expanduser(target))
            updated = []
            for src, rel in iter_items(base, spec["items"]):
                dst = tdir / rel
                if dst.is_file() and (same_text_or_bytes(src, dst) or dst.stat().st_mtime > src.stat().st_mtime + 2):
                    continue   # 같거나, 설치본이 더 새로우면 그대로 둔다
                if dst.is_file():
                    backup(dst, f"global_skills/{tdir.name}_{tdir.parent.parent.name}/{rel}", ctx["stamp"])
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                updated.append(str(rel))
            short = str(tdir).replace(str(HOME), "~")
            say(f"  전역 스킬 {short}: {'갱신 ' + str(len(updated)) + '개 (' + ', '.join(updated[:4]) + ')' if updated else '최신'}")


def pull_one(repo_info):
    name = repo_info["name"]
    repo = WORKSPACE / name
    if not (repo / ".git").is_dir():
        return name, "없음", "이 PC에 없음 (bootstrap 필요)" if (repo_info.get("remote") or repo_info.get("drive")) else ""
    code, upstream, _ = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if code != 0:
        return name, "로컬", "원격 없음(로컬 전용)" if not repo_info.get("remote") else "upstream 미설정 (install 필요)"
    code, _, err = git(repo, "fetch", "--quiet", timeout=90)
    if code != 0:
        return name, "오류", f"fetch 실패: {err.splitlines()[-1] if err else code}"
    _, counts, _ = git(repo, "rev-list", "--left-right", "--count", "HEAD...@{u}")
    ahead, behind = (int(x) for x in counts.split()) if counts else (0, 0)
    if behind == 0:
        return name, "최신", f"푸시 대기 {ahead}커밋" if ahead else ""
    if ahead:
        return name, "갈라짐", f"로컬 {ahead} / 원격 {behind} 커밋 — 직접 pull --rebase 또는 merge"
    code, _, err = git(repo, "merge", "--ff-only", "--quiet", "@{u}")
    if code != 0:
        return name, "보류", f"원격 {behind}커밋을 받지 못함(로컬 변경과 충돌): {err.splitlines()[-1] if err else ''}"
    return name, "받음", f"원격 {behind}커밋 fast-forward"


def step_git_pull(ctx):
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(pull_one, workspace_repos()))
    local_only = [n for n, s, note in results if s == "로컬" and note.startswith("원격 없음")]
    for name, state, note in results:
        if note and name not in local_only:
            say(f"  git {name:<30} {state:<4} {note}")
        if state in ("갈라짐", "보류", "오류") or note.startswith("upstream"):
            ctx["warn"].append(f"git {name}: {note}")
    got = sum(1 for _, s, _ in results if s == "받음")
    say(f"  git: {len(results)}개 저장소 확인, {got}개 갱신" + (f" (로컬 전용 {len(local_only)}개: 원격 없음)" if local_only else ""))


def step_drive_git_check(ctx):
    found = [str(ctx["my_drive"] / r["drive"] / ".git") for r in registry()
             if r.get("drive") and (ctx["my_drive"] / r["drive"] / ".git").exists()]
    if found:
        ctx["warn"].append("Drive 폴더에 .git이 있음(로컬 워크스페이스에만 두어야 함): " + ", ".join(found))
    say(f"  Drive 배포 폴더 .git: {'있음 ' + str(len(found)) + '개' if found else '0개 (정상)'}")


def drive_newer(repo_info, my_drive: Path):
    local, drive = WORKSPACE / repo_info["name"], my_drive / repo_info["drive"]
    if not local.is_dir() or not drive.is_dir():
        return []
    excl = set(repo_info.get("drive_exclude", []))
    newer = []
    for root, dirs, files in os.walk(drive):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in excl]
        for f in files:
            if f in SKIP_FILES or f.startswith("~$") or Path(f).suffix.lower() in SKIP_SUFFIXES:
                continue
            d = Path(root) / f
            rel = d.relative_to(drive)
            l = local / rel
            if not l.is_file():
                continue
            ds, ls = d.stat(), l.stat()
            if ds.st_mtime > ls.st_mtime + 2 and (ds.st_size != ls.st_size or not same_text_or_bytes(d, l)):
                newer.append(str(rel))
    return newer


def step_drive_newer_report(ctx):
    total = 0
    for r in registry():
        if not r.get("drive"):
            continue
        items = drive_newer(r, ctx["my_drive"])
        total += len(items)
        if items:
            say(f"  [DRIVE NEWER] {r['name']}: " + ", ".join(items[:6]) + (f" 외 {len(items) - 6}개" if len(items) > 6 else ""))
    if total:
        ctx["warn"].append(f"Drive 쪽이 더 새로운 산출물 {total}개 — 확인 후 로컬로 가져와 커밋(자동 복사하지 않음)")
    say(f"  Drive → 로컬 역방향 점검: {'Drive가 더 새로운 파일 ' + str(total) + '개' if total else '차이 없음'}")


def step_role_notice(ctx):
    say(f"  이 PC({ctx['host']})는 미러 PC입니다. Drive 정본·로컬 미러(규칙·지침·정본 데이터)는 고치지 않고, "
        f"변경이 필요하면 편집 PC({ctx['policy'].get('editor_host')})에서 반영합니다.")


STEPS = {"drive_mirror": step_drive_mirror, "agents_rules": step_agents_rules, "global_skills": step_global_skills,
         "git_pull": step_git_pull, "drive_git_check": step_drive_git_check,
         "drive_newer_report": step_drive_newer_report, "role_notice": step_role_notice}
DRIVE_STEPS = {"drive_mirror", "agents_rules", "global_skills", "drive_git_check", "drive_newer_report"}


def context():
    project = project_root()
    policy = load_json(project / ".claude" / "drive_canonical_policy.json", {}) or {}
    sync = {**DEFAULT_SYNC, **policy.get("workspace_sync", {})}
    return {"project": project, "my_drive": project.parent, "policy": policy, "sync": sync,
            "role": role(policy) if policy else "mirror", "host": os.environ.get("COMPUTERNAME", "?"),
            "drive_ok": project.is_dir() and bool(policy), "warn": [], "stamp": datetime.now().strftime("%Y%m%d_%H%M%S")}


def cmd_open(args):
    if LOCK_PATH.exists() and time.time() - LOCK_PATH.stat().st_mtime < 900:
        print("[워크스페이스 동기화] 다른 동기화가 실행 중이라 건너뜁니다.")
        return 0
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCK_PATH.write_text(str(os.getpid()), encoding="utf-8")
    try:
        ctx = context()
        role_ko = "편집·정본 PC" if ctx["role"] == "editor" else "미러 PC"
        say(f"[워크스페이스 동기화] {datetime.now():%Y-%m-%d %H:%M} · {ctx['host']} = {role_ko} · Drive: {ctx['project']}")
        if not ctx["drive_ok"]:
            ctx["warn"].append("Google Drive(도서 번역 또는 정책 파일)를 찾지 못해 Drive 단계를 건너뜀")
        steps = ctx["sync"]["on_ide_open"].get(ctx["role"], [])
        for name in steps:
            if name in DRIVE_STEPS and not ctx["drive_ok"]:
                continue
            fn = STEPS.get(name)
            if not fn:
                continue
            try:
                fn(ctx)
            except Exception as e:  # 한 단계가 실패해도 나머지는 진행
                ctx["warn"].append(f"{name} 실패: {e}")
        if ctx["warn"]:
            say("[확인 필요]")
            for w in ctx["warn"]:
                say(f"  - {w}")
        else:
            say("[워크스페이스 동기화] 완료 — 확인할 항목 없음")
        return 0
    finally:
        LOCK_PATH.unlink(missing_ok=True)
        try:
            with LOG_PATH.open("a", encoding="utf-8") as f:
                f.write("\n".join(OUT) + "\n\n")
            if LOG_PATH.stat().st_size > 2_000_000:
                LOG_PATH.write_text(LOG_PATH.read_text(encoding="utf-8")[-500_000:], encoding="utf-8")
        except OSError:
            pass


# ── status / deploy ─────────────────────────────────────────────────────
def cmd_status(args):
    ctx = context()
    say(f"PC: {ctx['host']} = {'편집·정본 PC' if ctx['role'] == 'editor' else '미러 PC'} "
        f"(editor_host={ctx['policy'].get('editor_host', '?')}) · Drive: {ctx['project']} {'연결됨' if ctx['drive_ok'] else '미연결'}")
    say(f"{'저장소':<30} {'브랜치':<6} {'원격':<10} {'앞/뒤':<7} {'변경':<5} Drive .git")
    for r in workspace_repos():
        repo = WORKSPACE / r["name"]
        if not (repo / ".git").is_dir():
            say(f"{r['name']:<30} (이 PC에 없음)")
            continue
        _, br, _ = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        code, up, _ = git(repo, "rev-parse", "--abbrev-ref", "@{u}")
        _, counts, _ = git(repo, "rev-list", "--left-right", "--count", "HEAD...@{u}") if code == 0 else (0, "", "")
        _, st, _ = git(repo, "status", "--porcelain")
        dgit = "있음!" if r.get("drive") and (ctx["my_drive"] / r["drive"] / ".git").exists() else "-"
        remote = up if code == 0 else ("로컬 전용" if not r.get("remote") else "upstream 없음")
        say(f"{r['name']:<30} {br:<6} {remote:<10} {counts.replace(chr(9), '/') if counts else '-':<7} "
            f"{len(st.splitlines()) if st else 0:<5} {dgit}" + ("  (등록부에 없음)" if r.get("unregistered") else ""))
    return 0


def cmd_deploy(args, rest):
    return subprocess.call([sys.executable, "-u", str(SCRIPTS / "deploy_workspace_outputs.py"), *rest])


# ── install / bootstrap ─────────────────────────────────────────────────
TASKS = [
    {"label": "워크스페이스: Drive 동기화 (IDE 시작)", "args": ["open"], "runOn": "folderOpen"},
    {"label": "워크스페이스: 결과물 Drive 배포", "args": ["deploy"]},
    {"label": "워크스페이스: 상태 점검", "args": ["status"]},
]


def merge_json_file(path: Path, updater):
    data = load_json(path, None) if path.exists() else {}
    if data is None:
        say(f"  ! {path} 를 JSON으로 읽지 못해 고치지 않았습니다(주석이 있으면 직접 추가하세요).")
        return False
    new = updater(dict(data))
    if new != data:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        path.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        say(f"  갱신: {path}")
    else:
        say(f"  최신: {path}")
    return True


def cmd_install(args):
    script = "${workspaceFolder}/acupoint_anatomy/scripts/workspace_sync.py"

    def upd_tasks(d):
        d.setdefault("version", "2.0.0")
        tasks = [t for t in d.get("tasks", []) if not str(t.get("label", "")).startswith("워크스페이스:")]
        for t in TASKS:
            task = {"label": t["label"], "type": "process", "command": "python", "args": [script, *t["args"]],
                    "options": {"cwd": "${workspaceFolder}", "env": {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}},
                    "presentation": {"reveal": "always" if "runOn" not in t else "silent", "panel": "dedicated",
                                     "clear": True, "showReuseMessage": False},
                    "problemMatcher": []}
            if t.get("runOn"):
                task["runOptions"] = {"runOn": t["runOn"]}
            tasks.append(task)
        d["tasks"] = tasks
        return d

    say("[1] IDE 시작 시 자동 실행 작업 (VS Code·Antigravity 공용)")
    merge_json_file(WORKSPACE / ".vscode" / "tasks.json", upd_tasks)

    say("[2] 자동 작업 허용 (사용자 설정)")
    appdata = Path(os.environ.get("APPDATA", HOME / "AppData" / "Roaming"))
    for app in ("Code", "Antigravity IDE", "Antigravity"):
        user_dir = appdata / app / "User"
        if user_dir.is_dir():
            merge_json_file(user_dir / "settings.json", lambda d: {**d, "task.allowAutomaticTasks": "on"})

    say("[3] 저장소 Git 설정 (사용자·자격 증명·upstream)")
    for r in registry():
        repo = WORKSPACE / r["name"]
        if not (repo / ".git").is_dir():
            say(f"  {r['name']}: 이 PC에 없음 → bootstrap")
            continue
        notes = []
        if r.get("user"):
            git(repo, "config", "user.name", r["user"][0])
            git(repo, "config", "user.email", r["user"][1])
        git(repo, "config", "credential.helper", "manager")
        if r.get("remote"):
            code, url, _ = git(repo, "remote", "get-url", "origin")
            if code != 0:
                git(repo, "remote", "add", "origin", r["remote"])
                notes.append("origin 추가")
            elif "ghp_" in url or "github_pat_" in url:
                git(repo, "remote", "set-url", "origin", r["remote"])
                notes.append("토큰 포함 URL 교체")
            if git(repo, "rev-parse", "--abbrev-ref", "@{u}")[0] != 0:
                _, br, _ = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
                git(repo, "fetch", "--quiet", "origin", timeout=90)
                if git(repo, "rev-parse", "--verify", "--quiet", f"origin/{br}")[0] == 0:
                    git(repo, "branch", f"--set-upstream-to=origin/{br}", br)
                    notes.append(f"upstream origin/{br} 설정")
        say(f"  {r['name']}: 설정 완료" + (f" ({', '.join(notes)})" if notes else ""))
    say("완료. VS Code·Antigravity에서 C:\\workspace 폴더를 열면 '워크스페이스: Drive 동기화' 작업이 자동 실행됩니다.")
    say("처음 한 번은 IDE가 자동 작업 허용 여부를 물을 수 있습니다 → 허용(Allow).")
    return 0


def cmd_bootstrap(args):
    ctx = context()
    for r in registry():
        repo = WORKSPACE / r["name"]
        if (repo / ".git").is_dir():
            continue
        if r.get("remote"):
            say(f"[clone] {r['name']} ← {r['remote']}")
            code = subprocess.call(["git", "clone", r["remote"], str(repo)], cwd=str(WORKSPACE))
            if code != 0:
                say(f"  ! clone 실패({code})")
                continue
        else:
            src = ctx["my_drive"] / r["drive"]
            if not src.is_dir():
                say(f"[건너뜀] {r['name']}: Drive 폴더 없음 {src}")
                continue
            say(f"[Drive 복사 + git init] {r['name']} ← {src}")
            subprocess.call(["robocopy", str(src), str(repo), "/E", "/XD", ".git", "__pycache__", ".venv", "node_modules",
                             *r.get("drive_exclude", []), "/XF", "desktop.ini", "*.gdoc", "*.gslides",
                             "/R:2", "/W:2", "/NP", "/NFL", "/NDL"])
            git(repo, "init", "-b", "main")
            git(repo, "add", "-A")
            git(repo, "-c", f"user.name={r['user'][0]}", "-c", f"user.email={r['user'][1]}",
                "commit", "-q", "-m", "Initial local workspace copy from Google Drive")
    say("bootstrap 끝. 이어서 'python workspace_sync.py install'을 실행하세요.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="C:\\workspace 통합 관리 (로컬 Git + Google Drive 정본 동기화)")
    ap.add_argument("command", choices=["open", "status", "deploy", "install", "bootstrap"])
    args, rest = ap.parse_known_args()
    if args.command == "deploy":
        return cmd_deploy(args, rest)
    return {"open": cmd_open, "status": cmd_status, "install": cmd_install, "bootstrap": cmd_bootstrap}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

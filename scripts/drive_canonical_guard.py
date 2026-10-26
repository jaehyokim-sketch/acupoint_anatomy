# -*- coding: utf-8 -*-
"""
drive_canonical_guard.py — Claude Code PreToolUse hook (Edit·Write·MultiEdit·NotebookEdit)

원칙(2026-10-26 사용자 결정): 김재효연구실 PC ⇄ Google Drive 정본 → GOYANGSOON PC 로컬 미러.
정책 파일 <DRIVE>/.claude/drive_canonical_policy.json의 editor_host가 아닌 PC(미러 PC)에서는
Drive 정본과 그 로컬 미러를 고치지 못하게 막는다. 편집 PC에서는 아무것도 막지 않는다.

막는 경로 (미러 PC)
  - Drive `도서 번역`의 정본 폴더: .claude · .agents · 01_Framework · 02_Master_Datasets · 01_도서_번역_및_원전
  - Drive(내 드라이브) 어디든 지침 파일: CLAUDE.md · AGENTS.md · GEMINI.md, .claude/ · .agents/ 아래
  - 로컬 미러: C:/workspace/CLAUDE.md, C:/workspace/.claude/skills/**, acupoint_anatomy의 framework/·skill/SKILL.md·
    미러 데이터(data/), huanglongxiang-scholar의 skill/·.agents/, 다른 저장소의 최상위 지침 파일·.claude/·.agents/
  (워크스페이스 C:/workspace/.claude/settings.json·각 settings.local.json 같은 PC별 설정, 산출물·코드는 막지 않는다)

정책 파일을 읽을 수 없으면(드라이브 미연결) 막지 않는다. 결과는 hook JSON으로 stdout에 낸다.
  시험: echo {"tool_name":"Edit","tool_input":{"file_path":"C:/workspace/CLAUDE.md"}} | python drive_canonical_guard.py
"""
import json
import os
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_claude_skill import DATA_FILES, OWN_SYNC_REPOS, REPO_FILES  # noqa: E402

WORKSPACE = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[1]
DRIVE = Path(os.environ.get("ACUPOINT_DRIVE_ROOT", r"G:\내 드라이브\도서 번역"))
PC_LOCAL = {"settings.local.json"}   # 저장소 .claude/settings.json은 Drive 정본의 미러이므로 막는다


def norm(p: Path) -> str:
    return os.path.normcase(os.path.abspath(str(p)))


def under(path: str, base: Path) -> str | None:
    """path가 base 아래면 base 기준 상대경로('/' 구분), 아니면 None."""
    b = norm(base)
    if path == b or path.startswith(b + os.sep):
        return path[len(b):].lstrip(os.sep).replace(os.sep, "/")
    return None


def protected(path: str, policy: dict) -> str | None:
    """막아야 하면 이유를, 아니면 None."""
    rule_files = {f.lower() for f in policy.get("rule_files", ["CLAUDE.md", "AGENTS.md", "GEMINI.md"])}
    rule_dirs = set(policy.get("rule_dirs", [".claude", ".agents"]))
    rel = under(path, DRIVE)
    if rel is not None:
        top = rel.split("/")[0]
        if top.lower() in {d.lower() for d in policy.get("canonical_dirs_in_project", [])}:
            return f"Drive 정본 폴더({top})"
    rel = under(path, DRIVE.parent)
    if rel is not None:
        parts = rel.lower().split("/")
        if parts[-1] in rule_files or any(p in rule_dirs for p in parts[:-1]):
            return "Drive의 지침 파일(정본)"
    rel = under(path, WORKSPACE)
    if rel is None:
        return None
    parts = rel.split("/")
    if rel.lower() == "claude.md" or rel.lower().startswith(".claude/skills/"):
        return "워크스페이스 지침·스킬 미러"
    mirrored = {r.lower() for _, r in REPO_FILES} | {f"data/{r}".lower() for _, r in DATA_FILES}
    if parts[0] == REPO.name:
        sub = "/".join(parts[1:]).lower()
        if sub in mirrored or sub.startswith("framework/"):
            return "acupoint_anatomy의 정본 미러(framework/·skill/·data/)"
        return None
    if parts[0] == "huanglongxiang-scholar":
        if len(parts) > 1 and parts[1] in ("skill", ".agents"):
            return "huanglongxiang-scholar의 스킬 규칙 미러(skill/·.agents/)"
        return None
    if len(parts) >= 2 and parts[0] not in OWN_SYNC_REPOS and (WORKSPACE / parts[0] / "deploy_to_gdrive.py").exists():
        if len(parts) == 2 and parts[1].lower() in rule_files:
            return f"{parts[0]}의 지침 파일 미러"
        if parts[1] in rule_dirs and not (len(parts) == 3 and parts[2] in PC_LOCAL):
            return f"{parts[0]}의 {parts[1]}/ 미러"
    return None


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))   # Windows 파이프 기본 인코딩(cp949) 대신 UTF-8
    except ValueError:
        return
    tool_input = data.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return
    try:
        policy = json.loads((DRIVE / ".claude" / "drive_canonical_policy.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    editor = policy.get("editor_host", "")
    me = os.environ.get("COMPUTERNAME", "")
    if not editor or me.casefold() == editor.casefold():
        return
    why = protected(norm(Path(target)), policy)
    if not why:
        return
    reason = (f"[Drive 정본 원칙] 이 PC({me})는 미러 PC입니다. {why}는 편집 PC({editor})에서만 고칩니다 "
              f"(김재효연구실 PC ⇄ Drive 정본 → 이 PC 로컬 미러, 2026-10-26). 바꿀 내용을 정리해 사용자에게 알리세요.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}, ensure_ascii=False))


if __name__ == "__main__":
    main()

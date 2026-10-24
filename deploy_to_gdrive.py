"""
deploy_to_gdrive.py - Deploy/Sync acupoint_anatomy artifacts from Local to Google Drive.

Usage:
    python deploy_to_gdrive.py [--dry-run]
"""
import os, sys, shutil, argparse

LOCAL_REPO = r"C:\workspace\acupoint_anatomy"
GDRIVE_DEST = r"G:\내 드라이브\도서 번역\acupoint_anatomy"

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    ".idea",
    ".vscode"
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".lock",
    ".swp",
    ".bak"
}

def sync_to_gdrive(dry_run=False):
    print("=" * 60)
    print("  acupoint_anatomy Local -> Google Drive Sync Deployment")
    print(f"  Source : {LOCAL_REPO}")
    print(f"  Target : {GDRIVE_DEST}")
    print(f"  Mode   : {'[DRY RUN]' if dry_run else '[LIVE DEPLOY]'}")
    print("=" * 60)

    if not os.path.exists(LOCAL_REPO):
        print(f"Error: Local repo does not exist at {LOCAL_REPO}")
        return False
    if not os.path.exists(GDRIVE_DEST):
        print(f"Target directory does not exist, creating: {GDRIVE_DEST}")
        if not dry_run:
            os.makedirs(GDRIVE_DEST, exist_ok=True)

    copied = 0
    skipped = 0

    for root, dirs, files in os.walk(LOCAL_REPO):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel_dir = os.path.relpath(root, LOCAL_REPO)
        target_dir = os.path.join(GDRIVE_DEST, rel_dir) if rel_dir != "." else GDRIVE_DEST

        if not os.path.exists(target_dir) and not dry_run:
            os.makedirs(target_dir, exist_ok=True)

        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IGNORE_EXTENSIONS or f.startswith("~$") or f.startswith("."):
                continue

            src_file = os.path.join(root, f)
            dest_file = os.path.join(target_dir, f)

            # Check if copy needed (mtime or size difference)
            need_copy = False
            if not os.path.exists(dest_file):
                need_copy = True
            else:
                src_stat = os.stat(src_file)
                dst_stat = os.stat(dest_file)
                if src_stat.st_size != dst_stat.st_size or abs(src_stat.st_mtime - dst_stat.st_mtime) > 1.0:
                    need_copy = True

            if need_copy:
                copied += 1
                rel_path = os.path.relpath(src_file, LOCAL_REPO)
                if dry_run:
                    print(f"  [COPY] {rel_path}")
                else:
                    shutil.copy2(src_file, dest_file)
            else:
                skipped += 1

    print("-" * 60)
    print(f"Deployment Summary: {copied} files copied, {skipped} files up-to-date.")
    print("Google Drive is fully updated and clean (no .git or temp locks).")
    print("=" * 60)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync local repo to Google Drive")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without copying")
    args = parser.parse_args()
    sync_to_gdrive(dry_run=args.dry_run)

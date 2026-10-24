"""
deploy_to_gdrive.py - Deploy/Sync acupoint_anatomy artifacts from Local to Google Drive.

Usage:
    python deploy_to_gdrive.py [--dry-run]
"""
import os, sys, shutil, argparse

# Support utf-8 console output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

def sync_to_gdrive(dry_run=False, prune=False):
    print("=" * 60)
    print("  acupoint_anatomy Local -> Google Drive Sync Deployment")
    print(f"  Source : {LOCAL_REPO}")
    print(f"  Target : {GDRIVE_DEST}")
    print(f"  Mode   : {'[DRY RUN]' if dry_run else '[LIVE DEPLOY]'}")
    if prune:
        print("  Prune  : [ENABLED] (Deleted local files/folders will be removed from GDrive)")
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

    pruned_files = 0
    pruned_dirs = 0

    if prune:
        print("\nChecking for files to prune in Google Drive...")
        # Pass 1: Prune files that no longer exist locally
        for root, dirs, files in os.walk(GDRIVE_DEST, topdown=False):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            rel_dir = os.path.relpath(root, GDRIVE_DEST)
            local_dir = os.path.join(LOCAL_REPO, rel_dir) if rel_dir != "." else LOCAL_REPO

            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IGNORE_EXTENSIONS or f.startswith("~$") or f.startswith("."):
                    continue

                dest_file = os.path.join(root, f)
                src_file = os.path.join(local_dir, f)

                if not os.path.exists(src_file):
                    pruned_files += 1
                    rel_path = os.path.relpath(dest_file, GDRIVE_DEST)
                    if dry_run:
                        print(f"  [PRUNE FILE] {rel_path}")
                    else:
                        try:
                            os.remove(dest_file)
                            print(f"  [DELETED FILE] {rel_path}")
                        except Exception as e:
                            print(f"  [ERROR] Failed to delete file {rel_path}: {e}")

        # Pass 2: Prune directories that are empty or do not exist locally
        for root, dirs, files in os.walk(GDRIVE_DEST, topdown=False):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            rel_dir = os.path.relpath(root, GDRIVE_DEST)
            if rel_dir == ".":
                continue
            local_dir = os.path.join(LOCAL_REPO, rel_dir)

            # If directory doesn't exist locally or has no files/subdirs
            is_empty = False
            try:
                is_empty = (len(os.listdir(root)) == 0)
            except Exception:
                pass

            if is_empty or (not os.path.exists(local_dir) and not dry_run and is_empty):
                pruned_dirs += 1
                if dry_run:
                    print(f"  [PRUNE DIR] {rel_dir}")
                else:
                    try:
                        os.rmdir(root)
                        print(f"  [DELETED DIR] {rel_dir}")
                    except Exception as e:
                        print(f"  [ERROR] Failed to delete dir {rel_dir}: {e}")

    print("-" * 60)
    print(f"Deployment Summary:")
    print(f"  Copied/Updated : {copied} files")
    print(f"  Up-to-date     : {skipped} files")
    if prune:
        print(f"  Pruned/Removed : {pruned_files} files, {pruned_dirs} directories")
    print("Google Drive is fully synchronized with local workspace.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync local repo to Google Drive")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without copying/deleting")
    parser.add_argument("--prune", action="store_true", help="Remove files/dirs from Google Drive that do not exist locally")
    args = parser.parse_args()
    sync_to_gdrive(dry_run=args.dry_run, prune=args.prune)

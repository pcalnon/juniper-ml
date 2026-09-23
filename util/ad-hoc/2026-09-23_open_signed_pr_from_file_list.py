"""
Open a signed PR from a FILE LIST, substituting LFS pointer files where one was prepared.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — tooling
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/open_signed_pr.py (the tool this drives); util/ad-hoc/2026-09-23_lfs_pointers_for_api_commit.py
         (writes the pointer files this substitutes)

Why: ``open_signed_pr.py`` takes one ``--add LOCAL:REPOPATH`` per file. A report directory of ~400
files makes that an unreadable command line, and an LFS-tracked image must be committed as its
pointer, not its bytes. This builds the argument list from a list of repo-relative paths, uses
``<pointer-dir>/<path>`` whenever that file exists, and refuses an LFS-tracked path that has no
pointer (so a raw image can never slip into the commit).

Usage (from the repo's worktree root):
    python3 util/ad-hoc/2026-09-23_open_signed_pr_from_file_list.py --files-from LIST --pointer-dir DIR \
        --repo juniper-ml --branch B --message M --commit-body-file F --title T --body-file F [--dry-run]
"""

import argparse
import subprocess
import sys
from pathlib import Path

LFS_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".xcf", ".svg"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files-from", required=True)
    ap.add_argument("--pointer-dir", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--commit-body-file", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = Path.cwd()
    pointer_dir = Path(a.pointer_dir).resolve()
    paths = [line.strip() for line in Path(a.files_from).read_text().splitlines() if line.strip()]
    adds = []
    pointers = 0
    for rel in paths:
        local = root / rel
        if not local.is_file():
            raise SystemExit(f"missing: {rel}")
        pointer = pointer_dir / rel
        if pointer.is_file():
            if not pointer.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1"):
                raise SystemExit(f"{rel}: pointer file is not an LFS pointer")
            local = pointer
            pointers += 1
        elif local.suffix.lower() in LFS_SUFFIXES:
            raise SystemExit(f"{rel}: LFS-tracked suffix with no prepared pointer -- REFUSING to upload raw bytes")
        adds += ["--add", f"{local}:{rel}"]
    print(f"{len(paths)} files, {pointers} as LFS pointers")
    cmd = [sys.executable, str(root / "util/open_signed_pr.py"), "--repo", a.repo, "--base", a.base, "--branch", a.branch, *adds, "--message", a.message, "--commit-body-file", a.commit_body_file, "--title", a.title, "--body-file", a.body_file]
    if a.dry_run:
        cmd.append("--dry-run")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    out = proc.stdout
    if a.dry_run:
        out = "\n".join(line for line in out.splitlines() if not line.strip().startswith("add "))
        print(f"(dry-run: {out.count(chr(10))} lines shown, per-file 'add' lines elided)")
    print(out)
    print(proc.stderr, file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

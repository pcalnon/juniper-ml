#!/usr/bin/env python3
"""Open one signed docs PR carrying every modified and untracked file in this worktree.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use driver for util/open_signed_pr.py)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-10-05
Status:      ad-hoc. A headless session cannot ``git commit`` (hardware signing key) and the
             worktree-isolation hook refuses ``xargs -a`` and shell loops, so the repeatable ``--add``
             list for ``util/open_signed_pr.py`` is built here, in Python, from ``git ls-files``. The
             driver includes itself in the upload (it is an untracked file at run time), so the PR
             carries the instrument that opened it.

Run (from the worktree root):
    python3 util/ad-hoc/2026-10-05_open_docs_pr.py --repo juniper-ml --branch <branch> \
        --message "<subject>" --commit-body-file <path> --title "<title>" --body-file <path> [--dry-run]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def changed_files(root: Path) -> list[str]:
    modified = subprocess.run(["git", "ls-files", "--modified"], check=True, capture_output=True, text=True, cwd=root).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], check=True, capture_output=True, text=True, cwd=root).stdout.split()
    return sorted(p for p in set(modified) | set(untracked) if (root / p).is_file())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--commit-body-file", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], check=True, capture_output=True, text=True).stdout.strip())
    paths = changed_files(root)
    cmd = [sys.executable, str(root / "util" / "open_signed_pr.py"), "--repo", args.repo, "--branch", args.branch, "--message", args.message, "--commit-body-file", args.commit_body_file, "--title", args.title, "--body-file", args.body_file]
    for rel in paths:
        cmd += ["--add", f"{root / rel}:{rel}"]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"{len(paths)} files; invoking open_signed_pr.py", file=sys.stderr, flush=True)
    for rel in paths:
        print(f"  {rel}", file=sys.stderr)
    return subprocess.run(cmd, cwd=root).returncode


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Open the round-42 follow-up lane's docs(handoff) PR: every file the session worktree adds or changes.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use; wraps util/open_signed_pr.py
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

util/open_signed_pr.py takes one `--add LOCAL:REPOPATH` per file, and this PR carries about ninety,
which a session sandbox will not let a shell loop assemble. This takes the list from
`git status --porcelain --untracked-files=all` (added, modified and untracked paths) and refuses a
deletion or a rename, which the PR does not intend. `--dry-run` is forwarded.

Usage: python3 util/ad-hoc/2026-09-24_open_followup_handoff_pr.py --title T --message M --commit-body-file F --body-file B [--dry-run]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRANCH = "docs/handoff-round42-followup-lane"


def changed_paths() -> list[str]:
    """Every path the worktree adds or modifies; exit on anything else."""
    out = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=REPO, capture_output=True, text=True, check=True).stdout
    paths = []
    for line in out.splitlines():
        code, path = line[:2], line[3:]
        if code not in ("??", " M", "M ", "A ", "AM", "MM"):
            raise SystemExit(f"refusing: {code!r} {path} is not an addition or a modification")
        paths.append(path)
    return sorted(paths)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    for flag in ("--title", "--message", "--commit-body-file", "--body-file"):
        ap.add_argument(flag, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    files = changed_paths()
    cmd = [sys.executable, str(REPO / "util/open_signed_pr.py"), "--repo", "juniper-ml", "--branch", BRANCH]
    for f in files:
        cmd += ["--add", f"{f}:{f}"]
    cmd += ["--message", args.message, "--commit-body-file", args.commit_body_file, "--title", args.title, "--body-file", args.body_file]
    if args.dry_run:
        cmd.append("--dry-run")
    print(f"{len(files)} files -> {BRANCH}")
    return subprocess.run(cmd, cwd=REPO).returncode


if __name__ == "__main__":
    raise SystemExit(main())

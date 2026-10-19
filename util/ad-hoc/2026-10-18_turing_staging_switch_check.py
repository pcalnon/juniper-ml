"""
Before discarding local staging state, prove a pushed PR head already carries all of it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-18
Status: ad-hoc — one-off (switching the turing Session 1 staging worktree from one landed task to the next)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-18_turing_verify_landed_branch.py

Why: turing never commits locally (an unsigned commit makes a branch unmergeable), so each task's wiring lives as
uncommitted edits plus untracked files until it is pushed through the API. Moving the staging worktree to the next
task discards that state, so this checks first. Untracked files: their blob must equal the PR head's blob.
Modified tracked files: merging the local change (local vs BASE) into the PR head's version must be a no-op,
i.e. the PR head already contains it, even if the head has since merged `main`.

Usage:
    python3 -I util/ad-hoc/2026-10-18_turing_staging_switch_check.py PR_HEAD_SHA LOCAL_BASE_SHA UNTRACKED[,...] MODIFIED[,...]

Exit 0 when everything is safe to discard; 1 otherwise.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

REF = sys.argv[1]  # the PR head
BASE = sys.argv[2]  # the local branch's HEAD the modifications sit on
UNTRACKED = sys.argv[3].split(",")
MODIFIED = sys.argv[4].split(",")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


ok = True
for p in UNTRACKED:
    local = git("hash-object", p).decode().strip()
    remote = git("rev-parse", f"{REF}:{p}").decode().strip()
    same = local == remote
    ok &= same
    print(f"{'SAME' if same else 'DIFF'}  untracked  {p}")

with tempfile.TemporaryDirectory() as d:
    for p in MODIFIED:
        base = Path(d, "base")
        theirs = Path(d, "theirs")
        mine = Path(d, "mine")
        base.write_bytes(git("show", f"{BASE}:{p}"))
        theirs.write_bytes(git("show", f"{REF}:{p}"))
        mine.write_bytes(Path(p).read_bytes())
        r = subprocess.run(["git", "merge-file", "-p", str(mine), str(base), str(theirs)], capture_output=True)
        contained = r.returncode == 0 and r.stdout == theirs.read_bytes()
        ok &= contained
        print(f"{'CONTAINED' if contained else 'NOT-CONTAINED'}  modified  {p}  (merge-file rc={r.returncode})")

print("ALL SAFE TO DISCARD" if ok else "STOP: something local is not in the PR head")
sys.exit(0 if ok else 1)

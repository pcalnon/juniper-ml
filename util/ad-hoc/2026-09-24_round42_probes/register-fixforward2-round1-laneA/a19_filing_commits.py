#!/usr/bin/env python3
"""Lane A: which commit first added each named register row (git log -S on the row's table prefix, oldest first).

git runs with cwd = this session's worktree (shared object store), read-only.
usage: a19_filing_commits.py <rev> <ID> [<ID> ...]
"""
import subprocess
import sys

W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
R = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
rev = sys.argv[1]
for rid in sys.argv[2:]:
    out = subprocess.run(["git", "log", "--reverse", "--format=%h %ad %s", "--date=iso-strict", "-S", f"| {rid} |", rev, "--", R], cwd=W, capture_output=True, text=True).stdout.strip().split("\n")
    print(f"{rid}: first {out[0][:130]}")
    if len(out) > 1:
        print(f"    (count-changing commits: {len(out)}; later: {[x[:9] for x in out[1:]]})")

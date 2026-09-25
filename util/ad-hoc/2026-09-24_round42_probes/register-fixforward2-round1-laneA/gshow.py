#!/usr/bin/env python3
"""Lane A helper: extract files at a commit with `git show`, run inside a given repo dir.

usage: gshow.py <repo_dir> <rev> <outdir> <path> [<path> ...]
Writes <outdir>/<basename-of-path>. Read-only on the repo.
"""
import os
import subprocess
import sys

repo, rev, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for p in sys.argv[4:]:
    data = subprocess.run(["git", "show", f"{rev}:{p}"], cwd=repo, check=True, capture_output=True).stdout
    dst = os.path.join(outdir, os.path.basename(p))
    with open(dst, "wb") as fh:
        fh.write(data)
    print(f"{rev}:{p} -> {dst} ({len(data)} bytes)")

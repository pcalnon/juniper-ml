#!/usr/bin/env python3
"""Print numbered line ranges of files at a commit (read-only; uses `git show`).

Usage: lines_at.py REPO_DIR SHA path:START-END [path:START-END ...]
"""
import subprocess
import sys

repo, sha = sys.argv[1], sys.argv[2]
for spec in sys.argv[3:]:
    path, rng = spec.rsplit(":", 1)
    if "-" in rng:
        a, b = (int(x) for x in rng.split("-"))
    else:
        a = b = int(rng)
    out = subprocess.run(["git", "-C", repo, "show", f"{sha}:{path}"], capture_output=True, text=True, check=True).stdout
    lines = out.split("\n")
    print(f"=== {path}:{a}-{b} @ {sha[:8]}")
    for n in range(a, b + 1):
        if 1 <= n <= len(lines):
            print(f"{n:6d}  {lines[n - 1][:260]}")

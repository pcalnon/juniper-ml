#!/usr/bin/env python3
"""Lane A: merge time (UTC) and title of named PRs, via read-only `gh api` GETs.

usage: a20_pr_dates.py <repo>#<n> [...]   (repo without owner; owner pcalnon)
"""
import json
import subprocess
import sys

for spec in sys.argv[1:]:
    repo, n = spec.split("#")
    r = subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/pulls/{n}"], capture_output=True, text=True)
    if r.returncode:
        print(f"{spec}: ERROR {r.stderr.strip()[:120]}")
        continue
    d = json.loads(r.stdout)
    print(f"{spec}: state={d['state']} merged_at={d.get('merged_at')} title={d['title'][:90]!r}")

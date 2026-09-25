#!/usr/bin/env python3
"""Read-only: print PR metadata (and optionally body) for pcalnon/<repo> PR numbers via gh api GET.

Usage: ghpr.py <repo> <n> [<n> ...] [--body]
"""
import json
import subprocess
import sys

repo = sys.argv[1]
nums = [a for a in sys.argv[2:] if a.isdigit()]
body = "--body" in sys.argv
for n in nums:
    d = json.loads(subprocess.run(["gh", "api", f"repos/pcalnon/{repo}/pulls/{n}"], check=True, capture_output=True, text=True).stdout)
    print(f"{repo}#{d['number']} state={d['state']} merged={d['merged']} merged_at={d['merged_at']} created={d['created_at']} closed={d['closed_at']}")
    print(f"   base={d['base']['ref']} head={d['head']['ref']} head_sha={d['head']['sha'][:12]} merge_sha={(d['merge_commit_sha'] or '')[:12]}")
    print(f"   title={d['title']}")
    if body:
        print("   body:\n" + (d.get("body") or "").replace("\r\n", "\n"))

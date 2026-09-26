#!/usr/bin/env python3
"""Lane A: merge commit SHA and merge time of named juniper-ml PRs (read-only gh api GETs)."""
import json
import subprocess
import sys

for n in sys.argv[1:]:
    d = json.loads(subprocess.run(["gh", "api", f"repos/pcalnon/juniper-ml/pulls/{n}"], capture_output=True, text=True, check=True).stdout)
    print(f"ml#{n}: merged_at={d.get('merged_at')} merge_sha={(d.get('merge_commit_sha') or '')[:8]} title={d['title'][:80]!r}")

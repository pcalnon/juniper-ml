#!/usr/bin/env python3
"""Round 4 lane F probe: workflow runs on the post-merge commits (read-only gh api GETs)."""
import json
import subprocess


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        return {"__error__": p.stderr.strip()[:300]}
    return json.loads(p.stdout)


for repo, sha in (("juniper-data", "264915319cd32632d362e7ce5f401028658c75f1"),
                  ("juniper-cascor", "0fbb447a1455ca19ef042a5f925b306ab2d3e3e2"),
                  ("juniper-cascor", "b9484fef98430a6b0c833c5a158cb94f4a132912")):
    r = gh("api", f"repos/pcalnon/{repo}/actions/runs?head_sha={sha}&per_page=50")
    print(f"== {repo} {sha[:8]}: {r.get('total_count')} runs ==")
    for run in r.get("workflow_runs", []):
        print(f"  {run['name'][:40]:40s} {run['event']:12s} {run['status']:10s} {str(run['conclusion']):10s} created {run['created_at']} updated {run['updated_at']}")
    cr = gh("api", f"repos/pcalnon/{repo}/commits/{sha}/check-runs?per_page=100")
    concl = {}
    for c in cr.get("check_runs", []):
        concl[c["conclusion"]] = concl.get(c["conclusion"], 0) + 1
    print("  check-runs by conclusion:", concl)

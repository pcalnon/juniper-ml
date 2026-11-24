"""Find runs whose artifact listing shows one name uploaded in two different attempts (read-only gh GETs).

Usage: python3 -I cross_attempt_artifacts.py REPO [REPO ...]
For each multi-attempt run in the newest 200 runs, list artifacts by name; report a name that appears twice with
created_at values that fall in different attempts' job windows.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import json
import subprocess
import sys
from collections import defaultdict


def gh(path):
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    return json.loads(proc.stdout) if proc.returncode == 0 else None


def main():
    for repo in sys.argv[1:]:
        found = 0
        for page in (1, 2):
            runs = (gh(f"repos/pcalnon/{repo}/actions/runs?per_page=100&page={page}") or {}).get("workflow_runs", [])
            for run in runs:
                if run.get("run_attempt", 1) < 2:
                    continue
                arts = (gh(f"repos/pcalnon/{repo}/actions/runs/{run['id']}/artifacts?per_page=100") or {}).get("artifacts", [])
                by_name = defaultdict(list)
                for a in arts:
                    by_name[a["name"]].append(a["created_at"])
                windows = []
                for attempt in range(1, run["run_attempt"] + 1):
                    jobs = (gh(f"repos/pcalnon/{repo}/actions/runs/{run['id']}/attempts/{attempt}/jobs?per_page=100") or {}).get("jobs", [])
                    stamps = sorted(t for j in jobs for t in (j.get("started_at"), j.get("completed_at")) if t)
                    windows.append((attempt, stamps[0] if stamps else None, stamps[-1] if stamps else None))
                for name, created in by_name.items():
                    if len(created) < 2:
                        continue
                    attempts = sorted({a for t in created for (a, lo, hi) in windows if lo and hi and lo <= t <= hi})
                    if len(attempts) >= 2:
                        found += 1
                        print(f"{repo} run {run['id']} ({run['name']}, attempts={run['run_attempt']}): {name!r} x{len(created)} created {sorted(created)} -> attempts {attempts}")
                if found >= 3:
                    return 0
        print(f"{repo}: {found} cross-attempt duplicate(s) found")
    return 0


if __name__ == "__main__":
    sys.exit(main())

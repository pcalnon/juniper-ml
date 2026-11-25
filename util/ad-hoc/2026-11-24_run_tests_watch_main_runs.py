"""
Wait until every workflow run for a commit has completed, then print each one's conclusion.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2629 (main at d7709ef7: CI/CD Pipeline, Post-Merge Main Verification and CodeQL Analysis succeeded)

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: wait until every workflow run for a commit has completed, then print each one's conclusion.

Exits 0 when all succeeded (or were skipped), 1 when any concluded otherwise, 2 on a timeout. Polls every 30 s.
"""

import json
import subprocess
import sys
import time

SHA = sys.argv[1]
DEADLINE = time.monotonic() + float(sys.argv[2] if len(sys.argv) > 2 else 3600)

while True:
    out = subprocess.run(["gh", "api", f"repos/pcalnon/juniper-ml/actions/runs?head_sha={SHA}&per_page=50"], capture_output=True, text=True, check=False)
    runs = json.loads(out.stdout or "{}").get("workflow_runs", []) if out.returncode == 0 else []
    if runs and all(run["status"] == "completed" for run in runs):
        bad = [run for run in runs if run["conclusion"] not in ("success", "skipped", "neutral")]
        for run in runs:
            print(f"{run['name']} | {run['event']} | {run['conclusion']} | {run['html_url']}")
        sys.exit(1 if bad else 0)
    if time.monotonic() > DEADLINE:
        for run in runs:
            print(f"{run['name']} | {run['status']}/{run['conclusion']}")
        print("timed out waiting")
        sys.exit(2)
    time.sleep(30)

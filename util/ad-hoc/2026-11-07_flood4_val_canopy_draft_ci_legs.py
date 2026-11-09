#!/usr/bin/env python3
"""
For each juniper-canopy flood-4 test draft, read its CI unit-test legs: runner image, and how its own test file ran.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; flood-4 validation brief (CI-parity lens)

Read-only `gh api` GETs. Finds the CI workflow run for each draft head, lists its "Unit Tests" jobs, downloads
each job's log into the scratch dir, and prints the runner image and the progress line(s) for the draft's own
test file (dots = passed, F = failed, s = skipped), plus the job's final pytest summary.

    python3 2026-11-07_flood4_val_canopy_draft_ci_legs.py <scratch dir>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "pcalnon/juniper-canopy"
DRAFTS = {
    "789": ("87b45f787386b3fdf9c77cd95cc5b814a2c85fa6", "test_bandit_sarif_upload.py"),
    "792": ("1006ccd8aa52c7075bad48c2786d091bac1cd854", "test_lockfile_regen_empty_payload.py"),
    "794": ("572e252b6f75abdcfe68d2025f87452ba492d6f0", "test_agents_md_date_check.py"),
    "795": ("d512cce82707bc84ca323f0635394552432a9a18", "test_codecov_token_upload.py"),
}


def api(path: str) -> dict | list:
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else {"error": out.stderr.strip()[:300]}


def main() -> int:
    scratch = Path(sys.argv[1])
    for pr, (head, test_file) in DRAFTS.items():
        runs = api(f"repos/{REPO}/actions/runs?head_sha={head}&per_page=30")
        ci_runs = [r for r in runs.get("workflow_runs", []) if r.get("path", "").endswith("/ci.yml")] if isinstance(runs, dict) else []
        print(f"\n=== #{pr} {head[:10]} CI runs: {[(r['id'], r['event'], r['conclusion']) for r in ci_runs]}")
        if not ci_runs:
            continue
        run = ci_runs[0]
        jobs = api(f"repos/{REPO}/actions/runs/{run['id']}/jobs?per_page=100")
        for job in jobs.get("jobs", []) if isinstance(jobs, dict) else []:
            if not job["name"].startswith("Unit Tests"):
                continue
            log_path = scratch / f"draft{pr}_job_{job['id']}.log"
            got = subprocess.run(["gh", "api", f"repos/{REPO}/actions/jobs/{job['id']}/logs"], capture_output=True, text=True, check=False)
            log_path.write_text(got.stdout, encoding="utf-8")
            text = got.stdout
            image = re.search(r"Image: (\S+)", text)
            rows = [line.split("Z ", 1)[-1] for line in text.splitlines() if test_file in line and ("::" not in line or "FAILED" in line or "SKIPPED" in line)]
            summary = [line.split("Z ", 1)[-1] for line in text.splitlines() if re.search(r"=+ .*(passed|failed).* in [0-9.]+s", line)]
            print(f"    job {job['id']} {job['conclusion']:8} {job['name']} image={image.group(1) if image else '?'}")
            for row in rows[:4]:
                print(f"        {row.strip()[:160]}")
            print(f"        summary: {summary[-1].strip() if summary else '(none)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

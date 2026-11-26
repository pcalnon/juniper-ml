"""
Census of juniper-canopy CI unit-lane failures of test_relay_cascade_add_does_not_block_the_loop since a date.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Usage:
    python <this file> --tsv <runs .tsv> --repo pcalnon/juniper-canopy --out <dir> [--max-runs 40]

The .tsv is one row per ci.yml run (id, run_attempt, conclusion, event, head_branch, prs, created_at, title), as
written by `gh api .../actions/workflows/ci.yml/runs --jq ... @tsv`. Selected: runs whose latest attempt failed, and
runs with more than one attempt (an earlier attempt may have failed and been re-run green). For every attempt of a
selected run, every "Unit Tests + Coverage" job whose conclusion is failure has its log fetched with read-only
`gh api` GETs into <out>/job_<id>.log and parsed: the runner image and version, the Python leg, every FAILED nodeid,
the relay test's stall, and the count of demo_mode "State broadcast failed" lines. Writes <out>/ci_history.json.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - read-only gh api GETs
import sys
from pathlib import Path

TEST = "test_relay_cascade_add_does_not_block_the_loop"
STALL = re.compile(r"the relay stalled the loop for ([0-9.]+)s")
FAILED = re.compile(r"^\S+Z FAILED (\S+)")
IMAGE = re.compile(r"^\S+Z Image: (\S+)")
VERSION = re.compile(r"^\S+Z Version: (\S+)")


def gh_json(path: str) -> dict:
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=True)  # nosec B603 B607
    return json.loads(out.stdout)


def gh_text(path: str) -> str:
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603 B607
    return out.stdout if out.returncode == 0 else ""


def parse_log(text: str) -> dict:
    image = version = None
    in_image = False
    failed: list[str] = []
    stalls: list[float] = []
    demo_lines = 0
    for line in text.splitlines():
        if line.endswith("##[group]Runner Image"):
            in_image = True
            continue
        if in_image:
            m = IMAGE.match(line)
            if m:
                image = m.group(1)
            m = VERSION.match(line)
            if m:
                version = m.group(1)
            if line.endswith("##[endgroup]"):
                in_image = False
        m = FAILED.match(line)
        if m and m.group(1) not in failed:
            failed.append(m.group(1))
        m = STALL.search(line)
        if m and " E " in line:
            stalls.append(float(m.group(1)))
        if "demo_mode: State broadcast failed" in line:
            demo_lines += 1
    return {"runner_image": image, "runner_image_version": version, "failed_nodeids": failed, "relay_stall_seconds": sorted(set(stalls)), "demo_state_broadcast_failed_lines": demo_lines}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tsv", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-runs", type=int, default=40)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = []
    for line in Path(args.tsv).read_text(encoding="utf-8").splitlines():
        fields = line.split("\t")
        if len(fields) < 8:
            continue
        run = {"id": int(fields[0]), "run_attempt": int(fields[1]), "conclusion": fields[2], "event": fields[3], "head_branch": fields[4], "prs": fields[5], "created_at": fields[6], "title": fields[7]}
        if run["conclusion"] == "failure" or run["run_attempt"] > 1:
            runs.append(run)
    runs = runs[: args.max_runs]
    records = []
    for run in runs:
        for attempt in range(1, run["run_attempt"] + 1):
            jobs = gh_json(f"repos/{args.repo}/actions/runs/{run['id']}/attempts/{attempt}/jobs?per_page=100").get("jobs", [])
            unit = [j for j in jobs if j.get("name", "").startswith("Unit Tests + Coverage")]
            for job in unit:
                rec = {"run_id": run["id"], "attempt": attempt, "run_conclusion_latest": run["conclusion"], "event": run["event"], "head_branch": run["head_branch"], "created_at": run["created_at"], "title": run["title"], "job_id": job["id"], "job_name": job["name"], "job_conclusion": job.get("conclusion")}
                if job.get("conclusion") == "failure":
                    text = gh_text(f"repos/{args.repo}/actions/jobs/{job['id']}/logs")
                    (out / f"job_{job['id']}.log").write_text(text, encoding="utf-8")
                    rec.update(parse_log(text))
                    rec["log"] = str(out / f"job_{job['id']}.log")
                    rec["relay_test_failed"] = any(TEST in n for n in rec["failed_nodeids"])
                records.append(rec)
    failed_jobs = [r for r in records if r.get("job_conclusion") == "failure"]
    relay = [r for r in failed_jobs if r.get("relay_test_failed")]
    summary = {"runs_examined": len(runs), "unit_lane_jobs_examined": len(records), "unit_lane_jobs_failed": len(failed_jobs), "relay_test_failures": len(relay), "relay_failures": [{k: r.get(k) for k in ("run_id", "attempt", "event", "head_branch", "created_at", "title", "job_id", "job_name", "runner_image", "runner_image_version", "relay_stall_seconds", "failed_nodeids", "demo_state_broadcast_failed_lines")} for r in relay], "other_failed_unit_jobs": [{k: r.get(k) for k in ("run_id", "attempt", "head_branch", "job_name", "failed_nodeids")} for r in failed_jobs if not r.get("relay_test_failed")]}
    with open(out / "ci_history.json", "w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "records": records, "runs": runs}, handle, indent=1)
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

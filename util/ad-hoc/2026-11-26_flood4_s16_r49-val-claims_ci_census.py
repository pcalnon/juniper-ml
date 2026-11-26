#!/usr/bin/env python3
"""
Independent CI census of juniper-canopy's X7 health test (test_health_stays_fast_while_upstream_is_slow) since a date.

Lists every ci.yml run created on or after --since, lists the jobs of EVERY attempt of every run (one GET per attempt),
and reads the job log of every unit-lane job that could hold a failure of the test: every failed, cancelled or
timed-out unit-lane job, and every job of the informational Python 3.15 leg, whose steps carry continue-on-error and so
conclude green when tests fail. From each log it takes the Python version, the runner image, the health test's verdict
and latency, and every other FAILED test. Only `gh api` GETs. A full log is kept only when it names the health test as
FAILED or ERROR; for every other log a digest is kept (size, sha256, the test's verdict, pytest's summary line).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens: settle the CI failure count)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 28, 49)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TEST = "test_health_stays_fast_while_upstream_is_slow"
NODE_RE = re.compile(r"test_x7_loop_responsiveness\.py::TestLoopStaysAnswerable::" + TEST + r"\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)")
LATENCY_RE = re.compile(r"/v1/health/live took ([0-9.]+)s while an upstream was slow")
FAILED_LINE_RE = re.compile(r"^(?:\S+\s+)?(FAILED|ERROR) (src/tests/\S+)")
PYTHON_RE = re.compile(r"platform (\w+) -- Python ([0-9.]+)")
IMAGE_RE = re.compile(r"^\S+\s+Image: (\S+)")
IMAGE_VERSION_RE = re.compile(r"^\S+\s+Version: (\S+)")
SUMMARY_RE = re.compile(r"=+ ((?:\d+ (?:failed|passed|skipped|deselected|errors?|warnings?|xfailed|xpassed)[, ]*)+ in [0-9.]+s(?: \([0-9:]+\))?) =+")


def gh_lines(args: list[str]) -> list[dict]:
    """Run one `gh api` GET whose --jq prints one JSON document per line; return the parsed documents."""
    proc = subprocess.run(["gh", "api", "-X", "GET", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {' '.join(args)} failed: {proc.stderr.strip()[:400]}")
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def list_runs(repo: str, workflow: str, since: str) -> list[dict]:
    jq = ".workflow_runs[] | {id, run_attempt, status, conclusion, event, head_branch, head_sha, created_at, updated_at, display_title} | tojson"
    rows = gh_lines([f"repos/{repo}/actions/workflows/{workflow}/runs", "-f", f"created=>={since}", "-f", "per_page=100", "--paginate", "--jq", jq])
    return [json.loads(r) if isinstance(r, str) else r for r in rows]


def list_jobs(repo: str, run_id: int, attempt: int) -> list[dict]:
    jq = ".jobs[] | {id, run_id, run_attempt, name, status, conclusion, started_at, completed_at, runner_name, labels, head_branch, head_sha, steps: [.steps[]? | {name, number, status, conclusion}]} | tojson"
    rows = gh_lines([f"repos/{repo}/actions/runs/{run_id}/attempts/{attempt}/jobs", "-f", "per_page=100", "--paginate", "--jq", jq])
    return [json.loads(r) if isinstance(r, str) else r for r in rows]


def fetch_log(repo: str, job_id: int) -> bytes:
    proc = subprocess.run(["gh", "api", f"repos/{repo}/actions/jobs/{job_id}/logs"], capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"log of job {job_id}: {proc.stderr.decode(errors='replace').strip()[:400]}")
    return proc.stdout


def digest_log(raw: bytes) -> dict:
    text = raw.decode("utf-8", errors="replace")
    out: dict = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "verdicts": [], "latencies": [], "failed_tests": [], "python": None, "platform": None, "image": None, "image_version": None, "summary": None}
    for line in text.splitlines():
        m = NODE_RE.search(line)
        if m:
            out["verdicts"].append(m.group(1))
        m = LATENCY_RE.search(line)
        if m:
            out["latencies"].append(float(m.group(1)))
        body = line.split(" ", 1)[1] if line[:4].isdigit() and " " in line else line
        m = FAILED_LINE_RE.match(body)
        if m:
            out["failed_tests"].append(f"{m.group(1)} {m.group(2)}")
        if out["python"] is None:
            m = PYTHON_RE.search(line)
            if m:
                out["platform"], out["python"] = m.group(1), m.group(2)
        if out["image"] is None:
            m = IMAGE_RE.match(line)
            if m:
                out["image"] = m.group(1)
        # The first "Version:" of a log is the Hosted Compute Agent's; the image's follows "Image:".
        if out["image"] is not None and out["image_version"] is None:
            m = IMAGE_VERSION_RE.match(line)
            if m:
                out["image_version"] = m.group(1)
        m = SUMMARY_RE.search(line)
        if m:
            out["summary"] = m.group(1)
    out["failed_tests"] = sorted(set(out["failed_tests"]))
    out["latencies"] = sorted(set(out["latencies"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--repo", default="pcalnon/juniper-canopy")
    ap.add_argument("--workflow", default="ci.yml")
    ap.add_argument("--since", default="2026-11-01")
    ap.add_argument("--out", required=True, help="output directory (created)")
    args = ap.parse_args()

    out = Path(args.out)
    (out / "jobs").mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    (out / "digests").mkdir(parents=True, exist_ok=True)

    runs = list_runs(args.repo, args.workflow, args.since)
    (out / "runs_all.json").write_text(json.dumps(runs, indent=1) + "\n", encoding="utf-8")
    print(f"runs listed: {len(runs)}", flush=True)

    unit_jobs: list[dict] = []
    for i, run in enumerate(runs):
        for attempt in range(1, int(run["run_attempt"]) + 1):
            cache = out / "jobs" / f"{run['id']}_{attempt}.json"
            if cache.exists() and run["status"] == "completed":
                with cache.open(encoding="utf-8") as fh:
                    jobs = json.load(fh)
            else:
                jobs = list_jobs(args.repo, run["id"], attempt)
                cache.write_text(json.dumps(jobs, indent=1) + "\n", encoding="utf-8")
            for job in jobs:
                if job["name"].startswith("Unit Tests + Coverage"):
                    job["run_event"] = run["event"]
                    job["run_title"] = run["display_title"]
                    job["run_created_at"] = run["created_at"]
                    job["run_status"] = run["status"]
                    job["run_conclusion"] = run["conclusion"]
                    job["attempt"] = attempt
                    unit_jobs.append(job)
        if i % 25 == 0:
            print(f"jobs listed for {i + 1}/{len(runs)} runs; unit-lane jobs so far {len(unit_jobs)}", flush=True)

    targets = [j for j in unit_jobs if j["conclusion"] in ("failure", "cancelled", "timed_out") or "Python 3.15" in j["name"]]
    print(f"unit-lane jobs: {len(unit_jobs)}; log targets: {len(targets)}", flush=True)

    records = []
    for k, job in enumerate(targets):
        digest_path = out / "digests" / f"{job['id']}.json"
        if digest_path.exists():
            with digest_path.open(encoding="utf-8") as fh:
                digest = json.load(fh)
        elif job["status"] != "completed":
            digest = {"skipped": f"job status {job['status']}"}
        else:
            try:
                raw = fetch_log(args.repo, job["id"])
            except RuntimeError as exc:
                digest = {"error": str(exc)}
            else:
                digest = digest_log(raw)
                if any(v in ("FAILED", "ERROR") for v in digest["verdicts"]) or digest["latencies"]:
                    (out / "logs" / f"{job['id']}.log").write_bytes(raw)
                    digest["log_kept"] = True
            digest_path.write_text(json.dumps(digest, indent=1) + "\n", encoding="utf-8")
        records.append({"job": {k2: job.get(k2) for k2 in ("id", "run_id", "attempt", "name", "status", "conclusion", "started_at", "completed_at", "head_branch", "head_sha", "run_event", "run_title", "run_created_at", "run_status", "run_conclusion")}, "unit_step": next((s for s in job.get("steps", []) if s["name"] == "Run Unit Tests with Coverage Gate"), None), "digest": digest})
        if k % 20 == 0:
            print(f"logs read {k + 1}/{len(targets)}", flush=True)

    health = [r for r in records if any(v in ("FAILED", "ERROR") for v in r["digest"].get("verdicts", [])) or r["digest"].get("latencies")]
    summary = {
        "repo": args.repo,
        "workflow": args.workflow,
        "since": args.since,
        "runs_listed": len(runs),
        "runs_not_completed": [{"id": r["id"], "status": r["status"], "created_at": r["created_at"]} for r in runs if r["status"] != "completed"],
        "attempts_listed": sum(int(r["run_attempt"]) for r in runs),
        "unit_lane_jobs": len(unit_jobs),
        "unit_lane_jobs_by_conclusion": {c: sum(1 for j in unit_jobs if j["conclusion"] == c) for c in sorted({str(j["conclusion"]) for j in unit_jobs})},
        "unit_lane_jobs_py315": sum(1 for j in unit_jobs if "Python 3.15" in j["name"]),
        "log_targets": len(targets),
        "health_test_failures": [
            {
                "run_id": r["job"]["run_id"],
                "attempt": r["job"]["attempt"],
                "job_id": r["job"]["id"],
                "job_name": r["job"]["name"],
                "job_conclusion": r["job"]["conclusion"],
                "event": r["job"]["run_event"],
                "branch": r["job"]["head_branch"],
                "head_sha": r["job"]["head_sha"],
                "title": r["job"]["run_title"],
                "started_at": r["job"]["started_at"],
                "python": r["digest"].get("python"),
                "image": r["digest"].get("image"),
                "image_version": r["digest"].get("image_version"),
                "latencies": r["digest"].get("latencies"),
                "verdicts": r["digest"].get("verdicts"),
                "other_failed_tests": [t for t in r["digest"].get("failed_tests", []) if TEST not in t],
                "summary": r["digest"].get("summary"),
            }
            for r in health
        ],
        "py315_jobs": [
            {"job_id": r["job"]["id"], "run_id": r["job"]["run_id"], "attempt": r["job"]["attempt"], "conclusion": r["job"]["conclusion"], "unit_step": r["unit_step"], "verdicts": r["digest"].get("verdicts"), "summary": r["digest"].get("summary"), "python": r["digest"].get("python"), "note": r["digest"].get("error") or r["digest"].get("skipped")}
            for r in records
            if "Python 3.15" in r["job"]["name"]
        ],
        "failed_unit_jobs": [
            {"job_id": r["job"]["id"], "run_id": r["job"]["run_id"], "attempt": r["job"]["attempt"], "name": r["job"]["name"], "conclusion": r["job"]["conclusion"], "event": r["job"]["run_event"], "branch": r["job"]["head_branch"], "failed_tests": r["digest"].get("failed_tests"), "health_verdicts": r["digest"].get("verdicts"), "note": r["digest"].get("error") or r["digest"].get("skipped")}
            for r in records
            if r["job"]["conclusion"] in ("failure", "cancelled", "timed_out")
        ],
    }
    (out / "census.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    (out / "unit_jobs.json").write_text(json.dumps(unit_jobs, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("runs_listed", "attempts_listed", "unit_lane_jobs", "unit_lane_jobs_by_conclusion", "unit_lane_jobs_py315", "log_targets")}, indent=1))
    print(f"health-test failures: {len(health)}")
    for h in summary["health_test_failures"]:
        print(json.dumps(h))
    return 0


if __name__ == "__main__":
    sys.exit(main())

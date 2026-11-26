"""
Re-derive juniper-canopy's unit-lane failures of the X7 health test since a date, from the GitHub job logs (gh api GETs).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) and its parent ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16 builder r49.
    Written independently of util/ad-hoc/2026-11-25_flood4_s14_r28-val-claims_ci_census.py, to re-measure its count.

Usage:
    python3 -I <this file> --repo pcalnon/juniper-canopy --since 2026-11-01 --out <output dir> [--max-runs 40]

Selection (bounded, as the r49 brief asks): every ci.yml run created on or after --since whose latest attempt concluded
"failure", plus every run with run_attempt > 1 (a green re-run can hide a failed first attempt). Newest first, at most
--max-runs runs. For each selected run every attempt's jobs are listed; only "Unit Tests + Coverage" jobs are kept, and
only FAILED ones have their log fetched (one GET each, cached in <out>/logs/).

Per failed unit-lane job it records the runner image and version ("Runner Image" group of Set up job), the Python
version pytest prints, every FAILED line of the short summary, and for the health test the latency in its message.
For a health-test failure it also resolves the pull request (the run's pull_requests, else GET commits/<sha>/pulls)
and the Actions-timestamp gap between the health test's verbose result line and the result line before it.

Outputs in --out: runs_all.json, census.json, failed_jobs.tsv, health_failures.json. Every call is a GET.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess  # nosec B404 - fixed gh argv lists, no shell
import sys
from pathlib import Path

UNIT_JOB_PREFIX = "Unit Tests + Coverage"
HEALTH_NODE = "test_x7_loop_responsiveness.py::TestLoopStaysAnswerable::test_health_stays_fast_while_upstream_is_slow"
TS_RE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z ")
FAILED_RE = re.compile(r"^FAILED (\S+::\S+)(?: - (.*))?$")
IMAGE_RE = re.compile(r"^\s*Image: (\S+)\s*$")
VERSION_RE = re.compile(r"^\s*Version: (\S+)\s*$")
PLATFORM_RE = re.compile(r"platform (\S+) -- Python (\d+\.\d+\.\d+)")
HEALTH_VALUE_RE = re.compile(r"/v1/health/live took (\d+\.\d+)s")
VERBOSE_RESULT_RE = re.compile(r"^(src/tests/\S+::\S+) (PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)")
PR_IN_MESSAGE_RE = re.compile(r"\(#(\d+)\)\s*$")


def gh_get(path: str, paginate: bool = False) -> str:
    argv = ["gh", "api", "-H", "Accept: application/vnd.github+json", path]
    if paginate:
        argv.insert(2, "--paginate")
    cp = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    if cp.returncode != 0:
        raise RuntimeError(f"gh api {path} failed ({cp.returncode}): {cp.stderr.strip()[:400]}")
    return cp.stdout


def gh_pages(path: str, key: str) -> list[dict]:
    text = gh_get(path, paginate=True).strip()
    decoder = json.JSONDecoder()
    items: list[dict] = []
    index = 0
    while index < len(text):
        obj, end = decoder.raw_decode(text, index)
        items.extend(obj.get(key, []))
        index = end
        while index < len(text) and text[index].isspace():
            index += 1
    return items


def _stamp(line: str) -> tuple[dt.datetime | None, str]:
    match = TS_RE.match(line)
    if not match:
        return None, line
    raw = match.group(1)
    head, _, frac = raw.partition(".")
    stamp = dt.datetime.fromisoformat(f"{head}.{frac[:6]}")
    return stamp, line[match.end() :]


def parse_log(text: str) -> dict:
    image = version = python = platform = None
    failed: list[dict] = []
    seen = set()
    previous_result: tuple[dt.datetime | None, str] | None = None
    health_gap = None
    for raw in text.splitlines():
        stamp, body = _stamp(raw.rstrip("\r"))
        if image is None:
            match = IMAGE_RE.match(body)
            if match:
                image = match.group(1)
        elif version is None:
            match = VERSION_RE.match(body)
            if match:
                version = match.group(1)
        if python is None:
            match = PLATFORM_RE.search(body)
            if match:
                platform, python = match.group(1), match.group(2)
        verbose = VERBOSE_RESULT_RE.match(body)
        if verbose:
            if HEALTH_NODE in verbose.group(1) and previous_result is not None and stamp is not None and previous_result[0] is not None:
                health_gap = {"previous_test": previous_result[1], "seconds": round((stamp - previous_result[0]).total_seconds(), 3), "result": verbose.group(2)}
            previous_result = (stamp, verbose.group(1))
        match = FAILED_RE.match(body)
        if match:
            key = (match.group(1), match.group(2) or "")
            if key in seen:
                continue
            seen.add(key)
            message = (match.group(2) or "")[:600]
            value = HEALTH_VALUE_RE.search(message)
            failed.append({"nodeid": match.group(1), "message": message, "health_latency_s": float(value.group(1)) if value else None})
    return {"image": image, "image_version": version, "platform": platform, "python": python, "failed": failed, "health_verbose_gap": health_gap}


def resolve_prs(repo: str, run: dict) -> list[int]:
    if run["pull_requests"]:
        return run["pull_requests"]
    if run["event"] == "push":
        match = PR_IN_MESSAGE_RE.search(run["head_commit_title"] or "")
        return [int(match.group(1))] if match else []
    pulls = json.loads(gh_get(f"repos/{repo}/commits/{run['head_sha']}/pulls"))
    return [p["number"] for p in pulls]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--since", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-runs", type=int, default=40)
    args = parser.parse_args()
    out = Path(args.out)
    (out / "logs").mkdir(parents=True, exist_ok=True)

    runs = gh_pages(f"repos/{args.repo}/actions/workflows/ci.yml/runs?created=%3E%3D{args.since}&per_page=100", "workflow_runs")
    slim = [
        {
            "id": r["id"],
            "run_attempt": r.get("run_attempt") or 1,
            "conclusion": r.get("conclusion"),
            "status": r.get("status"),
            "event": r.get("event"),
            "head_branch": r.get("head_branch"),
            "head_sha": r.get("head_sha"),
            "created_at": r.get("created_at"),
            "pull_requests": [p.get("number") for p in r.get("pull_requests") or []],
            "head_commit_title": (((r.get("head_commit") or {}).get("message") or "").splitlines() or [""])[0],
        }
        for r in runs
    ]
    (out / "runs_all.json").write_text(json.dumps(slim, indent=1), encoding="utf-8")
    selected = sorted((r for r in slim if r["conclusion"] == "failure" or r["run_attempt"] > 1), key=lambda r: r["created_at"], reverse=True)
    truncated = len(selected) > args.max_runs
    eligible = len(selected)
    selected = selected[: args.max_runs]

    records, health = [], []
    tsv = ["run\tattempt\tjob\tjob_name\tevent\tbranch\tprs\tcreated\timage\timage_version\tpython\tnodeid\thealth_latency_s"]
    for run in selected:
        for attempt in range(1, run["run_attempt"] + 1):
            for job in gh_pages(f"repos/{args.repo}/actions/runs/{run['id']}/attempts/{attempt}/jobs?per_page=100", "jobs"):
                if not (job.get("name") or "").startswith(UNIT_JOB_PREFIX):
                    continue
                record = {"run": run["id"], "attempt": attempt, "latest_attempt": run["run_attempt"], "run_conclusion": run["conclusion"], "event": run["event"], "branch": run["head_branch"], "head_sha": run["head_sha"], "created_at": run["created_at"], "job": job["id"], "job_name": job.get("name"), "job_conclusion": job.get("conclusion"), "started_at": job.get("started_at")}
                if job.get("conclusion") == "failure":
                    log_path = out / "logs" / f"job_{job['id']}.log"
                    if not log_path.exists():
                        log_path.write_text(gh_get(f"repos/{args.repo}/actions/jobs/{job['id']}/logs"), encoding="utf-8")
                    parsed = parse_log(log_path.read_text(encoding="utf-8", errors="replace"))
                    record.update(parsed)
                    health_rows = [f for f in parsed["failed"] if HEALTH_NODE in f["nodeid"]]
                    prs = resolve_prs(args.repo, run) if health_rows else run["pull_requests"]
                    record["prs"] = prs
                    for failure in parsed["failed"] or [{"nodeid": "(no FAILED line)", "health_latency_s": None}]:
                        tsv.append("\t".join(str(x) for x in (run["id"], attempt, job["id"], job.get("name"), run["event"], run["head_branch"], ",".join(map(str, prs)), run["created_at"], parsed["image"], parsed["image_version"], parsed["python"], failure["nodeid"], failure.get("health_latency_s"))))
                    for failure in health_rows:
                        health.append({**{k: record[k] for k in ("run", "attempt", "latest_attempt", "run_conclusion", "event", "branch", "head_sha", "created_at", "job", "job_name", "image", "image_version", "python")}, "prs": prs, "head_commit_title": run["head_commit_title"], "health_latency_s": failure["health_latency_s"], "message": failure["message"], "verbose_gap": parsed["health_verbose_gap"], "other_failures_in_job": [f["nodeid"] for f in parsed["failed"] if HEALTH_NODE not in f["nodeid"]]})
                records.append(record)
    summary = {"since": args.since, "all_runs_listed": len(slim), "eligible_runs": eligible, "selected_runs": len(selected), "truncated": truncated, "oldest_selected": selected[-1]["created_at"] if selected else None, "unit_lane_jobs": len(records), "failed_unit_lane_jobs": sum(1 for r in records if r["job_conclusion"] == "failure"), "health_failures": len(health)}
    (out / "census.json").write_text(json.dumps({"summary": summary, "records": records}, indent=1), encoding="utf-8")
    (out / "health_failures.json").write_text(json.dumps({"summary": summary, "health_failures": health}, indent=1), encoding="utf-8")
    (out / "failed_jobs.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())

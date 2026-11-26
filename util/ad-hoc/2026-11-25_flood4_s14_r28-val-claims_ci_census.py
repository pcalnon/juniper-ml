"""
Re-derive juniper-canopy's unit-lane failure history from GitHub with read-only gh api GETs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r28 (juniper-canopy's load-sensitive relay test). Written independently
    of the builder's census tooling, to re-measure its numbers.

Usage:
    python3 -I <this file> --repo pcalnon/juniper-canopy --since 2026-11-01 --out <output dir> [--max-runs 40]

Selection: every ci.yml run created on or after --since whose LATEST attempt concluded failure, plus every run whose
run_attempt is greater than 1 (a re-run: its earlier attempt may have failed and been hidden by a green re-run). At
most --max-runs runs are read (newest first). For each selected run, every attempt's jobs are listed; only the
"Unit Tests + Coverage" jobs are kept, and only FAILED unit-lane jobs have their log fetched (one GET each).

From each fetched log it records: the runner image and version (the "Runner Image" group of Set up job), the
interpreter pytest reports ("platform ... -- Python X.Y.Z"), every FAILED line of pytest's short summary, and the
stall or latency value in each failure message. Outputs in --out: runs_all.json (the listing), census.json (one
record per selected run, attempt and unit job), failed_jobs.tsv, logs/job_<id>.log.

Every call is a GET (`gh api <path>`); nothing is written to GitHub.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed gh argv lists, no shell
import sys
from pathlib import Path

UNIT_JOB_PREFIX = "Unit Tests + Coverage"
FAILED_RE = re.compile(r"^(?:\S+\s+)?FAILED (\S+?)(?: - (.*))?$")
VALUE_RES = (
    ("stall", re.compile(r"stalled the loop for (\d+\.\d+)s")),
    ("health", re.compile(r"(\d+\.\d+)\s*s")),
)
IMAGE_RE = re.compile(r"^\S*\s*Image: (\S+)\s*$")
VERSION_RE = re.compile(r"^\S*\s*Version: (\S+)\s*$")
PLATFORM_RE = re.compile(r"platform (\S+) -- Python (\d+\.\d+\.\d+\S*)")


def gh_get(path: str, paginate: bool = False) -> str:
    argv = ["gh", "api", "-H", "Accept: application/vnd.github+json", path]
    if paginate:
        argv.insert(2, "--paginate")
    cp = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603 - fixed argv
    if cp.returncode != 0:
        raise RuntimeError(f"gh api {path} failed ({cp.returncode}): {cp.stderr.strip()[:400]}")
    return cp.stdout


def gh_get_json_pages(path: str, key: str) -> list[dict]:
    out = gh_get(path, paginate=True)
    items: list[dict] = []
    # --paginate concatenates JSON objects; decode them one after another.
    dec = json.JSONDecoder()
    idx = 0
    out = out.strip()
    while idx < len(out):
        obj, end = dec.raw_decode(out, idx)
        items.extend(obj.get(key, []))
        idx = end
        while idx < len(out) and out[idx].isspace():
            idx += 1
    return items


def parse_log(text: str) -> dict:
    image = version = None
    platform = python = None
    failed: list[dict] = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        # strip the Actions timestamp prefix "2026-11-12T01:50:38.1234567Z "
        body = re.sub(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+Z ", "", line)
        if image is None:
            m = IMAGE_RE.match(body)
            if m:
                image = m.group(1)
        if version is None and image is not None:
            m = VERSION_RE.match(body)
            if m:
                version = m.group(1)
        if python is None:
            m = PLATFORM_RE.search(body)
            if m:
                platform, python = m.group(1), m.group(2)
        m = FAILED_RE.match(body)
        if m and "::" in m.group(1):
            failed.append({"nodeid": m.group(1), "message": (m.group(2) or "")[:600]})
    for f in failed:
        msg = f["message"]
        m = VALUE_RES[0][1].search(msg)
        f["value_s"] = float(m.group(1)) if m else None
        if f["value_s"] is None and "health" in f["nodeid"]:
            nums = [float(x) for x in re.findall(r"(\d+\.\d+)\s*s\b", msg)]
            f["value_s"] = nums[0] if nums else None
            f["all_numbers"] = nums
    # de-duplicate repeated summary lines (the summary can print twice with --verbose + -rA)
    seen = set()
    uniq = []
    for f in failed:
        key = (f["nodeid"], f["message"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return {"image": image, "image_version": version, "platform": platform, "python": python, "failed": uniq}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--since", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-runs", type=int, default=40)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "logs").mkdir(parents=True, exist_ok=True)

    runs = gh_get_json_pages(f"repos/{args.repo}/actions/workflows/ci.yml/runs?created=%3E%3D{args.since}&per_page=100", "workflow_runs")
    slim = [
        {
            "id": r["id"],
            "run_attempt": r.get("run_attempt"),
            "conclusion": r.get("conclusion"),
            "status": r.get("status"),
            "event": r.get("event"),
            "head_branch": r.get("head_branch"),
            "head_sha": r.get("head_sha"),
            "created_at": r.get("created_at"),
            "display_title": r.get("display_title"),
            "pull_requests": [p.get("number") for p in r.get("pull_requests") or []],
            "head_commit_message": ((r.get("head_commit") or {}).get("message") or "").splitlines()[:1],
        }
        for r in runs
    ]
    (out / "runs_all.json").write_text(json.dumps(slim, indent=1), encoding="utf-8")
    selected = [r for r in slim if r["conclusion"] == "failure" or (r["run_attempt"] or 1) > 1]
    selected.sort(key=lambda r: r["created_at"], reverse=True)
    truncated = len(selected) > args.max_runs
    selected = selected[: args.max_runs]

    census = []
    tsv = ["run\tattempt\tjob\tjob_name\tevent\tbranch\tprs\tcreated\timage\timage_version\tpython\tnodeid\tvalue_s"]
    for r in selected:
        for attempt in range(1, (r["run_attempt"] or 1) + 1):
            jobs = gh_get_json_pages(f"repos/{args.repo}/actions/runs/{r['id']}/attempts/{attempt}/jobs?per_page=100", "jobs")
            for j in jobs:
                if not (j.get("name") or "").startswith(UNIT_JOB_PREFIX):
                    continue
                rec = {
                    "run": r["id"],
                    "attempt": attempt,
                    "latest_attempt": r["run_attempt"],
                    "run_conclusion": r["conclusion"],
                    "event": r["event"],
                    "branch": r["head_branch"],
                    "prs": r["pull_requests"],
                    "head_sha": r["head_sha"],
                    "head_commit_message": r["head_commit_message"],
                    "created_at": r["created_at"],
                    "job": j["id"],
                    "job_name": j.get("name"),
                    "job_conclusion": j.get("conclusion"),
                    "labels": j.get("labels"),
                    "started_at": j.get("started_at"),
                }
                if j.get("conclusion") == "failure":
                    log_path = out / "logs" / f"job_{j['id']}.log"
                    if not log_path.exists():
                        log_path.write_text(gh_get(f"repos/{args.repo}/actions/jobs/{j['id']}/logs"), encoding="utf-8")
                    parsed = parse_log(log_path.read_text(encoding="utf-8", errors="replace"))
                    rec.update(parsed)
                    for f in parsed["failed"] or [{"nodeid": "(no FAILED line)", "value_s": None}]:
                        tsv.append(
                            "\t".join(
                                str(x)
                                for x in (
                                    r["id"],
                                    attempt,
                                    j["id"],
                                    j.get("name"),
                                    r["event"],
                                    r["head_branch"],
                                    ",".join(str(p) for p in r["pull_requests"]),
                                    r["created_at"],
                                    parsed["image"],
                                    parsed["image_version"],
                                    parsed["python"],
                                    f["nodeid"],
                                    f.get("value_s"),
                                )
                            )
                        )
                census.append(rec)
    (out / "census.json").write_text(json.dumps({"selected_runs": len(selected), "truncated": truncated, "all_runs_listed": len(slim), "records": census}, indent=1), encoding="utf-8")
    (out / "failed_jobs.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    unit = [c for c in census]
    failed = [c for c in census if c["job_conclusion"] == "failure"]
    print(f"runs listed since {args.since}: {len(slim)}; selected: {len(selected)} (truncated={truncated}); unit-lane jobs: {len(unit)}; failed unit-lane jobs: {len(failed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

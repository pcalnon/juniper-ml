#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################################################################################################################################################################
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# File Name:     2026-09-23_d6_advisory_firing_count.py
# Author:        Paul Calnon
# Version:       0.1.0
#
# Date Created:  2026-09-23
# Last Modified: 2026-09-23
#
# License:       MIT License
# Copyright:     Copyright (c) 2024-2026 Paul Calnon
#
# Description:
#    Count the D6 advisory's firings on juniper-cascor CI (owner ruling D6, 2026-09-22: "advisory
#    first -- count how often it fires on real cascor PRs, then decide whether it blocks"; the
#    rulings doc §5, notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md).
#
#    The advisory is cascor's `src/tests/unit/test_candidate_epochs_completed_advisory.py`
#    (cascor#682). On a mismatch it writes a check-run annotation titled
#    "D6 advisory - epochs_completed drift" on each `Unit Tests …` matrix leg.
#
#    WHY WORKFLOW RUNS AND NOT PR COMMITS: a PR's commit list forgets force-pushed heads, and a
#    cascor PR that needs a symbol-loss waiver is force-moved to one commit (cascor#683 was). Every
#    run keeps its head_sha, so enumerating runs sees every tree CI actually tested.
#
#    THE DENOMINATOR IS THE POINT. A firing count without the number of legs that COULD have fired
#    is not a rate. A leg is counted only if its tree contains the advisory file (checked per SHA
#    through the contents API) and the job reached a conclusion.
#
#    Usage:
#        python3 util/ad-hoc/2026-09-23_d6_advisory_firing_count.py [--since 2026-09-23T14:00:00Z] [--json]
#
#    Exit 0 always on a completed count (it is a report, not a gate); 2 on an API failure.
#####################################################################################################################################################################################################
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict

REPO = "pcalnon/juniper-cascor"
ADVISORY_PATH = "src/tests/unit/test_candidate_epochs_completed_advisory.py"
ANNOTATION_TITLE = "D6 advisory - epochs_completed drift"
LEG_PREFIX = "Unit Tests"
# cascor#682 opened 2026-09-23; nothing before it can carry the file.
DEFAULT_SINCE = "2026-09-23T00:00:00Z"
# A leg counts toward the denominator only if its tests RAN. A cancelled run leaves one
# placeholder leg named with the unexpanded matrix ("Python ${{ matrix.python-version }} …")
# whose conclusion is "cancelled"; the first draft of this script counted those as eligible.
RAN = ("success", "failure")
# The ruling counts firings "on real cascor PRs". A deliberate positive control (a throwaway
# `ci-probe/…` branch with the reference drifted, run once through workflow_dispatch) proves
# the emitter reaches the runner, and must never be added to that count.
COUNTED_EVENTS = ("pull_request", "push")
CONTROL_BRANCH_PREFIX = "ci-probe/"


def _is_counted(record: dict) -> bool:
    return record["event"] in COUNTED_EVENTS and not (record["branch"] or "").startswith(CONTROL_BRANCH_PREFIX)


def _gh(path: str) -> object:
    # No `--paginate --slurp`: gh 2.46.0 (this host) has no `--slurp`, and `--paginate` alone
    # concatenates JSON objects into one unparseable stream. Callers page explicitly.
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", path]
    for attempt in range(4):
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return json.loads(proc.stdout) if proc.stdout.strip() else None
        # A transport reset ("connection reset by peer") is transient; an HTTP 4xx is not.
        if "HTTP 4" in proc.stderr or attempt == 3:
            break
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"gh api {path}: {proc.stderr.strip()[:300]}")


def _all_runs(since: str) -> list[dict]:
    runs: list[dict] = []
    page = 1
    while True:
        batch = (_gh(f"repos/{REPO}/actions/runs?created=%3E%3D{since}&per_page=100&page={page}") or {}).get("workflow_runs", [])
        runs.extend(batch)
        if len(batch) < 100:
            return runs
        page += 1


def _tree_has_advisory(sha: str, cache: dict[str, bool]) -> bool:
    if sha not in cache:
        proc = subprocess.run(["gh", "api", f"repos/{REPO}/contents/{ADVISORY_PATH}?ref={sha}", "--jq", ".sha"], capture_output=True, text=True, check=False)
        cache[sha] = proc.returncode == 0
    return cache[sha]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=DEFAULT_SINCE, help="ISO-8601 UTC lower bound on run creation (default: %(default)s)")
    parser.add_argument("--json", action="store_true", help="emit the per-leg records as JSON")
    args = parser.parse_args()

    try:
        runs = _all_runs(args.since)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    has_file: dict[str, bool] = {}
    records = []
    for run in sorted(runs, key=lambda r: r["created_at"]):
        sha = run["head_sha"]
        try:
            jobs = _gh(f"repos/{REPO}/actions/runs/{run['id']}/jobs?per_page=100")
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        legs = [job for job in jobs.get("jobs", []) if job["name"].startswith(LEG_PREFIX)]
        if not legs:
            continue
        in_tree = _tree_has_advisory(sha, has_file)
        prs = ",".join(f"#{pr['number']}" for pr in run.get("pull_requests") or []) or "-"
        for job in legs:
            fired: list[str] = []
            if in_tree and job.get("conclusion") in RAN:
                try:
                    annotations = _gh(f"repos/{REPO}/check-runs/{job['id']}/annotations?per_page=100") or []
                except RuntimeError as exc:
                    print(f"ERROR: {exc}", file=sys.stderr)
                    return 2
                fired = [a.get("message", "") for a in annotations if a.get("title") == ANNOTATION_TITLE or a.get("message", "").startswith(ANNOTATION_TITLE)]
            records.append(
                {
                    "run_id": run["id"],
                    "created_at": run["created_at"],
                    "event": run["event"],
                    "branch": run["head_branch"],
                    "prs": prs,
                    "head_sha": sha,
                    "leg": job["name"],
                    "conclusion": job.get("conclusion"),
                    "advisory_in_tree": in_tree,
                    "eligible": bool(in_tree and job.get("conclusion") in RAN),
                    "firings": len(fired),
                    "messages": fired,
                }
            )
            records[-1]["counted"] = _is_counted(records[-1])

    if args.json:
        print(json.dumps(records, indent=1))
        return 0

    by_sha: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_sha[rec["head_sha"]].append(rec)
    print(f"repo {REPO}, runs created >= {args.since}: {len(runs)} runs, {len(records)} '{LEG_PREFIX}' legs")
    print(f"{'head_sha':<9} {'event':<13} {'prs':<7} {'branch':<44} {'eligible':>8} {'fired':>5}")
    for sha, recs in by_sha.items():
        first = recs[0]
        eligible = sum(r["eligible"] for r in recs)
        fired = sum(r["firings"] > 0 for r in recs)
        print(f"{sha[:8]:<9} {first['event']:<13} {first['prs']:<7} {first['branch'][:44]:<44} {eligible:>8} {fired:>5}")
        for rec in recs:
            for message in rec["messages"]:
                print(f"          {rec['leg']}: {message[:160]}")
    counted = {sha: recs for sha, recs in by_sha.items() if _is_counted(recs[0])}
    controls = {sha: recs for sha, recs in by_sha.items() if not _is_counted(recs[0])}
    eligible_legs = sum(r["eligible"] for recs in counted.values() for r in recs)
    firing_legs = sum(r["firings"] > 0 for recs in counted.values() for r in recs)
    eligible_shas = sum(any(r["eligible"] for r in recs) for recs in counted.values())
    firing_shas = sum(any(r["firings"] for r in recs) for recs in counted.values())
    print()
    print(f"COUNT (pull_request + push, excluding {CONTROL_BRANCH_PREFIX}*): eligible {eligible_shas} head SHAs / {eligible_legs} legs;  fired {firing_shas} SHAs / {firing_legs} legs")
    for sha, recs in controls.items():
        ran = sum(r["eligible"] for r in recs)
        fired = sum(r["firings"] > 0 for r in recs)
        print(f"control (not counted): {sha[:8]} {recs[0]['event']} {recs[0]['branch']}: fired on {fired} of {ran} legs that ran")
    return 0


if __name__ == "__main__":
    sys.exit(main())

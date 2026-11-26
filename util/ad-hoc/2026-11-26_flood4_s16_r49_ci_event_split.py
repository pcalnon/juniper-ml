"""
Split juniper-canopy's ci.yml runs since a date by event and conclusion, and estimate how many unit-lane health-test
executions each event class contributed (from the r49 census listing; no network access).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md
    section 8); flood-4 session 16 builder r49; input from util/ad-hoc/2026-11-26_flood4_s16_r49_ci_census.py

Usage:
    python3 -I <this file> --census-dir <dir holding runs_all.json and health_failures.json>
Prints JSON: runs per (event, branch == main, conclusion), and the health failures per event. A run that did not run
its unit-lane jobs (cancelled, skipped, in progress) is counted under its conclusion, so the split is of runs, not of
test executions; the figures are a lower-resolution check of whether the failures cluster on one event.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--census-dir", required=True)
    args = parser.parse_args()
    root = Path(args.census_dir)
    runs = json.loads((root / "runs_all.json").read_text(encoding="utf-8"))
    health = json.loads((root / "health_failures.json").read_text(encoding="utf-8"))["health_failures"]
    by_event = collections.Counter()
    by_event_concl = collections.Counter()
    for run in runs:
        key = f"{run['event']}|{'main' if run['head_branch'] == 'main' else 'other'}"
        by_event[key] += 1
        by_event_concl[f"{key}|{run['conclusion']}"] += 1
    failures = collections.Counter(f"{h['event']}|{'main' if h['branch'] == 'main' else 'other'}" for h in health)
    completed = {k: sum(v for kk, v in by_event_concl.items() if kk.startswith(k + "|") and kk.split("|")[2] in ("success", "failure")) for k in by_event}
    by_day = collections.defaultdict(collections.Counter)
    for run in runs:
        if run["conclusion"] in ("success", "failure"):
            by_day[run["created_at"][:10]]["main" if run["head_branch"] == "main" else "pr"] += 1
    failure_days = collections.Counter(h["created_at"][:10] for h in health)
    print(json.dumps({"runs_by_event": dict(by_event), "runs_completed_success_or_failure_by_event": completed, "runs_by_event_and_conclusion": dict(sorted(by_event_concl.items())), "health_failures_by_event": dict(failures), "completed_runs_by_day": {d: dict(c) for d, c in sorted(by_day.items())}, "health_failures_by_day": dict(sorted(failure_days.items()))}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

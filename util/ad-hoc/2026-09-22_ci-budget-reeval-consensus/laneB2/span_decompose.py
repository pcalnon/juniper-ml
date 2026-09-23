#!/usr/bin/env python3
"""
Lane B2 (argue HOLD) probe for the ml#2017 consensus round: is "within-span queueing" SHOWN?

Project: juniper-ml
Sub-Project: ad-hoc tooling (consensus round, lane B2)
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc -- investigation, read-only (GitHub REST reads only; writes nothing anywhere)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

For one head of a PR, lists every GitHub Actions job attached to it (all workflow runs on the
head SHA, all attempts) and splits the required-context span [S, E] second by second into:
  RUNNING  -- at least one job on the head is executing on a runner
  QUEUED   -- no job executing, at least one created-but-not-started (waiting for a runner)
  IDLE     -- neither (a gap between waves / needs: hand-off / nothing scheduled)
and prints each job's queue delay (started_at - created_at). If the long span is mostly RUNNING
with second-scale queue delays, "stretched by within-span queueing" is NOT shown.

Usage:
    python3 .../laneB2/span_decompose.py juniper-data 405
"""

from __future__ import annotations

import json
import subprocess  # nosec B404 -- fixed-argv gh reads
import sys
from datetime import datetime

OWNER = "pcalnon"


def gh(path: str):
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, check=False)  # nosec B603
    if proc.returncode != 0:
        raise SystemExit(f"gh api {path} -> exit {proc.returncode}: {proc.stderr.strip()[-300:]}")
    return json.loads(proc.stdout or "null")


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def required_contexts(slug: str) -> set[str]:
    out: set[str] = set()
    for entry in gh(f"repos/{slug}/rulesets") or []:
        detail = gh(f"repos/{slug}/rulesets/{entry['id']}")
        for rule in detail.get("rules") or []:
            if rule.get("type") == "required_status_checks":
                for c in (rule.get("parameters") or {}).get("required_status_checks") or []:
                    out.add(c["context"])
    return out


def main() -> int:
    repo, number = sys.argv[1], int(sys.argv[2])
    slug = f"{OWNER}/{repo}"
    pr = gh(f"repos/{slug}/pulls/{number}")
    sha = pr["head"]["sha"]
    required = required_contexts(slug)
    crs = gh(f"repos/{slug}/commits/{sha}/check-runs?filter=all&per_page=100")["check_runs"]
    req_runs = [c for c in crs if c["name"] in required]
    counts: dict = {}
    for c in req_runs:
        counts.setdefault(c["name"], []).append((c["started_at"], c["completed_at"], c["conclusion"]))
    starts = [ts(c["started_at"]) for c in req_runs if c["started_at"]]
    ends = [ts(c["completed_at"]) for c in req_runs if c["completed_at"]]
    S, E = min(starts), max(ends)
    span = (E - S).total_seconds()
    print(f"{repo}#{number} head {sha[:8]} created {pr['created_at']} merged {pr['merged_at']}")
    print(f"  required contexts: {len(required)}; required check-runs on head (filter=all): {len(req_runs)}")
    multi = {k: v for k, v in counts.items() if len(v) > 1}
    print(f"  required contexts with >1 check-run: {len(multi)}")
    for k, v in multi.items():
        print(f"    {k}: {v}")
    print(f"  span S={S.isoformat()} E={E.isoformat()} = {span:.0f} s")

    runs = gh(f"repos/{slug}/actions/runs?head_sha={sha}&per_page=100")["workflow_runs"]
    jobs = []
    for r in runs:
        for j in gh(f"repos/{slug}/actions/runs/{r['id']}/jobs?filter=all&per_page=100")["jobs"]:
            jobs.append((r["name"], r["event"], j))
    print(f"  workflow runs on head: {len(runs)} ({sorted({(r['name'], r['event'], r['run_attempt']) for r in runs})})")
    print(f"  jobs on head (all attempts): {len(jobs)}")

    secs = int(span)
    state = []
    for t in range(secs):
        now = S.timestamp() + t + 0.5
        running = queued = False
        for _wf, _ev, j in jobs:
            c, s, e = ts(j["created_at"]), ts(j["started_at"]), ts(j["completed_at"])
            if s and e and s.timestamp() <= now < e.timestamp() and (e - s).total_seconds() > 0:
                running = True
                break
            if c and s and c.timestamp() <= now < s.timestamp():
                queued = True
        state.append("R" if running else ("Q" if queued else "I"))
    print(f"  span split: RUNNING {state.count('R')} s / QUEUED-only {state.count('Q')} s / IDLE {state.count('I')} s")

    rows = []
    for wf, _ev, j in jobs:
        c, s, e = ts(j["created_at"]), ts(j["started_at"]), ts(j["completed_at"])
        q = (s - c).total_seconds() if (c and s) else None
        d = (e - s).total_seconds() if (s and e) else None
        rows.append((s or c, wf, j["name"], j.get("run_attempt"), j.get("conclusion"), q, d, j["name"] in required))
    rows.sort(key=lambda r: r[0])
    qs = [r[5] for r in rows if r[5] is not None]
    print(f"  queue delay per job: max {max(qs):.0f} s, sum {sum(qs):.0f} s, jobs queued >60 s: {sum(1 for q in qs if q > 60)}")
    print("  start(UTC)            queue_s  run_s  req  attempt conclusion  workflow / job")
    for st, wf, name, att, concl, q, d, req in rows:
        print(f"  {st.strftime('%m-%d %H:%M:%S') if st else '-':<20} {q if q is None else round(q):>7} {d if d is None else round(d):>6}  {'Y' if req else ' ':<4} {att!s:<7} {concl!s:<11} {wf} / {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

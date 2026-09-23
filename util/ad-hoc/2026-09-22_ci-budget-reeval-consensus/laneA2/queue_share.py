#!/usr/bin/env python3
"""Lane A2 helper: how much of a head's required-check span is runner QUEUE vs EXECUTION?

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc consensus-round tooling (Lane A2, CI-budget re-evaluation)
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-22
Status:      ad-hoc -- single-use helper for the 2026-09-22 CI-budget consensus round

Walks the critical chain back from the last-completing required job, using the Actions jobs
API (job.created_at = when the job became runnable, i.e. its `needs:` were met; job.started_at
= when a runner picked it up). The predecessor of a job is the job in the same workflow run
whose completion is the latest at or before the job's creation (+2 s tolerance). Reports, over
the chain and clipped to the span window [first required start, last required completion]:
queue = sum(started - created), exec = sum(completed - started), and the remainder.

Usage: python3 queue_share.py juniper-data:405 juniper-data-client:206 juniper-deploy:211
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import span_all_attempts as S  # noqa: E402


def main() -> int:
    for spec in sys.argv[1:]:
        repo, prn = spec.split(":")
        prn = int(prn)
        req = S.required_contexts(repo, offline=True)
        union = req["union"]
        smp = S.sample(repo, offline=True) or []
        pr = next(p for p in smp if p["number"] == prn)
        hd = S.head_data(repo, pr["headRefOid"], union, offline=True)
        jobs = []
        for r in hd["runs"]:
            js = S.rest_paged(f"repos/{S.OWNER}/{repo}/actions/runs/{r['id']}/jobs?filter=all", "jobs", S._trim_job, offline=True)
            if isinstance(js, list):
                jobs.extend(js)
        c = S.classify(S.executions(repo, hd, union))
        t0, t1 = c["first_pass_start"], c["first_pass_end"]
        req_jobs = [j for j in jobs if j["name"] in union and j.get("completed_at") and j.get("started_at")]
        last = max(req_jobs, key=lambda j: S.ts(j["completed_at"]))
        chain = [last]
        cur = last
        while True:
            created = S.ts(cur["created_at"])
            cands = [j for j in jobs if j["run_id"] == cur["run_id"] and j is not cur and j.get("completed_at") and S.ts(j["completed_at"]) <= created + 2]
            if not cands:
                break
            pred = max(cands, key=lambda j: S.ts(j["completed_at"]))
            if created - S.ts(pred["completed_at"]) > 5:  # no job finished just before this one was created: chain start
                break
            chain.append(pred)
            cur = pred
        chain.reverse()
        q = e = 0.0
        for j in chain:
            cr, st, co = S.ts(j["created_at"]), S.ts(j["started_at"]), S.ts(j["completed_at"])
            q += max(0.0, st - max(cr, t0))
            e += co - max(st, t0)
        span = t1 - t0
        print(f"{repo}#{prn}: span {span:.0f}s  chain: " + " -> ".join(f"{j['name']}[q{S.ts(j['started_at']) - S.ts(j['created_at']):.0f} x{S.ts(j['completed_at']) - S.ts(j['started_at']):.0f}]" for j in chain))
        print(f"    within-span queue {q:.0f}s ({100 * q / span:.0f}%), execution {e:.0f}s ({100 * e / span:.0f}%), other {span - q - e:.0f}s; window {S.hms(t0)}Z -> {S.hms(t1)}Z")
    return 0


if __name__ == "__main__":
    sys.exit(main())

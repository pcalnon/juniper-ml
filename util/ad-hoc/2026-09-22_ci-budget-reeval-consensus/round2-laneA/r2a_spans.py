#!/usr/bin/env python3
"""
Round-2 Lane A: an independent first-pass span instrument (GraphQL check suites, not REST
check-runs?filter=all as the reprobe, nor the Actions jobs API as round-1 lane A2).

Definition re-implemented from the claim (not from the reprobe's code):
  * required contexts = REST rules/branches/<default> `required_status_checks` (a different
    entry point from v2's ruleset listing);
  * sample = last N MERGED PRs by CREATION order (GraphQL orderBy CREATED_AT DESC);
  * per head: every check-run on every check suite (checkType ALL) plus legacy statuses;
    exact copies (same name/started/completed/conclusion) collapsed; FIRST execution per
    required context = earliest startedAt;
  * healthy = every first execution SUCCESS/SKIPPED/NEUTRAL; span = max(completed)-min(started);
  * p90 = sorted[int(0.9*(n-1))].
Also prints the per-suite LATEST span (what v2's filter=latest reads) and the all-executions span.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc -- consensus round 2, Lane A
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r2a_common import budget_line, gql, rest, ts  # noqa: E402

PASSED = {"SUCCESS", "SKIPPED", "NEUTRAL", "success", "skipped", "neutral"}


def required(repo: str) -> set:
    meta = rest(f"repos/pcalnon/{repo}")
    rules = rest(f"repos/pcalnon/{repo}/rules/branches/{meta['default_branch']}")
    out = set()
    for r in rules:
        if r.get("type") == "required_status_checks":
            for c in (r.get("parameters") or {}).get("required_status_checks") or []:
                out.add(c["context"])
    return out


def merged_prs(repo: str, n: int) -> list:
    q = f'query {{ repository(owner: "pcalnon", name: "{repo}") {{ pullRequests(states: MERGED, first: {n}, orderBy: {{field: CREATED_AT, direction: DESC}}) {{ nodes {{ number createdAt mergedAt headRefOid }} }} }} }}'
    return gql(q)["repository"]["pullRequests"]["nodes"]


def head_checks(repo: str, oids: list, batch: int = 4) -> dict:
    out = {}
    for i in range(0, len(oids), batch):
        parts = []
        for j, o in enumerate(oids[i : i + batch]):
            parts.append(
                f'c{j}: object(oid: "{o}") {{ ... on Commit {{ status {{ contexts {{ context state createdAt }} }} '
                f"checkSuites(first: 50) {{ totalCount nodes {{ app {{ slug }} workflowRun {{ databaseId event createdAt workflow {{ name }} }} "
                f"checkRuns(first: 100, filterBy: {{checkType: ALL}}) {{ totalCount nodes {{ databaseId name status conclusion startedAt completedAt }} }} "
                f"latest: checkRuns(first: 100, filterBy: {{checkType: LATEST}}) {{ nodes {{ databaseId }} }} }} }} }} }}"
            )
        data = gql(f'query {{ repository(owner: "pcalnon", name: "{repo}") {{ ' + " ".join(parts) + " } }")["repository"]
        for j, o in enumerate(oids[i : i + batch]):
            out[o] = data.get(f"c{j}")
    return out


def first_pass(execs: list) -> list:
    seen, dedup = set(), []
    for e in execs:
        k = (e["name"], e["started"], e["completed"], e["conclusion"])
        if k not in seen:
            seen.add(k)
            dedup.append(e)
    best = {}
    for e in dedup:
        if not e["started"]:
            continue
        cur = best.get(e["name"])
        if cur is None or (e["started"], e["completed"] or e["started"]) < (cur["started"], cur["completed"] or cur["started"]):
            best[e["name"]] = e
    return list(best.values())


def span(execs: list):
    st = [ts(e["started"]) for e in execs if e["started"]]
    en = [ts(e["completed"]) for e in execs if e["completed"]]
    return (max(en) - min(st)).total_seconds() if st and en else None


def p90(v: list):
    return v[int(0.9 * (len(v) - 1))]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("-n", type=int, default=30)
    ap.add_argument("--fetch", type=int, default=0, help="fetch this many heads (>= n) to allow window shifts")
    ap.add_argument("--json")
    ap.add_argument("--merged-before", default=None, help="ISO time: drop PRs merged after it (reconstruct a past window)")
    a = ap.parse_args()
    req = required(a.repo)
    prs = merged_prs(a.repo, max(a.n, a.fetch) + 12)
    if a.merged_before:
        dropped = [p["number"] for p in prs if p["mergedAt"] > a.merged_before]
        prs = [p for p in prs if p["mergedAt"] <= a.merged_before]
        print(f"   dropped (merged after {a.merged_before}): {dropped}")
    prs = prs[: max(a.n, a.fetch)]
    checks = head_checks(a.repo, [p["headRefOid"] for p in prs])
    rows = []
    for p in prs:
        node = checks.get(p["headRefOid"]) or {}
        suites = (node.get("checkSuites") or {}).get("nodes", [])
        if (node.get("checkSuites") or {}).get("totalCount", 0) > 50:
            print(f"WARNING #{p['number']}: >50 suites")
        allx, latest = [], []
        for s in suites:
            if s["checkRuns"]["totalCount"] > 100:
                print(f"WARNING #{p['number']}: suite with >100 check runs")
            lat_ids = {x["databaseId"] for x in s["latest"]["nodes"]}
            for c in s["checkRuns"]["nodes"]:
                if c["name"] in req:
                    e = {"name": c["name"], "started": c["startedAt"], "completed": c["completedAt"], "conclusion": c["conclusion"], "id": c["databaseId"], "run": (s.get("workflowRun") or {}).get("databaseId")}
                    allx.append(e)
                    if c["databaseId"] in lat_ids:
                        latest.append(e)
        have = {e["name"] for e in allx}
        for sc in ((node.get("status") or {}).get("contexts") or []):
            if sc["context"] in req and sc["context"] not in have:
                allx.append({"name": sc["context"], "started": sc["createdAt"], "completed": sc["createdAt"], "conclusion": sc["state"], "id": None, "run": None})
        fp = first_pass(allx)
        bad = sorted(f"{e['name']}={e['conclusion']}" for e in fp if (e["conclusion"] or "") not in PASSED)
        names = [e["name"] for e in allx]
        repeats = sorted({x for x in names if names.count(x) > 1})
        fs = min((e["started"] for e in fp if e["started"]), default=None)
        fe = max((e["completed"] for e in fp if e["completed"]), default=None)
        rows.append({"pr": p["number"], "merged": p["mergedAt"], "head": p["headRefOid"][:8], "healthy": not bad, "bad": bad, "first": span(fp), "first_start": fs, "first_end": fe, "latest": span(latest), "all": span(allx), "ctx": len(fp), "req": len(req), "repeats": repeats, "runs": sorted({e["run"] for e in fp if e["run"]})})
    sample = rows[: a.n]
    healthy = sorted([r for r in sample if r["healthy"] and r["first"] is not None], key=lambda r: r["first"])
    vals = [round(r["first"]) for r in healthy]
    print(f"{a.repo}: required contexts {len(req)}; sample #{sample[-1]['pr']}..#{sample[0]['pr']} (n={len(sample)}); healthy {len(healthy)}; unhealthy {[r['pr'] for r in sample if not r['healthy']]}")
    print(f"   first-pass healthy p90={p90(vals)} max={vals[-1]} (#{healthy[-1]['pr']})   sorted tail={vals[-5:]}")
    lat = sorted(round(r["latest"]) for r in sample if r["latest"] is not None)
    print(f"   raw per-suite LATEST over all {len(lat)} heads: p90={p90(lat)} max={lat[-1]}")
    for r in sample:
        if not r["healthy"]:
            print(f"   unhealthy #{r['pr']}: first={round(r['first'] or 0)} latest={round(r['latest'] or 0)} all={round(r['all'] or 0)} bad={r['bad'][:5]}")
    for r in sorted(sample, key=lambda r: -(r["first"] or 0))[:4]:
        print(f"   top #{r['pr']} merged {r['merged']} first={round(r['first'])} latest={round(r['latest'] or 0)} all={round(r['all'] or 0)} ctx={r['ctx']}/{r['req']} repeats={r['repeats'][:4]} runs={r['runs'][:6]}")
    if a.fetch > a.n:
        print("   sliding windows (drop newest k):")
        for k in range(0, a.fetch - a.n + 1):
            w = rows[k : k + a.n]
            h = sorted(round(r["first"]) for r in w if r["healthy"] and r["first"] is not None)
            print(f"      window #{w[-1]['pr']}..#{w[0]['pr']}: healthy {len(h)} p90={p90(h)} max={h[-1]}")
    print(budget_line())
    if a.json:
        Path(a.json).write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

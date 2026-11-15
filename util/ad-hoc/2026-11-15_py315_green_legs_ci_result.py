#!/usr/bin/env python3
"""Collect a PR's CI result for the green-informational-3.15-legs rollout (read-only; only ``gh`` reads).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (the "CI result" of juniper-data-client#262, juniper-cascor-client#197 and
        juniper-deploy#275)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_py315_pr_ci_result.py (phase 1's collector, which this extends);
         tmp/py315/GREEN_LEGS_BRIEF.md step 6 (what to verify on the PR's own run)

Why this exists
---------------
The green-legs brief's acceptance is read on the PR's own run: every required context posts and passes under its
old name, every 3.15 check concludes ``success``, its annotations carry the ``Python 3.15 (informational)`` warning
or notice, and the PR has no failing check at all. This prints, for the PR's CURRENT head (after an update-branch,
that is the merge commit): every check run, flagging any whose conclusion is not success / skipped / neutral; every
required context with its conclusion; every "3.15" check with its step conclusions and annotations; legacy commit
statuses; the Quality Gate's log lines; each workflow run's conclusion; mergeStateStatus; and the review threads.

Usage
-----
    python3 util/ad-hoc/2026-11-15_py315_green_legs_ci_result.py <bare-repo> <pr-number>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

OK = ("success", "skipped", "neutral")


def gh(*args: str) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def gh_json(*args: str):
    return json.loads(gh(*args))


def main(repo: str, pr: str) -> int:
    full = f"pcalnon/{repo}"
    info = gh_json("pr", "view", pr, "--repo", full, "--json", "headRefOid,mergeStateStatus,mergeable,state,url,baseRefName")
    sha = info["headRefOid"]
    print(f"PR {info['url']}  head={sha}  base={info['baseRefName']}  state={info['state']}  mergeStateStatus={info['mergeStateStatus']}  mergeable={info['mergeable']}")
    rules = gh_json("api", f"repos/{full}/rules/branches/main")
    required = [c["context"] for r in rules if r["type"] == "required_status_checks" for c in r["parameters"]["required_status_checks"]]
    runs: list[dict] = []
    page = 1
    while True:
        data = gh_json("api", f"repos/{full}/commits/{sha}/check-runs?per_page=100&page={page}")
        runs.extend(data["check_runs"])
        if len(data["check_runs"]) < 100:
            break
        page += 1
    latest: dict[str, dict] = {}
    for r in runs:
        if r["name"] not in latest or (r.get("started_at") or "") > (latest[r["name"]].get("started_at") or ""):
            latest[r["name"]] = r
    print(f"\n== all check runs on head ({len(runs)} runs, {len(latest)} names) ==")
    pending = [n for n, r in latest.items() if r["status"] != "completed"]
    bad = [n for n, r in latest.items() if r["status"] == "completed" and r["conclusion"] not in OK]
    tally: dict[str, int] = {}
    for r in latest.values():
        key = r["conclusion"] if r["status"] == "completed" else r["status"]
        tally[key] = tally.get(key, 0) + 1
    print(f"  tally: {tally}")
    print(f"  NOT OK (failing): {bad or 'none'}")
    print(f"  still running: {pending or 'none'}")
    print(f"\n== required contexts ({len(required)}) ==")
    for ctx in required:
        r = latest.get(ctx)
        print(f"  {'NOT POSTED' if r is None else r['status'] + ' ' + str(r['conclusion']):<22} {ctx}")
    print(f"  -> not posted: {[c for c in required if c not in latest] or 'none'}; not success: {[c for c in required if c in latest and latest[c]['conclusion'] != 'success'] or 'none'}")
    print("\n== 3.15 checks ==")
    for name in sorted(n for n in latest if "3.15" in n):
        r = latest[name]
        print(f"  {r['status']} {r['conclusion']}  {name}  (check run {r['id']})  required={name in required}")
        job = gh_json("api", f"repos/{full}/actions/jobs/{r['id']}")
        for s in job.get("steps", []):
            print(f"      step {s['number']:>2} {str(s.get('conclusion')):<9} {s['name']}")
        for a in gh_json("api", f"repos/{full}/check-runs/{r['id']}/annotations"):
            print(f"      annotation {a['annotation_level']}: {a.get('title') or ''} :: {a['message']}")
    st = gh_json("api", f"repos/{full}/commits/{sha}/status")
    print(f"\n== legacy commit statuses: combined={st['state']} ({len(st['statuses'])}) ==")
    for s in st["statuses"]:
        print(f"  {s['state']:<8} {s['context']}")
    print("\n== Quality Gate log ==")
    qg = latest.get("Quality Gate")
    if qg and qg["status"] == "completed":
        log = gh("api", f"repos/{full}/actions/jobs/{qg['id']}/logs")
        for ln in log.splitlines():
            ln = re.sub(r"^\S+Z ", "", ln)
            if re.search(r"^\s*(Unit Tests|Integration Tests|Pre-commit|Build|Security|Documentation|Docs|Compose|SOPS|Gitleaks|Memory|Published|Tests)\b.*:\s", ln) or ("Quality Gate" in ln and ("PASS" in ln or "FAIL" in ln)):
                print(f"  (job {qg['id']}) {ln.strip()}")
    else:
        print(f"  not completed: {qg['status'] if qg else 'not posted'}")
    print("\n== workflow runs on head ==")
    for w in gh_json("api", f"repos/{full}/actions/runs?head_sha={sha}&per_page=100")["workflow_runs"]:
        print(f"  {w['status']:<11} {str(w['conclusion']):<9} {w['name']}  (run {w['id']}, {w['event']})")
    owner, name = full.split("/")
    q = "query($o:String!,$n:String!,$p:Int!){repository(owner:$o,name:$n){pullRequest(number:$p){reviewThreads(first:50){nodes{isResolved comments(first:1){nodes{author{login} path body}}}}}}}"
    threads = gh_json("api", "graphql", "-f", f"query={q}", "-f", f"o={owner}", "-f", f"n={name}", "-F", f"p={pr}")
    nodes = threads["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    print(f"\n== review threads: {len(nodes)} ({sum(1 for t in nodes if not t['isResolved'])} unresolved) ==")
    for t in nodes:
        c = t["comments"]["nodes"][0] if t["comments"]["nodes"] else {}
        print(f"  resolved={t['isResolved']} author={(c.get('author') or {}).get('login')} path={c.get('path')}\n    {(c.get('body') or '')[:600]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

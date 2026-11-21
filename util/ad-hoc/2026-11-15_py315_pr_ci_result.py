#!/usr/bin/env python3
"""Collect a PR's CI result for the Python 3.15 informational-leg rollout (read-only; only ``gh`` reads).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (the "CI result" of juniper-cascor#759 and juniper-cascor-worker#228)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/py315/ROLLOUT_BRIEF.md (the rollout brief, whose "After opening the PR" step lists what to record)

Prints: every required context (from the branch ruleset) with its check-run conclusion on the PR head; every check run
whose name contains "3.15" with its conclusion and, if it failed, its first failing step plus the pytest summary /
error lines from its log; the Quality Gate log lines; each workflow run's conclusion on the head; mergeStateStatus.

Usage: ci_result.py <bare-repo> <pr-number>
"""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404
import sys


def gh(*args: str) -> str:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)  # nosec B603 B607
    if proc.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def gh_json(*args: str):
    return json.loads(gh(*args))


def main(repo: str, pr: str) -> int:
    full = f"pcalnon/{repo}"
    info = gh_json("pr", "view", pr, "--repo", full, "--json", "headRefOid,mergeStateStatus,mergeable,state,url")
    sha = info["headRefOid"]
    print(f"PR {info['url']}  head={sha}  state={info['state']}  mergeStateStatus={info['mergeStateStatus']}  mergeable={info['mergeable']}")
    rules = gh_json("api", f"repos/{full}/rules/branches/main")
    required = [c["context"] for r in rules if r["type"] == "required_status_checks" for c in r["parameters"]["required_status_checks"]]
    runs = []
    page = 1
    while True:
        data = gh_json("api", f"repos/{full}/commits/{sha}/check-runs?per_page=100&page={page}")
        runs.extend(data["check_runs"])
        if len(data["check_runs"]) < 100:
            break
        page += 1
    by_name: dict[str, list[dict]] = {}
    for r in runs:
        by_name.setdefault(r["name"], []).append(r)
    print(f"\n== required contexts ({len(required)}) ==")
    missing = 0
    for ctx in required:
        rs = by_name.get(ctx, [])
        if not rs:
            print(f"  NOT POSTED  {ctx}")
            missing += 1
            continue
        latest = max(rs, key=lambda r: r.get("started_at") or "")
        print(f"  {latest['status']:<11} {str(latest['conclusion']):<9} {ctx}")
    print(f"  -> not posted: {missing}")
    print("\n== 3.15 legs ==")
    wr_all = gh_json("api", f"repos/{full}/actions/runs?head_sha={sha}&per_page=100")["workflow_runs"]
    suite_to_wf = {w["check_suite_id"]: f"{w['name']} (run {w['id']})" for w in wr_all}
    for r in sorted((x for x in runs if "3.15" in x["name"]), key=lambda x: x["name"]):
        name = r["name"]
        wf = suite_to_wf.get((r.get("check_suite") or {}).get("id"), "?")
        print(f"  {r['status']:<11} {str(r['conclusion']):<9} {name}  [{wf}]  (job {r['id']})  required={name in required}")
        if r["conclusion"] == "failure":
            job = gh_json("api", f"repos/{full}/actions/jobs/{r['id']}")
            failed = [s for s in job.get("steps", []) if s.get("conclusion") == "failure"]
            print(f"      first failing step: {failed[0]['name'] if failed else '(none recorded)'}")
            log = gh("api", f"repos/{full}/actions/jobs/{r['id']}/logs")
            pat = re.compile(r"(=+ .*(passed|failed|error).* =+$|^E\s{2,}\S|ERROR:|Error:|error:|No matching distribution|Could not find a version|ModuleNotFoundError|Process completed with exit code)")
            hits = [re.sub(r"^\S+Z ", "", ln) for ln in log.splitlines() if pat.search(re.sub(r"^\S+Z ", "", ln))]
            for ln in hits[-12:]:
                print(f"      | {ln[:220]}")
    print("\n== Quality Gate log ==")
    for r in by_name.get("Quality Gate", []):
        if r["status"] != "completed":
            print(f"  (job {r['id']}) not completed yet: {r['status']}")
            continue
        log = gh("api", f"repos/{full}/actions/jobs/{r['id']}/logs")
        for ln in log.splitlines():
            ln = re.sub(r"^\S+Z ", "", ln)
            if re.match(r"^(Pre-commit|Unit Tests|Integration Tests|Quick Integration|Full Integration Tests|Build|Dependency Docs|Security|Documentation|Lockfile Check|Docker Build):\s", ln) or "Quality Gate" in ln and ("PASSED" in ln or "error" in ln.lower()):
                print(f"  (job {r['id']}) {ln}")
    print("\n== workflow runs on head ==")
    wr = gh_json("api", f"repos/{full}/actions/runs?head_sha={sha}&per_page=100")
    for w in wr["workflow_runs"]:
        print(f"  {w['status']:<11} {str(w['conclusion']):<9} {w['name']}  (run {w['id']}, {w['event']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

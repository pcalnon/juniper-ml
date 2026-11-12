#!/usr/bin/env python3
"""
Re-probe, with GitHub GETs only, the facts the round-4 M-1 carrier's PR body, commit body and CHANGELOG cite.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round-4 validation of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
A validator re-probes rather than re-reads. Every call here is a GET (gh api / gh issue list); nothing is written to
GitHub. Job logs are grepped for the one line each claim quotes; no log is printed whole.

Usage:
    python3 <this> --out <scratch dir>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: gh api GETs
import sys
from pathlib import Path

ACTION_SHA = "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e"


def gh(*args: str) -> tuple[int, str]:
    res = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)  # nosec B603 B607
    return res.returncode, res.stdout if res.returncode == 0 else res.stderr[:400]


def raw(path: str) -> str:
    out = gh("api", "-H", "Accept: application/vnd.github.raw", path)[1]
    return out if rc == 0 else f"ERROR {out}"


def grep_lines(text: str, pattern: str, limit: int = 6) -> list[str]:
    rx = re.compile(pattern)
    return [ln[:240] for ln in text.splitlines() if rx.search(ln)][:limit]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    facts: dict = {}
    out = gh("api", "repos/pcalnon/juniper-ml/pulls/2530", "--jq", "{merged: .merged, merged_at: .merged_at, sha: .merge_commit_sha}")[1]
    facts["ml2530"] = out.strip()
    out = gh("api", "repos/pcalnon/juniper-ml/contents/notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md?ref=main", "--jq", ".sha")[1]
    facts["record_on_ml_main_blob"] = out.strip()
    src = raw(f"repos/gitleaks/gitleaks-action/contents/src/gitleaks.js?ref={ACTION_SHA}")
    lines = src.splitlines()
    facts["gitleaks_js_113_117"] = lines[112:117]
    facts["gitleaks_js_160_172"] = lines[159:172]
    idx = raw(f"repos/gitleaks/gitleaks-action/contents/src/index.js?ref={ACTION_SHA}").splitlines()
    facts["index_js_196_204"] = idx[195:204]
    dist = raw(f"repos/gitleaks/gitleaks-action/contents/dist/index.js?ref={ACTION_SHA}")
    dl = dist.splitlines()
    facts["dist_paginate_lines"] = [(i + 1, ln.strip()[:160]) for i, ln in enumerate(dl) if "paginate(" in ln][:12]
    facts["dist_line_48470"] = dl[48469][:200] if len(dl) >= 48470 else "short"
    out = gh("api", f"repos/gitleaks/gitleaks-action/contents/dist/index.js?ref={ACTION_SHA}", "--jq", ".sha")[1]
    facts["dist_blob_sha"] = out.strip()
    jobs = {
        "jd_370_job_101319597180": ("pcalnon/juniper-data", "101319597180", r"commits scanned|--log-opts"),
        "ml_1797_job_101397489117": ("pcalnon/juniper-ml", "101397489117", r"commits scanned|--log-opts"),
        "jd_schedule_job_128648737468": ("pcalnon/juniper-data", "128648737468", r"commits scanned|no leaks found|leaks found"),
        "jd_push_job_128580840934": ("pcalnon/juniper-data", "128580840934", r"commits scanned|--log-opts"),
        "jd_dispatch_job_123788238937": ("pcalnon/juniper-data", "123788238937", r"commits scanned"),
        "jd_pr_job_128582358732": ("pcalnon/juniper-data", "128582358732", r"git version|Image: |Version: 2026"),
    }
    for name, (repo, job, pat) in jobs.items():
        meta = gh("api", f"repos/{repo}/actions/jobs/{job}", "--jq", "{conclusion: .conclusion, run_id: .run_id, name: .name, started: .started_at}")[1]
        log = raw(f"repos/{repo}/actions/jobs/{job}/logs")
        facts[name] = {"meta": meta.strip(), "lines": grep_lines(log, pat)}
    out = gh("api", "repos/pcalnon/juniper-ml/pulls/1797", "--jq", "{commits: .commits, head: .head.sha[0:8]}")[1]
    facts["ml1797"] = out.strip()
    out = gh("api", "repos/pcalnon/juniper-ml/compare/d1deaae2...973d9b7a", "--jq", "{ahead_by: .ahead_by, behind_by: .behind_by}")[1]
    facts["ml_compare_d1deaae2_973d9b7a"] = out.strip()
    out = gh("api", "repos/pcalnon/juniper-data/pulls/370", "--jq", "{commits: .commits, merged_at: .merged_at, merge_commit_sha: .merge_commit_sha[0:8]}")[1]
    facts["jd370"] = out.strip()
    out = gh("issue", "list", "-R", "pcalnon/juniper-data", "--state", "all", "--search", "force-push gitleaks", "--json", "number,title")[1]
    facts["jd_issue_force_push"] = out.strip()
    out = gh("issue", "list", "-R", "pcalnon/juniper-data", "--state", "all", "--search", "gitleaks in:title", "--json", "number,title,createdAt", "--limit", "10")[1]
    facts["jd_issue_gitleaks_titles"] = out.strip()
    (args.out / "logs").mkdir(parents=True, exist_ok=True)
    (args.out / "logs" / "gh_facts.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

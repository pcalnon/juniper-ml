#!/usr/bin/env python3
"""
Re-probe CodeQL for the juniper-canopy flood-4 test drafts: did CodeQL analyze them, and does canopy ever flag pytestmark?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; util/ad-hoc/2026-10-05_codeql_python_prescreen.py

Read-only `gh api` GETs. For each draft: its head's CodeQL check runs, the code-scanning ANALYSES on
refs/pull/<N>/merge (proof that CodeQL looked, and with which config), the alerts on that ref, and the PR's
review comments. Then canopy's whole alert history (every state) filtered to unused-global rules, and the
CodeQL workflow's query configuration as it is on main.

    python3 2026-11-07_flood4_val_canopy_codeql_probe.py <canopy worktree at main> > <log>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = "pcalnon/juniper-canopy"
DRAFTS = {"789": "87b45f787386b3fdf9c77cd95cc5b814a2c85fa6", "792": "1006ccd8aa52c7075bad48c2786d091bac1cd854", "794": "572e252b6f75abdcfe68d2025f87452ba492d6f0", "795": "d512cce82707bc84ca323f0635394552432a9a18"}


def api(path: str, paginate: bool = False):
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json", path]
    if paginate:
        cmd.insert(2, "--paginate")
    out = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if out.returncode != 0:
        return {"error": (out.stderr or out.stdout).strip()[:400]}
    text = out.stdout.strip()
    if paginate and text.startswith("[") and "][" in text:
        text = "[" + text[1:-1].replace("][", ",") + "]"
    try:
        return json.loads(text) if text else []
    except json.JSONDecodeError as exc:
        return {"error": f"json: {exc}"}


def main() -> int:
    worktree = Path(sys.argv[1])
    for pr, head in DRAFTS.items():
        print(f"\n=== #{pr} head {head}")
        runs = api(f"repos/{REPO}/commits/{head}/check-runs?per_page=100")
        if isinstance(runs, dict) and "check_runs" in runs:
            for run in runs["check_runs"]:
                name = run.get("name", "")
                if "codeql" in name.lower() or "analyze" in name.lower() or (run.get("app") or {}).get("slug") == "github-advanced-security":
                    out = run.get("output") or {}
                    print(f"    check-run: {name!r} app={(run.get('app') or {}).get('slug')} status={run.get('status')} conclusion={run.get('conclusion')} title={out.get('title')!r} annotations={out.get('annotations_count')}")
        else:
            print(f"    check-runs: {runs}")
        for ref in (f"refs/pull/{pr}/merge", f"refs/pull/{pr}/head"):
            analyses = api(f"repos/{REPO}/code-scanning/analyses?ref={ref}&per_page=20")
            if isinstance(analyses, list):
                for row in analyses[:6]:
                    print(f"    analysis {ref}: tool={row.get('tool', {}).get('name')} category={row.get('category')!r} commit={row.get('commit_sha', '')[:10]} created={row.get('created_at')} results={row.get('results_count')} rules={row.get('rules_count')} error={row.get('error')!r}")
                if not analyses:
                    print(f"    analysis {ref}: (none)")
            else:
                print(f"    analyses {ref}: {analyses}")
            alerts = api(f"repos/{REPO}/code-scanning/alerts?ref={ref}&per_page=100")
            if isinstance(alerts, list):
                print(f"    alerts on {ref}: {len(alerts)}")
                for alert in alerts:
                    loc = (alert.get("most_recent_instance") or {}).get("location") or {}
                    print(f"        #{alert.get('number')} {alert.get('rule', {}).get('id')} {alert.get('state')} {loc.get('path')}:{loc.get('start_line')}")
            else:
                print(f"    alerts on {ref}: {alerts}")
        comments = api(f"repos/{REPO}/pulls/{pr}/comments?per_page=100")
        if isinstance(comments, list):
            print(f"    review comments: {len(comments)} " + ", ".join(f"{c.get('user', {}).get('login')}:{c.get('path')}" for c in comments))
        else:
            print(f"    review comments: {comments}")
    print("\n=== canopy alert history, every state, rules matching 'unused'")
    alerts = api(f"repos/{REPO}/code-scanning/alerts?per_page=100", paginate=True)
    if isinstance(alerts, list):
        rules: dict[str, int] = {}
        for alert in alerts:
            rid = alert.get("rule", {}).get("id", "")
            rules[rid] = rules.get(rid, 0) + 1
        print(f"    total alerts listed: {len(alerts)}; rule ids: {json.dumps(rules, sort_keys=True)}")
        for alert in alerts:
            rid = alert.get("rule", {}).get("id", "")
            if "unused" in rid:
                inst = alert.get("most_recent_instance") or {}
                loc = inst.get("location") or {}
                msg = (inst.get("message") or {}).get("text", "")
                print(f"    #{alert.get('number')} {rid} {alert.get('state')} {loc.get('path')}:{loc.get('start_line')} ref={inst.get('ref')} msg={msg[:120]!r}")
    else:
        print(f"    {alerts}")
    print("\n=== CodeQL workflow/config on main")
    for rel in (".github/workflows/codeql.yml", ".github/workflows/codeql-analysis.yml", ".github/codeql/codeql-config.yml"):
        path = worktree / rel
        if path.is_file():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if any(key in line for key in ("queries", "config-file", "languages", "paths", "query-filters", "exclude", "security-and-quality", "security-extended", "pull_request", "on:")):
                    print(f"    {rel}:{number}: {line.rstrip()}")
        else:
            print(f"    {rel}: (absent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Probe juniper-data's CodeQL history for the flood-4 tests carrier: will CodeQL post a review thread on its files?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#512 #513 #514 #516 #517; flood-4 validation brief (CodeQL lens)

Read-only `gh api` GETs. Reports (1) every code-scanning alert in every state, grouped by rule and state,
with every py/unused-global-variable alert listed and any alert under juniper_data/tests/; (2) for each
draft head, the CodeQL check runs' conclusion and annotation count, and any review comment the code
scanning bot left on the draft PR; (3) the same for two merged PRs that added test files with a module
level pytestmark, when given.

    python3 2026-11-07_flood4_val_data_codeql_probe.py <owner/repo> <pr>=<head sha> [<pr>=<head sha> ...]
"""

from __future__ import annotations

import collections
import json
import subprocess
import sys


def gh_json(path: str, paginate: bool = False) -> object:
    args = ["gh", "api", path]
    if paginate:
        args.insert(2, "--paginate")
        args += ["--jq", ".[]"]
        out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
        return [json.loads(line) for line in out.splitlines() if line.strip()]
    out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main() -> int:
    repo = sys.argv[1]
    pairs = [arg.split("=", 1) for arg in sys.argv[2:]]

    print("=== code-scanning alerts, every state ===")
    alerts: list[dict] = []
    for state in ("open", "fixed", "dismissed"):
        got = gh_json(f"repos/{repo}/code-scanning/alerts?state={state}&per_page=100", paginate=True)
        assert isinstance(got, list)
        alerts.extend(got)
    by_rule = collections.Counter((a["rule"]["id"], a["state"]) for a in alerts)
    print(f"total alerts: {len(alerts)}")
    for (rule, state), n in sorted(by_rule.items()):
        print(f"  {rule:45s} {state:10s} {n}")
    print("--- every py/unused-global-variable alert ---")
    for a in alerts:
        if a["rule"]["id"] == "py/unused-global-variable":
            loc = a["most_recent_instance"]["location"]
            msg = a["most_recent_instance"]["message"]["text"]
            print(f"  #{a['number']} {a['state']} {loc['path']}:{loc['start_line']} {msg!r} created={a['created_at']}")
    print("--- every alert under juniper_data/tests/ (any rule, any state) ---")
    n_tests = 0
    for a in alerts:
        loc = a["most_recent_instance"]["location"]
        if loc["path"].startswith("juniper_data/tests/"):
            n_tests += 1
            msg = a["most_recent_instance"]["message"]["text"]
            print(f"  #{a['number']} {a['rule']['id']} {a['state']} {loc['path']}:{loc['start_line']} {msg[:90]!r}")
    print(f"  ({n_tests} alert(s) under juniper_data/tests/)")
    print(f"--- alerts whose message names pytestmark: {[a['number'] for a in alerts if 'pytestmark' in a['most_recent_instance']['message']['text']]}")

    print("\n=== CodeQL on each PR head ===")
    for pr, sha in pairs:
        runs = gh_json(f"repos/{repo}/commits/{sha}/check-runs?per_page=100")
        assert isinstance(runs, dict)
        for cr in runs["check_runs"]:
            name = cr["name"]
            if "codeql" in name.lower() or "analyze" in name.lower() or name in ("CodeQL",):
                out = cr.get("output") or {}
                print(f"#{pr} {sha[:10]} check '{name}' app={cr['app']['slug']} status={cr['status']} conclusion={cr['conclusion']} annotations={out.get('annotations_count')} title={out.get('title')!r}")
        comments = gh_json(f"repos/{repo}/pulls/{pr}/comments?per_page=100", paginate=True)
        assert isinstance(comments, list)
        bot = [c for c in comments if "advanced-security" in c["user"]["login"] or "codeql" in c["user"]["login"].lower()]
        print(f"#{pr} review comments total={len(comments)} by code-scanning bot={len(bot)}")
        for c in bot:
            print(f"   {c['path']}:{c.get('line')} {c['body'][:120]!r}")
        pr_alerts = gh_json(f"repos/{repo}/code-scanning/alerts?ref=refs/pull/{pr}/head&per_page=100", paginate=True)
        assert isinstance(pr_alerts, list)
        print(f"#{pr} alerts on refs/pull/{pr}/head: {len(pr_alerts)}")
        for a in pr_alerts:
            loc = a["most_recent_instance"]["location"]
            print(f"   #{a['number']} {a['rule']['id']} {a['state']} {loc['path']}:{loc['start_line']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

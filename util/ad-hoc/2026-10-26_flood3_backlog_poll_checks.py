#!/usr/bin/env python3
"""
Poll ``gh pr checks`` for a set of PRs until none is pending, any check fails, or a deadline passes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 2026-10-26 flood-3 backlog PRs (juniper-canopy, juniper-deploy, juniper-recurrence);
         notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md §4

Read-only: it only runs ``gh pr checks`` (gh 2.46 has no ``--json`` there, so it parses the tab-separated
rows: name, state, elapsed, link). It never re-runs, cancels or bypasses anything. Each round prints one line
per PR with its state counts and the names of pending / failing checks.

Usage:
    python3 2026-10-26_flood3_backlog_poll_checks.py --pr juniper-canopy:775 --pr juniper-deploy:265 \
        [--minutes 22] [--interval 60] [--stop-on-fail]

Exit: 0 = nothing pending and nothing failing; 1 = a check failed; 3 = deadline reached with checks pending.
"""

from __future__ import annotations

import argparse
import subprocess  # nosec B404 - fixed argv: gh pr checks
import sys
import time
from collections import Counter
from datetime import datetime, timezone


def _checks(repo: str, number: int) -> list[tuple[str, str, str]]:
    proc = subprocess.run(["gh", "pr", "checks", str(number), "--repo", f"pcalnon/{repo}"], capture_output=True, text=True, timeout=120, check=False)  # nosec B603 B607
    rows: list[tuple[str, str, str]] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0].strip(), parts[1].strip(), parts[3].strip() if len(parts) > 3 else ""))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", action="append", required=True, help="REPO:NUMBER (repeatable)")
    ap.add_argument("--minutes", type=float, default=22.0)
    ap.add_argument("--interval", type=float, default=60.0)
    ap.add_argument("--stop-on-fail", action="store_true")
    args = ap.parse_args(argv)
    prs = [(p.split(":")[0], int(p.split(":")[1])) for p in args.pr]
    deadline = time.monotonic() + args.minutes * 60
    while True:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        any_pending = False
        any_fail = False
        for repo, number in prs:
            rows = _checks(repo, number)
            counts = Counter(state for _, state, _ in rows)
            pending = sorted(name for name, state, _ in rows if state == "pending")
            failing = sorted(f"{name} <{link}>" for name, state, link in rows if state == "fail")
            any_pending = any_pending or bool(pending) or not rows
            any_fail = any_fail or bool(failing)
            print(f"{now} {repo}#{number} {dict(sorted(counts.items()))} pending={pending} failing={failing}", flush=True)
        if any_fail and args.stop_on_fail:
            print("STOP: a check failed", flush=True)
            return 1
        if not any_pending:
            print("DONE: nothing pending", flush=True)
            return 1 if any_fail else 0
        if time.monotonic() >= deadline:
            print("DEADLINE: checks still pending", flush=True)
            return 3
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())

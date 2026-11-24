#!/usr/bin/env python3
"""
List the pull requests of a saved census that hold a merge commit, newest first, to pick one whose job log to read.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-ml)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         util/ad-hoc/2026-11-14_flood4r2_r10-ml_pr_census.py (writes the JSON this reads)

WHY THIS EXISTS
A port quotes one real pull-request job log of its own repository: the action's argv and its "N commits scanned."
line beside the pull request's own commit count. Job logs expire, so the newest pull requests with a merge commit
are the ones whose logs can still be read. This prints, for each, the number, state, dates, head SHA, the commit and
merge counts, and how many of its own non-merge commits the action's simulated window misses. It reads only the
saved JSON and sends no request.

Usage:
    python3 <this> --census <saved census json> [--limit 15] [--min-number 2203]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--census", required=True, type=Path)
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--min-number", type=int, default=0)
    args = ap.parse_args()
    with open(args.census, encoding="utf-8") as fh:
        rows = json.load(fh)["rows"]
    picked = [r for r in rows if r["merges"] and r["number"] >= args.min_number]
    picked.sort(key=lambda r: r["number"], reverse=True)
    for r in picked[: args.limit]:
        window = r["action_window"] or {}
        lost = len(window.get("lost_non_merge") or [])
        print(f"#{r['number']} {r['state']} created={r['created_at'][:16]} merged={(r['merged_at'] or '-')[:16]} head={r['head_sha']} commits={r['commits']} merges={r['merges']} non_merge={r['non_merge']} window_scans_non_merge={window.get('scanned_non_merge')} lost={lost} author={r['author']}")
    print(f"{len(picked)} pull requests with a merge commit at or above #{args.min_number}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

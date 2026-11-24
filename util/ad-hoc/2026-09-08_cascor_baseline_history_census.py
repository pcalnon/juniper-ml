#!/usr/bin/env python3
"""
Census of every cascor ``baseline_*.json`` that ever existed: did any carry a timing key?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — investigation (perf lane P2 item 2.4 / PF-4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-09-08_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-RESCOPE-AND-MICRO-TIMING-REFERENCE.md

WHY THIS EXISTS

The 2026-09-07 perf-lane handoff said cascor's ``baseline_20260526.json`` is "gitignored with
zero commit history", which is true of THAT file and false of the directory: 21 baseline files
(2026-03-31 .. 2026-05-25) were tracked, then deleted together in cascor commit 971d35a. Before
claiming "no cascor baseline file has EVER held a timing figure" in a document, every one of
those 21 plus the live file is read here and its ``results`` keys tallied. Two files inspected by
hand are not 22 files; a sweep that reuses its own first pattern is the class this lane keeps
finding.

Reads git history only; changes nothing. Run from anywhere:

    python3 util/ad-hoc/2026-09-08_cascor_baseline_history_census.py [--cascor PATH]
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess  # nosec B404 -- read-only `git ls-tree` / `git show` with fixed argv, no shell
import sys
from pathlib import Path

DELETING_COMMIT = "971d35a"
BASELINES_DIR = "src/tests/performance/baselines"
TIMING_MARKERS = ("_ms", "_s", "time", "duration", "mean", "median", "stddev", "ops", "rounds")


def _git(cascor: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(cascor), *args], capture_output=True, text=True, check=True)  # nosec B603 B607
    return completed.stdout


def _is_timing_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in TIMING_MARKERS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cascor", type=Path, default=Path("/home/pcalnon/Development/python/Juniper/juniper-cascor"))
    args = parser.parse_args(argv)

    listing = _git(args.cascor, "ls-tree", "--name-only", f"{DELETING_COMMIT}^", BASELINES_DIR + "/")
    historical = sorted(line.strip() for line in listing.splitlines() if line.strip().endswith(".json"))
    live = sorted((args.cascor / BASELINES_DIR).glob("baseline_*.json"))

    rows: list[tuple[str, int, dict, set]] = []
    for rel in historical:
        entries = json.loads(_git(args.cascor, "show", f"{DELETING_COMMIT}^:{rel}"))
        rows.append((Path(rel).name + "  (deleted in " + DELETING_COMMIT + ")", len(entries), _key_tally(entries), _timing_keys(entries)))
    for path in live:
        entries = json.loads(path.read_text())
        rows.append((path.name + "  (live, gitignored)", len(entries), _key_tally(entries), _timing_keys(entries)))

    total_entries = 0
    files_with_timing = 0
    print(f"{'file':60} {'entries':>7}  result keys")
    for name, count, tally, timing in rows:
        total_entries += count
        files_with_timing += bool(timing)
        keys = ", ".join(f"{k}:{v}" for k, v in sorted(tally.items()))
        flag = "  <-- TIMING KEYS: " + ", ".join(sorted(timing)) if timing else ""
        print(f"{name:60} {count:>7}  {keys}{flag}")
    print()
    print(f"files: {len(rows)} ({len(historical)} historical + {len(live)} live)   entries: {total_entries}   files with any timing key: {files_with_timing}")
    return 0 if files_with_timing == 0 else 1


def _key_tally(entries: list[dict]) -> dict:
    tally: collections.Counter = collections.Counter()
    for entry in entries:
        for key in entry.get("results", {}):
            tally[key] += 1
    return dict(tally)


def _timing_keys(entries: list[dict]) -> set:
    return {key for entry in entries for key in entry.get("results", {}) if _is_timing_key(key)}


if __name__ == "__main__":
    sys.exit(main())

"""
Print a merged ruling-17 census as a per-port, per-file, per-test report.

Builder helper for the owner's ruling 17 ("canopy: tests hit :8050"). Reads a merged census JSON written by
util/ad-hoc/2026-11-09_flood4r2_r17-canopy-guard_run_groups.py and prints, for each port: the connect and test
counts and verdicts; then each test that connected, grouped by file, with its markers, outcome, phases, threads
and the innermost worktree frames of its first connect. ``--ports`` limits the per-test part to those ports.

Usage:
  python3 <this file> <merged census json> [--ports 8050 8100 ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 (flood-4 session 4), juniper-canopy unit-lane network guard
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("census", type=Path)
    parser.add_argument("--ports", nargs="*", type=int, default=[])
    args = parser.parse_args()
    with open(args.census, encoding="utf-8") as fh:
        record = json.load(fh)

    print(f"collected={record.get('collected')} outcomes={record.get('outcomes')} group_exits={record.get('groups')}")
    for port, entry in sorted(record.get("by_port", {}).items(), key=lambda pair: int(pair[0])):
        print(f"port {port}: connects={entry['connects']} tests={entry['n_tests']} verdicts={entry['verdicts']} hosts={entry['hosts']}")
    by_file: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for nodeid, entry in record.get("by_test", {}).items():
        ports = {int(key.split(":")[-2]) for key in entry["ports"]}
        if args.ports and not ports & set(args.ports):
            continue
        by_file[nodeid.split("::", 1)[0]].append((nodeid, entry))
    for path in sorted(by_file):
        print(f"\n== {path} ({len(by_file[path])} tests)")
        for nodeid, entry in sorted(by_file[path]):
            print(f"  {nodeid.split('::', 1)[-1]}  outcome={entry['outcome']} markers={entry['markers']} ports={entry['ports']} phases={entry['phases']} threads={entry['threads']}")
        print("    first frames: " + " <- ".join(reversed(by_file[path][0][1]["first_frames"][-4:])))
    failed = record.get("failed", [])
    print(f"\nfailed ({len(failed)}):")
    for nodeid in failed:
        print(f"  {nodeid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

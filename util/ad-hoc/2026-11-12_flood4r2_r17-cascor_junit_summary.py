#!/usr/bin/env python3
"""
Summarise one pytest JUnit XML file, or compare two of them test by test.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_r17-cascor_run_lane.py writes the JUnit files this reads
         (one per lane and tree); tmp/flood4/BRIEF_COMMON_R2.txt rule 14 (record what was run)

It REPORTS, it does not judge. A test's key is ``classname::name``; a test is ``failed`` when it
has a ``failure`` or ``error`` child, ``skipped`` when it has a ``skipped`` child, else ``passed``.
With pytest-repeat every repetition is its own test case, so a repeated test is counted once
per repetition.

Usage:
  2026-11-12_flood4r2_r17-cascor_junit_summary.py <junit.xml> [--match <substring>] [--out <json>]
      counts, the failing tests, and (with --match) the outcome and seconds of each matching test
  2026-11-12_flood4r2_r17-cascor_junit_summary.py <junit.xml> --against <other junit.xml> [--out <json>]
      tests in both files with a different outcome, and the tests only one of them holds
Exit: 0 when the report was written; 2 when a file cannot be read.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ElementTree  # nosec B405 -- reads JUnit files this session's own pytest runs wrote
from pathlib import Path


def _outcome(case) -> str:
    if case.find("failure") is not None or case.find("error") is not None:
        return "failed"
    if case.find("skipped") is not None:
        return "skipped"
    return "passed"


def _load(path: Path) -> list:
    root = ElementTree.parse(path).getroot()  # nosec B314 -- see the import
    return [(f"{case.get('classname', '')}::{case.get('name', '')}", _outcome(case), float(case.get("time", "0") or 0)) for case in root.iter("testcase")]


def _summary(cases: list, match: str) -> dict:
    counts = {"tests": len(cases), "passed": 0, "failed": 0, "skipped": 0}
    for _key, outcome, _seconds in cases:
        counts[outcome] += 1
    report = {"counts": counts, "failing": sorted(key for key, outcome, _seconds in cases if outcome == "failed")}
    if match:
        report["matching"] = [[key, outcome, seconds] for key, outcome, seconds in cases if match in key]
    return report


def _compare(ours: list, theirs: list) -> dict:
    mine = {key: outcome for key, outcome, _seconds in ours}
    other = {key: outcome for key, outcome, _seconds in theirs}
    shared = sorted(set(mine) & set(other))
    return {
        "shared": len(shared),
        "changed_outcome": [[key, mine[key], other[key]] for key in shared if mine[key] != other[key]],
        "only_in_first": sorted(set(mine) - set(other)),
        "only_in_first_outcomes": sorted({mine[key] for key in set(mine) - set(other)}),
        "only_in_second": sorted(set(other) - set(mine)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("junit", type=Path)
    parser.add_argument("--against", type=Path, help="a second JUnit file to compare with, test by test")
    parser.add_argument("--match", default="", help="list each test whose key holds this substring")
    parser.add_argument("--out", type=Path, help="also write the report here as JSON")
    args = parser.parse_args()
    try:
        cases = _load(args.junit)
        report = {"file": str(args.junit), **_summary(cases, args.match)}
        if args.against:
            report["against"] = str(args.against)
            report["comparison"] = _compare(cases, _load(args.against))
    except (OSError, ElementTree.ParseError) as exc:
        print(f"cannot read: {exc}")
        return 2
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

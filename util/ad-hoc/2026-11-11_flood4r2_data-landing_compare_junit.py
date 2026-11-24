#!/usr/bin/env python3
"""
Compare JUnit reports of one test lane run on several trees: which test ids each tree adds, loses or changes.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (a count that rises by N says nothing about WHICH tests; this names them)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_run_lane.py (which writes the reports)

Usage:
    python3 <this> --out <json> <name>=<junit.xml> <name>=<junit.xml> [...]

The first report is the reference (M0). Each later report is compared with the reference and with the report before
it (its parent stage): ids only in the later one, grouped by test module; ids only in the earlier one; and ids whose
outcome differs. An id is ``classname::name``; a duplicate id within one report is listed.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this arc's own pytest runs wrote
from pathlib import Path


def _load(path: Path) -> tuple[dict[str, str], list[str]]:
    outcomes: dict[str, str] = {}
    duplicates: list[str] = []
    for case in ET.parse(path).getroot().iter("testcase"):  # nosec B314
        tags = {child.tag for child in case}
        node = f"{case.get('classname')}::{case.get('name')}"
        if "failure" in tags:
            outcome = "failed"
        elif "error" in tags:
            outcome = "error"
        elif "skipped" in tags:
            outcome = "skipped"
        else:
            outcome = "passed"
        if node in outcomes:
            duplicates.append(node)
        outcomes[node] = outcome
    return outcomes, duplicates


def _module(node: str) -> str:
    return node.split("::", 1)[0].split(".Test")[0]


def _delta(earlier: dict[str, str], later: dict[str, str]) -> dict:
    added = sorted(set(later) - set(earlier))
    removed = sorted(set(earlier) - set(later))
    changed = sorted(node for node in set(earlier) & set(later) if earlier[node] != later[node])
    by_module = collections.Counter(_module(node) for node in added)
    return {
        "added": len(added),
        "added_by_module": dict(sorted(by_module.items())),
        "added_outcomes": dict(collections.Counter(later[node] for node in added)),
        "removed": removed,
        "outcome_changed": [{"id": node, "earlier": earlier[node], "later": later[node]} for node in changed],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("reports", nargs="+", help="<name>=<junit.xml>")
    args = ap.parse_args()
    loaded = []
    for item in args.reports:
        name, path = item.split("=", 1)
        outcomes, duplicates = _load(Path(path))
        loaded.append((name, outcomes, duplicates))
    reference_name, reference, _ = loaded[0]
    report: dict = {"reference": reference_name, "trees": {}}
    for index, (name, outcomes, duplicates) in enumerate(loaded):
        row: dict = {"tests": len(outcomes), "outcomes": dict(collections.Counter(outcomes.values())), "duplicate_ids": duplicates}
        if index > 0:
            row[f"against_{reference_name}"] = _delta(reference, outcomes)
            parent_name, parent, _ = loaded[index - 1]
            if index > 1:
                row[f"against_{parent_name}"] = _delta(parent, outcomes)
        report["trees"][name] = row
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

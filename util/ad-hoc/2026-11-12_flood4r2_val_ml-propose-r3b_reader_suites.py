#!/usr/bin/env python3
"""
Name the suites of CI's regression list that read what the ml-propose carrier changes, with the reason for each.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The carrier changes docs/REFERENCE.md, CHANGELOG.md, the release-train runbook, util/release_train/propose.py and
its test file, and adds 17 scripts under util/ad-hoc/. A suite can read any of them without naming the carrier.
The selection is by the suite's own source, and it is deliberately wide:

* named -- the source names docs/REFERENCE.md, CHANGELOG.md, the runbook, the release train or propose.py;
* walker -- the source walks a tree (rglob / glob / os.walk / iterdir / `git ls-files`) and names util, ad-hoc,
  notes or docs, so it may reach a new script or a changed document it does not name.

The list of suites is CI's own: every `python3 -m unittest ... tests/<file>.py` line of the workflow's regression
step, in the tree given.

Usage:
    python3 <this> --tree <repo root> --out <suites file> [--json <report>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORKFLOW = ".github/workflows/ci.yml"
SUITE = re.compile(r"python3? -m unittest(?: -v)? (tests/[A-Za-z0-9_./-]+\.py)")
NAMED = (("docs/REFERENCE.md", re.compile(r"REFERENCE\.md")), ("CHANGELOG.md", re.compile(r"CHANGELOG")), ("the runbook", re.compile(r"RELEASE-TRAIN-OPERATOR-RUNBOOK")), ("the release train", re.compile(r"release_train|release-train")), ("propose.py", re.compile(r"\bpropose\b")))
WALKS = re.compile(r"rglob\(|\.glob\(|os\.walk\(|iterdir\(\)|ls-files")
WALK_ROOTS = (("util", re.compile(r"[\"'/]util[\"'/]|\"util\"|'util'")), ("ad-hoc", re.compile(r"ad-hoc|ad_hoc")), ("notes", re.compile(r"[\"'/]notes[\"'/]")), ("docs", re.compile(r"[\"'/]docs[\"'/]")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    tree = args.tree.resolve()
    listed = []
    for found in SUITE.findall((tree / WORKFLOW).read_text(encoding="utf-8")):
        if found not in listed:
            listed.append(found)
    rows = []
    for suite in listed:
        path = tree / suite
        if not path.is_file():
            rows.append({"suite": suite, "selected": False, "why": ["NOT ON DISK"]})
            continue
        source = path.read_text(encoding="utf-8")
        why = [f"names {label}" for label, pattern in NAMED if pattern.search(source)]
        if WALKS.search(source):
            why += [f"walks a tree and names {label}" for label, pattern in WALK_ROOTS if pattern.search(source)]
        rows.append({"suite": suite, "selected": bool(why), "why": why})
    selected = [row["suite"] for row in rows if row["selected"]]
    args.out.write_text("\n".join(selected) + "\n", encoding="utf-8")
    report = {"tree": str(tree), "suites_in_ci_list": len(listed), "selected": len(selected), "named": sum(1 for row in rows if any(item.startswith("names ") for item in row["why"])), "walkers_only": sum(1 for row in rows if row["selected"] and not any(item.startswith("names ") for item in row["why"])), "rows": rows}
    if args.json:
        args.json.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"CI's list: {len(listed)} suites; selected {len(selected)} ({report['named']} name a changed file, {report['walkers_only']} are walkers only); not on disk: {[row['suite'] for row in rows if row['why'] == ['NOT ON DISK']]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

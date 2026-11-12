#!/usr/bin/env python3
"""
Report which lines a juniper-cascor change adds are missed, or start a partial branch, in a coverage XML report.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#753's "Coverage of the changed lines" check

Reads the added line numbers of each named file from ``git diff -U0 <base> -- <file>`` in the
checkout (the working tree against ``base``), and the ``<line>`` elements of a Cobertura XML
report. A line counts as MISSED when its hits are 0, and as PARTIAL when it is a branch whose
``condition-coverage`` is below 100%. ``--known-answer`` also feeds a crafted report naming two
added lines (one missed, one partial) and requires both to be reported.

Usage:
  2026-11-09_flood4r2_r17-cascor_changed_line_coverage.py --tree <checkout> --base <ref> --xml <coverage.xml> --file <repo-relative> [--file ...] [--known-answer]
Exit: 0 when no added line is missed or partial (and the known answer, when asked, is caught); 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 -- fixed-argv git diff
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses a coverage report this session wrote
from pathlib import Path


def _added_lines(tree: Path, base: str, relative: str) -> list:
    diff = subprocess.run(["git", "-C", str(tree), "diff", "-U0", base, "--", relative], capture_output=True, text=True, check=True).stdout  # nosec B603 B607 -- fixed argv
    added = []
    for match in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.MULTILINE):
        start, count = int(match.group(1)), int(match.group(2) or "1")
        added.extend(range(start, start + count))
    return added


def _report(root: ET.Element, relative: str) -> tuple:
    """(missed lines, partial-branch lines) for ``relative`` (matched on the path's tail under src/)."""
    tail = relative.split("src/", 1)[-1]
    missed, partial = set(), set()
    for cls in root.iter("class"):
        if not cls.get("filename", "").endswith(tail):
            continue
        for line in cls.iter("line"):
            number = int(line.get("number"))
            if line.get("hits") == "0":
                missed.add(number)
            coverage = line.get("condition-coverage")
            if line.get("branch") == "true" and coverage and not coverage.startswith("100%"):
                partial.add(number)
    return missed, partial


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--xml", required=True, type=Path)
    parser.add_argument("--file", action="append", required=True)
    parser.add_argument("--known-answer", action="store_true")
    args = parser.parse_args()
    root = ET.parse(args.xml).getroot()  # nosec B314 -- our own coverage report
    failed = False
    for relative in args.file:
        added = _added_lines(args.tree, args.base, relative)
        missed, partial = _report(root, relative)
        bad_missed = sorted(set(added) & missed)
        bad_partial = sorted(set(added) & partial)
        print(f"{relative}: {len(added)} added lines; missed among them: {bad_missed}; partial-branch sources among them: {bad_partial}")
        failed = failed or bool(bad_missed or bad_partial)
        if args.known_answer and len(added) >= 2:
            crafted = ET.fromstring(f'<coverage><packages><package><classes><class filename="{relative}"><lines><line number="{added[0]}" hits="0"/><line number="{added[1]}" hits="1" branch="true" condition-coverage="50% (1/2)"/></lines></class></classes></package></packages></coverage>')  # nosec B314 -- crafted literal
            k_missed, k_partial = _report(crafted, relative)
            caught = added[0] in k_missed and added[1] in k_partial
            print(f"  known answer (crafted report naming added lines {added[0]} missed and {added[1]} partial): {'CAUGHT' if caught else 'NOT CAUGHT'}")
            failed = failed or not caught
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

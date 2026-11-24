#!/usr/bin/env python3
"""
Place (or replace) the unrun-tests entry in juniper-data's CHANGELOG.md, byte for byte from changelog_entry.txt.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (keeps the deliverable changelog_entry.txt and the file's entry identical)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#529 (the precedent)

Usage:
    python3 <this> --changelog <juniper-data tree>/CHANGELOG.md --entry <changelog_entry.txt> [--check]

The entry goes under the top ``## [Unreleased]`` / ``### Fixed``, directly after the entry juniper-data#529 added
(``- **44 of `test_security.py`'s 116 tests never ran in CI ...``), so at least one existing entry of the subsection
sits above it and a later insertion at the top of the subsection cannot conflict with it. An entry already placed by
an earlier run (recognised by its first line) is replaced, so the script can be re-run after an edit of the text.
--check changes nothing and exits 1 unless the file holds the entry exactly once, in that place, inside the first
``## [`` section.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ANCHOR_HEAD = "- **44 of `test_security.py`'s 116 tests never ran in CI; the module is now marked `unit`**\n"


def _place(text: str, entry: str) -> str:
    lines = text.splitlines(keepends=True)
    first = entry.splitlines(keepends=True)[0]
    if first in lines:  # drop an entry an earlier run placed: its first line up to the next top-level bullet
        start = lines.index(first)
        end = start + 1
        while end < len(lines) and not lines[end].startswith(("- **", "### ", "## ")):
            end += 1
        del lines[start:end]
    if lines.count(ANCHOR_HEAD) != 1:
        raise SystemExit(f"the anchor entry occurs {lines.count(ANCHOR_HEAD)} times, expected 1")
    at = lines.index(ANCHOR_HEAD) + 1
    while at < len(lines) and not lines[at].startswith(("- **", "### ", "## ")):
        at += 1
    return "".join(lines[:at]) + entry + "".join(lines[at:])


def _check(text: str, entry: str) -> list[str]:
    problems = []
    if text.count(entry) != 1:
        problems.append(f"the entry occurs {text.count(entry)} times")
        return problems
    lines = text.splitlines(keepends=True)
    sections = [n for n, ln in enumerate(lines) if ln.startswith("## [")]
    where = text[: text.index(entry)].count("\n")
    if not (sections[0] < where < sections[1]):
        problems.append("the entry is not inside the first '## [' section")
    if lines[sections[0]].strip() != "## [Unreleased]":
        problems.append(f"the first section is {lines[sections[0]].strip()!r}")
    heading = [ln.strip() for ln in lines[sections[0] : where] if ln.startswith("### ")][-1]
    if heading != "### Fixed":
        problems.append(f"the entry sits under {heading!r}")
    above = [ln for ln in lines[sections[0] : where] if ln.startswith("- **")]
    if not above or above[-1] != ANCHOR_HEAD:
        problems.append("the entry does not directly follow the juniper-data#529 entry")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--changelog", type=Path, required=True)
    ap.add_argument("--entry", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    with open(args.changelog, encoding="utf-8") as fh:
        text = fh.read()
    with open(args.entry, encoding="utf-8") as fh:
        entry = fh.read()
    if not entry.startswith("- **") or not entry.endswith("\n"):
        raise SystemExit("the entry must start with a top-level bullet and end with a newline")
    if not args.check:
        text = _place(text, entry)
        with open(args.changelog, "w", encoding="utf-8") as fh:
            fh.write(text)
    problems = _check(text, entry)
    for problem in problems:
        print("PROBLEM:", problem)
    line = text[: text.index(entry)].count("\n") + 1 if not problems or text.count(entry) == 1 else None
    print(f"entry of {len(entry.splitlines())} lines at CHANGELOG.md:{line}; {'OK' if not problems else 'NOT OK'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

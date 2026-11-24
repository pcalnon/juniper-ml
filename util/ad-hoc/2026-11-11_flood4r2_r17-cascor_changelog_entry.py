#!/usr/bin/env python3
"""
Put juniper-cascor's stop-then-start CHANGELOG entry in place from its text file, or check that it is in place.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 9 (the entry goes under the top [Unreleased], below
         an existing entry of its subsection) and DELIVERABLES (changelog_entry.txt is the exact
         text put under [Unreleased])

The entry is one top-level bullet. It is recognised in ``CHANGELOG.md`` by its first line (the
first line of ``--entry``) and runs to the next top-level bullet or heading. ``--write`` replaces
that block with the entry file's text; when the block is absent it inserts the text before the
top-level bullet that starts with ``--before`` (the entry that should follow this one). Nothing
else in the file is touched, and the result is written only when every check below holds.

Checks (``--write`` and ``--check`` alike): the entry's text occurs exactly once; it sits under
the FIRST ``## [`` heading, which must be ``## [Unreleased]``, and under ``### Fixed`` there; at
least one other entry of that subsection sits above it; and it holds no ``PLACEHOLDER``.

Usage:
  2026-11-11_flood4r2_r17-cascor_changelog_entry.py --changelog <CHANGELOG.md> --entry <changelog_entry.txt> --check
  2026-11-11_flood4r2_r17-cascor_changelog_entry.py --changelog <CHANGELOG.md> --entry <changelog_entry.txt> --write --before "<first words of the next entry>"
Exit: 0 when the entry is in place and every check holds; 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _block_end(lines: list, start: int) -> int:
    """Index of the first line after ``start`` that begins a top-level bullet or a heading."""
    for index in range(start + 1, len(lines)):
        if lines[index].startswith(("- ", "## ", "### ")):
            return index
    return len(lines)


def _checks(text: str, entry: str) -> list:
    problems = []
    if "PLACEHOLDER" in entry:
        problems.append("the entry holds a PLACEHOLDER")
    count = text.count(entry)
    if count != 1:
        return problems + [f"the entry's text occurs {count} times, expected 1"]
    lines = text.splitlines()
    first_line = entry.splitlines()[0]
    at = lines.index(first_line)
    releases = [index for index, line in enumerate(lines) if line.startswith("## [")]
    if not releases or lines[releases[0]] != "## [Unreleased]":
        problems.append("the first release heading is not '## [Unreleased]'")
    elif len(releases) > 1 and not releases[0] < at < releases[1]:
        problems.append("the entry is not under the top '## [Unreleased]'")
    sections = [index for index in range(at) if lines[index].startswith("### ")]
    if not sections or lines[sections[-1]] != "### Fixed":
        problems.append(f"the entry's subsection is {lines[sections[-1]] if sections else None!r}, expected '### Fixed'")
    elif not any(line.startswith("- ") for line in lines[sections[-1] + 1 : at]):
        problems.append("no other entry of the subsection sits above this one")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--changelog", required=True, type=Path)
    parser.add_argument("--entry", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--before", help="with --write: the first words of the top-level bullet the entry goes before, when it is not in the file yet")
    args = parser.parse_args()
    entry = args.entry.read_text(encoding="utf-8")
    if not entry.endswith("\n") or entry.endswith("\n\n") or not entry.startswith("- "):
        print("the entry file must be one top-level bullet ending in exactly one newline")
        return 1
    text = args.changelog.read_text(encoding="utf-8")
    if args.write:
        lines = text.splitlines(keepends=True)
        first_line = entry.splitlines(keepends=True)[0]
        starts = [index for index, line in enumerate(lines) if line == first_line]
        if len(starts) == 1:
            end = _block_end(lines, starts[0])
            lines[starts[0] : end] = [entry]
            action = f"replaced the entry at line {starts[0] + 1} (it ran to line {end})"
        elif not starts and args.before:
            anchors = [index for index, line in enumerate(lines) if line.startswith("- " + args.before) or line.startswith(args.before)]
            if len(anchors) != 1:
                print(f"--before matches {len(anchors)} top-level bullets, expected 1")
                return 1
            lines[anchors[0] : anchors[0]] = [entry]
            action = f"inserted the entry before line {anchors[0] + 1}"
        else:
            print(f"the entry's first line occurs {len(starts)} times and no usable --before was given")
            return 1
        text = "".join(lines)
    problems = _checks(text, entry)
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    if args.write:
        args.changelog.write_text(text, encoding="utf-8")
        print(action)
    at = text.splitlines().index(entry.splitlines()[0]) + 1
    print(f"ok: the entry ({len(entry.splitlines())} lines) is in place at line {at}, under [Unreleased] / Fixed, below another entry")
    return 0


if __name__ == "__main__":
    sys.exit(main())

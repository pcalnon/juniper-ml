#!/usr/bin/env python3
"""
Put juniper-cascor's stop-then-start CHANGELOG entry in place from its text file, move it, or check that it is in place.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", second pass)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 9 (the entry goes under the top [Unreleased], below
         an existing entry of its subsection) and DELIVERABLES (changelog_entry.txt is the exact
         text put under [Unreleased]); 2026-11-11_flood4r2_r17-cascor_changelog_entry.py, which
         this copies and extends (that one is left as it ran)

The entry is one top-level bullet. It is recognised in ``CHANGELOG.md`` by its first line (the
first line of ``--entry``) and runs to the next top-level bullet or heading, trailing blank lines
included. ``--write`` removes that block when it is present and inserts the entry file's text
before the top-level bullet that starts with ``--before`` (the entry that should follow this one),
followed by one blank line when ``--blank-after`` is given. Nothing else in the file is touched,
and the result is written only when every check below holds.

Checks (``--write`` and ``--check`` alike):

* the entry's text occurs exactly once and holds no ``PLACEHOLDER``;
* it sits under the FIRST ``## [`` heading, which must be ``## [Unreleased]``, and under
  ``### Fixed`` there, with at least one other entry of that subsection above it;
* with ``--after``: the top-level bullet directly above it starts with those words;
* with ``--main``: taking the entry (and its blank line, with ``--blank-after``) back out of the
  result gives that file byte for byte, so the change is one insertion and nothing else.

Usage:
  2026-11-12_flood4r2_r17-cascor_changelog_entry.py --changelog <CHANGELOG.md> --entry <changelog_entry.txt> --check [--after "<words>"] [--main <main's CHANGELOG.md>] [--blank-after]
  2026-11-12_flood4r2_r17-cascor_changelog_entry.py --changelog <CHANGELOG.md> --entry <changelog_entry.txt> --write --before "<words>" [--after "<words>"] [--main <file>] [--blank-after]
Exit: 0 when the entry is in place and every check holds; 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BULLET_OR_HEADING = ("- ", "## ", "### ")


def _block_end(lines: list, start: int) -> int:
    """Index of the first line after ``start`` that begins a top-level bullet or a heading."""
    for index in range(start + 1, len(lines)):
        if lines[index].startswith(BULLET_OR_HEADING):
            return index
    return len(lines)


def _starts_with_words(line: str, words: str) -> bool:
    return line.startswith("- " + words) or line.startswith(words)


def _checks(text: str, entry: str, after: str, main_text: str, blank_after: bool) -> list:
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
        return problems
    above = [index for index in range(sections[-1] + 1, at) if lines[index].startswith("- ")]
    if not above:
        problems.append("no other entry of the subsection sits above this one")
    elif after and not _starts_with_words(lines[above[-1]], after):
        problems.append(f"the entry directly above starts {lines[above[-1]][:70]!r}, expected it to start with {after!r}")
    if main_text:
        inserted = entry + ("\n" if blank_after else "")
        if text.count(inserted) != 1:
            problems.append("the entry is not followed by the one blank line --blank-after names")
        elif text.replace(inserted, "", 1) != main_text:
            problems.append("taking the entry back out does not give --main's file byte for byte")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--changelog", required=True, type=Path)
    parser.add_argument("--entry", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--before", default="", help="with --write: the first words of the top-level bullet the entry goes before")
    parser.add_argument("--after", default="", help="check that the top-level bullet directly above the entry starts with these words")
    parser.add_argument("--main", type=Path, help="main's CHANGELOG.md: the result with the entry taken out must equal it")
    parser.add_argument("--blank-after", action="store_true", help="one blank line follows the entry (it separates it from the next one)")
    args = parser.parse_args()
    entry = args.entry.read_text(encoding="utf-8")
    if not entry.endswith("\n") or entry.endswith("\n\n") or not entry.startswith("- "):
        print("the entry file must be one top-level bullet ending in exactly one newline")
        return 1
    text = args.changelog.read_text(encoding="utf-8")
    action = "checked"
    if args.write:
        if not args.before:
            print("--write needs --before")
            return 1
        lines = text.splitlines(keepends=True)
        first_line = entry.splitlines(keepends=True)[0]
        starts = [index for index, line in enumerate(lines) if line == first_line]
        if len(starts) > 1:
            print(f"the entry's first line occurs {len(starts)} times, expected 0 or 1")
            return 1
        removed = "no earlier block"
        if starts:
            end = _block_end(lines, starts[0])
            removed = f"removed the block at lines {starts[0] + 1} to {end}"
            del lines[starts[0] : end]
        anchors = [index for index, line in enumerate(lines) if _starts_with_words(line, args.before)]
        if len(anchors) != 1:
            print(f"--before matches {len(anchors)} top-level bullets, expected 1")
            return 1
        lines[anchors[0] : anchors[0]] = [entry] + (["\n"] if args.blank_after else [])
        action = f"{removed}; inserted the entry before the bullet that was at line {anchors[0] + 1}"
        text = "".join(lines)
    main_text = args.main.read_text(encoding="utf-8") if args.main else ""
    problems = _checks(text, entry, args.after, main_text, args.blank_after)
    for problem in problems:
        print(f"FAIL: {problem}")
    if problems:
        return 1
    if args.write:
        args.changelog.write_text(text, encoding="utf-8")
    print(action)
    at = text.splitlines().index(entry.splitlines()[0]) + 1
    extras = [f"directly below the entry that starts {args.after!r}" if args.after else "below another entry"]
    if args.main:
        extras.append("a pure insertion against --main")
    print(f"ok: the entry ({len(entry.splitlines())} lines) is in place at line {at}, under [Unreleased] / Fixed, " + ", ".join(extras))
    return 0


if __name__ == "__main__":
    sys.exit(main())

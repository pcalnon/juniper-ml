#!/usr/bin/env python3
"""
Put the ml-propose carrier's CHANGELOG entry under `## [Unreleased]` when a release proposal has emptied that section.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14; juniper-ml#2558

WHY THIS EXISTS
The carrier's landing helper rebuilds CHANGELOG.md three-way, so its entry follows the entries it was written
between. A release proposal moves those entries under a new `## [X.Y.Z] - <date>` heading and leaves
`## [Unreleased]` empty, and the rebuilt entry then sits INSIDE the released section. The helper notices (exit 1)
but has already written the file, and it can never pass on such a main: it wants the entry below another
unreleased entry, and there is none.

This writes the CHANGELOG the landing needs instead: main's own file (the landing worktree's HEAD), byte for byte,
with one block inserted directly under `## [Unreleased]`:

    ### Fixed
    <blank line>
    <the entry>
    <blank line>

It refuses when main's [Unreleased] is not empty (the landing helper's own result is then the one to use), when
the entry is already on main, or when the result is not main plus exactly that block.

Usage:
    python3 <this> --tree <landing worktree> --entry <changelog_entry.txt> [--check-only]
Exit 0 = CHANGELOG.md in the tree is main's plus the block (written, or already so); 1 = refused.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the caller's own landing worktree
import sys
from pathlib import Path

CHANGELOG = "CHANGELOG.md"
EMPTY_UNRELEASED = re.compile(r"^## \[Unreleased\]\n(?:[ \t]*\n)*(?=## \[\d+\.\d+\.\d+\] - \d{4}-\d{2}-\d{2}\n)", re.MULTILINE)


def build(main_text: str, entry: str) -> "tuple[str | None, str]":
    """main's CHANGELOG with the entry under a new `### Fixed` in an empty [Unreleased]; (None, why) to refuse."""
    entry = entry.rstrip("\n") + "\n"
    if entry in main_text:
        return None, "the entry is already in main's CHANGELOG.md"
    hits = list(EMPTY_UNRELEASED.finditer(main_text))
    if len(hits) != 1:
        return None, "main's `## [Unreleased]` is not an empty section directly above a release heading: use the landing helper's own CHANGELOG.md"
    block = "## [Unreleased]\n\n### Fixed\n\n" + entry + "\n"
    return main_text[: hits[0].start()] + block + main_text[hits[0].end() :], "ok"


def placement(text: str, entry: str) -> dict:
    entry = entry.rstrip("\n") + "\n"
    if text.count(entry) != 1:
        return {"occurrences": text.count(entry)}
    head = text[: text.index(entry)].split("\n")
    return {
        "occurrences": 1,
        "first_line": len(head),
        "release_headings_above": [line for line in head if line.startswith("## [")],
        "subsection": next((line for line in reversed(head) if line.startswith("### ")), None),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--entry", required=True, type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    tree = args.tree.resolve()
    entry = args.entry.read_text(encoding="utf-8")
    main_bytes = subprocess.run(["git", "show", f"HEAD:{CHANGELOG}"], cwd=tree, capture_output=True, check=True).stdout  # nosec B603 B607
    main_text = main_bytes.decode("utf-8")
    current = (tree / CHANGELOG).read_text(encoding="utf-8")
    print("in the tree now:", placement(current, entry))
    wanted, why = build(main_text, entry)
    if wanted is None:
        print("REFUSED:", why)
        return 1
    after = placement(wanted, entry)
    lost = wanted.replace("### Fixed\n\n" + entry.rstrip("\n") + "\n\n", "", 1)
    if after.get("release_headings_above") != ["## [Unreleased]"] or after.get("subsection") != "### Fixed" or lost != main_text.replace(EMPTY_UNRELEASED.search(main_text).group(0), "## [Unreleased]\n\n", 1):
        print("REFUSED: the result is not main's CHANGELOG.md plus the one block under [Unreleased]")
        return 1
    if current == wanted:
        print("already so:", after)
        return 0
    if args.check_only:
        print("WOULD WRITE:", after)
        return 1
    (tree / CHANGELOG).write_bytes(wanted.encode("utf-8"))
    print("written:", after, "sha256", hashlib.sha256(wanted.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())

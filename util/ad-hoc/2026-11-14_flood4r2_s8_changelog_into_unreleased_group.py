#!/usr/bin/env python3
"""
Put a carrier's CHANGELOG entry at the end of an EXISTING group (for example `### Fixed`) of the top `## [Unreleased]`.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, landing)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: landing the ml-propose and ml-tests carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_changelog_after_cut.py (the empty-[Unreleased] case)

WHY THIS EXISTS
A carrier's landing helper rebuilds CHANGELOG.md three-way, so its entry follows the entries it was written between.
After a release proposal those entries sit under the released heading, and the rebuilt entry lands there too. The
session-7 helper fixes that only while `## [Unreleased]` is EMPTY. On juniper-ml main 16f2512b it is not: juniper-ml#2548
filled it with `### Added` and `### Fixed`. This writes main's own CHANGELOG.md (the landing worktree's HEAD), byte
for byte, with the entry appended as the LAST item of the named group of the top `## [Unreleased]`, one blank line
before and after it. It never adds a second heading of the same name.

It refuses when: the entry is already on main; the first `## [` heading is not `## [Unreleased]`; the group heading
occurs other than exactly once in that section; the group does not end with a blank line; or the result is not
main plus exactly the entry block.

Usage:
    python3 <this> --tree <landing worktree> --entry <changelog_entry.txt> --group '### Fixed' [--check-only]
Exit 0 = CHANGELOG.md in the tree is main's plus the entry (written, or already so); 1 = refused (nothing written).
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the caller's own landing worktree
import sys
from pathlib import Path

CHANGELOG = "CHANGELOG.md"
UNRELEASED = "## [Unreleased]"


def build(main_text: str, entry: str, group: str) -> "tuple[str | None, str]":
    """Return (main's CHANGELOG with the entry appended to the group, "ok"), or (None, why) to refuse."""
    entry = entry.rstrip("\n") + "\n"
    if entry in main_text:
        return None, "the entry is already in main's CHANGELOG.md"
    lines = main_text.split("\n")
    releases = [i for i, line in enumerate(lines) if line.startswith("## [")]
    if not releases or lines[releases[0]] != UNRELEASED:
        return None, "the first release heading is not `## [Unreleased]`"
    start = releases[0]
    end = releases[1] if len(releases) > 1 else len(lines)
    heads = [i for i in range(start + 1, end) if lines[i] == group]
    if len(heads) != 1:
        return None, f"{group!r} occurs {len(heads)} times under the top [Unreleased] (need exactly 1)"
    stop = next((i for i in range(heads[0] + 1, end) if lines[i].startswith("### ")), end)
    if stop - 1 <= heads[0] or lines[stop - 1] != "":
        return None, "the group does not end with a blank line"
    insert_at = sum(len(line) + 1 for line in lines[:stop])
    wanted = main_text[:insert_at] + entry + "\n" + main_text[insert_at:]
    return wanted, "ok"


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
    parser.add_argument("--group", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    tree = args.tree.resolve()
    entry = args.entry.read_text(encoding="utf-8")
    main_bytes = subprocess.run(["git", "show", f"HEAD:{CHANGELOG}"], cwd=tree, capture_output=True, check=True).stdout  # nosec B603 B607
    main_text = main_bytes.decode("utf-8")
    current = (tree / CHANGELOG).read_text(encoding="utf-8")
    print("in the tree now:", placement(current, entry))
    wanted, why = build(main_text, entry, args.group)
    if wanted is None:
        print("REFUSED:", why)
        return 1
    after = placement(wanted, entry)
    block = entry.rstrip("\n") + "\n\n"
    if after.get("release_headings_above") != [UNRELEASED] or after.get("subsection") != args.group or wanted.replace(block, "", 1) != main_text:
        print("REFUSED: the result is not main's CHANGELOG.md plus the one entry at the end of the group")
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

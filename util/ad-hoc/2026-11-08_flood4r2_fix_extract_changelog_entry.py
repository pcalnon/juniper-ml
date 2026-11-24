#!/usr/bin/env python3
"""
Copy a carrier's CHANGELOG entry, exactly as it stands in the worktree, into its changelog_entry.txt deliverable.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: refreshed carrier deliverables after the validators' fixes)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt DELIVERABLES (changelog_entry.txt: "the exact text you put under [Unreleased]")

Usage:
  2026-11-08_flood4r2_fix_extract_changelog_entry.py <worktree> <first line prefix> <out file>

The entry starts at the one line that begins with <first line prefix> and runs to the line before the first blank
line, the next top-level bullet (a line starting "- ") or the next heading. The prefix must match exactly one line,
and that line must sit under the CURRENT top "## [Unreleased]" (before the next "## [" heading). Prints the entry's
line span and its section headings.
"""

from __future__ import annotations

import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    worktree, prefix, out = Path(argv[1]), argv[2], Path(argv[3])
    lines = (worktree / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(starts) != 1:
        print(f"prefix matches {len(starts)} lines")
        return 1
    start = starts[0]
    releases = [i for i, line in enumerate(lines) if line.startswith("## [")]
    if not releases or not lines[releases[0]].startswith("## [Unreleased]") or not (len(releases) == 1 or start < releases[1]) or start < releases[0]:
        print("the entry is not under the top ## [Unreleased]")
        return 1
    end = start + 1
    while end < len(lines) and lines[end].strip() and not lines[end].startswith(("- ", "#")):
        end += 1
    subsection = next((lines[i] for i in range(start, releases[0], -1) if lines[i].startswith("### ")), None)
    out.write_text("\n".join(lines[start:end]) + "\n", encoding="utf-8")
    print(f"entry: CHANGELOG.md lines {start + 1}-{end} ({end - start} lines) under {lines[releases[0]]!r} / {subsection!r}; written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

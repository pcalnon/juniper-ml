#!/usr/bin/env python3
"""
Put the agent guard 1.4.0 CHANGELOG entry where it belongs: the LAST entry of the top Unreleased "### Fixed" group.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: CHANGELOG.md; the carrier's changelog_entry.txt.

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_changelog_place.py <CHANGELOG.md> <entry.md>

Removes the entry whose first line starts with ENTRY_HEAD (if present; up to the next top-level "- **" bullet or
heading), then inserts <entry.md> after the last line of the "### Fixed" group under the first "## [Unreleased]"
heading, before the next "## " heading, with one blank line on each side. Refuses when the groups are not found.
"""

from __future__ import annotations

import sys
from pathlib import Path

ENTRY_HEAD = "- **The agent guard also reads each Bash command as bash 5.3 builds its words"


def main(argv: list) -> int:
    path, entry_path = Path(argv[1]), Path(argv[2])
    lines = path.read_text(encoding="utf-8").split("\n")
    entry = entry_path.read_text(encoding="utf-8").rstrip("\n").split("\n")
    if not entry[0].startswith(ENTRY_HEAD):
        raise SystemExit("the entry does not start with the expected head")
    starts = [k for k, line in enumerate(lines) if line.startswith(ENTRY_HEAD)]
    if len(starts) > 1:
        raise SystemExit("the entry appears %d times" % len(starts))
    if starts:
        start = starts[0]
        end = start + 1
        while end < len(lines) and not lines[end].startswith(("- **", "## ", "### ")):
            end += 1
        while end > start and lines[end - 1] == "":
            end -= 1
        del lines[start:end]
        if start < len(lines) and lines[start] == "" and start > 0 and lines[start - 1] == "":
            del lines[start]
    unreleased = lines.index("## [Unreleased]")
    nxt = next(k for k in range(unreleased + 1, len(lines)) if lines[k].startswith("## "))
    fixed = next(k for k in range(unreleased + 1, nxt) if lines[k] == "### Fixed")
    last = nxt - 1
    while last > fixed and lines[last] == "":
        last -= 1
    lines[last + 1 : last + 1] = [""] + entry
    path.write_text("\n".join(lines), encoding="utf-8")
    print("entry placed at line %d, before line %d (%s)" % (last + 3, last + 3 + len(entry), lines[last + 2 + len(entry)][:40] if last + 2 + len(entry) < len(lines) else "end"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

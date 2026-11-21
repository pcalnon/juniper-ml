#!/usr/bin/env python3
"""Insert one entry at the top of a CHANGELOG's ``[Unreleased]`` -> ``### Security`` subsection.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use; R-OBS-SC-2's second lock round, plan Security step 4)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Created:     2026-11-09
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The four consumer CHANGELOGs differ: juniper-data's and juniper-canopy's ``[Unreleased]`` already
hold a ``### Security`` subsection (the entry goes first in it), juniper-cascor's has none, and
juniper-recurrence's ``[Unreleased]`` is empty. A missing subsection is created as the LAST one
in ``[Unreleased]``, Keep a Changelog's order (Added, Changed, Deprecated, Removed, Fixed,
Security). Nothing outside ``[Unreleased]`` is touched, and the script refuses a file with no
``## [Unreleased]`` heading or an entry that is already present.

Usage: python3 util/ad-hoc/2026-11-09_lock_round_2_changelog_insert.py <CHANGELOG.md> <entry.md>
"""

from __future__ import annotations

import sys
from pathlib import Path


def insert(text: str, entry: str) -> str:
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.strip() == "## [Unreleased]"), None)
    if start is None:
        raise SystemExit("no '## [Unreleased]' heading; refusing")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    entry_lines = entry.strip("\n").split("\n")
    if entry_lines[0] in lines[start:end]:
        raise SystemExit("the entry's first line is already in [Unreleased]; refusing")
    security = next((i for i in range(start + 1, end) if lines[i].strip() == "### Security"), None)
    if security is not None:
        at = security + 1
        while at < end and not lines[at].strip():
            at += 1
        new = lines[:at] + entry_lines + [""] + lines[at:]
    else:
        at = end
        while at > start + 1 and not lines[at - 1].strip():
            at -= 1
        new = lines[:at] + ([""] if at > start + 1 else []) + ["### Security", ""] + entry_lines + [""] + lines[end:]
        if at == start + 1:
            new = lines[: start + 1] + ["", "### Security", ""] + entry_lines + [""] + lines[end:]
    return "\n".join(new)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    before = path.read_text(encoding="utf-8")
    after = insert(before, Path(sys.argv[2]).read_text(encoding="utf-8"))
    path.write_text(after, encoding="utf-8")
    added = len(after.split("\n")) - len(before.split("\n"))
    print(f"{path}: {added} line(s) inserted into [Unreleased] ### Security")
    return 0


if __name__ == "__main__":
    sys.exit(main())

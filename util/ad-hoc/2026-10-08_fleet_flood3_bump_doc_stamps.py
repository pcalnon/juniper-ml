#!/usr/bin/env python3
"""2026-10-08_fleet_flood3_bump_doc_stamps.py -- bump a consolidated doc's version stamps ONCE.

Project: juniper-ml
Sub-Project: fleet triage / Cursor-fleet PR-flood remediation (round 3, 2026-10-04..06)
Application: ad-hoc automation (draft-PR backlog disposition)
Author: Paul Calnon
License: MIT License
Created: 2026-10-08
Status: ad-hoc -- investigation (cursor-fleet PR disposition)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

WHY THIS EXISTS

Every fleet docs PR bumps each file's `**Version**` as though all of its siblings had landed first:
juniper-ml#2181 moves `docs/REFERENCE.md` from 0.6.59 to **0.6.82** -- twenty-three versions for one
change -- and every sibling rewrites the same line, which is why all of them conflict with each other
by construction. A consolidation carries their content and must bump each file exactly once, from the
value on the tree it is applied to, never from any fleet branch.

What it does per file: every `**Version**` stamp (both the `**Version:** x` and `**Version**: x`
spellings, header and footer) is set to (the highest version found in that file) + 1 patch, so a file
whose header and footer had drifted apart (`docs/QUICK_START.md`: 0.3.40 vs 0.3.39) is reconciled
rather than bumped twice; every `**Last Updated**` / `**Date**` stamp is set to `--date`. Version-
history TABLE rows are not touched -- add one by hand if the file keeps a history table.

Usage:
    2026-10-08_fleet_flood3_bump_doc_stamps.py --date 2026-10-08 <file.md> [...] [--check]

Exit: 0 on success; 1 when a file has no `**Version**` stamp; 2 on bad input.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VERSION = re.compile(r"^(\*\*Version(?::\*\*|\*\*:))(\s*)(\d+)\.(\d+)\.(\d+)(\s*)$", re.M)
DATED = re.compile(r"^(\*\*(?:Last Updated|Date)(?::\*\*|\*\*:))(\s*)(\d{4}-\d{2}-\d{2})(\s*)$", re.M)
# The client repos spell the date long-hand ("**Last Updated:** October 5, 2026"); keep each file's own style.
DATED_LONG = re.compile(r"^(\*\*(?:Last Updated|Date)(?::\*\*|\*\*:))(\s*)((?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4})(\s*)$", re.M)


_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def bump(text: str, date: str) -> tuple[str, str | None, str | None]:
    found = [tuple(int(g) for g in m.group(3, 4, 5)) for m in VERSION.finditer(text)]
    if not found:
        return text, None, None
    old = max(found)
    new = (old[0], old[1], old[2] + 1)
    new_s = ".".join(map(str, new))
    text = VERSION.sub(lambda m: f"{m.group(1)}{m.group(2)}{new_s}{m.group(6)}", text)
    text = DATED.sub(lambda m: f"{m.group(1)}{m.group(2)}{date}{m.group(4)}", text)
    y, mo, d = (int(x) for x in date.split("-"))
    long_date = f"{_MONTHS[mo - 1]} {d}, {y}"
    text = DATED_LONG.sub(lambda m: f"{m.group(1)}{m.group(2)}{long_date}{m.group(4)}", text)
    return text, ".".join(map(str, old)), new_s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--date", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.date):
        print(f"bad --date {args.date!r}", file=sys.stderr)
        return 2
    rc = 0
    for name in args.files:
        path = Path(name)
        text = path.read_text(encoding="utf-8")
        new_text, old, new = bump(text, args.date)
        if old is None:
            print(f"{name}: NO **Version** stamp")
            rc = 1
            continue
        print(f"{name}: {old} -> {new}")
        if not args.check:
            path.write_text(new_text, encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())

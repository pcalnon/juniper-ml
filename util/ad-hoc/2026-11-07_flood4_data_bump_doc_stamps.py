#!/usr/bin/env python3
"""
Bump a consolidated juniper-data doc's version stamps ONCE from the value on the tree (flood-4 adaptation).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data docs carrier)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-08_fleet_flood3_bump_doc_stamps.py (copied and adapted); flood-4 common brief rule 8

Every fleet docs PR rewrites the stamps as though its siblings had landed first (juniper-data#511 jumps
0.4.3 -> 0.4.8; #515 moved docs/REFERENCE.md's header to 0.4.6 and left its footer at 0.4.4). The carrier
drops those hunks and bumps each touched file exactly once, from the highest version already in that file.

Adaptation over the flood-3 script: juniper-data's docs/DEVELOPER_CHEATSHEET.md keeps its stamps on ONE line,
`**Version**: 0.4.4 | **Date**: 2026-10-08 | **Project**: ...`, which the flood-3 end-anchored pattern does not
match. That inline form is handled here. Template placeholders (`**Version:** X.Y.Z`, `Month DD, YYYY`) never
match the digit patterns and are left alone.

Usage:
    2026-11-07_flood4_data_bump_doc_stamps.py --date 2026-11-07 <file.md> [...] [--check]

Prints `<file>: <old> -> <new> (<n> version stamps, <m> date stamps)`. Exit 0 on success; 1 when a file has no
version stamp; 2 on bad input.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VERSION = re.compile(r"^(\*\*Version(?::\*\*|\*\*:))(\s*)(\d+)\.(\d+)\.(\d+)(\s*)$", re.M)
INLINE = re.compile(r"^(\*\*Version\*\*:\s*)(\d+)\.(\d+)\.(\d+)(\s*\|\s*\*\*Date\*\*:\s*)(\d{4}-\d{2}-\d{2})(\s*\|)", re.M)
DATED = re.compile(r"^(\*\*(?:Last Updated|Date)(?::\*\*|\*\*:))(\s*)(\d{4}-\d{2}-\d{2})(\s*)$", re.M)
DATED_LONG = re.compile(r"^(\*\*(?:Last Updated|Date)(?::\*\*|\*\*:))(\s*)((?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4})(\s*)$", re.M)
_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def bump(text: str, date: str) -> tuple[str, str | None, str | None, int, int]:
    found = [tuple(int(g) for g in m.group(3, 4, 5)) for m in VERSION.finditer(text)]
    found += [tuple(int(g) for g in m.group(2, 3, 4)) for m in INLINE.finditer(text)]
    if not found:
        return text, None, None, 0, 0
    old = max(found)
    new_s = f"{old[0]}.{old[1]}.{old[2] + 1}"
    y, mo, d = (int(x) for x in date.split("-"))
    long_date = f"{_MONTHS[mo - 1]} {d}, {y}"
    text, n_v = VERSION.subn(lambda m: f"{m.group(1)}{m.group(2)}{new_s}{m.group(6)}", text)
    text, n_i = INLINE.subn(lambda m: f"{m.group(1)}{new_s}{m.group(5)}{date}{m.group(7)}", text)
    text, n_d = DATED.subn(lambda m: f"{m.group(1)}{m.group(2)}{date}{m.group(4)}", text)
    text, n_l = DATED_LONG.subn(lambda m: f"{m.group(1)}{m.group(2)}{long_date}{m.group(4)}", text)
    return text, ".".join(map(str, old)), new_s, n_v + n_i, n_d + n_l + n_i


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
        new_text, old, new, n_versions, n_dates = bump(text, args.date)
        if old is None:
            print(f"{name}: NO version stamp")
            rc = 1
            continue
        print(f"{name}: {old} -> {new} ({n_versions} version stamps, {n_dates} date stamps)")
        if not args.check:
            path.write_text(new_text, encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main())

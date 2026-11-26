#!/usr/bin/env python3
"""
Join a hard-wrapped Markdown PR body into one line per paragraph and per list item.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition, session 15: landing the session-14 carriers)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (the session-15 landings' PR bodies)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (rulings 23, 27, 28)

Why
---
GitHub renders a single newline inside a pull-request description as a line break, so a body wrapped at a fixed
width shows ragged lines. The builders write their texts wrapped; this joins them before the PR is opened.

What it does
------------
Reads INPUT, writes OUTPUT. A line that continues the paragraph or list item above it (not blank, not a heading,
not a list-item start, not a table row, not inside a fenced code block) is joined to it with one space. Headings,
blank lines, table rows and fenced blocks are copied unchanged. A list item's indentation is kept; a continuation
line's own indentation is dropped. Prints the line counts before and after.

Usage
-----
    python3 util/ad-hoc/2026-11-26_flood4_s15_unwrap_pr_body.py INPUT OUTPUT
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LIST_START = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def unwrap(text: str) -> str:
    out: list[str] = []
    joinable = False
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            joinable = False
            continue
        if in_fence or not stripped or stripped.startswith("#") or stripped.startswith("|"):
            out.append(line)
            joinable = False
            continue
        if LIST_START.match(line):
            out.append(line.rstrip())
            joinable = True
            continue
        if joinable:
            out[-1] = out[-1].rstrip() + " " + stripped
            continue
        out.append(line.rstrip())
        joinable = True
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    source = Path(argv[1]).read_text(encoding="utf-8")
    result = unwrap(source)
    Path(argv[2]).write_text(result, encoding="utf-8")
    print(f"{len(source.splitlines())} lines -> {len(result.splitlines())} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

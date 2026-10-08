#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice, group G3)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use. Read a unified diff and write it back WITHOUT the hunks whose every changed line is a
# documentation stamp (**Version**, **Last Updated**, **Date** in either bold-colon style). The
# consolidation assembler bumps each file's stamps once; carrying the fleet PRs' stamp edits would
# only manufacture conflicts. A hunk that mixes a stamp with content is kept whole and reported, so a
# stamp edit inside a content hunk is visible rather than silently carried.
# Usage: 2026-10-08_flood3_canopy_docs_g3_strip_stamps.py <in.diff> <out.diff>
"""Drop stamp-only hunks from a unified diff."""

from __future__ import annotations

import re
import sys
from pathlib import Path

STAMP = re.compile(r"^[+-]\*\*(Version|Last Updated|Date)(\*\*:|:\*\*)")


def main(argv: list[str]) -> int:
    src, dst = Path(argv[0]), Path(argv[1])
    lines = src.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    header: list[str] = []
    hunk: list[str] = []
    kept_hunks_in_file = 0
    dropped = mixed = 0

    def flush_hunk() -> None:
        nonlocal hunk, dropped, mixed, kept_hunks_in_file
        if not hunk:
            return
        changed = [ln for ln in hunk[1:] if ln.startswith(("+", "-"))]
        if changed and all(STAMP.match(ln) for ln in changed):
            dropped += 1
        else:
            if any(STAMP.match(ln) for ln in changed):
                mixed += 1
                print(f"MIXED hunk kept: {hunk[0].strip()}")
            out.extend(header if kept_hunks_in_file == 0 else [])
            out.extend(hunk)
            kept_hunks_in_file += 1
        hunk = []

    for ln in lines:
        if ln.startswith("diff --git"):
            flush_hunk()
            header = [ln]
            kept_hunks_in_file = 0
        elif ln.startswith("@@"):
            flush_hunk()
            hunk = [ln]
        elif hunk:
            hunk.append(ln)
        else:
            header.append(ln)
    flush_hunk()
    dst.write_text("".join(out), encoding="utf-8")
    print(f"dropped {dropped} stamp-only hunks; {mixed} mixed hunks kept")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

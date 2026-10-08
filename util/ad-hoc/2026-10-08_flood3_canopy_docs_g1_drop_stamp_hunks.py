#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice, fork G1)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use. Read a unified diff and write it back without the hunks whose every changed line is a
# documentation stamp (**Version**, **Last Updated**, **Date**, in bold-colon or bold-then-colon form).
# The consolidation assembler bumps each file's stamps once, so a PR's own stamp edits are noise.
# Optionally drop whole files (--drop-file PATH, repeatable). Prints what it dropped to stderr.
# Usage: 2026-10-08_flood3_canopy_docs_g1_drop_stamp_hunks.py <in.diff> <out.diff> [--drop-file PATH ...]
"""Drop stamp-only hunks (and named files) from a unified diff."""

from __future__ import annotations

import re
import sys
from pathlib import Path

STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)(\*\*:|:\*\*)")


def split_files(lines: list[str]) -> list[list[str]]:
    files, cur = [], []
    for ln in lines:
        if ln.startswith("diff --git ") and cur:
            files.append(cur)
            cur = []
        cur.append(ln)
    if cur:
        files.append(cur)
    return files


def main(argv: list[str]) -> int:
    src, dst, rest = Path(argv[0]), Path(argv[1]), argv[2:]
    drop_files = {rest[i + 1] for i, a in enumerate(rest) if a == "--drop-file"}
    out: list[str] = []
    for block in split_files(src.read_text(encoding="utf-8").splitlines(keepends=True)):
        header_end = next(i for i, ln in enumerate(block) if ln.startswith("@@"))
        header, body = block[:header_end], block[header_end:]
        path = next(ln[6:].strip() for ln in header if ln.startswith("+++ b/"))
        if path in drop_files:
            print(f"dropped file {path}", file=sys.stderr)
            continue
        hunks, cur = [], []
        for ln in body:
            if ln.startswith("@@") and cur:
                hunks.append(cur)
                cur = []
            cur.append(ln)
        if cur:
            hunks.append(cur)
        kept = []
        for h in hunks:
            changed = [ln[1:] for ln in h[1:] if ln[:1] in "+-"]
            if changed and all(STAMP.match(c) for c in changed):
                print(f"dropped stamp hunk {path} {h[0].strip()[:60]}", file=sys.stderr)
                continue
            kept.append(h)
        if kept:
            out.extend(header)
            for h in kept:
                out.extend(h)
    dst.write_text("".join(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

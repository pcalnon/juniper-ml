#!/usr/bin/env python3
"""
Print the last checkpoint lines of each running or killed agent, from the PROGRESS.txt files a list names.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: eight agents were killed at once by a usage limit)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt ("CHECKPOINT AS YOU GO": every agent appends to PROGRESS.txt)

Usage:
  2026-11-11_flood4r2_s5_checkpoints.py <list file> [--lines N] [--chars N]

<list file> holds one entry per line, ``<label> <absolute or relative path to a PROGRESS.txt>``; blank lines and lines
that start with ``#`` are skipped. For each entry it prints the label, the file's line count and modification time
(UTC), and its last N lines (default 2), each cut to ``--chars`` characters (default 400). A missing file is reported,
not an error. It reads the listed files and writes nothing. Exit 0 always: this is a reading aid.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path


def option(argv: list[str], name: str, default: int) -> int:
    return int(argv[argv.index(name) + 1]) if name in argv and argv.index(name) + 1 < len(argv) else default


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 0
    lines_wanted = option(argv, "--lines", 2)
    chars = option(argv, "--chars", 400)
    for raw in Path(argv[1]).read_text(encoding="utf-8").splitlines():
        entry = raw.strip()
        if not entry or entry.startswith("#"):
            continue
        label, _, location = entry.partition(" ")
        path = Path(location.strip())
        if not path.is_file():
            print(f"== {label}: NO PROGRESS FILE ({path})")
            continue
        text = path.read_text(encoding="utf-8", errors="replace").splitlines()
        stamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).strftime("%m-%d %H:%MZ")
        print(f"== {label}: {len(text)} lines, last written {stamp}")
        for line in text[-lines_wanted:]:
            print("   " + line[:chars] + (" …" if len(line) > chars else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

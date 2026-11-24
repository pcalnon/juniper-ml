#!/usr/bin/env python3
"""Append one clock-stamped line to a builder's PROGRESS.txt.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     juniper-data#530, juniper-data-client#260
Version:     0.1.0
License:     MIT License

The stamp comes from the clock (UTC, second resolution), never from the caller, so it cannot be typed from memory.

Usage:
    python3 util/ad-hoc/2026-11-14_flood4r2_r35-data_progress.py <PROGRESS.txt> <text> [<text> ...]

The words after the file are joined with one space. The file is created if it does not exist; its directory must.
"""

from __future__ import annotations

import datetime
import pathlib
import sys


def main(argv: list[str]) -> int:
    """Append the stamped line and echo it."""
    if len(argv) < 2:
        print("usage: <PROGRESS.txt> <text> [<text> ...]", file=sys.stderr)
        return 2
    path = pathlib.Path(argv[0])
    if not path.parent.is_dir():
        print(f"refusing: {path.parent} is not a directory", file=sys.stderr)
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {' '.join(argv[1:]).strip()}\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

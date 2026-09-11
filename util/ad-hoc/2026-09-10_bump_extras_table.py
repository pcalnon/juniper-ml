#!/usr/bin/env python3
"""Rewrite the Min Version cell of a split-column extras table, keyed on the package name.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-10
Version:     0.1.0
License:     MIT License
Status:      single-use (decision-11 release train, juniper-ml 0.8.0 floors)

Why this exists
---------------
``docs/REFERENCE.md``'s "Available Extras" table is split-column: the extra name appears once
and its remaining packages sit on continuation rows with an empty first cell. A whole-line
substitution therefore has to guess whether a given package is the FIRST row of its group
(``| `servers` | `juniper-canopy` | ...``) or a continuation (``| | `juniper-cascor` | ...``),
and guessing wrong silently matches nothing -- which is how a floor bump quietly skips a row.

This keys on the package-name cell instead of the line shape, and requires each package to be
rewritten EXACTLY once, so a missed or duplicated row is an error rather than a silent no-op.
The old value must also match, so a row already bumped by someone else is left alone loudly.

Usage
-----
    python3 util/ad-hoc/2026-09-10_bump_extras_table.py --file docs/REFERENCE.md \\
        --bump 'juniper-canopy:`>=0.5.0`:`>=0.7.0`' ...
"""

from __future__ import annotations

import argparse
import io
import re
import sys

_PKG_CELL = re.compile(r"`([A-Za-z0-9._-]+)`")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    ap.add_argument(
        "--bump",
        action="append",
        required=True,
        metavar="PKG:OLD:NEW",
        help="package name, its current Min Version cell, and the replacement (colon-separated)",
    )
    args = ap.parse_args()

    want: dict = {}
    for spec in args.bump:
        pkg, old, new = spec.split(":", 2)
        want[pkg] = (old, new)

    lines = io.open(args.file, encoding="utf-8").read().splitlines(True)
    done = {k: 0 for k in want}

    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        m = _PKG_CELL.fullmatch(cells[2])
        if not m:
            continue
        name = m.group(1)
        if name not in want:
            continue
        old, new = want[name]
        if cells[3] != old:
            continue
        lines[i] = line.replace(old, new)
        done[name] += 1

    bad = {k: v for k, v in done.items() if v != 1}
    if bad:
        for k, v in sorted(bad.items()):
            print(f"error: {k} rewritten {v} time(s), expected exactly 1", file=sys.stderr)
        return 1

    io.open(args.file, "w", encoding="utf-8").writelines(lines)
    print(f"{args.file}: {len(done)} rows updated, each exactly once")
    return 0


if __name__ == "__main__":
    sys.exit(main())

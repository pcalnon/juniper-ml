#!/usr/bin/env python3
"""
Count, per file, the lines that match the flood-4 briefs' plain-text patterns for the CodeQL trap shapes, beside a baseline copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2: Overtoad ruling 17, "cascor: stop-then-start", carrier round 2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt section 7 ("grep for them before you finish");
         util/ad-hoc/2026-11-11_flood4r2_n3-r3_codeql_shapes.py, the syntax screen this sits beside

A line count per pattern and file, nothing more: the syntax screen is the one that reads the
code. A pattern can match inside a string literal (the paused-fit mutation check holds
``if True:`` in its mutant texts), so a count is compared with the same file under
``--baseline-root`` when one is given, and a file is reported NEW only for lines the baseline
copy does not hold. The four patterns: an ``except`` that names ``BaseException``; an
``except`` with no class at all; a statement that is only ``await <name>``; an ``if`` /
``elif`` / ``while`` on a literal. (They are spelled here, and built below, so that this file
does not match its own patterns.)

Usage:
  2026-11-12_flood4r2_r17-cascor_shape_greps.py [--root <dir> [--baseline-root <dir>]] <files...>
Exit: 0 when no file has a matching line its baseline copy lacks; 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERNS = (
    ("an except of the base exception class", re.compile(r"except\s+Base" + r"Exception")),
    ("an except with no class", re.compile(r"except\s*:")),
    ("bare await statement", re.compile(r"^\s+await [A-Za-z_][A-Za-z_0-9]*\s*$")),
    ("constant conditional", re.compile(r"^\s*(if|elif|while) (True|False|None|[0-9]+)\s*:")),
)


def _matches(path: Path, pattern: re.Pattern) -> list:
    if not path.is_file():
        return []
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if pattern.search(line)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--root", type=Path, help="files are relative to this directory")
    parser.add_argument("--baseline-root", type=Path, help="the same relative files in a baseline tree")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    new_total = 0
    for name in args.files:
        path = (args.root / name) if args.root else Path(name)
        for label, pattern in PATTERNS:
            found = _matches(path, pattern)
            baseline = _matches(args.baseline_root / name, pattern) if args.baseline_root else []
            new = [line for line in found if line not in baseline]
            new_total += len(new)
            print(f"{path.name}: {label}: {len(found)} line(s), {len(new)} new" + (f" (baseline {len(baseline)})" if args.baseline_root else ""))
            for line in new:
                print(f"    NEW: {line.strip()}")
    print(f"new matching lines: {new_total}")
    return 1 if new_total else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. End-to-end carry check for the consolidation: for each source diff, every
# line it ADDS must be present in the result tree's copy of the same file. Comparison unit is the
# whitespace-collapsed line, so a re-wrapped or re-indented line still matches; a re-WORDED line does
# not, and is listed for classification. Stamp lines (**Version**, **Last Updated**, **Date**) are
# counted separately, never silently skipped.
# Usage: ..._carry_check.py --repo <wt> [--show N] <diff> [<diff> ...]
"""Report, per source diff, which added lines are absent from the result."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STAMP = re.compile(r"^\*\*(Version|Last Updated|Date)\*?\*?:?\*?\*?:?")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def added_lines(diff_text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cur = None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            cur = line[6:] if line.startswith("+++ b/") else None
            continue
        if cur and line.startswith("+") and not line.startswith("+++"):
            out.setdefault(cur, []).append(line[1:])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--show", type=int, default=12)
    ap.add_argument("diffs", nargs="+")
    args = ap.parse_args()
    for d in args.diffs:
        adds = added_lines(Path(d).read_text(encoding="utf-8"))
        total = present = stamps = blank = 0
        missing: list[tuple[str, str]] = []
        for path, lines in adds.items():
            target = Path(args.repo) / path
            have = set()
            if target.exists():
                have = {norm(x) for x in target.read_text(encoding="utf-8").splitlines()}
            for ln in lines:
                n = norm(ln)
                if not n:
                    blank += 1
                    continue
                total += 1
                if STAMP.match(n):
                    stamps += 1
                    continue
                if n in have:
                    present += 1
                else:
                    missing.append((path, n))
        content = total - stamps
        pct = (100.0 * present / content) if content else 100.0
        print(f"== {Path(d).name}: {content} content lines added, {present} present ({pct:.0f}%), {len(missing)} absent; {stamps} stamp lines")
        for path, n in missing[: args.show]:
            print(f"   ABSENT {path}: {n[:150]}")
        if len(missing) > args.show:
            print(f"   ... {len(missing) - args.show} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())

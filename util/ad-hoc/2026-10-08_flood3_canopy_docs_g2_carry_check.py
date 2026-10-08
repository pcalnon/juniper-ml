#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice, group G2)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use, read-only. End-to-end carry check for a docs consolidation: for every line a source
# PR diff ADDS, report whether the same line (whitespace-collapsed) is present in the result file
# in <repo>'s working tree. Lines not found are printed so each can be classified by hand as
# CORRECTED (deliberately rewritten) or DROPPED (stamp / re-wrap noise). Per-hunk success cannot
# see content that never made it into a hunk; this can.
# Usage: 2026-10-08_flood3_canopy_docs_g2_carry_check.py <repo> <pr.diff> [<pr.diff> ...]
"""Which added lines of each source diff are absent from the consolidated working tree."""

from __future__ import annotations

import sys
from pathlib import Path


def norm(s: str) -> str:
    return " ".join(s.split())


def main(argv: list[str]) -> int:
    repo = Path(argv[0])
    for diff_path in argv[1:]:
        current = None
        cache: dict[Path, set[str]] = {}
        added = present = 0
        misses: list[str] = []
        for line in Path(diff_path).read_text(encoding="utf-8").splitlines():
            if line.startswith("+++ b/"):
                current = repo / line[6:]
                continue
            if not line.startswith("+") or line.startswith("+++") or current is None:
                continue
            text = norm(line[1:])
            if not text:
                continue
            added += 1
            if current not in cache:
                cache[current] = {norm(x) for x in current.read_text(encoding="utf-8").splitlines()} if current.is_file() else set()
            if text in cache[current]:
                present += 1
            else:
                misses.append(f"  {current.relative_to(repo)}: {text[:200]}")
        print(f"== {Path(diff_path).name}: {added} non-blank added lines, {present} present verbatim, {len(misses)} not")
        print("\n".join(misses))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

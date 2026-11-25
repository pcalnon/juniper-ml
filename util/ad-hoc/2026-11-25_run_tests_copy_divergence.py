#!/usr/bin/env python3
"""
Measure how far a repo's copy of util/run_tests.py has diverged from juniper-ml's, section by section.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- the run_tests rollout: evidence for the engine-extraction proposal the Overtoad asked for after
        two copies (ruling of 2026-11-25)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/run_tests.py (juniper-ml#2629); juniper-recurrence#240 (the first copy)

The runner is laid out in sections headed by a ruled comment (``# Reading the workflows``, ``# Lanes and jobs``,
``# Selection``, ``# Environment``, ``# Preflight``, ``# Planning``, ``# Running``, ``# Output``, ``# The command
line``), after a preamble (docstring, imports, constants). For each section this prints the lines of the original,
the lines of the copy, and how many lines a unified diff adds and removes there, so the sections that stayed
identical (the engine) and those that changed (the repo adapter) can be read off.

Usage: ``python3 util/ad-hoc/2026-11-25_run_tests_copy_divergence.py ORIGINAL COPY [COPY ...]``, with local files
(use ``2026-11-25_run_tests_rollout_sibling_worktree.py show`` to get a copy from a sibling's main).
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

HEADER = re.compile(r"^# -{20,}\n# (?P<name>[^\n]+)\n# -{20,}\n", re.M)


def sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    marks = [(match.start(), match.group("name").strip()) for match in HEADER.finditer(text)]
    starts = [(0, "preamble"), *marks]
    for index, (start, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        out[name] = text[start:end].splitlines()
    return out


def compare(original: Path, copy: Path) -> None:
    left = sections(original.read_text(encoding="utf-8"))
    right = sections(copy.read_text(encoding="utf-8"))
    print(f"== {copy}  vs  {original}")
    print(f"   {'section':<22} {'orig':>6} {'copy':>6} {'+':>6} {'-':>6}  verdict")
    totals = [0, 0, 0, 0]
    for name in [*left, *(key for key in right if key not in left)]:
        a, b = left.get(name, []), right.get(name, [])
        added = removed = 0
        for line in difflib.unified_diff(a, b, lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1
        verdict = "identical" if not (added or removed) else ("changed" if a and b else ("only in copy" if b else "only in original"))
        print(f"   {name:<22} {len(a):>6} {len(b):>6} {added:>6} {removed:>6}  {verdict}")
        for index, value in enumerate((len(a), len(b), added, removed)):
            totals[index] += value
    print(f"   {'TOTAL':<22} {totals[0]:>6} {totals[1]:>6} {totals[2]:>6} {totals[3]:>6}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    original = Path(argv[0])
    for copy in argv[1:]:
        compare(original, Path(copy))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

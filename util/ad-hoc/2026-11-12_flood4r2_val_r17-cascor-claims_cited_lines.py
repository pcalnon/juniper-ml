#!/usr/bin/env python3
"""
Print the source lines a carrier's texts cite as ``file:line``, each beside the pattern the text says is there.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2 validation: Overtoad ruling 17, "cascor: stop-then-start", claims lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_VALIDATE_R2.txt; tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt

Reads a JSON spec: a list of {"tree": "<label>", "file": "<repo path>", "line": N, "expect": "<regex>"}.
``--tree <label>=<checkout>`` maps each label to a directory. For every entry the script prints the
line, whether the regex matches it, and, when it does not, the nearest line within ``--window`` that does.

Usage:
  2026-11-12_flood4r2_val_r17-cascor-claims_cited_lines.py --spec <spec.json> --tree main=<dir> --tree carrier=<dir> [--window 8]
Exit: 0 when every entry matches on its cited line, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _nearest(lines: list[str], index: int, pattern: re.Pattern[str], window: int) -> int | None:
    """Return the 1-based number of the closest line within ``window`` of ``index`` that matches."""
    best = None
    for offset in range(1, window + 1):
        for candidate in (index - offset, index + offset):
            if 0 <= candidate < len(lines) and pattern.search(lines[candidate]):
                best = candidate + 1
                break
        if best is not None:
            break
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--tree", action="append", default=[], help="label=directory")
    parser.add_argument("--window", type=int, default=8)
    args = parser.parse_args()
    trees = dict(item.split("=", 1) for item in args.tree)
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    cache: dict[Path, list[str]] = {}
    misses = 0
    for entry in spec:
        path = Path(trees[entry["tree"]]) / entry["file"]
        if path not in cache:
            cache[path] = path.read_text(encoding="utf-8").splitlines()
        lines = cache[path]
        number = int(entry["line"])
        pattern = re.compile(entry["expect"])
        text = lines[number - 1] if 0 < number <= len(lines) else "<no such line>"
        hit = bool(pattern.search(text))
        verdict = "OK  "
        note = ""
        if not hit:
            misses += 1
            verdict = "MISS"
            near = _nearest(lines, number - 1, pattern, args.window)
            note = f"   [pattern found at :{near}]" if near else "   [pattern not within the window]"
        print(f"{verdict} {entry['tree']:7s} {entry['file']}:{number}  /{entry['expect']}/{note}\n        | {text.strip()[:200]}")
    print(f"\n{len(spec)} cited lines, {misses} miss(es)")
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())

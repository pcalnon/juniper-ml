#!/usr/bin/env python3
"""
Check a validator's text_fixes.json: every ``old`` occurs exactly once in its file, and the fixes apply together.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 round 2 validation: Overtoad ruling 17, "cascor: stop-then-start", claims lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_VALIDATE_R2.txt (text fixes are EXACT old -> new, old occurring once)

``file`` is ``COPY/<repo path>`` (resolved under ``--copy``) or ``DELIVERABLES/<name>`` (under
``--deliverables``). Nothing is written to either tree: the fixes are applied in memory, in file order.
For each file the script reports the count of every ``old`` at the moment it is applied, whether the
result parses (Python files, with ``ast``), and whether each edited Markdown table row keeps its number
of cell separators.

Usage:
  2026-11-12_flood4r2_val_r17-cascor-claims_check_text_fixes.py --fixes <text_fixes.json> --copy <checkout> --deliverables <dir>
Exit: 0 when every ``old`` occurred exactly once and every Python result parses, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def _row_pipes(text: str, needle: str) -> list[int]:
    """Return the ``|`` counts of the lines that hold the first line of ``needle``."""
    first = needle.splitlines()[0]
    return [line.count("|") for line in text.splitlines() if first in line and line.lstrip().startswith("|")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--fixes", required=True, type=Path)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--deliverables", required=True, type=Path)
    args = parser.parse_args()
    roots = {"COPY": args.copy, "DELIVERABLES": args.deliverables}
    fixes = json.loads(args.fixes.read_text(encoding="utf-8"))
    texts: dict[str, str] = {}
    bad = 0
    for fix in fixes:
        name = fix["file"]
        root, relative = name.split("/", 1)
        if name not in texts:
            texts[name] = (roots[root] / relative).read_text(encoding="utf-8")
        count = texts[name].count(fix["old"])
        pipes_before = _row_pipes(texts[name], fix["old"])
        verdict = "OK  " if count == 1 else "BAD "
        if count != 1:
            bad += 1
        else:
            texts[name] = texts[name].replace(fix["old"], fix["new"])
        pipes_after = _row_pipes(texts[name], fix["new"])
        note = "" if pipes_before == pipes_after else f"  [table separators {pipes_before} -> {pipes_after}]"
        print(f"{verdict} {fix['finding']:4s} {name}: old occurs {count}x{note}")
    for name, text in texts.items():
        if name.endswith(".py"):
            try:
                ast.parse(text)
                print(f"PARSE OK   {name}")
            except SyntaxError as exc:
                bad += 1
                print(f"PARSE FAIL {name}: {exc}")
        longest = max(len(line) for line in text.splitlines())
        print(f"           {name}: longest line after the fixes is {longest} characters")
    print(f"\n{len(fixes)} fixes over {len(texts)} files; {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

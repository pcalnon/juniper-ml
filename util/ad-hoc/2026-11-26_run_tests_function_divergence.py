#!/usr/bin/env python3
"""
Compare copies of util/run_tests.py function by function: what the engine extraction can share as-is.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-26
Status: ad-hoc -- the run_tests rollout's engine-extraction proposal
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-25_run_tests_copy_divergence.py (the same comparison by section)

Each top-level ``def``, ``class`` and assignment of each FILE is one unit, compared by its source text with trailing
whitespace removed. A unit is ``same`` when every copy holding it has the same text, ``N/M`` when N of the M copies
holding it agree with the first, and ``absent`` in a copy without it. The summary counts lines: how much of each
copy is shared verbatim with every other copy, and how much varies.

Usage: python3 util/ad-hoc/2026-11-26_run_tests_function_divergence.py LABEL=FILE LABEL=FILE [LABEL=FILE ...] [--all]
``--all`` prints every unit; by default only the units that are not the same everywhere.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def units(path: Path) -> dict[str, tuple[str, int]]:
    """name -> (normalised source, line count) for each top-level def, class and assignment."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found: dict[str, tuple[str, int]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {node.name}"
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [target.id for target in targets if isinstance(target, ast.Name)]
            if not names:
                continue
            name = f"= {names[0]}"
        else:
            continue
        start = min([node.lineno, *(decorator.lineno for decorator in getattr(node, "decorator_list", []))])
        text = "\n".join(line.rstrip() for line in source.splitlines()[start - 1 : node.end_lineno])
        found[name] = (text, node.end_lineno - start + 1)
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("copies", nargs="+", metavar="LABEL=FILE")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    labels: list[str] = []
    tables: list[dict[str, tuple[str, int]]] = []
    for item in args.copies:
        label, _, file = item.partition("=")
        labels.append(label)
        tables.append(units(Path(file)))
    names = list(dict.fromkeys(name for table in tables for name in table))
    shared_lines = [0] * len(tables)
    varied_lines = [0] * len(tables)
    print(f"{'unit':44} {'verdict':10} " + " ".join(f"{label:>8}" for label in labels))
    for name in names:
        present = [table.get(name) for table in tables]
        held = [entry for entry in present if entry is not None]
        same = all(entry[0] == held[0][0] for entry in held) and len(held) == len(tables)
        for index, entry in enumerate(present):
            if entry is not None:
                (shared_lines if same else varied_lines)[index] += entry[1]
        if same and not args.all:
            continue
        agree = sum(1 for entry in held if entry[0] == held[0][0])
        verdict = "same" if same else (f"{agree}/{len(held)}" if len(held) == len(tables) else "partial")
        cells = " ".join(f"{(str(entry[1]) if entry else 'absent'):>8}" for entry in present)
        print(f"{name[:44]:44} {verdict:10} {cells}")
    print()
    for label, shared, varied in zip(labels, shared_lines, varied_lines):
        total = shared + varied
        print(f"{label}: {shared} lines in units the same in every copy, {varied} in units that vary ({shared * 100 // max(total, 1)}% shared)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

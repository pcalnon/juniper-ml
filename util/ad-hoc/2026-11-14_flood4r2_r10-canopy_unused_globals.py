#!/usr/bin/env python3
"""
List module-level names that a Python file assigns and never reads, and locals assigned twice before any read.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-canopy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); the session-6 addendum's
         seven CodeQL shapes, which util/ad-hoc/2026-10-05_codeql_python_prescreen.py does not model

WHY THIS EXISTS
Two of the CodeQL shapes that block a merge are an unused module-level global and a local assigned twice before any
read. The port's shipped scripts carry long constant tables adapted from another repository's copy, where a constant
left behind by a removed mutation is easy to miss. This parses each file with `ast` (it runs nothing), and prints each
module-level name that is assigned but never loaded anywhere in the file, and each function-local name whose first two
statements-level assignments come with no load between them. Exit 0 when it finds neither; 1 otherwise.

Usage:
    python3 <this> <file.py> [<file.py> ...]
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def module_unused(tree: ast.Module) -> list[str]:
    assigned = set()
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
        for target in targets:
            if isinstance(target, ast.Name):
                assigned.add(target.id)
    loaded = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return sorted(name for name in assigned - loaded if name not in ("__all__",))


def double_assignments(tree: ast.Module) -> list[str]:
    found = []
    for func in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        events: list[tuple[int, int, str, str]] = []
        for n in ast.walk(func):
            if isinstance(n, ast.Name):
                events.append((n.lineno, n.col_offset, n.id, "store" if isinstance(n.ctx, ast.Store) else "load"))
        last: dict[str, str] = {}
        for _, _, name, kind in sorted(events):
            if kind == "store" and last.get(name) == "store":
                found.append(f"{func.name}: {name}")
            last[name] = kind
    return sorted(set(found))


def main() -> int:
    bad = 0
    for arg in sys.argv[1:]:
        tree = ast.parse(Path(arg).read_text(encoding="utf-8"))
        unused = module_unused(tree)
        doubles = double_assignments(tree)
        print(f"{arg}: unused module-level {unused or 'none'}; stored twice before a read {doubles or 'none'}")
        bad += bool(unused) + bool(doubles)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Report module-level names that a Python file binds and never reads (CodeQL's py/unused-global-variable shape, which
util/ad-hoc/2026-10-05_codeql_python_prescreen.py does not model).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: screening the session's helpers before they ship)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (the four CodeQL shapes the prescreen misses)

Usage:
  2026-11-09_flood4r2_land_unused_globals.py <file.py> ...

A name counts as bound at module level when a top-level Assign / AnnAssign / AugAssign target is a plain Name.
It counts as read when any Name node with a Load context, an ``__all__`` string, or a ``global`` statement inside a
function names it. Dunder names and ``_`` are ignored. Exit 0 = no unused global; 1 = at least one (each printed).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def unused_globals(source: str) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    bound: dict[str, int] = {}
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
        for target in targets:
            for name_node in ast.walk(target):
                if isinstance(name_node, ast.Name):
                    bound.setdefault(name_node.id, node.lineno)
    read: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            read.add(node.id)
        elif isinstance(node, ast.Global):
            read.update(node.names)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            read.update(elt.value for elt in ast.walk(node.value) if isinstance(elt, ast.Constant) and isinstance(elt.value, str))
    return sorted((line, name) for name, line in bound.items() if name not in read and name != "_" and not (name.startswith("__") and name.endswith("__")))


def main(argv: list[str]) -> int:
    hits = 0
    for arg in argv:
        for line, name in unused_globals(Path(arg).read_text(encoding="utf-8")):
            print(f"{arg}:{line}: unused global {name}")
            hits += 1
    print(f"{hits} unused global(s) in {len(argv)} file(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

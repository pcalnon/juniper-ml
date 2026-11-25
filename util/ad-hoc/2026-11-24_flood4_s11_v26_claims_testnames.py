#!/usr/bin/env python3
"""
Compare a test module's test names, helpers and docstrings between main and a frozen copy (V26 claims lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 26 ports, session 11, validator V26 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (checks "no test is renamed or removed", the named helpers and the docstring claims
        of the ruling-26 PR texts)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 26);
         juniper-canopy#814 (the model fix)

What it does
------------
Parses two versions of a Python test module with ``ast`` (``--main`` may be absent for a new file) and prints: the
test functions/methods (with their class) only in main (removed or renamed), only in the frozen copy (added), and in
both; every function whose docstring differs, with both docstrings; the base classes of each class; the module-level
``pytestmark``; and, for each name given with ``--show``, the frozen copy's source of that function. Read-only.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_claims_testnames.py --main FILE --final FILE [--show NAME ...]
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def _functions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    found: dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[f"{node.name}.{sub.name}"] = sub
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--show", nargs="*", default=[])
    args = parser.parse_args()

    new_src = args.final.read_text(encoding="utf-8")
    new_tree = ast.parse(new_src)
    old_tree = ast.parse(args.main.read_text(encoding="utf-8")) if args.main.exists() else ast.Module(body=[], type_ignores=[])
    old_f, new_f = _functions(old_tree), _functions(new_tree)
    is_test = lambda name: name.split(".")[-1].startswith("test")  # noqa: E731
    print("removed or renamed tests (only in main):", sorted(n for n in old_f if is_test(n) and n not in new_f))
    print("added tests (only in final):", sorted(n for n in new_f if is_test(n) and n not in old_f))
    print("added helpers (only in final):", sorted(n for n in new_f if not is_test(n) and n not in old_f))
    print("removed helpers (only in main):", sorted(n for n in old_f if not is_test(n) and n not in new_f))
    print("tests in both:", len([n for n in new_f if is_test(n) and n in old_f]))
    for name in sorted(set(old_f) & set(new_f)):
        a, b = ast.get_docstring(old_f[name]), ast.get_docstring(new_f[name])
        if a != b:
            print(f"--- docstring changed: {name}\n    main : {a!r}\n    final: {b!r}")
    print("module docstring changed:", ast.get_docstring(old_tree) != ast.get_docstring(new_tree))
    for node in new_tree.body:
        if isinstance(node, ast.ClassDef):
            print(f"class {node.name} bases: {[ast.unparse(b) for b in node.bases]}")
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets):
            print("pytestmark =", ast.unparse(node.value))
    for name in args.show:
        node = new_f.get(name)
        if node is None:
            print(f"--- {name}: NOT FOUND in final")
            continue
        print(f"--- source of {name} (final, lines {node.lineno}-{node.end_lineno}):")
        print(ast.get_source_segment(new_src, node))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Screen Python files for the seven CodeQL shapes the prescreen does not model, against an optional baseline copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — one-off (Cursor flood-4 round 2: the r32 pause fix carrier's fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session6/BRIEF_S6_ADDENDUM.txt section 7 (the seven shapes); util/ad-hoc/2026-10-05_codeql_python_prescreen.py

The shapes: (1) a constant test in ``if`` / ``while`` other than ``while True``; (2) a module-level name bound
and never read in the module; (3) one module imported both as ``import X`` and ``from X import Y``; (4) a bare
``await <name>`` statement; (5) a local bound twice in a row in one block with no read of it in between;
(6) a subclass ``__init__`` assigning ``self.<attr>`` after ``super().__init__()`` when a base class defined in
the same file assigns it in its own ``__init__``; (7) ``except BaseException`` or a bare ``except:`` whose body
does not re-raise. Each is a heuristic: it reports candidates to read, never a verdict.

Usage:
  2026-11-16_flood4r2_r32-cascor_seven_shapes.py FILE[=BASELINE] [FILE[=BASELINE] ...]
With ``=BASELINE`` only hits whose (shape, text) the baseline lacks are counted.
Exit: 1 when any counted hit remains; 0 otherwise.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BARE_AWAIT = re.compile(r"^\s+await [A-Za-z_][A-Za-z_0-9]*\s*$")


def _names_read(tree: ast.AST) -> set:
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)} | {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}


def _reraises(handler: ast.ExceptHandler) -> bool:
    return any(isinstance(node, ast.Raise) for node in ast.walk(handler))


def _double_binds(body: list, hits: list) -> None:
    """Shape 5 within one statement list: Name stored by two consecutive simple statements, no read between."""
    for first, second in zip(body, body[1:]):
        if isinstance(first, ast.Assign) and isinstance(second, ast.Assign):
            stored = {t.id for t in first.targets if isinstance(t, ast.Name)}
            again = {t.id for t in second.targets if isinstance(t, ast.Name)}
            read_in_second = {n.id for n in ast.walk(second.value) if isinstance(n, ast.Name)}
            for name in sorted(stored & again - read_in_second):
                hits.append(("5-double-bind", f"{name} @ {first.lineno}"))
    for node in body:
        for field in ("body", "orelse", "finalbody"):
            inner = getattr(node, field, None)
            if isinstance(inner, list):
                _double_binds(inner, hits)
        for handler in getattr(node, "handlers", []) or []:
            _double_binds(handler.body, hits)


def screen(path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    hits: list = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While)) and isinstance(node.test, ast.Constant) and not (isinstance(node, ast.While) and node.test.value is True):
            hits.append(("1-constant-conditional", ast.unparse(node.test) + f" @ {node.lineno}"))
        if isinstance(node, ast.ExceptHandler):
            catches_all = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            if catches_all and not _reraises(node):
                hits.append(("7-except-base", f"line {node.lineno}"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _double_binds(node.body, hits)
    read = _names_read(tree)
    for stmt in tree.body:
        targets = []
        if isinstance(stmt, ast.Assign):
            targets = [t for t in stmt.targets if isinstance(t, ast.Name)]
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            targets = [stmt.target]
        for target in targets:
            if target.id not in read and target.id != "__all__" and not target.id.startswith("__"):
                hits.append(("2-unused-global", target.id))
    plain = {alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names}
    froms = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    for module in sorted(plain & froms):
        hits.append(("3-import-both-ways", module))
    for number, line in enumerate(text.splitlines(), 1):
        if BARE_AWAIT.match(line):
            hits.append(("4-bare-await", f"{line.strip()} @ {number}"))
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def _init_attrs(cls: ast.ClassDef) -> set:
        attrs = set()
        for item in cls.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for node in ast.walk(item):
                    if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) and node.value.id == "self":
                        attrs.add(node.attr)
        return attrs

    for cls in classes.values():
        base_attrs = set()
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                base_attrs |= _init_attrs(classes[base.id])
        for attr in sorted(_init_attrs(cls) & base_attrs):
            hits.append(("6-overwrite-base-attr", f"{cls.name}.{attr}"))
    return hits


def _key(hit: tuple) -> tuple:
    return hit[0], re.sub(r" @ \d+$|line \d+", "", hit[1])


def main(argv: list) -> int:
    if not argv:
        print(__doc__)
        return 2
    total = 0
    for spec in argv:
        name, _, baseline = spec.partition("=")
        hits = screen(Path(name))
        if baseline:
            base_keys = {_key(hit) for hit in screen(Path(baseline))}
            counted = [hit for hit in hits if _key(hit) not in base_keys]
            print(f"{name}: {len(counted)} hit(s) the baseline lacks ({len(hits)} in all)")
        else:
            counted = hits
            print(f"{name}: {len(counted)} hit(s)")
        for hit in counted:
            print(f"    {hit[0]}: {hit[1]}")
        total += len(counted)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

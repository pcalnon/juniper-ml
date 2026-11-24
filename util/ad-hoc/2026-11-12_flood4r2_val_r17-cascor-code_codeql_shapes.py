"""
Screen Python files for the seven CodeQL shapes the flood-4 briefs name, which the prescreen does not model.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, ruling 17 cascor stop-then-start, code lens)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt and tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt (the seven shapes); ruling 17

Usage: python3 <this> [--baseline OLDFILE:NEWFILE ...] FILE [FILE ...]

Shapes, by AST: (1) a constant in a conditional; (2) a module-level name bound and never read in the
module; (3) a module imported both as ``import X`` and ``from X import Y``; (4) a bare ``await <name>``
statement; (5) a local assigned immediately before a ``try:`` whose body assigns it again (the
"defined multiple times" form the session-5 addendum names); (6) a subclass ``__init__`` that assigns a
``self`` attribute after ``super().__init__()`` (listed for a manual look); (7) ``except BaseException``
or a bare ``except:`` whose body does not re-raise. Prints ``<file>:<line>: <shape>: <detail>`` per hit.
With ``--baseline OLD:NEW`` the hits of NEW are compared with OLD's by (shape, detail) and only the ones
OLD lacks are printed for NEW, so a large file is judged on what a change added. Exit 1 on any hit.
"""

import ast
import sys
from pathlib import Path


def _hits(path: Path) -> list:
    tree = ast.parse(path.read_text(), filename=str(path))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.IfExp)) and isinstance(node.test, ast.Constant):
            hits.append((node.lineno, "1-constant-conditional", repr(node.test.value)))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            hits.append((node.lineno, "4-bare-await", node.value.value.id))
        if isinstance(node, ast.ExceptHandler):
            broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            if broad and not any(isinstance(inner, ast.Raise) for inner in ast.walk(node)):
                hits.append((node.lineno, "7-broad-except-no-reraise", "bare" if node.type is None else "BaseException"))
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for first, second in zip(body, body[1:]):
                if isinstance(first, ast.Assign) and len(first.targets) == 1 and isinstance(first.targets[0], ast.Name) and isinstance(second, ast.Try):
                    name = first.targets[0].id
                    reassigned = any(isinstance(inner, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in inner.targets) for stmt in second.body for inner in ast.walk(stmt))
                    if reassigned:
                        hits.append((first.lineno, "5-default-before-try-reassigned", name))
        if isinstance(node, ast.ClassDef) and node.bases:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    seen_super = False
                    for stmt in item.body:
                        if any(isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute) and inner.func.attr == "__init__" for inner in ast.walk(stmt)):
                            seen_super = True
                            continue
                        if seen_super:
                            for inner in ast.walk(stmt):
                                if isinstance(inner, ast.Attribute) and isinstance(inner.ctx, ast.Store) and isinstance(inner.value, ast.Name) and inner.value.id == "self":
                                    hits.append((inner.lineno, "6-self-attribute-after-super-init", f"{node.name}.{inner.attr}"))
    imported, imported_from = set(), set()
    bound = {}
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            imported.update(alias.name for alias in stmt.names)
        elif isinstance(stmt, ast.ImportFrom) and stmt.module:
            imported_from.add(stmt.module)
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            for target in targets:
                if isinstance(target, ast.Name) and not (target.id.startswith("__") and target.id.endswith("__")):
                    bound.setdefault(target.id, stmt.lineno)
    for name in sorted(imported & imported_from):
        hits.append((1, "3-imported-both-ways", name))
    loaded = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    for name, lineno in sorted(bound.items()):
        if name not in loaded:
            hits.append((lineno, "2-unused-module-global", name))
    return sorted(hits)


def main() -> int:
    args = sys.argv[1:]
    total = 0
    while args and args[0] == "--baseline":
        old, new = (Path(p) for p in args[1].split(":", 1))
        args = args[2:]
        old_keys = {(shape, detail) for _line, shape, detail in _hits(old)}
        fresh = [hit for hit in _hits(new) if (hit[1], hit[2]) not in old_keys]
        print(f"{new}: {len(fresh)} hit(s) the baseline lacks ({len(_hits(new))} in all, {len(old_keys)} distinct in the baseline)")
        for line, shape, detail in fresh:
            print(f"{new}:{line}: {shape}: {detail}")
        total += len(fresh)
    for name in args:
        hits = _hits(Path(name))
        print(f"{name}: {len(hits)} hit(s)")
        for line, shape, detail in hits:
            print(f"{name}:{line}: {shape}: {detail}")
        total += len(hits)
    print(f"TOTAL {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Screen Python files for the seven CodeQL alert shapes the prescreen does not model (flood-4 session-6 addendum, section 7).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10);
         util/ad-hoc/2026-10-05_codeql_python_prescreen.py (the prescreen these shapes are outside of)

WHY THIS EXISTS
Each of these shapes opens a CodeQL review thread that blocks the merge, with every check green, and the prescreen
models none of them. Per file it reports:
  1. a constant conditional (`if True:` / `if False:` / `while False:`);
  2. a module-level name that is assigned and never read anywhere in the module;
  3. a module imported both as `import X` and as `from X import Y`;
  4. a bare `await <name>` statement;
  5. a local assigned and then assigned again with no read in between, within one straight-line block;
  6. a class whose `__init__` assigns `self.<attr>` after calling `super().__init__()` (flagged for review);
  7. `except BaseException:` or a bare `except:` whose body does not re-raise.
It reads the files and prints findings; exit 1 when there is any.

Usage:
    python3 <this> FILE [FILE ...]
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def loads(tree: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def reads_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def stores_in(stmt: ast.stmt) -> list[str]:
    if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        return [t.id for t in targets if isinstance(t, ast.Name)]
    return []


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While)) and isinstance(node.test, ast.Constant):
            found.append(f"{path}:{node.lineno}: constant conditional")
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            found.append(f"{path}:{node.lineno}: bare await of a name")
        if isinstance(node, ast.ExceptHandler):
            broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            reraises = any(isinstance(n, ast.Raise) for n in ast.walk(node))
            if broad and not reraises:
                found.append(f"{path}:{node.lineno}: except BaseException / bare except without re-raise")
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    calls_super = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__init__" for n in ast.walk(item))
                    sets_self = any(isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self" and isinstance(n.ctx, ast.Store) for n in ast.walk(item))
                    if calls_super and sets_self:
                        found.append(f"{path}:{item.lineno}: __init__ calls super().__init__() and assigns self attributes: review")
        body_lists = [getattr(node, attr) for attr in ("body", "orelse", "finalbody") if isinstance(getattr(node, attr, None), list)]
        for body in body_lists:
            pending: dict[str, int] = {}
            for stmt in body:
                if not isinstance(stmt, ast.stmt):
                    continue
                used = reads_in(stmt)
                for name in list(pending):
                    if name in used:
                        del pending[name]
                for name in stores_in(stmt):
                    if name in pending and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        found.append(f"{path}:{stmt.lineno}: {name} assigned again with no read since line {pending[name]}")
                    pending[name] = stmt.lineno
                if isinstance(stmt, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    pending.clear()
    plain = {a.name for n in tree.body if isinstance(n, ast.Import) for a in n.names}
    froms = {n.module for n in tree.body if isinstance(n, ast.ImportFrom) and n.module}
    for both in sorted(plain & froms):
        found.append(f"{path}: {both} imported both as `import` and as `from ... import`")
    used = loads(tree)
    for stmt in tree.body:
        for name in stores_in(stmt):
            if name not in used and not name.startswith("__"):
                found.append(f"{path}:{stmt.lineno}: module-level {name} is never read")
    return found


def main() -> int:
    findings = [f for arg in sys.argv[1:] for f in check(Path(arg))]
    for line in findings:
        print(line)
    print(f"{len(findings)} finding(s) in {len(sys.argv) - 1} file(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())

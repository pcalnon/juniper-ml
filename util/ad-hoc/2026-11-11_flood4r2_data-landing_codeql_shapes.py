#!/usr/bin/env python3
"""
Screen Python files for the seven CodeQL shapes that block a merge and that the 2026-10-05 prescreen does not model.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (a candidate list for a reader; it is not CodeQL and proves nothing by passing)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (four shapes); tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt
         § THREE MORE CODEQL SHAPES (juniper-ml#2545 was refused on them with every check green)

Usage:
    python3 <this> [--json <out file>] FILE [FILE ...]

Shapes, each reported as a CANDIDATE with its line:
    constant-conditional    an ``if`` / ``while`` / conditional expression whose test is a literal constant
    unused-global           a module-level name assigned once and never read in the module (``__all__`` and dunders
                            excepted). ``pytestmark`` is reported too and marked: pytest reads it by name.
    import-both-ways        one module imported as ``import X`` and as ``from X import Y``
    bare-await              an expression statement that is only ``await <name>``
    redefined-before-read   a name bound at block level (an assignment, tuple targets included, or ``with ... as``)
                            whose next mention in that block binds it again without reading it, or is a ``try:``
                            whose body binds it before reading it. CodeQL itself exempts a first assignment of a
                            simple literal and a tuple some of whose names ARE read; this reports them anyway.
    overwritten-attribute   a subclass ``__init__`` that assigns ``self.x`` after calling ``super().__init__``,
                            where a base class defined in the same file assigns ``self.x`` in its own ``__init__``
    except-base             ``except BaseException`` or a bare ``except:`` whose body holds no bare ``raise``

Exit 0 when no candidate is found, 1 otherwise. The reader decides what each candidate is.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def _names(node: ast.AST, ctx: type) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ctx)}


def _simple_targets(stmt: ast.stmt) -> set[str]:
    """Names a statement defines: assignment targets (tuple and list targets included) and ``with ... as`` names."""
    if isinstance(stmt, ast.Assign):
        return {n.id for target in stmt.targets for n in ast.walk(target) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    if isinstance(stmt, ast.AnnAssign) and stmt.value is not None and isinstance(stmt.target, ast.Name):
        return {stmt.target.id}
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        return {n.id for item in stmt.items if item.optional_vars is not None for n in ast.walk(item.optional_vars) if isinstance(n, ast.Name)}
    return set()


def _reads_before_defining(stmt: ast.stmt, name: str) -> bool:
    """Whether a statement that defines ``name`` also reads its OLD value (the right-hand side, or a ``with`` expression)."""
    if isinstance(stmt, (ast.Assign, ast.AnnAssign)):
        return stmt.value is not None and name in _names(stmt.value, ast.Load)
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        return any(name in _names(item.context_expr, ast.Load) for item in stmt.items)
    return True


def _first_touch(stmts: list[ast.stmt], name: str) -> str:
    """How a statement list first touches ``name``: 'read', 'write' or 'none' (a write that reads it is a read)."""
    for stmt in stmts:
        if name in _simple_targets(stmt):
            return "read" if _reads_before_defining(stmt, name) else "write"
        if name in _names(stmt, ast.Load) | _names(stmt, ast.Store):
            return "read"
    return "none"


def _redefined(body: list[ast.stmt], found: list[dict]) -> None:
    for index, stmt in enumerate(body):
        for name in sorted(_simple_targets(stmt)):
            if isinstance(stmt, (ast.With, ast.AsyncWith)) and any(name in _names(inner, ast.Load) for inner in stmt.body):
                continue  # the with body reads what it bound
            for later in body[index + 1 :]:
                touched = name in _names(later, ast.Load) | _names(later, ast.Store)
                if not touched:
                    continue
                if name in _simple_targets(later) and not _reads_before_defining(later, name):
                    found.append({"shape": "redefined-before-read", "line": stmt.lineno, "name": name, "redefined_at": later.lineno})
                elif isinstance(later, ast.Try) and _first_touch(later.body, name) == "write":
                    found.append({"shape": "redefined-before-read", "line": stmt.lineno, "name": name, "redefined_at": later.lineno, "note": "the try body assigns it first; a handler or a later line may still read the default"})
                break
        for field in ("body", "orelse", "finalbody"):
            inner = getattr(stmt, field, None)
            if isinstance(inner, list) and inner and isinstance(inner[0], ast.stmt) and not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                _redefined(inner, found)
        for handler in getattr(stmt, "handlers", []):
            _redefined(handler.body, found)


def _self_attrs(func: ast.FunctionDef) -> dict[str, int]:
    attrs: dict[str, int] = {}
    for node in ast.walk(func):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and isinstance(node.value, ast.Name) and node.value.id == "self":
            attrs.setdefault(node.attr, node.lineno)
    return attrs


def screen(path: Path) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.IfExp)) and isinstance(node.test, ast.Constant):
            found.append({"shape": "constant-conditional", "line": node.lineno, "test": repr(node.test.value)})
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            found.append({"shape": "bare-await", "line": node.lineno, "name": node.value.value.id})
        if isinstance(node, ast.ExceptHandler):
            base = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            reraises = any(isinstance(n, ast.Raise) and n.exc is None for n in ast.walk(node))
            if base and not reraises:
                found.append({"shape": "except-base", "line": node.lineno})
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _redefined(node.body, found)
    _redefined(tree.body, found)
    plain ={alias.name for node in tree.body if isinstance(node, ast.Import) for alias in node.names}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in plain:
            found.append({"shape": "import-both-ways", "line": node.lineno, "module": node.module})
    loads = _names(tree, ast.Load)
    exported: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            exported = {c.value for c in ast.walk(node.value) if isinstance(c, ast.Constant) and isinstance(c.value, str)}
    for node in tree.body:
        for name in _simple_targets(node):
            if name not in loads and name not in exported and not (name.startswith("__") and name.endswith("__")):
                note = "pytest reads pytestmark by name" if name == "pytestmark" else None
                found.append({"shape": "unused-global", "line": node.lineno, "name": name, "note": note})
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    for cls in classes.values():
        init = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
        if init is None:
            continue
        calls_super = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "__init__" and isinstance(n.func.value, ast.Call) and isinstance(n.func.value.func, ast.Name) and n.func.value.func.id == "super" for n in ast.walk(init))
        if not calls_super:
            continue
        mine = _self_attrs(init)
        for base in cls.bases:
            parent = classes.get(base.id) if isinstance(base, ast.Name) else None
            parent_init = next((n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None) if parent else None
            if parent_init is None:
                continue
            for attr in sorted(set(mine) & set(_self_attrs(parent_init))):
                found.append({"shape": "overwritten-attribute", "line": mine[attr], "class": cls.name, "attribute": attr, "base": parent.name})
    return sorted(found, key=lambda item: (item["line"], item["shape"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--json", type=Path)
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()
    report = {str(path): screen(path) for path in args.files}
    total = sum(len(items) for items in report.values())
    for path, items in report.items():
        print(f"{path}: {len(items)} candidate(s)")
        for item in items:
            print("   " + json.dumps(item))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
            fh.write("\n")
    print(f"total candidates: {total}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

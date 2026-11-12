"""
Screen Python files for the three CodeQL shapes the flood-4 session-4 addendum names as merge-blocking.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, n1 r2 code lens)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (TRAPS: CodeQL raises alerts the prescreen does not model)

Usage: python3 <this> FILE [FILE ...]

Reports, per file:
  import-and-import-from -- a module imported with ``import M`` (any alias) and ``from M import ...``
                            anywhere in the same file (CodeQL py/import-and-import-from);
  constant-conditional   -- ``if``/``elif``/``while``/ternary tests that are a literal constant other
                            than ``while True`` (CodeQL py/constant-conditional-expression shape);
  unused-module-global   -- a module-level assigned name never loaded anywhere in the file and not
                            listed in ``__all__`` (CodeQL py/unused-global-variable shape).
Exit 1 when any shape is found. Read-only.
"""

import ast
import sys
from pathlib import Path


def _imports(tree: ast.AST) -> list:
    plain, members = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                plain.setdefault(alias.name, []).append(node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            members.setdefault(node.module, []).append(node.lineno)
    return [f"import-and-import-from: {name} (import at {plain[name]}, from-import at {members[name]})" for name in sorted(set(plain) & set(members))]


def _constant_tests(tree: ast.AST) -> list:
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.IfExp)) and isinstance(node.test, ast.Constant):
            if isinstance(node, ast.While) and node.test.value is True:
                continue
            hits.append(f"constant-conditional: line {node.lineno} test={node.test.value!r}")
    return hits


def _unused_globals(tree: ast.Module) -> list:
    assigned = {}
    for stmt in tree.body:
        targets = []
        if isinstance(stmt, ast.Assign):
            targets = stmt.targets
        elif isinstance(stmt, (ast.AnnAssign, ast.AugAssign)):
            targets = [stmt.target]
        for target in targets:
            for node in ast.walk(target):
                if isinstance(node, ast.Name):
                    assigned.setdefault(node.id, stmt.lineno)
    exported = set()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in stmt.targets) and isinstance(stmt.value, (ast.List, ast.Tuple)):
            exported |= {e.value for e in stmt.value.elts if isinstance(e, ast.Constant)}
    loaded = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    loaded |= {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    return [f"unused-module-global: {name} (line {line})" for name, line in sorted(assigned.items(), key=lambda kv: kv[1]) if name not in loaded and name not in exported and name != "__all__" and not (name.startswith("__") and name.endswith("__"))]


def main() -> int:
    found = 0
    for arg in sys.argv[1:]:
        path = Path(arg)
        with open(path) as fh:
            tree = ast.parse(fh.read(), filename=str(path))
        hits = _imports(tree) + _constant_tests(tree) + _unused_globals(tree)
        print(f"{path}: {'clean' if not hits else ''}")
        for hit in hits:
            print(f"  {hit}")
        found += len(hits)
    print(f"total shapes: {found}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())

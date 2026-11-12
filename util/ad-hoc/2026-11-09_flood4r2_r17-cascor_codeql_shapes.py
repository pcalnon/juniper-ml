#!/usr/bin/env python3
"""
Screen Python files for four CodeQL alert shapes the juniper-ml prescreen does not fully model.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: owner ruling 17, "cascor: stop-then-start")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt ("TRAPS LEARNED IN SESSION 3")

Shapes (each opens a CodeQL review thread that blocks a merge):
  import-both-ways   -- a module imported as ``import X`` (or ``import X as Y``) and also ``from X import Y``;
  constant-if        -- ``if`` / ``while`` / ternary whose test is a literal constant (``if True:``);
  unused-global      -- a module-level simple assignment whose name is never loaded in the module
                        (dunder names and ``__all__`` members excepted);
  bare-await-name    -- an expression statement ``await <name>``.
``--known-answer`` screens a crafted source that has one of each and requires all four.

Usage:
  2026-11-09_flood4r2_r17-cascor_codeql_shapes.py FILE [FILE ...] [--known-answer]
Exit: 1 when any shape is found (or the known answer misses one); 0 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

_KNOWN = """import os
import os.path
from os import path
import asyncio

UNUSED = 1


async def f(task):
    await task


if True:
    pass
"""


def screen(source: str, label: str) -> list:
    tree = ast.parse(source)
    findings = []
    plain, from_ = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                plain.setdefault(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            from_.setdefault(node.module, node.lineno)
        elif isinstance(node, (ast.If, ast.While, ast.IfExp)) and isinstance(node.test, ast.Constant):
            findings.append(f"{label}:{node.lineno}: constant-if: test is the constant {node.test.value!r}")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            findings.append(f"{label}:{node.lineno}: bare-await-name: await {node.value.value.id}")
    for module in sorted(set(plain) & set(from_)):
        findings.append(f"{label}:{plain[module]}: import-both-ways: {module} (from-import at line {from_[module]})")
    loaded = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    exported = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets) and isinstance(node.value, (ast.List, ast.Tuple)):
            exported |= {e.value for e in node.value.elts if isinstance(e, ast.Constant)}
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else ([node.target] if isinstance(node, ast.AnnAssign) else [])
        for target in targets:
            if isinstance(target, ast.Name) and target.id not in loaded and not target.id.startswith("__") and target.id not in exported:
                findings.append(f"{label}:{node.lineno}: unused-global: {target.id}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("files", nargs="*")
    parser.add_argument("--known-answer", action="store_true")
    args = parser.parse_args()
    failed = False
    if args.known_answer:
        kinds = {line.split(": ")[1] for line in screen(_KNOWN, "<known>")}
        missing = {"import-both-ways", "constant-if", "unused-global", "bare-await-name"} - kinds
        print(f"known answer: {'PASS' if not missing else 'FAIL, missed ' + str(sorted(missing))}")
        failed = bool(missing)
    total = 0
    for name in args.files:
        found = screen(Path(name).read_text(encoding="utf-8"), name)
        total += len(found)
        for line in found:
            print(line)
    print(f"{total} finding(s) in {len(args.files)} file(s)")
    return 1 if failed or total else 0


if __name__ == "__main__":
    sys.exit(main())

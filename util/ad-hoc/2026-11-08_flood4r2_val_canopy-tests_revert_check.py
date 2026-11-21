"""
Show that a carrier's Python change is docstring-only and its text-file changes are pure insertions over main.

Validator helper for the flood-4 round-2 canopy carriers (tests/code/CI lens). For each ``--py MAIN CARRIER``
pair it compares the two modules' ASTs with every docstring removed (equal = no code changed). For each
``--text MAIN CARRIER`` pair it runs difflib over the lines and reports every opcode that is not ``equal`` or
``insert`` (a ``delete`` or ``replace`` would be content main has that the carrier drops). For each
``--unreleased FILE`` it reports the line of the first ``## [`` heading and whether it is ``## [Unreleased]``.

Usage:
  python3 <this file> --py <main.py> <carrier.py> --text <main.md> <carrier.md> ... --unreleased <file.md> ...

Prints one JSON object. Exit 0 when every py pair is AST-equal and every text pair is insert-only, else 1.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-canopy#800, #801, #798, #799 (flood-4 round 2), canopy carrier validation
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import sys
from pathlib import Path


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree


def _code_dump(path: Path) -> str:
    return ast.dump(_strip_docstrings(ast.parse(path.read_text(encoding="utf-8"))), include_attributes=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--py", nargs=2, action="append", default=[], metavar=("MAIN", "CARRIER"))
    parser.add_argument("--text", nargs=2, action="append", default=[], metavar=("MAIN", "CARRIER"))
    parser.add_argument("--unreleased", action="append", default=[])
    args = parser.parse_args()
    report: dict = {"py": [], "text": [], "unreleased": []}
    ok = True
    for main_path, carrier_path in args.py:
        equal = _code_dump(Path(main_path)) == _code_dump(Path(carrier_path))
        ok = ok and equal
        report["py"].append({"main": main_path, "carrier": carrier_path, "code_ast_equal_without_docstrings": equal})
    for main_path, carrier_path in args.text:
        a = Path(main_path).read_text(encoding="utf-8").splitlines(keepends=True)
        b = Path(carrier_path).read_text(encoding="utf-8").splitlines(keepends=True)
        ops = [(tag, i1 + 1, i2, j1 + 1, j2) for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes() if tag != "equal"]
        bad = [op for op in ops if op[0] != "insert"]
        ok = ok and not bad
        report["text"].append({"main": main_path, "carrier": carrier_path, "non_equal_opcodes": ops, "non_insert_opcodes": bad})
    for path in args.unreleased:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        headings = [(n + 1, line) for n, line in enumerate(lines) if line.startswith("## [")]
        report["unreleased"].append({"file": path, "first_headings": headings[:2], "top_is_unreleased": bool(headings) and headings[0][1].startswith("## [Unreleased]")})
    print(json.dumps(report, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

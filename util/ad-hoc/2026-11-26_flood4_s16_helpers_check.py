#!/usr/bin/env python3
"""
Check ad-hoc helper scripts before they ride a pull request: the util/ad-hoc/README.md header, no home-directory
literal, and the two CodeQL queries the prescreen does not model.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition, session 16: the canopy carriers' helpers PR)
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- one-off (the r27 / r28 helpers PR; reusable for any later helpers PR)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/README.md (the header it requires); util/ad-hoc/2026-10-05_codeql_python_prescreen.py (the
         queries it does model); juniper-ml#2671, whose four CodeQL review threads were py/import-and-import-from (3)
         and py/catch-base-exception (1) in helpers the prescreen had passed

What it does
------------
For each FILE (a .py path), reads it and reports, per file:
  * header -- each of the README's header fields (Project, Sub-Project, Author, Created, Status, Retire when, Related)
    must appear as "<field>:" in the file's first 60 lines; Author must read Paul Calnon and Retire when must start
    RETAINED;
  * home -- no literal home-directory path (a "/home/<user>/" or "/Users/<user>/" prefix, or a tilde-slash home prefix inside a
    string literal); paths are taken as arguments;
  * import-and-import-from -- no module both imported (``import X`` / ``import X as y``) and imported from
    (``from X import y``) in the same file, the shape of CodeQL's py/import-and-import-from;
  * catch-base-exception -- no bare ``except:`` and no handler naming ``BaseException`` (alone or in a tuple), the
    shape of CodeQL's py/catch-base-exception;
  * syntax -- the file parses.
Prints one line per problem and a summary; --json writes the full result. Reads only. Exit 0 when no file has a
problem, 1 otherwise, 2 on a usage error.

Usage
-----
    python3 util/ad-hoc/2026-11-26_flood4_s16_helpers_check.py FILE [FILE ...] [--json OUT.json]
    python3 util/ad-hoc/2026-11-26_flood4_s16_helpers_check.py --list LIST.txt [--json OUT.json]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

FIELDS = ("Project", "Sub-Project", "Author", "Created", "Status", "Retire when", "Related")
HOME_RE = re.compile(r"/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/")
TILDE_HOME = "~" + "/"  # built, so this file holds no such literal itself


def _header_problems(lines: list[str]) -> list[str]:
    head = lines[:60]
    problems = []
    for field in FIELDS:
        hits = [line for line in head if re.search(rf"(^|[#\s]){re.escape(field)}:", line)]
        if not hits:
            problems.append(f"header: no '{field}:' line in the first 60 lines")
            continue
        value = hits[0].split(f"{field}:", 1)[1].strip()
        if field == "Author" and "Paul Calnon" not in value:
            problems.append(f"header: Author reads {value!r}")
        if field == "Retire when" and not value.startswith("RETAINED"):
            problems.append(f"header: Retire when reads {value[:40]!r}")
    return problems


def _string_literals(tree: ast.AST) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            found.append((node.lineno, node.value))
    return found


def _ast_problems(tree: ast.AST) -> list[str]:
    problems = []
    imported: dict[str, int] = {}
    imported_from: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.setdefault(alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported_from.setdefault(node.module, node.lineno)
        elif isinstance(node, ast.ExceptHandler):
            kind = node.type
            names = []
            if kind is None:
                problems.append(f"catch-base-exception: bare except at line {node.lineno}")
                continue
            if isinstance(kind, ast.Tuple):
                names = [elt.id for elt in kind.elts if isinstance(elt, ast.Name)]
            elif isinstance(kind, ast.Name):
                names = [kind.id]
            if "BaseException" in names:
                problems.append(f"catch-base-exception: BaseException caught at line {node.lineno}")
    for module in sorted(set(imported) & set(imported_from)):
        problems.append(f"import-and-import-from: {module} imported at line {imported[module]} and imported from at line {imported_from[module]}")
    return problems


def check(path: Path) -> dict:
    result = {"file": str(path), "problems": []}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        result["problems"].append(f"read: {exc}")
        return result
    lines = text.splitlines()
    result["problems"].extend(_header_problems(lines))
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        result["problems"].append(f"syntax: {exc}")
        return result
    for lineno, value in _string_literals(tree):
        if HOME_RE.search(value) or TILDE_HOME in value:
            result["problems"].append(f"home: a home-directory path literal at line {lineno}")
    for number, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("#") and HOME_RE.search(stripped):
            result["problems"].append(f"home: a home-directory path in a comment at line {number}")
    result["problems"].extend(_ast_problems(tree))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--list", type=Path, help="a file naming one path per line")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    paths = list(args.files)
    if args.list:
        paths += [Path(line.strip()) for line in args.list.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not paths:
        parser.error("no files given")
    results = [check(path) for path in paths]
    bad = [result for result in results if result["problems"]]
    for result in bad:
        for problem in result["problems"]:
            print(f"{result['file']}: {problem}")
    print(f"checked {len(results)} file(s): {len(bad)} with problems")
    if args.json:
        args.json.write_text(json.dumps({"results": results}, indent=1) + "\n", encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

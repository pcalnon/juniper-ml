"""
Compare the source of named methods of ServiceLifecycleManager between two copies of lifecycle/manager.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, claims lens r23l-val-claims: "0.7.2 has both defects")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Prints, for each method of the class in either file, IDENTICAL or DIFFERS (its exact source text, decorators
included), and the sha256 of each file. Reads the files only.

Usage: python3 -I <this file> A.py B.py
"""

import ast
import hashlib
import sys


def _methods(path: str) -> tuple[dict[str, str], str]:
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    tree = ast.parse(text)
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ServiceLifecycleManager":
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[item.name] = ast.get_source_segment(text, item) or ""
    return found, hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    first, first_sha = _methods(sys.argv[1])
    second, second_sha = _methods(sys.argv[2])
    print(f"A {first_sha}  {sys.argv[1]}")
    print(f"B {second_sha}  {sys.argv[2]}")
    for name in sorted(set(first) | set(second)):
        if name not in first or name not in second:
            print(f"ONLY-{'A' if name in first else 'B'}  {name}")
        else:
            print(f"{'IDENTICAL' if first[name] == second[name] else 'DIFFERS  '}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

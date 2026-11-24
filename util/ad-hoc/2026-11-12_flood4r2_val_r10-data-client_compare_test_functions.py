"""
Compare the port's test functions with juniper-data's, function by function, and print a diff of each adapted one.

Both files are parsed with ``ast``; a function is "identical" when its source segment is byte-equal in the two files.
Module-level assignments are compared the same way.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_compare_test_functions.py <port test file> <juniper-data test file>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import ast
import difflib
import sys
from pathlib import Path


def segments(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions, assignments = {}, {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([node.lineno] + [decorator.lineno for decorator in node.decorator_list])
            functions[node.name] = "\n".join(source.splitlines()[start - 1 : node.end_lineno])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = ast.get_source_segment(source, node) or ""
    return functions, assignments


def main() -> int:
    port_functions, port_assignments = segments(Path(sys.argv[1]))
    data_functions, data_assignments = segments(Path(sys.argv[2]))
    identical = sorted(name for name in port_functions if data_functions.get(name) == port_functions[name])
    adapted = sorted(name for name in port_functions if name in data_functions and data_functions[name] != port_functions[name])
    new = sorted(name for name in port_functions if name not in data_functions)
    not_ported = sorted(name for name in data_functions if name not in port_functions)
    print(f"port functions: {len(port_functions)}; identical: {len(identical)}; adapted: {len(adapted)}; new: {len(new)}; juniper-data functions not ported: {len(not_ported)}")
    print("new:", new)
    print("not ported:", not_ported)
    for name in adapted:
        print(f"\n=== adapted: {name}")
        for line in difflib.unified_diff(data_functions[name].splitlines(), port_functions[name].splitlines(), "juniper-data", "port", lineterm="", n=1):
            print(line)
    print("\n=== module-level assignments")
    for name in sorted(set(port_assignments) | set(data_assignments)):
        ours, theirs = port_assignments.get(name), data_assignments.get(name)
        if ours == theirs:
            continue
        print(f"{name}:\n  data: {theirs}\n  port: {ours}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

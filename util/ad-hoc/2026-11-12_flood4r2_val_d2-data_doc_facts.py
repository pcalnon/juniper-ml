#!/usr/bin/env python3
"""
Validator facts for juniper-data's "run the unrun tests" carrier: the counts its texts and documents state, read
from a tree (test modules per directory, module-level ``pytestmark`` lines, stamp lines, AGENTS.md's size).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt (checks E and F)

Usage: 2026-11-12_flood4r2_val_d2-data_doc_facts.py --tree <juniper-data tree> [--tree <another> ...] [--out <json>]

The scope is chosen on purpose: only ``juniper_data/tests/<dir>/test_*.py`` of the named tree is read, never its
``tmp/`` directory.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

STAMPED = ("AGENTS.md", "docs/REFERENCE.md", "docs/testing/TESTING_MANUAL.md", "docs/testing/TESTING_REFERENCE.md", "docs/DEVELOPER_CHEATSHEET.md")


def module_marks(path: Path) -> list[str]:
    """The unparsed value of every module-level ``pytestmark`` assignment."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for statement in tree.body:
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target] if isinstance(statement, ast.AnnAssign) else []
        if any(isinstance(target, ast.Name) and target.id == "pytestmark" for target in targets):
            found.append(ast.unparse(statement.value))
    return found


def facts(tree: Path) -> dict:
    tests = tree / "juniper_data" / "tests"
    directories = {}
    for directory in sorted(p for p in tests.iterdir() if p.is_dir() and not p.name.startswith("__")):
        modules = sorted(directory.glob("test_*.py"))
        marked = {module.name: module_marks(module) for module in modules}
        directories[directory.name] = {
            "test_modules": len(modules),
            "with_module_pytestmark": sum(1 for value in marked.values() if value),
            "with_module_pytestmark_naming_unit": sum(1 for value in marked.values() if any("unit" in item for item in value)),
            "with_module_pytestmark_naming_integration": sum(1 for value in marked.values() if any("integration" in item for item in value)),
        }
    stamps = {}
    for name in STAMPED:
        path = tree / name
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            stamps[name] = [{"line": index + 1, "text": line} for index, line in enumerate(lines) if line.startswith("**Version") or line.startswith("**Last Updated")]
    agents = (tree / "AGENTS.md").read_text(encoding="utf-8")
    return {"tree": str(tree), "directories": directories, "stamps": stamps, "agents_md": {"characters": len(agents), "bytes": len(agents.encode("utf-8")), "lines": agents.count("\n")}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", action="append", required=True)
    parser.add_argument("--out")
    ns = parser.parse_args()
    report = [facts(Path(tree)) for tree in ns.tree]
    for entry in report:
        print(f"== {entry['tree']}")
        for name, row in entry["directories"].items():
            print(f"   tests/{name}: {row}")
        for name, sites in entry["stamps"].items():
            print(f"   {name}: " + " | ".join(f"{site['line']}: {site['text']}" for site in sites))
        print(f"   AGENTS.md: {entry['agents_md']}")
    if ns.out:
        Path(ns.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

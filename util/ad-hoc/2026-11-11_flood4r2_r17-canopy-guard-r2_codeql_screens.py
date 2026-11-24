"""
Screen changed Python for CodeQL alerts: the 2026-10-05 prescreen against a baseline, plus the seven trap shapes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round 2 of the Overtoad's ruling-17 fix "canopy: tests hit :8050" (tmp/flood4/session5/BRIEF_S5_ADDENDUM.txt)

Usage:
    python3 <this file> --out <json> [--pair <changed file>=<baseline copy> ...] [--new <file> ...]

An unresolved CodeQL review thread blocks a merge while every check is green. Two screens:

1. util/ad-hoc/2026-10-05_codeql_python_prescreen.py on each file. For a --pair the same screen runs on the baseline
   copy (the file as it is on main) and only predictions the baseline does not already carry are reported, compared
   with line numbers removed; for a --new file every prediction is reported.
2. The seven shapes the session-4 and session-5 addenda name, which the prescreen does not model or models only for
   the standard library, from the AST of the changed file (for a --pair, again only what the baseline lacks):
   constant-conditional (`if`/`while` on a literal other than `while True`), import-both-ways (any module, not only
   the standard library), bare-await-name (`await x` as a statement), base-exception-swallowed (`except:` or
   `except BaseException` with no `raise` in the body), dead-default-before-try (a name assigned immediately before
   a `try` whose body assigns it again first), subclass-init-overwrite (a subclass `__init__` assigning an attribute
   that a base class defined in the same file also assigns in its `__init__`). An unused module-level global and a
   name defined twice are the prescreen's `unused-global` and `multiple-definition`.

Exit 1 when either screen reports anything new.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from pathlib import Path

PRESCREEN = Path(__file__).resolve().parent / "2026-10-05_codeql_python_prescreen.py"


def prescreen(path: Path) -> list[str]:
    proc = subprocess.run([sys.executable, str(PRESCREEN), str(path)], capture_output=True, text=True)  # nosec B603 - fixed argv
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return [re.sub(r"^.*?\.py[: ]*\d*[: ]*", "", re.sub(r"(?<=[:\s(])\d+(?=[:\s)]|$)", "N", line)) for line in lines if ".py" in line]


def init_self_attributes(cls: ast.ClassDef) -> set[str]:
    names: set[str] = set()
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            for node in ast.walk(item):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.AugAssign)) else []
                names.update(target.attr for target in targets if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self")
    return names


def assigned_names(statement: ast.stmt) -> set[str]:
    if isinstance(statement, ast.Assign):
        return {target.id for target in statement.targets if isinstance(target, ast.Name)}
    if isinstance(statement, ast.AnnAssign) and statement.value is not None and isinstance(statement.target, ast.Name):
        return {statement.target.id}
    return set()


def shapes(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found: list[str] = []
    plain = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    found += [f"import-both-ways: {node.module}" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module in plain]
    classes = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for cls in classes.values():
        for base in cls.bases:
            if isinstance(base, ast.Name) and base.id in classes:
                found += [f"subclass-init-overwrite: {cls.name}.{name} (base {base.id})" for name in sorted(init_self_attributes(cls) & init_self_attributes(classes[base.id]))]
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While)) and isinstance(node.test, ast.Constant) and not (isinstance(node, ast.While) and node.test.value is True):
            found.append(f"constant-conditional: {type(node).__name__.lower()} {node.test.value!r}")
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            found.append(f"bare-await-name: await {node.value.value.id}")
        if isinstance(node, ast.ExceptHandler) and (node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")):
            if not any(isinstance(inner, ast.Raise) for inner in ast.walk(node)):
                found.append(f"base-exception-swallowed: except {'<bare>' if node.type is None else 'BaseException'}")
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            for before, after in zip(block, block[1:]):
                if isinstance(after, ast.Try) and after.body:
                    found += [f"dead-default-before-try: {name}" for name in sorted(assigned_names(before) & assigned_names(after.body[0]))]
    return found


def new_only(changed: list[str], baseline: list[str]) -> list[str]:
    remaining = list(baseline)
    result = []
    for entry in changed:
        if entry in remaining:
            remaining.remove(entry)
        else:
            result.append(entry)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen changed Python for CodeQL alerts against a baseline.")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--pair", action="append", default=[], help="<changed file>=<baseline copy>")
    parser.add_argument("--new", action="append", default=[], type=Path)
    args = parser.parse_args()
    jobs = [(Path(changed), Path(baseline)) for changed, baseline in (entry.split("=", 1) for entry in args.pair)] + [(path, None) for path in args.new]
    record = {}
    reported = 0
    for changed, baseline in jobs:
        entry = {
            "baseline": str(baseline) if baseline else None,
            "prescreen_new": new_only(prescreen(changed), prescreen(baseline) if baseline else []),
            "shapes_new": new_only(shapes(changed), shapes(baseline) if baseline else []),
        }
        entry["prescreen_all"] = len(prescreen(changed))
        record[str(changed)] = entry
        reported += len(entry["prescreen_new"]) + len(entry["shapes_new"])
        print(f"[codeql] {changed.name}: prescreen new={entry['prescreen_new']} shapes new={entry['shapes_new']}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(f"[codeql] {len(jobs)} files, {reported} new predictions; record {args.out}")
    return 1 if reported else 0


if __name__ == "__main__":
    sys.exit(main())

"""
Re-derive the countable claims of the ruling-17 canopy lockfile-print carrier's texts from the files themselves.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: Cursor flood-4 disposition, Overtoad ruling 17 ("canopy: dead error path"), session-5 validation

Checks: the CHANGELOG entry text is in CHANGELOG.md exactly once, under the top [Unreleased] / ### Fixed, below an
existing entry; the test functions main has are all still present; which are new; every backticked repo path a
deliverable names exists; no CI-skip marker; and the CodeQL shapes the session addenda list are absent from the
changed test file. Reads only; main's copies come from `git show`.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

TEST_FILE = "src/tests/regression/test_lockfile_regen_empty_payload.py"
SKIP_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]", "skip-checks:")


def _show(repo: Path, rev: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(repo), "show", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout


def _tests(source: str) -> dict[str, int]:
    """Test function name -> number of parametrized cases (1 when not parametrized)."""
    found: dict[str, int] = {}
    for node in ast.parse(source).body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
            continue
        cases = 1
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and ast.unparse(decorator.func).endswith("parametrize") and len(decorator.args) >= 2 and isinstance(decorator.args[1], ast.List):
                cases = len(decorator.args[1].elts)
        found[node.name] = cases
    return found


def _codeql_shapes(source: str) -> dict[str, list[int]]:
    shapes: dict[str, list[int]] = {"bare_await": [], "constant_conditional": [], "bare_or_base_except": [], "import_both_ways": []}
    tree = ast.parse(source)
    plain: set[str] = set()
    from_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Await) and isinstance(node.value.value, ast.Name):
            shapes["bare_await"].append(node.lineno)
        if isinstance(node, (ast.If, ast.While)) and isinstance(node.test, ast.Constant):
            shapes["constant_conditional"].append(node.lineno)
        if isinstance(node, ast.ExceptHandler):
            is_base = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "BaseException")
            reraises = any(isinstance(child, ast.Raise) and child.exc is None for child in ast.walk(node))
            if is_base and not reraises:
                shapes["bare_or_base_except"].append(node.lineno)
        if isinstance(node, ast.Import):
            plain.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            from_names.add(node.module)
    for module in sorted(plain & from_names):
        shapes["import_both_ways"].append(source.splitlines().index(next(line for line in source.splitlines() if line.startswith(f"import {module}"))) + 1)
    return shapes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", required=True, type=Path)
    parser.add_argument("--main", required=True)
    parser.add_argument("--deliverables", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    report: dict[str, object] = {}
    changelog = (args.copy / "CHANGELOG.md").read_text(encoding="utf-8")
    entry = (args.deliverables / "changelog_entry.txt").read_text(encoding="utf-8").rstrip("\n")
    lines = changelog.splitlines()
    headings = [(number, line) for number, line in enumerate(lines, start=1) if line.startswith("## [")]
    entry_first = entry.splitlines()[0]
    entry_line = next((number for number, line in enumerate(lines, start=1) if line == entry_first), None)
    subsection = None
    entries_above = 0
    if entry_line is not None:
        for number in range(entry_line - 1, 0, -1):
            if lines[number - 1].startswith("### "):
                subsection = (number, lines[number - 1])
                break
            if lines[number - 1].startswith("- "):
                entries_above += 1
    report["changelog"] = {
        "entry_occurrences": changelog.count(entry),
        "entry_line": entry_line,
        "top_heading": headings[0] if headings else None,
        "second_heading": headings[1] if len(headings) > 1 else None,
        "subsection": subsection,
        "entries_above_in_subsection": entries_above,
        "in_main_changelog": _show(args.copy, args.main, "CHANGELOG.md").count(entry),
        "longest_line": max(len(line) for line in entry.splitlines()),
    }

    main_tests = _tests(_show(args.copy, args.main, TEST_FILE))
    head_source = (args.copy / TEST_FILE).read_text(encoding="utf-8")
    head_tests = _tests(head_source)
    report["tests"] = {
        "main_functions": len(main_tests),
        "main_cases": sum(main_tests.values()),
        "carrier_functions": len(head_tests),
        "carrier_cases": sum(head_tests.values()),
        "removed_or_renamed": sorted(set(main_tests) - set(head_tests)),
        "new": {name: head_tests[name] for name in sorted(set(head_tests) - set(main_tests))},
        "case_count_changed": {name: [main_tests[name], head_tests[name]] for name in sorted(set(main_tests) & set(head_tests)) if main_tests[name] != head_tests[name]},
    }
    report["codeql_shapes_in_test_file"] = _codeql_shapes(head_source)

    texts: dict[str, object] = {}
    for name in ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt"):
        body = (args.deliverables / name).read_text(encoding="utf-8")
        paths = sorted(set(re.findall(r"`((?:\.github|src|docs|notes|util|conf)/[A-Za-z0-9_./-]+)`", body)))
        missing = [path for path in paths if not (args.copy / path).exists()]
        texts[name] = {
            "skip_markers": [marker for marker in SKIP_MARKERS if marker in body.lower()],
            "repo_paths_named": paths,
            "missing_in_copy": missing,
            "pr_numbers": sorted(set(re.findall(r"(?:juniper-[a-z-]+)?#\d+", body))),
            "trailer_like_last_line": bool(re.match(r"^[A-Za-z-]+: \S", body.rstrip("\n").splitlines()[-1])),
            "lines": len(body.splitlines()),
        }
    report["texts"] = texts
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

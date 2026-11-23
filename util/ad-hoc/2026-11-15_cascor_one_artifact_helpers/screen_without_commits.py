"""Apply the sequence-safety docs screen's own classifier, and a duplicated-def scan, to BASE vs HEAD trees (no commits).

Usage: python3 -I screen_without_commits.py BASE_TREE HEAD_TREE --docs REL [REL ...] --py REL [REL ...]
Prints each docs finding (FAIL / WARN, as juniper-docs-additions-check would) and any def name bound twice in one scope.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import ast
import subprocess
import sys
from pathlib import Path

from juniper_ci_tools import docs_additions_check as dac


def docs(base: Path, head: Path, rel: str) -> int:
    old, new = base / rel, head / rel
    proc = subprocess.run(["diff", "-U0", str(old), str(new)], capture_output=True, text=True, check=False)
    hunks = dac.parse_hunks(proc.stdout)
    findings = dac.classify_file(rel, hunks, dac.DEFAULT_MIN_RUN, dac.fenced_lines(old.read_text(encoding="utf-8")), dac.fenced_lines(new.read_text(encoding="utf-8")))
    fails = [f for f in findings if f.severity == "FAIL"]
    print(f"{rel}: {len(hunks)} hunk(s), {len(fails)} FAIL, {len(findings) - len(fails)} other")
    for f in findings:
        print(f"    {f.severity} {f.reason} {f.detail}")
    return len(fails)


def duplicates(head: Path, rel: str) -> int:
    tree = ast.parse((head / rel).read_text(encoding="utf-8"))
    found = 0
    scopes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
    for scope in scopes:
        names = [n.name for n in scope.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        dup = sorted({n for n in names if names.count(n) > 1})
        if dup:
            found += len(dup)
            print(f"{rel}: duplicated in {getattr(scope, 'name', '<module>')}: {dup}")
    print(f"{rel}: {found} duplicated def name(s)")
    return found


def main() -> int:
    base, head = Path(sys.argv[1]), Path(sys.argv[2])
    rest = sys.argv[3:]
    docs_files = rest[rest.index("--docs") + 1 : rest.index("--py")]
    py_files = rest[rest.index("--py") + 1 :]
    bad = sum(docs(base, head, rel) for rel in docs_files) + sum(duplicates(head, rel) for rel in py_files)
    print(f"total blocking: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

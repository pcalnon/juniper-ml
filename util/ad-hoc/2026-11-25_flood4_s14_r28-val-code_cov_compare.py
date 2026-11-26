"""
Compare what two runs of juniper-canopy's X7 site tests executed in the code under test, per test, from each run's
coverage database (recorded with --cov-context=test).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code

Usage (run with an interpreter that has coverage installed):
    python <this file> --old <old .coverage> --old-tree <tree> --new <new .coverage> --new-tree <tree> --out <json>

For each code-under-test file (src/backend/cascor_service_adapter.py, src/backend/service_backend.py,
src/backend/state_sync.py) and each test context (the test function name, the parametrisation and phase stripped,
the renamed control mapped to its old name), the set of executed line numbers in each run, and the two differences.
Line numbers are comparable because the code under test is byte-identical in both trees (checked here by sha256).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import coverage

FILES = ["src/backend/cascor_service_adapter.py", "src/backend/service_backend.py", "src/backend/state_sync.py"]
RENAMED = {"test_the_held_call_detects_an_inline_call": "test_the_ticker_detects_an_inline_block"}


def per_test(db: str, tree: Path) -> dict:
    data = coverage.CoverageData(basename=db)
    data.read()
    out: dict = {}
    contexts = data.measured_contexts()
    for rel in FILES:
        path = str((tree / rel).resolve())
        out[rel] = {}
        for context in contexts:
            if not context:
                continue
            data.set_query_contexts([re.escape(context)])
            lines = data.lines(path) or []
            name = context.split("::")[-1].split("|")[0]
            name = re.sub(r"\[.*\]$", "", name)
            name = RENAMED.get(name, name)
            out[rel].setdefault(name, set()).update(lines)
        data.set_query_contexts(None)
    return out


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True)
    parser.add_argument("--old-tree", required=True)
    parser.add_argument("--new", required=True)
    parser.add_argument("--new-tree", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    old_tree, new_tree = Path(args.old_tree), Path(args.new_tree)
    same = {rel: sha(old_tree / rel) == sha(new_tree / rel) for rel in FILES}
    old, new = per_test(args.old, old_tree), per_test(args.new, new_tree)
    report: dict = {"code_under_test_identical": same, "files": {}}
    for rel in FILES:
        tests = sorted(set(old[rel]) | set(new[rel]))
        rows = {}
        for test in tests:
            a, b = old[rel].get(test, set()), new[rel].get(test, set())
            if not a and not b:
                continue
            rows[test] = {"old_lines": len(a), "new_lines": len(b), "only_old": sorted(a - b), "only_new": sorted(b - a)}
        union_old = set().union(*old[rel].values()) if old[rel] else set()
        union_new = set().union(*new[rel].values()) if new[rel] else set()
        report["files"][rel] = {"per_test": rows, "file_union_old": len(union_old), "file_union_new": len(union_new), "file_only_old": sorted(union_old - union_new), "file_only_new": sorted(union_new - union_old)}
    Path(args.out).write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({rel: {k: v for k, v in body.items() if k != "per_test"} for rel, body in report["files"].items()}, indent=1))
    print(json.dumps(report["code_under_test_identical"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Flood-4 validation: prove every test the carrier adds to a sub-package is COLLECTED and RUN (not skipped)
under that sub-package's own pytest config, the way its CI workflow invokes it.

For each carrier-touched file under juniper-service-core/tests/ and juniper-ci-tools/tests/, the AST gives
the test functions/methods the carrier ADDED (vs origin/main); pytest is then run on the file exactly as the
workflow would (service-core: `pytest juniper-service-core/tests/<file>` from the repo root; ci-tools: from
juniper-ci-tools/), with junit XML, and every added test must appear as passed (no skip, no xfail).

Usage: python3 <this> <out.json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens), item 2
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses pytest's own junit output
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=HERE, check=check, capture_output=True, text=True)


def test_names(src: str) -> set[str]:
    names: set[str] = set()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            names.add(node.name)
        if isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test"):
                    names.add(f"{node.name}::{sub.name}")
    return names


def async_unmarked(src: str) -> list[str]:
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.AsyncFunctionDef) and node.name.startswith("test"):
            decos = [ast.unparse(d) for d in node.decorator_list]
            if not any("asyncio" in d for d in decos):
                out.append(node.name)
    return out


def main() -> int:
    out = Path(sys.argv[1])
    paths = [p for p in git("diff", "--name-only", "--no-renames", BASE, TREE).stdout.splitlines() if p.startswith(("juniper-service-core/tests/", "juniper-ci-tools/tests/")) and p.endswith(".py")]
    rows = []
    for p in paths:
        new_src = (HERE / p).read_text()
        old = git("show", f"{BASE}:{p}", check=False)
        added = sorted(test_names(new_src) - (test_names(old.stdout) if old.returncode == 0 else set()))
        pkg = p.split("/")[0]
        junit = HERE / "tmp" / f"val_junit_{Path(p).stem}.xml"
        env = dict(os.environ, PYTHONPATH=str(HERE / pkg))
        if pkg == "juniper-service-core":
            cmd = [sys.executable, "-m", "pytest", p, "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
            cwd = HERE
        else:
            cmd = [sys.executable, "-m", "pytest", p.split("/", 1)[1], "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
            cwd = HERE / pkg
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=900)
        results: dict[str, str] = {}
        for case in ET.parse(junit).getroot().iter("testcase"):
            cls = case.get("classname", "").split(".")[-1]
            name = case.get("name", "").split("[")[0]
            status = "passed"
            for child in case:
                if child.tag in ("skipped", "failure", "error"):
                    status = child.tag
            key = f"{cls}::{name}" if cls and not cls.startswith("test_") else name
            prev = results.get(key)
            results[key] = status if prev in (None, "passed") else prev
        junit.unlink()
        missing = [t for t in added if t not in results]
        not_passed = {t: results[t] for t in added if t in results and results[t] != "passed"}
        rows.append({"path": p, "rc": r.returncode, "added_tests": len(added), "missing_from_run": missing, "not_passed": not_passed, "async_unmarked": async_unmarked(new_src), "summary": r.stdout.strip().splitlines()[-1:]})
        print(f"{p}: rc={r.returncode} added={len(added)} missing={missing} not_passed={not_passed} async_unmarked={async_unmarked(new_src)} {r.stdout.strip().splitlines()[-1:]}")
    out.write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

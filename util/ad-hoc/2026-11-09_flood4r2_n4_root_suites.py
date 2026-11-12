#!/usr/bin/env python3
"""
Run juniper-ml root regression suites one process each, as ci.yml's regression step does, and tabulate the outcomes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (verification evidence for the N-4 fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         .github/workflows/ci.yml (the regression step: one ``python3 -m unittest -v tests/<file>`` per suite)

Each suite named in ``--list`` (one ``tests/test_*.py`` path per line) runs as
``<python> -m unittest -v <path>`` from ``--tree``, at most four at a time, each bounded by a
timeout. Before running, it refuses when any ``pyproject.toml`` sits under the tree's ``tmp/``:
``tests/test_release_train_registry.py`` walks ``tmp/`` and would read it as a package. Usage::

    python3 <this file> --tree <root> --list <file> --python <interpreter> --out <json>
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SUITE_TIMEOUT_SECONDS = 1800


def _run(tree: Path, python: str, suite: str) -> dict:
    try:
        proc = subprocess.run([python, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT_SECONDS, check=False)
    except subprocess.TimeoutExpired:
        # Round 2: a suite that outruns the bound is one row, not the end of the whole run (the results are written last).
        return {"suite": suite, "exit": "timeout", "ran": None, "verdict": f"no result within {SUITE_TIMEOUT_SECONDS} s", "failed": []}
    text = proc.stderr + proc.stdout
    ran = re.findall(r"^Ran (\d+) tests?", text, flags=re.MULTILINE)
    verdict = re.findall(r"^(OK.*|FAILED.*)$", text, flags=re.MULTILINE)
    failed = re.findall(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", text, flags=re.MULTILINE)
    return {"suite": suite, "exit": proc.returncode, "ran": int(ran[-1]) if ran else None, "verdict": verdict[-1] if verdict else text[-400:], "failed": failed}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--list", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    tree = args.tree.resolve()
    strays = sorted(str(p) for p in (tree / "tmp").rglob("pyproject.toml")) if (tree / "tmp").is_dir() else []
    if strays:
        print(json.dumps({"refused": "pyproject.toml under tmp/", "paths": strays[:20]}, indent=1))
        return 2
    suites = [line.strip() for line in args.list.read_text(encoding="utf-8").splitlines() if line.strip()]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda s: _run(tree, args.python, s), suites))
    bad = [r for r in results if r["exit"] != 0]
    summary = {"tree": str(tree), "python": args.python, "suites": len(results), "tests": sum(r["ran"] or 0 for r in results), "failing_suites": [r["suite"] for r in bad]}
    args.out.write_text(json.dumps({"summary": summary, "results": results}, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

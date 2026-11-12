#!/usr/bin/env python3
"""
Stress repeat: run one pytest file N times per interpreter, each run in a fresh process, and count the outcomes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (flakiness evidence for the N-4 pins)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (section 8, ruling 11);
         juniper-service-core/tests/test_websocket_broadcast_drop_close.py

The interpreters run concurrently (one stream each, at most four); runs within a stream are
sequential. PYTHONPATH is the tree's ``juniper-service-core`` and ``juniper-model-core``; nothing is
written into the tree (``-p no:cacheprovider``, no bytecode, ``--basetemp`` under ``--out``). Usage::

    python3 <this file> --tree <root> --test <path under root> --runs N --out <dir> <python> [<python> ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def _stream(python: str, tree: Path, test: str, runs: int, out: Path, index: int) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(tree / "juniper-service-core"), str(tree / "juniper-model-core")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    outcomes: dict[str, int] = {}
    failures: list[str] = []
    for run in range(runs):
        cmd = [python, "-m", "pytest", test, "-q", "-p", "no:cacheprovider", f"--basetemp={out / f'bt-{index}'}"]
        proc = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True, timeout=600, check=False)
        summary = next((line for line in reversed(proc.stdout.splitlines()) if re.search(r"\d+ (passed|failed)", line)), "no summary")
        key = f"exit={proc.returncode} {re.sub(r' in [0-9.]+s', '', summary).strip('= ')}"
        outcomes[key] = outcomes.get(key, 0) + 1
        if proc.returncode != 0:
            failures.append(f"run {run}: {proc.stdout[-2000:]}")
    return {"python": python, "runs": runs, "outcomes": outcomes, "failures": failures[:5]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--test", required=True)
    parser.add_argument("--runs", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("pythons", nargs="+")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tree = args.tree.resolve()
    with ThreadPoolExecutor(max_workers=min(4, len(args.pythons))) as pool:
        results = list(pool.map(lambda pair: _stream(pair[1], tree, args.test, args.runs, out, pair[0]), enumerate(args.pythons)))
    print(json.dumps(results, indent=1))
    return 0 if all(not r["failures"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

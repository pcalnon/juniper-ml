#!/usr/bin/env python3
"""
Run juniper-cascor-worker's tests/test_gitleaks_pr_scan.py five ways on a given tree and record each run's counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor-worker)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530

WHY THIS EXISTS
Adapted from 2026-11-12_flood4r2_r10-data-client_file_five_ways.py (the pilot's). The port's pull-request text states
how the new test file behaves with no engine, with two builds of the engine, on the oldest Python CI uses and under a
second pytest. juniper-cascor-worker's tests/conftest.py imports the package, so every run here uses an interpreter
that holds it (no --noconftest), and the counts are this port's 26 cases. The five runs:

    no-binary         the main interpreter, GITLEAKS_BIN and GITLEAKS_PARITY_REQUIRED unset (the unit lane's situation)
    official-engine   the main interpreter, the official release binary, GITLEAKS_PARITY_REQUIRED=1
    precommit-engine  the main interpreter, pre-commit's source build, GITLEAKS_PARITY_REQUIRED=1
    python312         the second interpreter (the oldest Python CI uses), the official binary, required
    other-pytest      the third interpreter (another pytest and pytest-asyncio), the official binary, required

Each run is one pytest process with its own basetemp under --out; at most four run side by side. Every run has the six
Sentry DSN variables set to the empty string, writes no bytecode and no pytest cache, and its counts are read from its
junit report. Nothing is written into the tree.

Usage:
  2026-11-14_flood4r2_r10-cascor-worker_file_five_ways.py --tree <checkout> --out <dir> --python <main interpreter>
      --python312 <interpreter> --python-other <interpreter> --engine <official binary> --engine-precommit <binary>

Exit 0 = no-binary passed 18 and skipped 8, and each of the other four passed 26; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - fixed argv: the chosen interpreters running pytest, and the engines' version command
import sys
import xml.etree.ElementTree as ElementTree
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
TEST_FILE = "tests/test_gitleaks_pr_scan.py"
ENGINE_NAMES = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")


def said(argv: list[str]) -> str:
    res = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603
    return (res.stdout + res.stderr).strip().splitlines()[0] if (res.stdout + res.stderr).strip() else ""


def run(label: str, python: str, engine: str | None, extra: list[str], tree: Path, out: Path) -> dict:
    env = {name: value for name, value in os.environ.items() if name not in ENGINE_NAMES}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if engine is not None:
        env["GITLEAKS_BIN"] = engine
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    junit = out / f"file-{label}.junit.xml"
    argv = [python, "-m", "pytest", TEST_FILE, "-v", "-v", "--timeout=300", "-p", "no:cacheprovider", f"--basetemp={out / 'basetemp' / label}", f"--junitxml={junit}", *extra]
    res = subprocess.run(argv, cwd=tree, capture_output=True, text=True, env=env, check=False)  # nosec B603
    log = out / f"file-{label}.log"
    log.write_text("$ " + " ".join(argv) + "\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    if junit.is_file():
        for case in ElementTree.parse(junit).getroot().iter("testcase"):
            if case.find("failure") is not None:
                counts["failed"] += 1
            elif case.find("error") is not None:
                counts["error"] += 1
            elif case.find("skipped") is not None:
                counts["skipped"] += 1
            else:
                counts["passed"] += 1
    return {
        "label": label,
        "interpreter": python,
        "python_version": said([python, "--version"]),
        "pytest_version": said([python, "-m", "pytest", "--version"]),
        "engine": engine,
        "engine_sha256": hashlib.sha256(Path(engine).read_bytes()).hexdigest() if engine else None,
        "engine_version": said([engine, "version"]) if engine else None,
        "command": " ".join(argv),
        "exit": res.returncode,
        "counts": counts,
        "log": str(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--python312", required=True)
    parser.add_argument("--python-other", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--engine-precommit", required=True)
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    (out / "basetemp").mkdir(parents=True, exist_ok=True)
    for stale in (tree / "tests" / "__pycache__").glob("test_gitleaks_pr_scan*.pyc"):
        stale.unlink()
    plan = [
        ("no-binary", args.python, None, []),
        ("official-engine", args.python, args.engine, []),
        ("precommit-engine", args.python, args.engine_precommit, []),
        ("python312", args.python312, args.engine, []),
        ("other-pytest", args.python_other, args.engine, []),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run, label, python, engine, extra, tree, out) for label, python, engine, extra in plan]
        rows = [future.result() for future in futures]
    test_file = tree / TEST_FILE
    record = {"tree": str(tree), "test_file_sha256": hashlib.sha256(test_file.read_bytes()).hexdigest(), "runs": rows}
    (out / "file_five_ways.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    ok = True
    for row in rows:
        want = {"passed": 18, "failed": 0, "error": 0, "skipped": 8} if row["label"] == "no-binary" else {"passed": 26, "failed": 0, "error": 0, "skipped": 0}
        good = row["counts"] == want and row["exit"] == 0
        ok = ok and good
        print(f"{'ok  ' if good else 'BAD '} {row['label']:<17} exit={row['exit']} {row['counts']}  [{row['python_version']}; {row['pytest_version']}; engine {row['engine_version']}]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

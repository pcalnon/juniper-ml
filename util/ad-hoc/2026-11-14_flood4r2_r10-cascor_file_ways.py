#!/usr/bin/env python3
"""
Run juniper-cascor's src/tests/unit/test_gitleaks_pr_scan.py the ways CI and a developer run it, and record each run's counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor; adapted from
        2026-11-12_flood4r2_r10-data-client_file_five_ways.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530

WHY THIS EXISTS
juniper-cascor's unit lane selects by marker (`-m "unit and not slow" src/tests/unit`) and loads src/tests/conftest.py,
which imports torch and cascor's modules; the Security Scans self-test runs the same file with `--noconftest` in a job
that installs only pytest, pytest-asyncio, pytest-timeout and PyYAML for it. Each claim the port's texts make about the
file is one run here:

    unit-lane-no-binary     the env interpreter, the unit lane's -m expression and timeouts, the conftest, no binary
    selftest-official       the env interpreter, ci.yml's self-test arguments (--noconftest), the official binary
    selftest-precommit      the same with pre-commit's source build of 8.24.3
    selftest-min-venv       a venv holding only the four packages the job installs, the binary found on PATH as in CI
    conftest-official       the env interpreter, the conftest loaded, the official binary (a developer's plain run)
    parity-no-binary        GITLEAKS_PARITY_REQUIRED=1 and no binary: the eight real-engine cases must ERROR, not skip
    min-venv-with-conftest  the minimal venv WITHOUT --noconftest: shows why the self-test passes it

Each run is one pytest process with its own basetemp under --out; at most four run side by side. Every run has the six
Sentry DSN variables set to the empty string, writes no bytecode and no pytest cache, and its counts are read from its
junit report (or, when collection fails before one is written, from its exit status). Nothing is written into the tree.

Usage:
  python3 <this> --tree <juniper-cascor checkout> --out <dir> --python <env interpreter> --python-min <venv interpreter>
      --engine <official binary> --engine-precommit <binary>

Exit 0 = every run matched its expectation (listed in PLAN below); 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - runs pytest and gitleaks with fixed argv
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree  # nosec B405 - parses the junit report pytest wrote in this run

TEST_FILE = "src/tests/unit/test_gitleaks_pr_scan.py"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
UNIT_LANE = ["-m", "unit and not slow", "--verbose", "--timeout=60", "--maxfail=5"]
SELF_TEST = ["--noconftest", "-v", "-v", "--timeout=120"]


def said(argv: list[str]) -> str:
    res = subprocess.run(argv, capture_output=True, text=True, check=False)  # nosec B603
    return (res.stdout or res.stderr).strip().splitlines()[0] if (res.stdout or res.stderr).strip() else f"[exit {res.returncode}]"


def run(label: str, python: str, engine: str | None, via: str, parity: bool, extra: list[str], tree: Path, out: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if parity:
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    if engine is not None and via == "bin":
        env["GITLEAKS_BIN"] = engine
    if engine is not None and via == "path":
        env["PATH"] = str(Path(engine).parent) + os.pathsep + env.get("PATH", os.defpath)
    junit = out / f"file-{label}.junit.xml"
    argv = [python, "-m", "pytest", TEST_FILE, *extra, "-p", "no:cacheprovider", f"--basetemp={out / 'basetemp' / label}", f"--junitxml={junit}"]
    res = subprocess.run(argv, cwd=tree, capture_output=True, text=True, env=env, check=False, timeout=1800)  # nosec B603
    log = out / f"file-{label}.log"
    log.write_text("$ " + " ".join(argv) + "\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    counts = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
    if junit.is_file():
        for case in ElementTree.parse(junit).getroot().iter("testcase"):  # nosec B314 - this run's own report
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
        "engine_found_via": via if engine else None,
        "engine_sha256": hashlib.sha256(Path(engine).read_bytes()).hexdigest() if engine else None,
        "engine_version": said([engine, "version"]) if engine else None,
        "parity_required": parity,
        "command": " ".join(argv),
        "exit": res.returncode,
        "counts": counts,
        "junit_written": junit.is_file(),
        "log": str(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--python-min", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--engine-precommit", required=True)
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    (out / "basetemp").mkdir(parents=True, exist_ok=True)
    for stale in (tree / "src" / "tests" / "unit" / "__pycache__").glob("test_gitleaks_pr_scan*.pyc"):
        stale.unlink()
    ok25 = {"passed": 25, "failed": 0, "error": 0, "skipped": 0}
    # (label, interpreter, engine, how the engine is found, parity, extra argv, expected counts, expected exit)
    plan = [
        ("unit-lane-no-binary", args.python, None, "", False, UNIT_LANE, {"passed": 17, "failed": 0, "error": 0, "skipped": 8}, 0),
        ("selftest-official", args.python, args.engine, "bin", True, SELF_TEST, ok25, 0),
        ("selftest-precommit", args.python, args.engine_precommit, "bin", True, SELF_TEST, ok25, 0),
        ("selftest-min-venv", args.python_min, args.engine, "path", True, SELF_TEST, ok25, 0),
        ("conftest-official", args.python, args.engine, "bin", True, ["-v", "--timeout=120"], ok25, 0),
        ("parity-no-binary", args.python, None, "", True, SELF_TEST, {"passed": 17, "failed": 0, "error": 8, "skipped": 0}, 1),
        ("min-venv-with-conftest", args.python_min, args.engine, "path", True, ["-v", "-v", "--timeout=120"], None, None),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run, label, python, engine, via, parity, extra, tree, out) for label, python, engine, via, parity, extra, _, _ in plan]
        rows = [future.result() for future in futures]
    record = {"tree": str(tree), "test_file_sha256": hashlib.sha256((tree / TEST_FILE).read_bytes()).hexdigest(), "runs": rows}
    ok = True
    for row, (_, _, _, _, _, _, want, want_exit) in zip(rows, plan):
        if want is None:
            # The negative case: it must fail, whatever its counts.
            good = row["exit"] != 0
        else:
            good = row["counts"] == want and row["exit"] == want_exit
        row["expected"] = {"counts": want, "exit": want_exit if want is not None else "non-zero"}
        row["as_expected"] = good
        ok = ok and good
        print(f"{'ok  ' if good else 'BAD '} {row['label']:<23} exit={row['exit']} {row['counts']}  [{row['python_version']}; {row['pytest_version']}; engine {row['engine_version']}]")
    (out / "file_ways.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

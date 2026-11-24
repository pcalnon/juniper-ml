#!/usr/bin/env python3
"""
Run juniper-deploy's tests/test_gitleaks_pr_scan.py five ways on a given tree and record each run's counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-deploy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530

WHY THIS EXISTS
Adapted from 2026-11-14_flood4r2_r10-cascor-worker_file_five_ways.py. The port's pull-request text states how the new
test file behaves with no engine, with two builds of the engine, under the Gitleaks job's own interpreter pair (Python
3.12 and pytest 9.2.0, from requirements-test.txt), and as the job's self-test step runs it. juniper-deploy's
requirements-test.txt installs no pytest-timeout, so no run passes --timeout (each run is bounded here instead), and
pyproject.toml's addopts carry no -q, so one -v is enough. The five runs:

    no-binary         the main interpreter, GITLEAKS_BIN and GITLEAKS_PARITY_REQUIRED unset (the unit lane's situation)
    official-engine   the main interpreter, the official release binary, GITLEAKS_PARITY_REQUIRED=1
    precommit-engine  the main interpreter, pre-commit's source build, GITLEAKS_PARITY_REQUIRED=1
    python312         the CI-pair interpreter, the official binary, required
    self-test-step    the CI-pair interpreter first on PATH as `pytest`, the official binary first on PATH as `gitleaks`
                      (no GITLEAKS_BIN), GITLEAKS_PARITY_REQUIRED=1, and the step's own `run:` text (read from the
                      tree's ci.yml) under `bash -e -c`, the shell GitHub uses for a step that names none

Each run is one pytest process with its own basetemp under --out; at most four run side by side. Every run has the six
Sentry DSN variables set to the empty string, writes no bytecode and no pytest cache, and its counts are read from its
junit report. Nothing is written into the tree.

Usage:
  2026-11-14_flood4r2_r10-deploy_file_ways.py --tree <checkout> --out <dir> --python <main interpreter>
      --python312 <CI-pair interpreter> --engine <official binary> --engine-precommit <binary> [--expect-cases 25]

Exit 0 = no-binary passed (cases - 8) and skipped 8, and each of the other four passed every case; 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv: the chosen interpreters running pytest, bash running the step's text, the engines' version command
import sys
import xml.etree.ElementTree as ElementTree
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
TEST_FILE = "tests/test_gitleaks_pr_scan.py"
SELF_TEST_STEP = "Gitleaks pull-request scan self-test (real engine)"
ENGINE_NAMES = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
REAL_ENGINE_CASES = 8


def said(argv: list[str]) -> str:
    res = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=120)  # nosec B603
    return (res.stdout + res.stderr).strip().splitlines()[0] if (res.stdout + res.stderr).strip() else ""


def counts_of(junit: Path) -> dict:
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
    return counts


def run(label: str, python: str, engine: str | None, tree: Path, out: Path) -> dict:
    env = {name: value for name, value in os.environ.items() if name not in ENGINE_NAMES}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    junit = out / f"file-{label}.junit.xml"
    common = ["-p", "no:cacheprovider", f"--basetemp={out / 'basetemp' / label}", f"--junitxml={junit}"]
    if label == "self-test-step":
        # The step's own text, with this run's report options appended: the step's `run:` is one pytest command line.
        steps = yaml.safe_load((tree / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]["gitleaks"]["steps"]
        step_run = next(str(s["run"]).strip() for s in steps if s.get("name") == SELF_TEST_STEP)
        bindir = out / "self-test-bin"
        bindir.mkdir(parents=True, exist_ok=True)
        for name, target in (("gitleaks", engine), ("pytest", str(Path(python).parent / "pytest"))):
            link = bindir / name
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(target)
        env["PATH"] = f"{bindir}{os.pathsep}{env.get('PATH', os.defpath)}"
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
        argv = ["bash", "-e", "-c", step_run + " " + " ".join(common)]
    else:
        if engine is not None:
            env["GITLEAKS_BIN"] = engine
            env["GITLEAKS_PARITY_REQUIRED"] = "1"
        argv = [python, "-m", "pytest", TEST_FILE, "-v", *common]
    res = subprocess.run(argv, cwd=tree, capture_output=True, text=True, env=env, check=False, timeout=1500)  # nosec B603
    log = out / f"file-{label}.log"
    log.write_text("$ " + " ".join(argv) + "\n" + res.stdout + "\n--- stderr ---\n" + res.stderr + f"\n[exit {res.returncode}]\n", encoding="utf-8")
    return {
        "label": label,
        "interpreter": python,
        "python_version": said([python, "--version"]),
        "pytest_version": said([python, "-m", "pytest", "--version"]),
        "engine": engine,
        "engine_sha256": hashlib.sha256(Path(engine).read_bytes()).hexdigest() if engine else None,
        "engine_version": said([engine, "version"]) if engine else None,
        "which_gitleaks_in_run": shutil.which("gitleaks", path=env.get("PATH")),
        "command": " ".join(argv),
        "exit": res.returncode,
        "counts": counts_of(junit),
        "log": str(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--python312", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--engine-precommit", required=True)
    parser.add_argument("--expect-cases", type=int, default=25)
    args = parser.parse_args()
    tree, out = args.tree.resolve(), args.out.resolve()
    (out / "basetemp").mkdir(parents=True, exist_ok=True)
    for stale in (tree / "tests" / "__pycache__").glob("test_gitleaks_pr_scan*.pyc"):
        stale.unlink()
    plan = [
        ("no-binary", args.python, None),
        ("official-engine", args.python, args.engine),
        ("precommit-engine", args.python, args.engine_precommit),
        ("python312", args.python312, args.engine),
        ("self-test-step", args.python312, args.engine),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run, label, python, engine, tree, out) for label, python, engine in plan]
        rows = [future.result() for future in futures]
    test_file = tree / TEST_FILE
    record = {"tree": str(tree), "test_file_sha256": hashlib.sha256(test_file.read_bytes()).hexdigest(), "runs": rows}
    (out / "file_ways.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    ok = True
    cases = args.expect_cases
    for row in rows:
        if row["label"] == "no-binary":
            want = {"passed": cases - REAL_ENGINE_CASES, "failed": 0, "error": 0, "skipped": REAL_ENGINE_CASES}
        else:
            want = {"passed": cases, "failed": 0, "error": 0, "skipped": 0}
        good = row["counts"] == want and row["exit"] == 0
        ok = ok and good
        print(f"{'ok  ' if good else 'BAD '} {row['label']:<17} exit={row['exit']} {row['counts']}  [{row['python_version']}; {row['pytest_version']}; engine {row['engine_version']}]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

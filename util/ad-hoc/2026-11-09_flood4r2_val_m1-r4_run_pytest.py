#!/usr/bin/env python3
"""
Run juniper-data's gitleaks test file (or CI's unit lane) on the round-4 validator's copy, in named engine modes.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round-4 validation of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
An independent runner, so the validator does not re-use the builder's: TMPDIR is left as the session gave it; only
pytest's --basetemp and GIT_CEILING_DIRECTORIES point under --out. Counts come from pytest's junit file. Modes run in
the order given, one pytest process at a time.

    official-parity    test file; the official 8.24.3 release binary first on PATH; GITLEAKS_PARITY_REQUIRED=1
    precommit-parity   test file; pre-commit's source build of v8.24.3 first on PATH; parity required
    no-binary          test file; no engine anywhere on PATH (as CI's unit job sees it)
    no-binary-parity   test file; no engine, parity required (every real-engine case must turn red)
    unit-lane          CI's unit lane: -m "unit and not slow" juniper_data/tests/unit --timeout=60 --maxfail=5

Usage:
    python3 <this> --worktree <copy> --out <scratch> --official <bin> --precommit <bin> --tag <t> <mode> [<mode> ...]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv: the JuniperData interpreter running pytest
import sys
import time
import xml.etree.ElementTree as ET  # nosec B405 - parses the junit file pytest itself just wrote
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
TEST_FILE = "juniper_data/tests/unit/test_gitleaks_config.py"
SCRUB = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
CLEAN_PATH = "/opt/miniforge3/envs/JuniperData/bin:/usr/local/bin:/usr/bin:/bin"


def junit_counts(path: Path) -> dict:
    if not path.is_file():
        return {"junit": "missing"}
    root = ET.parse(path).getroot()  # nosec B314 - pytest's own output
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    red: list[str] = []
    for case in root.iter("testcase"):
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        if case.find("failure") is not None:
            counts["failed"] += 1
            red.append(name)
        elif case.find("error") is not None:
            counts["errors"] += 1
            red.append(name)
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    return {**counts, "red": red}


def bindir(out: Path, name: str, target: str) -> str:
    d = out / f"bin-{name}"
    d.mkdir(parents=True, exist_ok=True)
    link = d / "gitleaks"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target)
    return str(d)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worktree", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--official", required=True)
    ap.add_argument("--precommit", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("modes", nargs="+")
    args = ap.parse_args()
    logs = args.out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    bt_root = args.out / "pytest-bt"
    bt_root.mkdir(parents=True, exist_ok=True)
    env_base = {k: v for k, v in os.environ.items() if k not in SCRUB}
    env_base["PYTHONDONTWRITEBYTECODE"] = "1"
    ceiling = env_base.get("GIT_CEILING_DIRECTORIES", "")
    env_base["GIT_CEILING_DIRECTORIES"] = f"{bt_root}:{ceiling}" if ceiling else str(bt_root)
    probe = shutil.which("gitleaks", path=CLEAN_PATH)
    if probe:
        print(f"a gitleaks is on the clean PATH ({probe}); abort")
        return 3
    results = {}
    for mode in args.modes:
        env = dict(env_base)
        targets = [TEST_FILE]
        extra: list[str] = []
        if mode == "official-parity":
            env["PATH"] = f"{bindir(args.out, 'official', args.official)}:{CLEAN_PATH}"
            env["GITLEAKS_PARITY_REQUIRED"] = "1"
        elif mode == "precommit-parity":
            env["PATH"] = f"{bindir(args.out, 'precommit', args.precommit)}:{CLEAN_PATH}"
            env["GITLEAKS_PARITY_REQUIRED"] = "1"
        elif mode == "no-binary":
            env["PATH"] = CLEAN_PATH
        elif mode == "no-binary-parity":
            env["PATH"] = CLEAN_PATH
            env["GITLEAKS_PARITY_REQUIRED"] = "1"
        elif mode == "unit-lane":
            env["PATH"] = CLEAN_PATH
            targets = ["juniper_data/tests/unit"]
            extra = ["-m", "unit and not slow", "--timeout=60", "--maxfail=5"]
        else:
            print(f"unknown mode {mode}")
            return 2
        label = f"{mode}{args.tag}"
        bt = bt_root / label
        if bt.exists():
            shutil.rmtree(bt)
        junit = logs / f"junit_{label}.xml"
        log = logs / f"pytest_{label}.log"
        argv = [PYTHON, "-m", "pytest", *extra, *targets, "-p", "no:cacheprovider", "-q", "-rs", f"--basetemp={bt}", f"--junitxml={junit}"]
        t0 = time.time()
        with log.open("w") as fh:
            proc = subprocess.run(argv, cwd=args.worktree, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False)  # nosec B603
        res = {"exit": proc.returncode, "seconds": round(time.time() - t0, 1), **junit_counts(junit), "argv": argv[1:]}
        results[label] = res
        tail = log.read_text(errors="replace").splitlines()[-2:]
        print(json.dumps({label: {k: v for k, v in res.items() if k != "argv"}, "tail": tail}))
        sys.stdout.flush()
    (logs / f"pytest_results{args.tag}.json").write_text(json.dumps(results, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

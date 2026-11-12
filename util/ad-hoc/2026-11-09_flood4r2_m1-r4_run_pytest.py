#!/usr/bin/env python3
"""
Run juniper-data's pytest in one named configuration and log it, with junit counts, under the round-4 directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (round 4 of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
Round 2's runner (2026-11-08_flood4r2_jd-gitleaks_run_pytest.py) pointed TMPDIR at its scratch directory. Session 4's
brief forbids changing TMPDIR at all, so this one leaves it as the session gave it and keeps only pytest's --basetemp
and GIT_CEILING_DIRECTORIES under --out. It also writes a junit XML file per run, so the counts it prints come from
pytest's own record rather than from a summary line. Modes:

    real-official   test_gitleaks_config.py, GITLEAKS_BIN = the official 8.24.3 release binary, parity required
    real-precommit  the same, with pre-commit's source build of v8.24.3
    no-binary       test_gitleaks_config.py with no engine, as CI's unit job sees it
    lane-file       CI's unit-lane options (-m "unit and not slow" --timeout=60 --maxfail=5) on test_gitleaks_config.py
    unit-lane       CI's unit lane: -m "unit and not slow" juniper_data/tests/unit --timeout=60 --maxfail=5 (no binary)
    full            every test under testpaths, with the official engine and parity required
    nodes           the node ids given after --, with the official engine and parity required

pytest runs in one process (juniper-data has no pytest-xdist), well inside the brief's four-worker cap.

Usage:
    python3 <this> --worktree <juniper-data worktree> --out <r4 dir> --mode <mode> --official <bin> [--precommit <bin>] [--tag <t>] [-- <pytest args>]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 - fixed argv: the JuniperData interpreter running pytest
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses the junit file pytest itself just wrote
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
TEST_FILE = "juniper_data/tests/unit/test_gitleaks_config.py"
SCRUB = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
LANE = ["-m", "unit and not slow", "--timeout=60", "--maxfail=5"]


def junit_counts(path: Path) -> dict:
    """Counts and the failed/errored node names from pytest's junit file."""
    if not path.is_file():
        return {"junit": "missing"}
    root = ET.parse(path).getroot()  # nosec B314 - pytest's own output
    cases = root.iter("testcase")
    counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    red: list[str] = []
    for case in cases:
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", required=True, choices=["real-official", "real-precommit", "no-binary", "lane-file", "unit-lane", "full", "nodes"])
    ap.add_argument("--official", type=Path, required=True, help="the official gitleaks 8.24.3 release binary")
    ap.add_argument("--precommit", type=Path, default=Path.home() / ".cache" / "pre-commit" / "repotw5tescj" / "golangenv-system" / "bin" / "gitleaks")
    ap.add_argument("--tag", default="", help="suffix for the log, junit and basetemp names")
    ap.add_argument("extra", nargs="*")
    args = ap.parse_args()

    label = args.mode + args.tag
    basetemp = args.out / "pytest-bt" / label
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    logs = args.out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    junit = logs / f"junit_{label}.xml"
    env = {k: v for k, v in os.environ.items() if k not in SCRUB}
    ceiling = [str(basetemp.parent)] + ([env["GIT_CEILING_DIRECTORIES"]] if env.get("GIT_CEILING_DIRECTORIES") else [])
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "GIT_CEILING_DIRECTORIES": os.pathsep.join(ceiling)})
    argv = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", f"--basetemp={basetemp}", f"--junitxml={junit}"]
    engine = {"real-official": args.official, "full": args.official, "nodes": args.official, "real-precommit": args.precommit}.get(args.mode)
    if engine is not None:
        if not engine.is_file():
            raise SystemExit(f"no engine at {engine}")
        env["GITLEAKS_BIN"] = str(engine)
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    elif shutil.which("gitleaks", path=env.get("PATH")):
        raise SystemExit("a gitleaks binary is on PATH; the no-engine modes need PATH without one")
    if args.mode in ("real-official", "real-precommit", "no-binary"):
        argv += [TEST_FILE, "-v", "-rA"]
    elif args.mode == "lane-file":
        argv += [*LANE, TEST_FILE, "-v", "-rA"]
    elif args.mode == "unit-lane":
        argv += [*LANE, "juniper_data/tests/unit"]
    elif args.mode == "nodes":
        argv += ["-v", "-rA"]
    argv += args.extra
    log = logs / f"pytest_{label}.log"
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("$ " + " ".join(argv) + "\n")
        fh.write(f"# cwd={args.worktree} GITLEAKS_BIN={env.get('GITLEAKS_BIN', '<unset>')} GITLEAKS_PARITY_REQUIRED={env.get('GITLEAKS_PARITY_REQUIRED', '<unset>')} TMPDIR=<unchanged>\n")
        fh.flush()
        proc = subprocess.run(argv, cwd=args.worktree, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False)  # nosec B603
        fh.write(f"\n[exit {proc.returncode}]\n")
    counts = junit_counts(junit)
    print(f"mode={label} exit={proc.returncode} junit={counts}")
    print(f"log: {log}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

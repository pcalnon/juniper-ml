#!/usr/bin/env python3
"""
Run juniper-data's pytest in one named configuration (engine / no engine / unit lane / full suite) and log it under the round-2 directory.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (round 2 of the juniper-data pull-request Gitleaks fix)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
The session refuses compound shell lines, and every run needs the same hygiene: the JuniperData interpreter, the
GITLEAKS_* variables scrubbed and then set per mode, TMPDIR, pytest's basetemp and GIT_CEILING_DIRECTORIES all
under --r2 (never /tmp, and never above the scratch repositories a test builds), no cache or bytecode written into
the worktree. Modes:

    real-official   test_gitleaks_config.py, GITLEAKS_BIN = the official 8.24.3 release binary, parity required
    real-precommit  the same, with pre-commit's source build of v8.24.3
    no-binary       test_gitleaks_config.py with no engine, as CI's unit job sees it
    unit-lane       CI's unit lane: -m "unit and not slow" juniper_data/tests/unit --timeout=60 --maxfail=5 (no binary)
    full            every test under testpaths, with the official engine and parity required

Usage:
    python3 <this> --worktree <juniper-data worktree> --r2 <r2 dir> --mode <mode> [--official <bin>] [--precommit <bin>] [-- <extra pytest args>]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv: the JuniperData interpreter running pytest
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
TEST_FILE = "juniper_data/tests/unit/test_gitleaks_config.py"
SCRUB = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
SUMMARY = re.compile(r"^=*\s*(\d+ (passed|failed|error).*?)\s*=*$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--worktree", type=Path, required=True)
    ap.add_argument("--r2", type=Path, required=True)
    ap.add_argument("--mode", required=True, choices=["real-official", "real-precommit", "no-binary", "unit-lane", "full"])
    ap.add_argument("--official", type=Path, default=Path("/home/pcalnon/Development/python/Juniper/juniper-ml/tmp/val-a-m1/release/bin/gitleaks"))
    ap.add_argument("--precommit", type=Path, default=Path("/home/pcalnon/.cache/pre-commit/repotw5tescj/golangenv-system/bin/gitleaks"))
    ap.add_argument("--tag", default="", help="suffix for the log name")
    ap.add_argument("extra", nargs="*")
    args = ap.parse_args()

    basetemp = args.r2 / "pytest-basetemp" / (args.mode + args.tag)
    tmpdir = args.r2 / "pytest-tmpdir" / (args.mode + args.tag)
    if tmpdir.exists():
        shutil.rmtree(tmpdir)
    tmpdir.mkdir(parents=True)
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in SCRUB}
    env.update({"TMPDIR": str(tmpdir), "PYTHONDONTWRITEBYTECODE": "1", "GIT_CEILING_DIRECTORIES": f"{basetemp.parent}:{tmpdir.parent}"})
    argv = [PYTHON, "-m", "pytest", "-p", "no:cacheprovider", f"--basetemp={basetemp}"]
    if args.mode in ("real-official", "real-precommit"):
        env["GITLEAKS_BIN"] = str(args.official if args.mode == "real-official" else args.precommit)
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
        argv += [TEST_FILE, "-v", "-rA"]
    elif args.mode == "no-binary":
        argv += [TEST_FILE, "-v", "-rA"]
    elif args.mode == "unit-lane":
        argv += ["-m", "unit and not slow", "juniper_data/tests/unit", "--timeout=60", "--maxfail=5"]
    else:
        env["GITLEAKS_BIN"] = str(args.official)
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    if args.mode in ("no-binary", "unit-lane") and shutil.which("gitleaks", path=env.get("PATH")):
        raise SystemExit("a gitleaks binary is on PATH; the no-engine modes need PATH without one")
    argv += args.extra
    log = args.r2 / "logs" / f"pytest_{args.mode}{args.tag}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("$ " + " ".join(argv) + "\n")
        fh.write(f"# GITLEAKS_BIN={env.get('GITLEAKS_BIN', '<unset>')} GITLEAKS_PARITY_REQUIRED={env.get('GITLEAKS_PARITY_REQUIRED', '<unset>')}\n")
        fh.flush()
        proc = subprocess.run(argv, cwd=args.worktree, env=env, stdout=fh, stderr=subprocess.STDOUT, check=False)  # nosec B603
        fh.write(f"\n[exit {proc.returncode}]\n")
    with open(log, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    summary = next((m.group(1) for line in reversed(lines) if (m := SUMMARY.match(line.strip()))), "<no summary line>")
    print(f"mode={args.mode}{args.tag} exit={proc.returncode} summary: {summary}")
    print(f"log: {log}")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())

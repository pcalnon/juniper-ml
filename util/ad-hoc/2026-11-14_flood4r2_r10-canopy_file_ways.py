#!/usr/bin/env python3
"""
Run juniper-canopy's two Gitleaks test files the ways its two CI lanes run them, and record each run's counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-canopy)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530;
         adapted from 2026-11-12_flood4r2_r10-data-client_file_five_ways.py (the pilot's)

WHY THIS EXISTS
juniper-canopy runs its Gitleaks tests in two lanes, and the port's texts state how each behaves. The unit lane runs
src/tests/regression/ through src/tests/conftest.py under a negative marker expression, with no gitleaks binary. The
Security Scans job's self-test runs both files with --noconftest, `-o addopts=""` and only pytest and PyYAML installed,
with the engine on PATH and GITLEAKS_PARITY_REQUIRED=1. This reads the self-test's pytest line from the tree's own
ci.yml (so the command measured is the command CI runs), and runs:

    unit-lane-no-binary         the canopy interpreter, conftest, the unit lane's -m, the new file; no binary
    unit-lane-official-engine   the same, GITLEAKS_BIN = the official release binary, GITLEAKS_PARITY_REQUIRED=1
    unit-lane-precommit-engine  the same with pre-commit's source build of the engine
    selftest-py314              the workflow's self-test pytest line in a venv holding only pytest and PyYAML
                                (CPython 3.14, the job's version), the official binary first on PATH, required
    selftest-py312              the same in a CPython 3.12 venv (the oldest Python the unit lane uses)
    selftest-no-binary          the py314 self-test with no binary, required: it must FAIL, not skip

Each run is one pytest process with its own basetemp and junit report under --out; at most four run side by side.
Every run has the six Sentry DSN variables set to the empty string, writes no bytecode and no pytest cache. Nothing is
written into the tree. It prints no environment variable.

Usage:
    python3.14 <this> --tree <canopy checkout> --out <new dir> --canopy-python <interpreter with the test extra>
        --venv314 <venv python> --venv312 <venv python> --official <gitleaks> --precommit <gitleaks>
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess  # nosec B404 - runs pytest with fixed argv
import xml.etree.ElementTree as ET  # nosec B405 - parses junit reports this script's own runs wrote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
NEW_FILE = "src/tests/regression/test_gitleaks_pr_scan.py"
UNIT_LANE_MARKS = "not requires_cascor and not requires_server and not slow"
SELF_TEST_STEP = "Gitleaks config and pull-request scan self-test (real engine)"


def self_test_argv(tree: Path) -> list[str]:
    """The self-test step's pytest line, as ci.yml states it, minus the leading `python`."""
    steps = yaml.safe_load((tree / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    run = next(str(s["run"]) for s in steps if s.get("name") == SELF_TEST_STEP)
    line = next(ln for ln in run.splitlines() if ln.startswith("python -m pytest"))
    return shlex.split(line)[1:]


def counts(junit: Path) -> dict:
    if not junit.is_file():
        return {"junit": "missing"}
    root = ET.parse(junit).getroot()  # nosec B314 - this script's own report
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    total["passed"] = total["tests"] - total["failures"] - total["errors"] - total["skipped"]
    return total


def run(name: str, argv: list[str], tree: Path, out: Path, extra_env: dict[str, str], drop: tuple[str, ...], path_prefix: str | None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env.update({n: "" for n in SENTRY_DSN_NAMES})
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"})
    env.update(extra_env)
    if path_prefix:
        env["PATH"] = path_prefix + os.pathsep + env.get("PATH", os.defpath)
    junit = out / f"{name}.junit.xml"
    full = [*argv, "-p", "no:cacheprovider", f"--junitxml={junit}", f"--basetemp={out / ('bt-' + name)}"]
    res = subprocess.run(full, cwd=tree, env=env, capture_output=True, text=True, timeout=1800, check=False)  # nosec B603
    (out / f"{name}.log").write_text(res.stdout + res.stderr, encoding="utf-8")
    return {"name": name, "argv": full, "exit": res.returncode, "counts": counts(junit), "env_set": sorted(extra_env), "env_dropped": sorted(drop), "path_prefix": path_prefix}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--canopy-python", required=True)
    ap.add_argument("--venv314", required=True)
    ap.add_argument("--venv312", required=True)
    ap.add_argument("--official", required=True)
    ap.add_argument("--precommit", required=True)
    args = ap.parse_args()
    tree = args.tree.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    no_bin = ("GITLEAKS_BIN", "GITLEAKS_PARITY_REQUIRED", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML")
    unit = [args.canopy_python, "-m", "pytest", "-m", UNIT_LANE_MARKS, NEW_FILE, "-q"]
    selftest = self_test_argv(tree)
    official_dir = str(Path(args.official).resolve().parent)
    plan = [
        ("unit-lane-no-binary", [*unit, "--timeout=60"], {}, no_bin, None),
        ("unit-lane-official-engine", [*unit, "--timeout=180"], {"GITLEAKS_BIN": args.official, "GITLEAKS_PARITY_REQUIRED": "1"}, no_bin[2:], None),
        ("unit-lane-precommit-engine", [*unit, "--timeout=180"], {"GITLEAKS_BIN": args.precommit, "GITLEAKS_PARITY_REQUIRED": "1"}, no_bin[2:], None),
        ("selftest-py314", [args.venv314, *selftest], {"GITLEAKS_PARITY_REQUIRED": "1"}, ("GITLEAKS_BIN", *no_bin[2:]), official_dir),
        ("selftest-py312", [args.venv312, *selftest], {"GITLEAKS_PARITY_REQUIRED": "1"}, ("GITLEAKS_BIN", *no_bin[2:]), official_dir),
        ("selftest-no-binary", [args.venv314, *selftest], {"GITLEAKS_PARITY_REQUIRED": "1"}, ("GITLEAKS_BIN", *no_bin[2:]), None),
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda p: run(p[0], p[1], tree, out, p[2], p[3], p[4]), plan))
    record = {"tree": str(tree), "self_test_pytest_line": selftest, "runs": results}
    (out / "file_ways.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    for r in results:
        print(f"{r['name']:28} exit={r['exit']} {r['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

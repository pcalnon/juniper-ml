#!/usr/bin/env python3
"""
Report, for each candidate interpreter, its version, executable and base prefix, and which modules a test lane needs it can import.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-cascor-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
Since 2026-11-14 this host's `python3` resolves to the system CPython without any conda environment's packages, so a
test run is evidence only when the interpreter that ran it is named and known to hold the lane's dependencies. This
starts each interpreter given with `-I` (no user site, no script directory on sys.path), prints sys.version,
sys.executable and sys.base_prefix, and tries to import each module named, printing the version it finds or the
error. The six Sentry DSN variables are set to the empty string in the child. It prints no environment variable.

Usage:
    python3 <this> --modules pytest,yaml,pytest_timeout <interpreter> [<interpreter> ...] [--json <out file>]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 - runs the interpreters it is given with a fixed probe program
import sys

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
PROBE = """
import importlib, json, sys
out = {"version": sys.version.split()[0], "executable": sys.executable, "base_prefix": sys.base_prefix, "modules": {}}
for name in sys.argv[1].split(","):
    try:
        mod = importlib.import_module(name)
        out["modules"][name] = str(getattr(mod, "__version__", "imported"))
    except Exception as exc:  # report every import failure, of any kind
        out["modules"][name] = "MISSING: " + type(exc).__name__ + ": " + str(exc)[:120]
print(json.dumps(out))
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--modules", required=True)
    ap.add_argument("--json", default=None)
    ap.add_argument("interpreters", nargs="+")
    args = ap.parse_args()
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}}
    report = {}
    for interp in args.interpreters:
        proc = subprocess.run([interp, "-I", "-c", PROBE, args.modules], capture_output=True, text=True, timeout=120, env=env, check=False)  # nosec B603
        if proc.returncode != 0:
            report[interp] = {"error": proc.stderr.strip()[-400:]}
        else:
            report[interp] = json.loads(proc.stdout)
        print(interp, json.dumps(report[interp]))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Run every suite of a juniper-ml tree's ci.yml regression step, one `python -m unittest -v <file>` process each, and list the failures.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-ml)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
A juniper-ml carrier runs CI's whole regression list, one process per suite, and states which failures also fail on a
clean main. This reads the `python3 -m unittest -v tests/<file>` lines (comment lines skipped) of the tree's own
ci.yml `tests` job step `Run Python regression tests`, in order, and runs each from the tree's root with the six
Sentry DSN variables set to the empty string, a session-bus address that does not exist, and no gitleaks binary
named (GITLEAKS_BIN removed, as on CI's regression legs). `--suites` limits the run to named suites (a re-run on a clean
main of what failed on the port). It writes one log per suite under --logs and a JSON summary to --out, and prints
the totals and every failing suite. TMPDIR is left as the session gave it; nothing is printed from the environment.

Usage (the interpreter needs the regression job's installs: PyYAML, packaging, juniper-ci-tools, numpy, matplotlib,
h5py, setuptools, wheel, cryptography):
    python3 <this> --tree <juniper-ml tree> --python <interpreter> --logs <dir> --out <json> [--workers 3] [--suites tests/test_a.py ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: <interpreter> -m unittest -v <file>
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
INVOCATION = re.compile(r"^\s*python3 -m unittest -v (tests/test_[A-Za-z0-9_]+\.py)\s*$")
RAN = re.compile(r"^Ran (\d+) tests? in ([0-9.]+)s$", re.MULTILINE)
VERDICT = re.compile(r"^(?:OK|FAILED)\b.*$", re.MULTILINE)


def regression_suites(tree: Path) -> list[str]:
    steps = yaml.safe_load((tree / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]["tests"]["steps"]
    run = next(str(s["run"]) for s in steps if s.get("name") == "Run Python regression tests")
    return [m.group(1) for m in (INVOCATION.match(line) for line in run.splitlines()) if m]


def child_env() -> dict[str, str]:
    env = dict(os.environ.items())
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("GITLEAKS_BIN", None)
    env.pop("GITLEAKS_PARITY_REQUIRED", None)
    return env


def run_unittest(python: str, suite: str, tree: Path, timeout: int) -> tuple[str, int]:
    """``python -m unittest -v suite`` in ``tree``; returns (stdout + stderr, exit status), 124 on a timeout."""
    try:
        proc = subprocess.run([python, "-m", "unittest", "-v", suite], cwd=tree, capture_output=True, text=True, env=child_env(), check=False, timeout=timeout)  # nosec B603
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s", 124
    return proc.stdout + proc.stderr, proc.returncode


def run_one(tree: Path, python: str, logs: Path, suite: str, timeout: int) -> dict:
    start = time.monotonic()
    output, code = run_unittest(python, suite, tree, timeout)
    (logs / f"{Path(suite).stem}.log").write_text(output, encoding="utf-8")
    ran = RAN.findall(output)
    verdicts = VERDICT.findall(output)
    return {"suite": suite, "exit": code, "seconds": round(time.monotonic() - start, 1), "ran": int(ran[-1][0]) if ran else None, "verdict": verdicts[-1] if verdicts else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--python", required=True)
    ap.add_argument("--logs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--suites", nargs="*")
    args = ap.parse_args()
    suites = args.suites or regression_suites(args.tree)
    args.logs.mkdir(parents=True, exist_ok=True)
    workers = max(1, min(args.workers, 4))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda suite: run_one(args.tree, args.python, args.logs, suite, args.timeout), suites))
    failed = [r for r in rows if r["exit"] != 0]
    summary = {"tree": str(args.tree), "python": args.python, "suites": len(rows), "tests_ran": sum(r["ran"] or 0 for r in rows), "failed": failed, "rows": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    print(f"{len(rows)} suites, {summary['tests_ran']} tests ran, {len(failed)} suite(s) failed")
    for r in failed:
        print(f"  FAILED {r['suite']}: exit {r['exit']}; Ran {r['ran']}; {r['verdict']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

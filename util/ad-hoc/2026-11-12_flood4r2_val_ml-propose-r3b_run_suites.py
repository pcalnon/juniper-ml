#!/usr/bin/env python3
"""
Run unittest suites in a tree, one process per suite, with the six Sentry DSN variables empty, and record the counts.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
CI runs each regression suite as its own `python3 -m unittest <file>` process from the repository root. This does
the same in any tree, on any interpreter, at most a few at a time, keeps each suite's whole output in a log file,
and writes a summary that two runs (a landed tree and a clean main) can be compared by.

Usage:
    python3 <this> --tree <repo root> --python <interpreter> --out <dir> --label <name>
                   [--suite tests/test_x.py ...] [--suites-file <one path per line>] [--workers 3] [--timeout 900]
                   [--test <dotted test id or -k pattern, passed after the suite>]
Exit 0 = every suite's process exited 0.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: the interpreter and the suite path are arguments of this run
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
# No test run may reach the desktop session bus: an older tree's scheduled-backup suite runs the real notify-send.
QUIET_DESKTOP = {"DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
RAN = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
RESULT = re.compile(r"^(OK|FAILED)(?: \((.*)\))?\s*$", re.MULTILINE)
PROBLEM = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+?)\)(?: \[(.*)\]| \((.*)\))?\s*$", re.MULTILINE)


def run_one(tree: Path, python: str, suite: str, extra: list, log: Path, timeout: int) -> dict:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, **QUIET_DESKTOP}
    started = time.time()
    argv = [python, "-B", "-m", "unittest", "-v", suite, *extra]
    try:
        done = subprocess.run(argv, cwd=tree, env=env, capture_output=True, text=True, timeout=timeout, check=False)  # nosec B603
        output, code = done.stdout + done.stderr, done.returncode
    except subprocess.TimeoutExpired as stopped:
        output, code = (stopped.stdout or b"").decode("utf-8", "replace") + (stopped.stderr or b"").decode("utf-8", "replace") + "\nTIMEOUT\n", 124
    log.write_text(output, encoding="utf-8")
    ran = RAN.findall(output)
    result = RESULT.findall(output)
    failing = sorted({f"{m.group(3)}.{m.group(2)}" + (f" [{m.group(4)}]" if m.group(4) else "") + (f" ({m.group(5)})" if m.group(5) else "") for m in PROBLEM.finditer(output)})
    return {
        "suite": suite,
        "exit": code,
        "ran": int(ran[-1]) if ran else None,
        "result": (result[-1][0] + (f" ({result[-1][1]})" if result[-1][1] else "")) if result else None,
        "failing": failing,
        "seconds": round(time.time() - started, 1),
        "log": str(log),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--suite", action="append", default=[])
    parser.add_argument("--suites-file", type=Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--test", action="append", default=[], help="an argument passed after the suite (for example -k and a pattern)")
    args = parser.parse_args()
    if args.workers > 4:
        raise SystemExit("at most 4 workers")
    suites = list(args.suite)
    if args.suites_file:
        suites += [line.strip() for line in args.suites_file.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    tree = args.tree.resolve()
    logs = args.out.resolve() / args.label
    logs.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([args.python, "--version"], capture_output=True, text=True, check=False).stdout.strip()  # nosec B603

    def job(suite: str) -> dict:
        return run_one(tree, args.python, suite, args.test, logs / (Path(suite).name + ".log"), args.timeout)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(job, suites))
    summary = {
        "tree": str(tree),
        "python": args.python,
        "python_version": version,
        "label": args.label,
        "extra_arguments": args.test,
        "suites": len(rows),
        "passed": sum(1 for row in rows if row["exit"] == 0),
        "failed": [row["suite"] for row in rows if row["exit"] != 0],
        "tests_ran": sum(row["ran"] or 0 for row in rows),
        "rows": rows,
    }
    (logs / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{'ok ' if row['exit'] == 0 else 'NOT'} {row['suite']}: ran {row['ran']}, {row['result']}, exit {row['exit']}, {row['seconds']}s" + (f"; failing: {row['failing'][:6]}{' ...' if len(row['failing']) > 6 else ''}" if row["failing"] else ""))
    print(f"{args.label} [{version}]: {summary['passed']} of {summary['suites']} suites passed, {summary['tests_ran']} tests ran; summary {logs / 'summary.json'}")
    return 0 if not summary["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())

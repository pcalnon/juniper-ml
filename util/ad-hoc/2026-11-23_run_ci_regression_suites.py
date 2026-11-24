#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   util/ad-hoc
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
# Created:       2026-11-23
# Status:        ad-hoc (single arc: repair of the 2026-11-20 "owner -> Overtoad" rename PRs)
"""Run every suite of ci.yml's "Run Python regression tests" step locally, past failures.

Why this exists
---------------
CI runs the step's ~261 ``python3 -m unittest`` commands under ``bash -e``, so it stops at the first
failing suite and says nothing about the rest. A 2,000-file change needs the whole list. This reads the
commands from the checkout's own ci.yml, runs each one in order with a timeout, and records every result.

Two local hazards it neutralises (juniper-ml memory, 2026-11-12/13): a suite can reach the real
``notify-send`` and raise a "Backup FAILED" desktop alert, so ``DBUS_SESSION_BUS_ADDRESS`` points nowhere;
and five suites fail locally only, because ``TMPDIR`` sits inside a checkout. Compare failures with a run
on clean main before blaming a change.

Usage
-----
    python3 2026-11-23_run_ci_regression_suites.py --checkout DIR --out DIR [--timeout 900] [--only N,M]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time

STEP = "name: Run Python regression tests"


def commands(checkout: str) -> list[str]:
    path = os.path.join(checkout, "." + "github", "workflows", "ci.yml")
    lines = open(path, encoding="utf-8").read().split("\n")
    start = next(i for i, line in enumerate(lines) if line.strip().endswith(STEP) or line.strip() == f"- {STEP}")
    found, in_run, indent = [], False, None
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not in_run:
            if stripped.startswith("run:"):
                in_run = True
            elif stripped.startswith("- name:"):
                break
            continue
        if stripped and indent is None:
            indent = len(line) - len(line.lstrip())
        if stripped and len(line) - len(line.lstrip()) < (indent or 0):
            break
        if re.match(r"python3? -m unittest\b", stripped):
            found.append(stripped)
    if not found:
        raise SystemExit(f"no unittest commands found after {STEP!r} in {path}")
    return found


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--checkout", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--only", help="comma-separated 1-based indexes to run")
    args = ap.parse_args(argv)
    checkout = os.path.abspath(args.checkout)
    os.makedirs(args.out, exist_ok=True)
    cmds = commands(checkout)
    pick = {int(x) for x in args.only.split(",")} if args.only else None
    env = dict(os.environ, DBUS_SESSION_BUS_ADDRESS="unix:path=/nonexistent/no-session-bus")
    failures = 0
    with open(os.path.join(args.out, "results.tsv"), "w", encoding="utf-8") as table:
        table.write("index\trc\tseconds\tcommand\n")
        for index, cmd in enumerate(cmds, 1):
            if pick and index not in pick:
                continue
            began = time.monotonic()
            try:
                proc = subprocess.run(cmd, shell=True, cwd=checkout, env=env, capture_output=True, text=True, timeout=args.timeout)
                rc, output = proc.returncode, proc.stdout + proc.stderr
            except subprocess.TimeoutExpired as exc:
                rc, output = 124, f"TIMEOUT after {args.timeout}s\n{exc.stdout or ''}{exc.stderr or ''}"
            seconds = time.monotonic() - began
            table.write(f"{index}\t{rc}\t{seconds:.1f}\t{cmd}\n")
            table.flush()
            if rc != 0:
                failures += 1
                with open(os.path.join(args.out, f"fail_{index:03d}.log"), "w", encoding="utf-8") as log:
                    log.write(f"$ {cmd}\n{output}")
    total = len(pick) if pick else len(cmds)
    print(f"{total} suites run, {failures} failed; results in {args.out}/results.tsv")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""
Probe: can ``check`` hand the Retry-After formula a ZERO remainder? Only with a window no float holds.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (is the floor in ``max(1, math.ceil(...))`` reachable through the public API?)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_mutants.py (the mutant "ceil without the floor");
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    <venv python> <this> --tree <a juniper-data checkout> [--tree <another>] --out <json>

juniper-data's ``RateLimiter.check`` and ``FailedAuthThrottle.check`` both return on a rolled-over window
(``now - window_start >= window``) before they compute ``window - (now - window_start)``. For two floats, or a
float and an int a float holds exactly, ``a < b`` implies ``b - a > 0``, so the remainder is positive and ``ceil``
is at least 1: the floor of 1 does nothing. An ``int`` window ABOVE 2**53 is different. Python compares an int and
a float exactly, but subtracts them after rounding the int to a float, so with ``window = 2**53 + 1`` and an
elapsed time of exactly ``2.0**53`` the roll-over check says "still inside" and the subtraction says 0.0.

This script runs that case, and the control ``window = 2**53`` (which a float holds), against each tree's own
``juniper_data.api.security`` and prints what ``check`` answers. It imports each tree in a child interpreter so two
trees cannot share a module cache. Read-only: it writes only --out.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess  # nosec B404 - fixed argv: this file, run by the same interpreter
import sys
import types
from pathlib import Path

BIG = 2**53
IP = "203.0.113.9"


def _probe_tree(tree: Path) -> dict:
    sys.path.insert(0, str(tree))
    from juniper_data.api import security  # the tree's own copy: imported after the path insert, on purpose

    held = {"now": 0.0}
    real_time = security.time
    security.time = types.SimpleNamespace(time=lambda: held["now"])
    rows = {}
    try:
        for label, window in (("window_2**53_plus_1", BIG + 1), ("control_window_2**53", BIG)):
            held["now"] = 0.0
            throttle = security.FailedAuthThrottle(max_failures=1, window_seconds=window)
            throttle.record_failure(IP)
            limiter = security.RateLimiter(requests_per_minute=1, window_seconds=window)
            first = limiter.check("k")
            held["now"] = float(BIG)
            rows[label] = {
                "window": window,
                "elapsed": held["now"],
                "elapsed_ge_window": held["now"] >= window,
                "window_minus_elapsed": window - held["now"],
                "ceil_of_that": math.ceil(window - held["now"]),
                "FailedAuthThrottle.check": list(throttle.check(IP)),
                "RateLimiter.check_first": list(first),
                "RateLimiter.check_second": list(limiter.check("k")),
            }
    finally:
        security.time = real_time
    return {"security_py": str(Path(security.__file__).resolve()), "cases": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--tree", type=Path, action="append", default=[])
    ap.add_argument("--out", type=Path)
    ap.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.child is not None:
        print(json.dumps(_probe_tree(args.child.resolve())))
        return 0
    if not args.tree or args.out is None:
        ap.error("--tree (one or more) and --out are required")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    report = {"python": sys.version.split()[0], "trees": {}}
    for tree in args.tree:
        done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", str(tree)], capture_output=True, text=True, check=False, env=env, cwd=str(tree))  # nosec B603
        report["trees"][tree.name] = json.loads(done.stdout) if done.returncode == 0 else {"error": done.stderr[-2000:]}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
        fh.write("\n")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

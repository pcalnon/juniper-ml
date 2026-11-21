#!/usr/bin/env python3
"""
Say where a suite goes in main-verify.yml's Regression Battery so that the battery keeps ci.yml's order.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-ml)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
main-verify.yml's `battery` job re-runs a subset of ci.yml's regression suites against each merged tip, and its SYNC
NOTE asks for a new suite to be mirrored there in the same pull request; the Overtoad ruled on 2026-11-14 that new suites
go there in ci.yml's order. The battery holds fewer suites than ci.yml, so "ci.yml's order" means: after the last
battery suite that ci.yml runs before the new one, and before the next. This reads the real
`python3 -m unittest -v tests/<file>` lines (comment lines skipped) of ci.yml's `tests` job step `Run Python
regression tests` and of main-verify.yml's `battery` job step `Run Python regression battery` (other jobs of either
file run suites too, and are not the lists the SYNC NOTE pairs), says whether the battery's own order already agrees
with ci.yml's (and, where it does not, which battery suites are out of order), and prints the battery suite the new
one follows and the one it precedes. It reads only.

Usage (the interpreter needs PyYAML):
    python3 <this> --ci <ci.yml> --main-verify <main-verify.yml> --suite tests/test_x.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

INVOCATION = re.compile(r"^\s*python3 -m unittest -v (tests/test_[A-Za-z0-9_]+\.py)\s*$")


def suites(path: Path, job: str, step: str) -> list[str]:
    steps = yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"][job]["steps"]
    run = next(str(s["run"]) for s in steps if s.get("name") == step)
    return [m.group(1) for m in (INVOCATION.match(line) for line in run.splitlines()) if m]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--ci", type=Path, required=True)
    ap.add_argument("--main-verify", type=Path, required=True)
    ap.add_argument("--suite", required=True)
    args = ap.parse_args()
    ci = suites(args.ci, "tests", "Run Python regression tests")
    battery = suites(args.main_verify, "battery", "Run Python regression battery")
    if args.suite not in ci:
        raise SystemExit(f"{args.suite} is not invoked by {args.ci}")
    position = {name: i for i, name in enumerate(ci)}
    missing = [name for name in battery if name not in position]
    in_order = [position[name] for name in battery if name in position]
    print(f"ci.yml invokes {len(ci)} suites; the battery {len(battery)}; battery suites ci.yml does not invoke: {missing or 'none'}")
    print(f"battery already in ci.yml's order: {in_order == sorted(in_order)}")
    known = [name for name in battery if name in position]
    for earlier, later in zip(known, known[1:]):
        if position[earlier] > position[later]:
            print(f"  out of ci.yml's order: {earlier} (ci.yml suite {position[earlier] + 1}) runs before {later} (ci.yml suite {position[later] + 1})")
    if args.suite in battery:
        print(f"{args.suite} is already in the battery, at position {battery.index(args.suite) + 1}")
        return 0
    mine = position[args.suite]
    before = [name for name in battery if name in position and position[name] < mine]
    after = [name for name in battery if name in position and position[name] > mine]
    print(f"{args.suite} is ci.yml's suite {mine + 1}; in the battery it follows {before[-1] if before else '(nothing: it goes first)'} and precedes {after[0] if after else '(nothing: it goes last)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

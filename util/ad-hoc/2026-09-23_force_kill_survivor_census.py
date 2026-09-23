"""
Census every ``_force_kill`` copy in the launcher test suites: does the pid it is handed survive it?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2046 (named two copies in one file; ten existed across four)

Wraps each ``_force_kill`` -- the module-level function and every ``TestCase`` method of that
name -- in the given test modules, runs each module's full suite in-process, and records, per
copy and per call: whether the pid led a process group when it was handed over, whether it was
still running (not a zombie) the instant the copy returned, and whether it was STILL running
after a further 1 s grace. The grace separates the two: some copies have no wait loop, so a
SIGKILL they did send has simply not landed yet at return. Only the second column is survival.
Survivors are then SIGKILLed, so the census leaves nothing behind.

A copy is BROKEN IN PRACTICE when a call site hands it a live pid that leads no group and the
pid outlives it. A copy that is only ever handed ``setsid`` leaders is fine by construction,
whatever its code says -- which is why this measures call sites rather than grepping code.

Usage (from the repo root)::

    PYTHONDONTWRITEBYTECODE=1 python3 util/ad-hoc/2026-09-23_force_kill_survivor_census.py
    # the pre-fix picture: point --root at an export of the old tests/ + util/ files
    PYTHONDONTWRITEBYTECODE=1 python3 util/ad-hoc/2026-09-23_force_kill_survivor_census.py --root <export> \\
        tests.test_isolated_stack_script tests.test_experiment_stack_script
"""

from __future__ import annotations

import argparse
import importlib
import io
import os
import signal
import sys
import time
import unittest
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODULES = (
    "tests.test_isolated_stack_script",
    "tests.test_experiment_stack_script",
    "tests.test_juniper_chop_all",
    "tests.test_juniper_plant_all",
)


def _state(pid: int) -> "str | None":
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except OSError:
        return None


def _leads_group(pid: int) -> "bool | None":
    try:
        return os.getpgid(pid) == pid
    except OSError:
        return None


def _running(pid: int) -> bool:
    return _state(pid) not in (None, "Z", "X")


def census(module_name: str) -> "tuple[dict, unittest.TestResult]":
    mod = importlib.import_module(module_name)
    rows: "dict[str, list[tuple[bool | None, bool, bool, bool]]]" = defaultdict(list)
    survivors: "list[int]" = []

    def wrap(label: str, original, bound: bool):
        def recorder(*args):
            pid = args[1] if bound else args[0]
            was_running = _running(pid)
            leader = _leads_group(pid)
            original(*args)
            at_return = _running(pid)
            deadline = time.monotonic() + 1.0
            while _running(pid) and time.monotonic() < deadline:
                time.sleep(0.02)
            survived = _running(pid)
            rows[label].append((leader, was_running, at_return, survived))
            if survived:
                survivors.append(pid)

        return recorder

    # The shared helper is imported as ``force_kill``; the hand copies it replaced were ``_force_kill``.
    for global_name in ("force_kill", "_force_kill"):
        if callable(getattr(mod, global_name, None)):
            setattr(mod, global_name, wrap(f"{module_name}:{global_name} (module)", getattr(mod, global_name), bound=False))
    for name in dir(mod):
        cls = getattr(mod, name)
        if isinstance(cls, type) and issubclass(cls, unittest.TestCase) and "_force_kill" in vars(cls):
            cls._force_kill = wrap(f"{module_name}:{name}._force_kill", vars(cls)["_force_kill"], bound=True)

    suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    for pid in survivors:
        try:
            os.kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    return rows, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("modules", nargs="*", default=list(DEFAULT_MODULES))
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="tree whose tests/ and util/ are censused (default: this checkout)")
    args = parser.parse_args()
    sys.path.insert(0, str(args.root.resolve()))
    print(f"root: {args.root.resolve()}")
    broken = 0
    for module_name in args.modules:
        rows, result = census(module_name)
        print(f"{module_name}: ran {result.testsRun}, failures {len(result.failures)}, errors {len(result.errors)}")
        if not rows:
            print("  (no _force_kill call reached)")
        for label, calls in sorted(rows.items()):
            live = [c for c in calls if c[1]]
            non_leader_live = [c for c in live if c[0] is False]
            at_return = [c for c in live if c[2]]
            survived = [c for c in live if c[3]]
            verdict = "BROKEN IN PRACTICE" if survived else "ok"
            broken += verdict != "ok"
            print(f"  {label.split(':', 1)[1]:52s} calls={len(calls):2d} live-at-call={len(live):2d} non-leader-live={len(non_leader_live):2d} " f"running-at-return={len(at_return):2d} survived-1s={len(survived):2d}  {verdict}")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())

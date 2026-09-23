"""
Mutation-check ``TestForceKill``: every way ``force_kill`` has been, or could plausibly be, wrong must fail a test.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2046; tests/process_cleanup.py (``force_kill``); tests/test_isolated_stack_script.py (``TestForceKill``)

Each mutant replaces the test module's global ``force_kill`` -- every call site there and every
``TestForceKill`` case resolves it at call time -- and the class is run in-process. A mutant
counts as KILLED when at least one case fails or errors. The unmutated helper runs first as the
control and must pass all four, or the matrix below it means nothing.

One mutation is deliberately NOT run: ``os.killpg(os.getpgid(pid), …)``. A nohup'd stub shares
the runner's process group, so that mutant kills this script (and whatever shares its group).

Usage (from the repo root)::

    PYTHONDONTWRITEBYTECODE=1 python3 util/ad-hoc/2026-09-23_force_kill_mutation_check.py
"""

from __future__ import annotations

import io
import os
import signal
import sys
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tests import process_cleanup as pc  # noqa: E402
from tests import test_isolated_stack_script as mod  # noqa: E402

SHIPPED = pc.force_kill


def m_main_at_7fb40892(pid: int) -> None:
    """The three copies as they stood on ``main``: a ``killpg`` miss reads as "already dead"."""
    for kill_target in (lambda: os.killpg(pid, signal.SIGKILL), lambda: os.kill(pid, signal.SIGKILL)):
        try:
            kill_target()
            break
        except ProcessLookupError:
            return
        except PermissionError:
            continue
    for _ in range(20):
        if not Path(f"/proc/{pid}").exists():
            return
        time.sleep(0.05)


def m_issue_suggested_fix(pid: int) -> None:
    """#2046's suggestion: fall through to ``os.kill`` -- kills the stub, orphans what it has in flight."""
    for kill in (os.killpg, os.kill):
        try:
            kill(pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            continue
    for _ in range(20):
        if not Path(f"/proc/{pid}").exists():
            return
        time.sleep(0.05)


def _descendants_only(pid: int) -> "list[int]":
    table = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            info = pc.proc_stat(int(entry.name))
            if info is not None:
                table[int(entry.name)] = info
    found: "set[int]" = set()
    frontier = [pid]
    while frontier:
        parent = frontier.pop()
        for child, (_state, ppid, _pgrp) in table.items():
            if ppid == parent and child not in found:
                found.add(child)
                frontier.append(child)
    return sorted(found)


def m_no_group_reach(pid: int) -> None:
    """Shipped, minus BOTH group mechanisms (the ``killpg`` and the ``pgrp`` scan)."""
    try:
        os.kill(pid, signal.SIGSTOP)
    except (ProcessLookupError, PermissionError):
        return
    victims = [pid, *_descendants_only(pid)]
    for victim in victims:
        try:
            os.kill(victim, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    for _ in range(40):
        if not any(pc.is_running(victim) for victim in victims):
            return
        time.sleep(0.05)


def m_raises_when_already_gone(pid: int) -> None:
    """Shipped, minus the guard on the first signal: a pid stop_port already killed now raises."""
    os.kill(pid, signal.SIGSTOP)
    SHIPPED(pid)


def m_no_final_wait(pid: int) -> None:
    """Shipped, minus the wait: SIGKILL is asynchronous, so a victim may still run on return."""
    try:
        os.kill(pid, signal.SIGSTOP)
    except (ProcessLookupError, PermissionError):
        return
    victims = [pid, *pc.reachable_from(pid)]
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    for victim in victims:
        try:
            os.kill(victim, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


MUTANTS = {
    "control (shipped)": SHIPPED,
    "main@7fb40892": m_main_at_7fb40892,
    "#2046 suggested fix": m_issue_suggested_fix,
    "no group reach": m_no_group_reach,
    "raises when already gone": m_raises_when_already_gone,
    "no final wait": m_no_final_wait,
}


def run_class() -> "list[str]":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(mod.TestForceKill)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    return sorted(test.id().rsplit(".", 1)[1] for test, _trace in result.failures + result.errors)


def main() -> int:
    survivors = []
    control_failed = False
    for name, mutant in MUTANTS.items():
        mod.force_kill = mutant
        try:
            caught = run_class()
        finally:
            mod.force_kill = SHIPPED
        if name.startswith("control"):
            control_failed = bool(caught)
            print(f"{name:26s} {'FAILED: ' + ', '.join(caught) if caught else 'passes all 4 (required)'}")
            continue
        verdict = "KILLED" if caught else "SURVIVED"
        if not caught:
            survivors.append(name)
        print(f"{name:26s} {verdict:8s} by {', '.join(caught) if caught else '-'}")
    if control_failed:
        print("control failed -- the matrix is void")
        return 2
    print(f"{len(MUTANTS) - 1 - len(survivors)}/{len(MUTANTS) - 1} mutants killed")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())

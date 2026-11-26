"""
pytest plugin: a per-test census of the threads alive in the pytest process (juniper-canopy unit lane).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28 (juniper-canopy test_relay_cascade_add_does_not_block_the_loop)

Loaded with ``-p r28_census`` from a plugin directory on PYTHONPATH (the runner,
util/ad-hoc/2026-11-25_flood4_s14_r28_run_lane.py, links this file there under that name).
Writes one JSON line per test to the file named by R28_CENSUS_OUT:

    {"nodeid", "alive_at_setup", "training_loop_at_setup", "alive_after", "training_loop_after",
     "leaked": [names of threads started during the test and still alive after its teardown]}

A DemoMode training thread is ``threading.Thread(target=self._training_loop)``, which Python names
``Thread-N (_training_loop)``; "training_loop" counts threads whose name ends with that suffix.
Thread names and counts only: no frame, no variable, no environment value is recorded.
"""

from __future__ import annotations

import gc
import json
import os
import threading
import time

import pytest

_OUT = os.environ.get("R28_CENSUS_OUT", "")
_MARK = "(_training_loop)"
_before: dict[str, set[int]] = {}

# R28_GC_OUT (optional): every cyclic-GC pass of at least R28_GC_MIN_MS milliseconds (default 50) is written there as
# {"nodeid", "phase", "generation", "ms", "thread", "collected", "t"} -- the stop-the-world pauses (a collection
# holds the GIL throughout, so every thread of the process stops for its duration).
_GC_OUT = os.environ.get("R28_GC_OUT", "")
_GC_MIN = float(os.environ.get("R28_GC_MIN_MS", "50")) / 1000.0
_gc_state = {"nodeid": "", "phase": "", "start": 0.0}


def _gc_callback(phase, info):
    if phase == "start":
        _gc_state["start"] = time.perf_counter()
        return
    took = time.perf_counter() - _gc_state["start"]
    if took >= _GC_MIN:
        row = {"nodeid": _gc_state["nodeid"], "phase": _gc_state["phase"], "generation": info.get("generation"), "ms": round(took * 1000, 1), "thread": threading.current_thread().name, "collected": info.get("collected"), "t": round(time.time(), 3)}
        with open(_GC_OUT, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")


if _GC_OUT:
    gc.callbacks.append(_gc_callback)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    _gc_state["nodeid"] = item.nodeid
    yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_call(item):
    _gc_state["phase"] = "call"
    yield
    _gc_state["phase"] = "teardown"


def _snapshot() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t is not threading.main_thread()]


def _demo_count(threads: list[threading.Thread]) -> int:
    return sum(1 for t in threads if t.name.endswith(_MARK))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_setup(item):
    _gc_state["phase"] = "setup"
    if _OUT:
        threads = _snapshot()
        _before[item.nodeid] = {t.ident for t in threads}
        item.stash_r28 = {"alive_at_setup": len(threads), "training_loop_at_setup": _demo_count(threads)}
    yield


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_teardown(item, nextitem):
    yield
    if not _OUT:
        return
    threads = _snapshot()
    before = _before.pop(item.nodeid, set())
    record = {"nodeid": item.nodeid}
    record.update(getattr(item, "stash_r28", {}))
    record["alive_after"] = len(threads)
    record["training_loop_after"] = _demo_count(threads)
    record["leaked"] = sorted(t.name for t in threads if t.ident not in before)
    with open(_OUT, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")

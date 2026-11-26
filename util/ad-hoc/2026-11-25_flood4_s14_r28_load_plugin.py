"""
pytest plugin: recreate, inside the test process, the load under which juniper-canopy's X7 ticker tests fail in CI.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Loaded with ``-p r28_load`` from a plugin directory on PYTHONPATH. Nothing happens unless R28_LOAD names a load:

    gc      CI's late-session heap and its full collections: R28_LOAD_HEAP_MILLIONS (default 8) million retained small
            lists are allocated at session start, and a daemon thread runs gc.collect() every R28_LOAD_GC_INTERVAL
            seconds (default 0.2). Each pass holds the interpreter -- every thread of the process stops -- for its
            duration (about 57 ms per million tracked objects on this host's Python 3.13.18, measured by
            util/ad-hoc/2026-11-25_flood4_s14_r28_gc_pause_size.py).
    demo    two DemoMode(update_interval=0.1).start() training threads, as the two leaking unit tests leave behind.
    gc+demo both.

R28_LOAD_OUT (optional) receives one JSON line per collection the load thread ran: {"ms", "t"}.
No host-wide load: everything is threads of this one process.
"""

from __future__ import annotations

import gc
import json
import os
import threading
import time

import pytest

_LOAD = os.environ.get("R28_LOAD", "")
_state: dict = {"keep": [], "stop": threading.Event(), "threads": [], "demos": []}


def _collector(interval: float, out: str) -> None:
    while not _state["stop"].is_set():
        start = time.perf_counter()
        gc.collect()
        took = time.perf_counter() - start
        if out:
            with open(out, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"ms": round(took * 1000, 1), "t": round(time.time(), 3)}) + "\n")
        _state["stop"].wait(interval)


def pytest_sessionstart(session):
    if "gc" in _LOAD:
        millions = float(os.environ.get("R28_LOAD_HEAP_MILLIONS", "8"))
        keep = _state["keep"]
        for i in range(int(millions * 1_000_000)):
            keep.append([i])
        interval = float(os.environ.get("R28_LOAD_GC_INTERVAL", "0.2"))
        thread = threading.Thread(target=_collector, args=(interval, os.environ.get("R28_LOAD_OUT", "")), daemon=True, name="r28-load-gc")
        thread.start()
        _state["threads"].append(thread)


@pytest.fixture(scope="session", autouse=True)
def r28_demo_load(request):
    """Start the 'demo' load inside the session, after canopy's conftest has mocked the data client."""
    if "demo" in _LOAD:
        request.getfixturevalue("mock_juniper_data_client")
        from demo_mode import DemoMode

        for _ in range(2):
            demo = DemoMode(update_interval=0.1)
            demo.start()
            _state["demos"].append(demo)
    yield


def pytest_sessionfinish(session, exitstatus):
    _state["stop"].set()
    for thread in _state["threads"]:
        thread.join(timeout=30)
    for demo in _state["demos"]:
        demo._stop.set()
        if demo.thread is not None:
            demo.thread.join(timeout=30)
    _state["keep"].clear()

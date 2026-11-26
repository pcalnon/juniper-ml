"""
pytest plugin for flood-4 r49: inject a whole-process stop into juniper-canopy's X7 health test, and record where its
slow upstream call ran and which source tree was imported.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26) and its parent ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16 builder r49.
    Modelled on the R28V_HEALTH_STALL_S option of util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_plugin.py.

Loaded as ``-p r49_stall`` (a run-lane helper links this file under that name into a PYTHONPATH directory). With
R49_OUT unset it does nothing at all. It wraps ``_SlowBackend.get_status`` of the module
``test_x7_loop_responsiveness`` (old or new test: both keep that name), so the stop lands inside the test's measurement
whatever the test asserts:

    R49_OUT          output file, one JSON object per line (kind-tagged)
    R49_STALL_KIND   ""   no stop (record only)
                     gil  hold the GIL for R49_STALL_S seconds: one C-level sum over a range, no bytecode, so no hand-off
                     gc   a full gc.collect() over R49_HEAP_M million retained empty lists, allocated at configure time
                          (a generation-2 pass, the mechanism ruling 28 measured in the unit lane: every thread stops)
    R49_STALL_AT     entry  on the FIRST get_status call of each test, before the stub's own body, on that call's thread
                     held   on that first call, start a helper thread that waits R49_STALL_DELAY_S (default 0.002) and
                            then stops the process, so the stop lands after the call has entered, while it is in flight
                     request  on the loop thread, at the FIRST http request into ``main.app`` of each test, before the
                            app handles it (an outer wrapper of ``main.app.middleware_stack``): the stop sits at the start
                            of the measurement, before any driver reaches its upstream call and while every probe waits
    R49_STALL_S      seconds for the gil kind (calibrated once per process against sum(range))
    R49_HEAP_M       millions of retained objects for the gc kind (default 16)
    R49_GC=1         record every cyclic-GC pass of at least R49_GC_MIN_MS (default 50) ms: generation, thread, test

It records: the imported ``main`` and test-module files (session), every get_status call (test, thread name, whether it
ran on the main thread -- pytest-asyncio's loop thread), every injected stop (kind, point, thread, seconds), and with
R49_GC=1 every long GC pass.
"""

from __future__ import annotations

import gc
import json
import os
import threading
import time

_OUT = os.environ.get("R49_OUT", "")
_KIND = os.environ.get("R49_STALL_KIND", "")
_AT = os.environ.get("R49_STALL_AT", "entry")
_LOCK = threading.Lock()
_STATE: dict = {"test": None, "keep": [], "range": 0}


def _emit(kind: str, payload: dict) -> None:
    if not _OUT:
        return
    line = json.dumps({"kind": kind, "t": round(time.time(), 4), **payload}, default=str) + "\n"
    with _LOCK:
        with open(_OUT, "a", encoding="utf-8") as handle:
            handle.write(line)


def _calibrate(seconds: float) -> int:
    probe = 5_000_000
    started = time.perf_counter()
    sum(range(probe))
    per_item = (time.perf_counter() - started) / probe
    return max(1, int(seconds / per_item))


def _stop(point: str, test: str | None) -> None:
    started = time.perf_counter()
    if _KIND == "gil":
        sum(range(_STATE["range"]))  # one C call: holds the GIL throughout
    elif _KIND == "gc":
        gc.collect()
    _emit("stop", {"test": test, "stop_kind": _KIND, "point": point, "thread": threading.current_thread().name, "seconds": round(time.perf_counter() - started, 4)})


def _gc_callback(phase: str, info: dict) -> None:
    ident = threading.get_ident()
    starts = _STATE.setdefault("gc_start", {})
    if phase == "start":
        starts[ident] = time.perf_counter()
        return
    started = starts.pop(ident, None)
    if started is None:
        return
    seconds = time.perf_counter() - started
    if seconds * 1000.0 >= float(os.environ.get("R49_GC_MIN_MS", "50")):
        _emit("gc", {"seconds": round(seconds, 4), "generation": info.get("generation"), "collected": info.get("collected"), "thread": threading.current_thread().name, "test": _STATE["test"]})


def _wrap(module) -> None:
    cls = getattr(module, "_SlowBackend", None)
    if cls is None or getattr(cls.get_status, "_r49_wrapped", False):
        return
    original = cls.get_status

    def get_status(self, *args, **kwargs):
        first = not getattr(self, "_r49_seen", False)
        self._r49_seen = True
        thread = threading.current_thread()
        test = _STATE["test"]
        _emit("call", {"test": test, "thread": thread.name, "on_main_thread": thread is threading.main_thread(), "first": first})
        if first and _KIND:
            if _AT == "entry":
                _stop("entry", test)
            elif _AT == "held":
                delay = float(os.environ.get("R49_STALL_DELAY_S", "0.002"))

                def _later() -> None:
                    time.sleep(delay)
                    _stop("held", test)

                threading.Thread(target=_later, name="r49-stop", daemon=True).start()
        started = time.perf_counter()
        try:
            return original(self, *args, **kwargs)
        finally:
            _emit("call_end", {"test": test, "thread": thread.name, "first": first, "seconds_in_call": round(time.perf_counter() - started, 4)})

    get_status._r49_wrapped = True
    cls.get_status = get_status


def _wrap_app_entry(app) -> None:
    """Stop the process on the loop thread at the first http request of each test into ``app``."""
    if getattr(app, "_r49_entry_wrapped", False):
        return
    if app.middleware_stack is None:
        app.middleware_stack = app.build_middleware_stack()
    inner = app.middleware_stack

    async def stack(scope, receive, send):
        test = _STATE["test"]
        if scope.get("type") == "http" and _STATE.get("request_stopped") != test:
            _STATE["request_stopped"] = test
            _stop("request", test)
        await inner(scope, receive, send)

    app.middleware_stack = stack
    app._r49_entry_wrapped = True


def pytest_configure(config):
    if not _OUT:
        return
    import sys

    if os.environ.get("R49_GC") == "1":
        gc.callbacks.append(_gc_callback)
    if _KIND == "gil":
        _STATE["range"] = _calibrate(float(os.environ.get("R49_STALL_S", "1.3")))
    elif _KIND == "gc":
        millions = float(os.environ.get("R49_HEAP_M", "16"))
        _STATE["keep"].append([[] for _ in range(int(millions * 1_000_000))])
    _emit("session", {"python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "stall_kind": _KIND, "stall_at": _AT, "env": {k: os.environ[k] for k in sorted(os.environ) if k.startswith("R49_") and k != "R49_OUT"}, "gil_range": _STATE["range"]})


def pytest_collection_finish(session):
    if not _OUT:
        return
    import importlib

    seen = set()
    for item in session.items:
        module = getattr(item, "module", None)
        if module is None or module.__name__ in seen:
            continue
        seen.add(module.__name__)
        if module.__name__.endswith("test_x7_loop_responsiveness"):
            _wrap(module)
            main = importlib.import_module("main")
            admission = importlib.import_module("backend.admission")
            if _KIND and _AT == "request":
                _wrap_app_entry(main.app)
            _emit("modules", {"test_module": getattr(module, "__file__", None), "main": getattr(main, "__file__", None), "admission": getattr(admission, "__file__", None)})


try:
    import pytest

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(item, nextitem):
        _STATE["test"] = item.nodeid
        yield
        _STATE["test"] = None

except ImportError:  # imported outside pytest
    pass

"""
pytest plugin for the r28 code lens: observational recorders, optional in-process loads, and an in-process repeat.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code; runner util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_run.py

Loaded as ``-p r28v_plugin`` (the runner symlinks this file under that name into a PYTHONPATH directory). Written
independently of the r28 builder's census and load plugins. Everything is driven by environment variables; with
R28V_OUT unset the plugin does nothing at all.

    R28V_OUT          output prefix (required): <prefix>.r28v.jsonl (one JSON object per line, kind-tagged)
    R28V_GC=1         record every cyclic-GC pass >= R28V_GC_MIN_MS (default 50) with its generation, thread and test
    R28V_THREADS=1    record the live threads at setup of every test in a test_x7_*.py file, and, for every test,
                      the threads it started that are still alive after its teardown (a leak)
    R28V_HELD=1       wrap test_x7_sites_outside_main_gate._HeldCall.__call__ (when the module has it) to record, per
                      call, the thread verdict, the release verdict and the seconds spent inside the call
    R28V_LOOP_STALL_ON_ENTRY=S   (with R28V_HELD) when a held call enters OFF the loop thread, first queue a
                      ``time.sleep(S)`` callback on the loop, ahead of the harness's own release callback: the loop
                      cannot run for S seconds from a cause outside the code under test (a deterministic stand-in for
                      a whole-process stop), so the release is delayed by S. Shows where the hold cap bites.
    R28V_LOAD=gc      retain R28V_HEAP_M million GC-tracked objects and run gc.collect() from a daemon thread every
                      R28V_GC_INTERVAL seconds (default 0.25)
    R28V_LOAD=cpu     R28V_SPINNERS (default 4) pure-Python daemon threads contending for the GIL
    R28V_LOAD=gilstall  a daemon thread that holds the GIL for R28V_STALL_S seconds (a C-level sum over a range, no
                      bytecode, so no GIL hand-off) every R28V_STALL_PERIOD seconds: whole-process stops
    R28V_LOAD=cpu_in_call  R28V_SPINNERS pure-Python threads started at the CALL phase of each test in
                      test_x7_sites_outside_main_gate.py and stopped after it (always-on spinners starve pytest's own
                      setup through the GIL convoy, so this puts the pressure on the code and harness under test only)
    R28V_LOAD may name several, comma-separated.
    R28V_REPEAT=N     run every collected test N times in this process (parametrised like pytest-repeat)
    R28V_PREIMPORT=a,b  import these modules after collection, so a test's patch.dict(sys.modules) does not drop them
                      (they exist before it enters) -- the state a full lane is in after earlier tests import them
    R28V_HEALTH_STALL_S=S  wrap test_x7_loop_responsiveness._SlowBackend.get_status so that its FIRST call in each
                      test holds the GIL for S seconds (one C-level sum over a range) before the stub's own sleep. The
                      route offloads get_status to a worker thread, so this is a whole-process stop inside the probe
                      window that the code under test did not cause -- the shape of a collection on another thread.
"""

from __future__ import annotations

import gc
import json
import os
import threading
import time

_OUT = os.environ.get("R28V_OUT", "")
_LOCK = threading.Lock()
_STATE = {"test": None, "gc_start": {}}
_KEEP: list = []


def _emit(kind: str, payload: dict) -> None:
    if not _OUT:
        return
    payload = {"kind": kind, "t": round(time.time(), 4), **payload}
    line = json.dumps(payload, default=str) + "\n"
    with _LOCK:
        with open(_OUT + ".r28v.jsonl", "a", encoding="utf-8") as handle:
            handle.write(line)


def _target_name(thread: threading.Thread) -> str:
    target = getattr(thread, "_target", None)
    if target is None:
        return type(thread).__name__ if type(thread) is not threading.Thread else ""
    owner = getattr(target, "__self__", None)
    qual = getattr(target, "__qualname__", repr(target))
    return f"{type(owner).__name__}.{getattr(target, '__name__', qual)}" if owner is not None else qual


def _threads() -> list[dict]:
    return [{"name": t.name, "ident": t.ident, "daemon": t.daemon, "target": _target_name(t)} for t in threading.enumerate()]


# ---------------------------------------------------------------- GC recorder
def _gc_callback(phase: str, info: dict) -> None:
    ident = threading.get_ident()
    if phase == "start":
        _STATE["gc_start"][ident] = time.perf_counter()
        return
    started = _STATE["gc_start"].pop(ident, None)
    if started is None:
        return
    seconds = time.perf_counter() - started
    if seconds * 1000.0 >= float(os.environ.get("R28V_GC_MIN_MS", "50")):
        _emit("gc", {"seconds": round(seconds, 4), "generation": info.get("generation"), "collected": info.get("collected"), "thread": threading.current_thread().name, "test": _STATE["test"]})


# ---------------------------------------------------------------- loads
def _gc_load() -> None:
    millions = float(os.environ.get("R28V_HEAP_M", "8"))
    _KEEP.append([[] for _ in range(int(millions * 1_000_000))])
    interval = float(os.environ.get("R28V_GC_INTERVAL", "0.25"))

    def _collector() -> None:
        while True:
            time.sleep(interval)
            gc.collect()

    threading.Thread(target=_collector, name="r28v-gc-load", daemon=True).start()


def _cpu_load() -> None:
    def _spin() -> None:
        while True:
            total = 0
            for i in range(2000):
                total += i * i

    for n in range(int(os.environ.get("R28V_SPINNERS", "4"))):
        threading.Thread(target=_spin, name=f"r28v-spinner-{n}", daemon=True).start()


def _calibrate_range_for(seconds: float) -> int:
    probe = 5_000_000
    started = time.perf_counter()
    sum(range(probe))
    per_item = (time.perf_counter() - started) / probe
    return max(1, int(seconds / per_item))


def _gilstall_load() -> None:
    seconds = float(os.environ.get("R28V_STALL_S", "0.6"))
    period = float(os.environ.get("R28V_STALL_PERIOD", "1.0"))
    count = _calibrate_range_for(seconds)
    _emit("gilstall_calibration", {"seconds": seconds, "period": period, "range": count})

    def _staller() -> None:
        while True:
            time.sleep(period)
            started = time.perf_counter()
            sum(range(count))  # one C call: holds the GIL throughout, no eval-breaker hand-off
            _emit("gilstall", {"seconds": round(time.perf_counter() - started, 4), "test": _STATE["test"]})

    threading.Thread(target=_staller, name="r28v-gilstall", daemon=True).start()


# ---------------------------------------------------------------- held-call wrapper
def _wrap_held(module) -> None:
    cls = getattr(module, "_HeldCall", None)
    if cls is None or getattr(cls.__call__, "_r28v_wrapped", False):
        return
    original = cls.__call__

    def __call__(self, *args, **kwargs):
        stall = float(os.environ.get("R28V_LOOP_STALL_ON_ENTRY", "0") or 0)
        off_loop = threading.get_ident() != self._loop_thread
        if stall > 0 and off_loop:
            self._loop.call_soon_threadsafe(time.sleep, stall)
        started = time.perf_counter()
        try:
            return original(self, *args, **kwargs)
        finally:
            _emit("held", {"test": _STATE["test"], "seconds_in_call": round(time.perf_counter() - started, 4), "ran_on_loop_thread": self.ran_on_loop_thread, "released_by_loop": self.released_by_loop, "hold_seconds": self.hold_seconds, "calls": self.calls, "stall_injected": stall if off_loop else 0.0, "thread": threading.current_thread().name})

    __call__._r28v_wrapped = True
    cls.__call__ = __call__


# ---------------------------------------------------------------- pytest hooks
def pytest_configure(config):
    if not _OUT:
        return
    if os.environ.get("R28V_GC") == "1":
        gc.callbacks.append(_gc_callback)
    loads = [x.strip() for x in os.environ.get("R28V_LOAD", "").split(",") if x.strip()]
    for load in loads:
        {"gc": _gc_load, "cpu": _cpu_load, "gilstall": _gilstall_load, "cpu_in_call": lambda: None}[load]()
    import sys

    _emit("session", {"python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "loads": loads, "gc_thresholds": gc.get_threshold(), "env": {k: os.environ[k] for k in sorted(os.environ) if k.startswith("R28V_") and k != "R28V_OUT"}})


def pytest_generate_tests(metafunc):
    count = int(os.environ.get("R28V_REPEAT", "1") or 1)
    if _OUT and count > 1:
        metafunc.fixturenames.append("r28v_repeat_index")
        metafunc.parametrize("r28v_repeat_index", range(count), ids=[f"rep{n:02d}" for n in range(count)])


def pytest_collection_finish(session):
    if not _OUT:
        return
    import importlib as _importlib

    for name in [x.strip() for x in os.environ.get("R28V_PREIMPORT", "").split(",") if x.strip()]:
        _importlib.import_module(name)
        _emit("preimported", {"module": name})
    modules = {}
    for item in session.items:
        module = getattr(item, "module", None)
        if module is not None:
            modules[module.__name__] = module
    for name, module in modules.items():
        stall = float(os.environ.get("R28V_HEALTH_STALL_S", "0") or 0)
        backend_cls = getattr(module, "_SlowBackend", None)
        if stall > 0 and name.endswith("test_x7_loop_responsiveness") and backend_cls is not None and not getattr(backend_cls.get_status, "_r28v_wrapped", False):
            count = _calibrate_range_for(stall)
            original_get_status = backend_cls.get_status

            def get_status(self, _original=original_get_status, _count=count):
                if not getattr(self, "_r28v_stalled", False):
                    self._r28v_stalled = True
                    started = time.perf_counter()
                    sum(range(_count))  # one C call: holds the GIL throughout
                    _emit("health_stall", {"test": _STATE["test"], "seconds": round(time.perf_counter() - started, 4), "thread": threading.current_thread().name})
                return _original(self)

            get_status._r28v_wrapped = True
            backend_cls.get_status = get_status
            _emit("health_stall_wrapped", {"module": name, "seconds": stall, "range": count})
        if os.environ.get("R28V_HELD") == "1" and name.endswith("test_x7_sites_outside_main_gate"):
            _wrap_held(module)
            _emit("held_wrapped", {"module": name, "file": getattr(module, "__file__", None)})
        if name.endswith("test_x7_sites_outside_main_gate"):
            import importlib

            for dep in ("backend.cascor_service_adapter", "backend.service_backend", "backend.state_sync"):
                mod = importlib.import_module(dep)
                _emit("module_file", {"module": dep, "file": getattr(mod, "__file__", None)})


try:
    import pytest

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(item, nextitem):
        if not _OUT:
            yield
            return
        _STATE["test"] = item.nodeid
        watch = os.environ.get("R28V_THREADS") == "1"
        before = {t.ident for t in threading.enumerate()} if watch else set()
        if watch and "test_x7_" in item.nodeid:
            _emit("threads_at_setup", {"test": item.nodeid, "threads": _threads()})
        yield
        if watch:
            leaked = [t for t in threading.enumerate() if t.ident not in before and t.is_alive()]
            if leaked:
                _emit("leak", {"test": item.nodeid, "threads": [{"name": t.name, "daemon": t.daemon, "target": _target_name(t)} for t in leaked]})
        _STATE["test"] = None

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(item):
        wanted = _OUT and "cpu_in_call" in os.environ.get("R28V_LOAD", "") and "test_x7_sites_outside_main_gate" in item.nodeid
        if not wanted:
            yield
            return
        stop = threading.Event()

        def _spin() -> None:
            while not stop.is_set():
                total = 0
                for i in range(2000):
                    total += i * i

        spinners = [threading.Thread(target=_spin, name=f"r28v-call-spinner-{n}", daemon=True) for n in range(int(os.environ.get("R28V_SPINNERS", "4")))]
        started = time.perf_counter()
        for spinner in spinners:
            spinner.start()
        try:
            yield
        finally:
            stop.set()
            for spinner in spinners:
                spinner.join(timeout=5)
            _emit("call_phase", {"test": item.nodeid, "seconds": round(time.perf_counter() - started, 4), "spinners": len(spinners)})

except ImportError:  # imported outside pytest
    pass

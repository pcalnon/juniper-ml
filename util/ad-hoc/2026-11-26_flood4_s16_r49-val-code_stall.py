"""
pytest plugin for the r49 code lens: a whole-process stop injected at a chosen point of juniper-canopy's T-A2
measurement (src/tests/regression/test_x7_loop_responsiveness.py), an in-process repeat, and one verdict record per
test. Run as a script it calibrates the stop mechanisms against a ticking thread.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 49 (2026-11-26), a follow-up of ruling 28
    (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8); flood-4 session 16, code lens
    r49-val-code (validation of carrier r49, juniper-canopy). Written independently of the r49 builder's stall plugin.

Loaded as ``-p r49v_stall``: symlink this file under that name into a directory on PYTHONPATH (for instance the
plugins/ directory of util/ad-hoc/2026-11-25_flood4_s14_r27-val-code2_run_lane.py). With R49V_OUT unset it does nothing.

    R49V_OUT      output prefix (required): <prefix>.r49v.jsonl, one JSON object per line, kind-tagged
    R49V_STALL_S  seconds of each injected stop (default 0: nothing is injected)
    R49V_AT       where, comma-separated (default probe):
                    probe   -- on the event-loop thread, as the test's first /v1/health/live request enters the ASGI
                               transport: inside every probe's window, in the old harness and the new alike
                    driver  -- on the event-loop thread, as the test's first /api/status request enters the transport
                    worker  -- inside the stub's first get_status call (a worker thread when the route offloads)
                    release -- on the event-loop thread, as the new harness first calls _SlowBackend.release()
    R49V_MECH     how (default gil):
                    gil  -- one C call that sleeps while it holds the GIL (libc usleep through ctypes.PyDLL, which
                            does not release it): every Python thread of the process stops for R49V_STALL_S, the
                            shape of a stop-the-world garbage collection
                    gc   -- gc.collect() over R49V_HEAP_M million retained lists allocated at configure: the real
                            mechanism; the stop lasts as long as the collection does (recorded)
                    loop -- time.sleep on the calling thread: at a loop point only the loop stops
    R49V_HEAP_M   millions of retained empty lists for R49V_MECH=gc (default 0)
    R49V_ONLY     substring of the node ids that get the injection (default
                  test_health_stays_fast_while_upstream_is_slow); every test still gets its verdict record
    R49V_REPEAT   run every collected test N times in this process (parametrised, ids rep00..)

Run directly: ``python <this file> --calibrate [--seconds S] [--heap-m M]`` prints, per mechanism, the stop it made
and the longest gap a 1 ms ticking thread saw meanwhile (JSON).
"""

from __future__ import annotations

import argparse
import ctypes
import gc
import json
import os
import sys
import threading
import time

_OUT = os.environ.get("R49V_OUT", "")
_SECONDS = float(os.environ.get("R49V_STALL_S", "0") or 0)
_AT = {x.strip() for x in os.environ.get("R49V_AT", "probe").split(",") if x.strip()}
_MECH = os.environ.get("R49V_MECH", "gil")
_ONLY = os.environ.get("R49V_ONLY", "test_health_stays_fast_while_upstream_is_slow")
_LOCK = threading.Lock()
_STATE: dict = {"test": None, "inject": False, "done": set(), "stub": None, "stalls": []}
_KEEP: list = []
_LIBC: list = []
PROBE_PATH = "/v1/health/live"
DRIVER_PATH = "/api/status"


def _emit(kind: str, payload: dict) -> None:
    if not _OUT:
        return
    line = json.dumps({"kind": kind, "t": round(time.time(), 4), **payload}, default=str) + "\n"
    with _LOCK:
        with open(_OUT + ".r49v.jsonl", "a", encoding="utf-8") as handle:
            handle.write(line)


def gil_sleep(seconds: float) -> None:
    """Sleep in one C call that keeps the GIL: no other Python thread of this process runs meanwhile."""
    if not _LIBC:
        libc = ctypes.PyDLL(None)  # PyDLL, unlike CDLL, does not release the GIL around the call
        libc.usleep.argtypes = [ctypes.c_uint]
        _LIBC.append(libc)
    _LIBC[0].usleep(int(seconds * 1_000_000))


def _stop(where: str) -> None:
    started = time.perf_counter()
    if _MECH == "gil":
        gil_sleep(_SECONDS)
    elif _MECH == "gc":
        gc.collect()
    elif _MECH == "loop":
        time.sleep(_SECONDS)
    else:
        raise ValueError(f"unknown R49V_MECH {_MECH!r}")
    record = {"where": where, "mech": _MECH, "asked": _SECONDS, "seconds": round(time.perf_counter() - started, 4), "thread": threading.current_thread().name, "main_thread": threading.current_thread() is threading.main_thread(), "test": _STATE["test"]}
    with _LOCK:
        _STATE["stalls"].append(record)
    _emit("stall", record)


def _maybe_stop(where: str) -> None:
    if _SECONDS <= 0 or where not in _AT:
        return
    with _LOCK:
        if not _STATE["inject"] or where in _STATE["done"]:
            return
        _STATE["done"].add(where)
    _stop(where)


def _wrap_transport() -> None:
    import httpx

    cls = httpx.ASGITransport
    if getattr(cls.handle_async_request, "_r49v", False):
        return
    original = cls.handle_async_request

    async def handle_async_request(self, request, _original=original):
        path = request.url.path
        if path == PROBE_PATH:
            _maybe_stop("probe")
        elif path == DRIVER_PATH:
            _maybe_stop("driver")
        return await _original(self, request)

    handle_async_request._r49v = True
    cls.handle_async_request = handle_async_request


def _wrap_stub(module) -> None:
    cls = getattr(module, "_SlowBackend", None)
    if cls is None or getattr(cls, "_r49v_wrapped", False):
        return
    original_init, original_get_status = cls.__init__, cls.get_status
    original_release = getattr(cls, "release", None)

    def __init__(self, *args, _original=original_init, **kwargs):
        _original(self, *args, **kwargs)
        _STATE["stub"] = self

    def get_status(self, _original=original_get_status):
        _maybe_stop("worker")
        return _original(self)

    cls.__init__ = __init__
    cls.get_status = get_status
    if original_release is not None:

        def release(self, _original=original_release):
            _maybe_stop("release")
            return _original(self)

        cls.release = release
    cls._r49v_wrapped = True
    _emit("stub_wrapped", {"module": module.__name__, "file": getattr(module, "__file__", None), "has_release": original_release is not None})


def _stub_verdict() -> dict:
    stub = _STATE["stub"]
    if stub is None:
        return {}
    verdict = {"calls": getattr(stub, "calls", None)}
    for name in ("ran_on_loop_thread", "released_by_loop", "hold_seconds", "loop_only_seconds"):
        if hasattr(stub, name):
            verdict[name] = getattr(stub, name)
    return verdict


# ---------------------------------------------------------------------------------------------------- pytest hooks
def pytest_configure(config):
    if not _OUT:
        return
    heap = float(os.environ.get("R49V_HEAP_M", "0") or 0)
    if heap > 0:
        _KEEP.append([[] for _ in range(int(heap * 1_000_000))])
    _wrap_transport()
    _emit("session", {"python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "seconds": _SECONDS, "at": sorted(_AT), "mech": _MECH, "heap_m": heap, "only": _ONLY, "repeat": os.environ.get("R49V_REPEAT", "1")})


def pytest_generate_tests(metafunc):
    count = int(os.environ.get("R49V_REPEAT", "1") or 1)
    if _OUT and count > 1:
        metafunc.fixturenames.append("r49v_rep")
        metafunc.parametrize("r49v_rep", range(count), ids=[f"rep{n:02d}" for n in range(count)])


def pytest_collection_finish(session):
    if not _OUT:
        return
    seen = {}
    for item in session.items:
        module = getattr(item, "module", None)
        if module is not None:
            seen[module.__name__] = module
    for name, module in seen.items():
        if name.endswith("test_x7_loop_responsiveness"):
            _wrap_stub(module)
    files = {}
    for name in ("main", "backend.admission", "middleware", "httpx", "fastapi", "starlette"):
        module = sys.modules.get(name)
        files[name] = getattr(module, "__file__", None)
    _emit("module_files", files)


try:
    import pytest

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(item):
        if not _OUT:
            yield
            return
        with _LOCK:
            _STATE["test"] = item.nodeid
            _STATE["inject"] = _ONLY in item.nodeid
            _STATE["done"] = set()
            _STATE["stub"] = None
            _STATE["stalls"] = []
        started = time.perf_counter()
        outcome = yield
        seconds = round(time.perf_counter() - started, 4)
        error = None
        excinfo = getattr(outcome, "excinfo", None)
        if excinfo is not None:
            error = f"{excinfo[0].__name__}: {str(excinfo[1]).splitlines()[0] if str(excinfo[1]) else ''}"[:400]
        with _LOCK:
            stalls = list(_STATE["stalls"])
            _STATE["inject"] = False
        _emit("verdict", {"test": item.nodeid, "passed": excinfo is None, "seconds": seconds, "error": error, "stalls": stalls, "stub": _stub_verdict()})

except ImportError:  # imported outside pytest (the calibration run)
    pass


# ---------------------------------------------------------------------------------------------------- calibration
def _calibrate(seconds: float, heap_m: float) -> list[dict]:
    results = []
    gaps = {"max": 0.0}
    stop = threading.Event()

    def ticker() -> None:
        last = time.perf_counter()
        while not stop.is_set():
            time.sleep(0.001)
            now = time.perf_counter()
            gaps["max"] = max(gaps["max"], now - last)
            last = now

    thread = threading.Thread(target=ticker, name="r49v-ticker", daemon=True)
    thread.start()
    time.sleep(0.2)
    for mech in ("gil", "loop", "gc"):
        if mech == "gc":
            if heap_m <= 0:
                continue
            _KEEP.append([[] for _ in range(int(heap_m * 1_000_000))])
            time.sleep(0.2)
        gaps["max"] = 0.0
        started = time.perf_counter()
        if mech == "gil":
            gil_sleep(seconds)
        elif mech == "loop":
            time.sleep(seconds)
        else:
            gc.collect()
        took = time.perf_counter() - started
        time.sleep(0.05)
        results.append({"mech": mech, "asked": seconds if mech != "gc" else None, "heap_m": heap_m if mech == "gc" else None, "stop_seconds": round(took, 4), "ticker_max_gap_seconds": round(gaps["max"], 4)})
    stop.set()
    thread.join(timeout=5)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--seconds", type=float, default=1.3)
    parser.add_argument("--heap-m", type=float, default=0.0)
    args = parser.parse_args()
    if not args.calibrate:
        parser.error("nothing to do: pass --calibrate (as a pytest plugin, load it with -p)")
    print(json.dumps({"python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix, "results": _calibrate(args.seconds, args.heap_m)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

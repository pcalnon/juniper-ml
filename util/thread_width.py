#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Thread-width reads that cannot disturb what they measure -- the perf lane's shared instrument helper.

Why this exists
---------------
The perf lane measures OpenMP thread width: the width a thread will actually use for its next
parallel region, which is the calling thread's ``nthreads-var`` ICV. Two ways of reading it have
each destroyed a measurement, and both were written down as prose warnings first:

1. **``torch.get_num_threads()`` is not a passive read.** On a thread where torch has not yet run
   its per-thread lazy init, the getter runs it, and that RE-PINS the thread's ICV to torch's
   global (16 -> 8 on this host). An instrument that reads it ends the burst it exists to observe.
   Found 2026-09-11 (``notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md``
   §1.1-1.2), written into that note and into project memory, and walked into again by the next
   instrument six days later (``notes/JUNIPER_2026-09-16_JUNIPER-ECOSYSTEM_PERF-LANE-THREAD-WIDTH-SWEEP.md``
   §5: "Prose warnings do not bind. The guard belongs *inside* a shared helper that instruments
   cannot bypass.").
2. **``ctypes.CDLL("libgomp.so.1")`` is not guaranteed to be the runtime torch uses.** A bare soname
   finds an already-loaded library only when that library's SONAME is literally ``libgomp.so.1``.
   Measured 2026-09-23 in ``JuniperCascor1`` (torch 2.11.0+cu130):

   - after ``import torch`` the mapped runtime is torch's BUNDLED copy,
     ``site-packages/torch/lib/libgomp.so.1`` -- not the conda env's ``lib/libgomp.so.1.0.0``
     that the 2026-09-11 note recorded before the 3.13 -> 3.14 upgrade;
   - ``CDLL("libgomp.so.1")`` called BEFORE ``import torch`` loads the env's copy first, and torch
     then binds to THAT one. The instrument chose the runtime the system under test ran on.

   manylinux wheels rename a bundled runtime (``libgomp-<hash>.so.1``) and give it that name as
   its SONAME, so there a bare ``libgomp.so.1`` misses and loads a SECOND, independent runtime
   whose ICV nothing else reads. Every figure would then be "some libgomp says N".

What this module does instead
-----------------------------
* :class:`OpenMPRuntime` opens only a runtime that is ALREADY MAPPED, found in
  ``/proc/self/maps``, and opens it with ``RTLD_NOLOAD``, so it can never load one. If none is
  mapped it raises: import torch first. If more than one distinct runtime is mapped it raises
  instead of guessing. Its ``path`` goes into every result, so a reading is tied to a file.
* :func:`install_torch_getter_guard` replaces ``torch.get_num_threads`` so that a call from any
  thread but the main thread raises :class:`ThreadWidthHazard`. Calls made from inside the
  ``torch`` package are passed through: they are the system's own behaviour, not the
  instrument's. The main thread is allowed because torch has already initialised it by the time
  an instrument can call anything; ``--self-check`` measures that premise instead of assuming it.
* The guard is UNCONDITIONAL on purpose. Under ``OMP_NUM_THREADS=2`` -- cascor's default since
  cascor#683 -- a fresh thread already sits at torch's global width, so the getter's re-pin is
  2 -> 2 and invisible (measured 2026-09-23: ``--self-check`` reports it NOT SEEN there, and
  16 -> 8 with the variables unset). An instrument validated in the capped environment would pass
  and then corrupt its uncapped arm; that is the arm a width sweep exists to compare.

Enforcement
-----------
``tests/test_thread_width.py`` fails CI when an instrument under ``util/ad-hoc/`` or
``util/experiments/`` calls ``get_num_threads()`` or opens an OpenMP runtime by soname itself.
The instruments that predate this module are grandfathered BY NAME, because their evidence was
produced by the code as it stands; the list can only shrink.

Usage (from an instrument under ``util/ad-hoc/``)::

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # util/
    from thread_width import OpenMPRuntime, install_torch_getter_guard

    import torch
    install_torch_getter_guard(torch)
    omp = OpenMPRuntime()            # after torch is imported: it only opens what is mapped
    width = omp.max_threads()        # the CALLING thread's ICV; mutates nothing
    record = {"openmp_runtime": omp.path, "icv": width}

Self-check, in an environment that has torch (it measures both hazards and the helper)::

    /opt/miniforge3/envs/JuniperCascor1/bin/python util/thread_width.py --self-check
"""

from __future__ import annotations

import argparse
import ctypes
import functools
import json
import os
import re
import sys
import threading
from collections.abc import Callable
from typing import Any

MAPS_PATH = "/proc/self/maps"

#: One OpenMP runtime file: GNU (``libgomp``), Intel (``libiomp5``) or LLVM (``libomp``), with an
#: optional manylinux hash suffix and an optional version tail. ``libompd`` (the OMPD debugging
#: library) and ``libgomp-plugin-*`` (offload plugins) are deliberately not matched.
OPENMP_RUNTIME_RE = re.compile(r"/lib(?:gomp|iomp5|omp)(?:-[0-9a-f]{6,})?\.so(?:\.\d+)*$")

#: Set on the replacement so a second install is a no-op, and so a test can tell guarded from raw.
GUARD_MARKER = "__juniper_thread_width_guard__"

#: The self-check verdict that records the hazard rather than a claim of this module. It is
#: environment-dependent: with ``OMP_NUM_THREADS=2`` (cascor's default since cascor#683) every
#: thread starts at torch's global width, the getter re-pins 2 -> 2, and nothing is visible.
HAZARD_OBSERVATION = "raw_getter_repins_a_fresh_thread"


class OpenMPRuntimeError(RuntimeError):
    """No usable OpenMP runtime to read."""


class OpenMPRuntimeNotMapped(OpenMPRuntimeError):
    """The process has no OpenMP runtime mapped, or not the one asked for."""


class AmbiguousOpenMPRuntime(OpenMPRuntimeError):
    """More than one distinct OpenMP runtime is mapped; reading "the" ICV would be a guess."""


class ThreadWidthHazard(RuntimeError):
    """An instrument called ``torch.get_num_threads()`` off the main thread."""


def parse_openmp_runtimes(maps_text: str) -> list[str]:
    """Distinct OpenMP runtime paths in a ``/proc/<pid>/maps`` text, in first-mapped order.

    A ``(deleted)`` suffix is kept out of the path: a runtime whose file was replaced after it was
    mapped is still the runtime in use, and ``/proc`` appends the marker after the path.
    """
    seen: list[str] = []
    for line in maps_text.splitlines():
        fields = line.split(None, 5)
        if len(fields) < 6:
            continue
        path = fields[5].strip()
        if path.endswith(" (deleted)"):
            path = path[: -len(" (deleted)")]
        if OPENMP_RUNTIME_RE.search(path) and path not in seen:
            seen.append(path)
    return seen


def mapped_openmp_runtimes() -> list[str]:
    """Distinct OpenMP runtime paths mapped into THIS process right now."""
    with open(MAPS_PATH, "r", encoding="utf-8", errors="replace") as handle:
        return parse_openmp_runtimes(handle.read())


class OpenMPRuntime:
    """A handle on the OpenMP runtime this process already uses. Reads mutate nothing.

    ``path`` is the file the reading came from; record it with every result.
    """

    def __init__(self, path: str | None = None) -> None:
        mapped = mapped_openmp_runtimes()
        if path is None:
            if not mapped:
                raise OpenMPRuntimeNotMapped("no OpenMP runtime is mapped into this process; import the library under test (torch) before opening one, because opening one first chooses the runtime it will bind to")
            if len(mapped) > 1:
                raise AmbiguousOpenMPRuntime(f"{len(mapped)} distinct OpenMP runtimes are mapped ({', '.join(mapped)}); each has its own ICVs, so pass path= to name the one under test")
            path = mapped[0]
        elif path not in mapped:
            raise OpenMPRuntimeNotMapped(f"{path} is not mapped into this process (mapped: {', '.join(mapped) or 'none'})")
        self.path = path
        # RTLD_NOLOAD: return the existing mapping or fail. It can never load a second copy.
        self._lib = ctypes.CDLL(path, mode=os.RTLD_NOLOAD | os.RTLD_LAZY)
        self._lib.omp_get_max_threads.restype = ctypes.c_int
        self._lib.omp_get_max_threads.argtypes = []
        self._lib.omp_get_num_procs.restype = ctypes.c_int
        self._lib.omp_get_num_procs.argtypes = []

    def max_threads(self) -> int:
        """The CALLING thread's ``nthreads-var`` ICV: the width of its next parallel region."""
        return int(self._lib.omp_get_max_threads())

    def num_procs(self) -> int:
        return int(self._lib.omp_get_num_procs())

    def describe(self) -> dict[str, Any]:
        return {"openmp_runtime": self.path, "omp_num_procs": self.num_procs()}


def _caller_module(depth: int) -> str:
    try:
        frame = sys._getframe(depth + 1)
    except ValueError:
        return ""
    return str(frame.f_globals.get("__name__", ""))


def install_torch_getter_guard(torch_module: Any = None) -> Callable[[], None]:
    """Make ``torch.get_num_threads()`` raise :class:`ThreadWidthHazard` off the main thread.

    Idempotent. Returns an uninstaller that restores the original getter only if the guard is
    still the installed one. A call whose immediate caller lives in the ``torch`` package is
    passed through: that call is the system under test re-pinning itself, which is a result.
    """
    if torch_module is None:
        import torch as torch_module  # noqa: PLC0415 -- deferred: this module must import without torch

    current = torch_module.get_num_threads
    if getattr(current, GUARD_MARKER, False):
        return lambda: None
    original = current

    @functools.wraps(original)
    def guarded_get_num_threads(*args: Any, **kwargs: Any) -> Any:
        if threading.current_thread() is threading.main_thread():
            return original(*args, **kwargs)
        caller = _caller_module(1)
        if caller == "torch" or caller.startswith("torch."):
            return original(*args, **kwargs)
        raise ThreadWidthHazard(
            f"torch.get_num_threads() called from thread {threading.current_thread().name!r} (module {caller or '?'}). "
            "It is not a passive read: on a thread torch has not initialised it RE-PINS that thread's OpenMP width "
            "and ends the burst being measured. Read OpenMPRuntime().max_threads() instead, or read the getter "
            "on the main thread after the measurement."
        )

    setattr(guarded_get_num_threads, GUARD_MARKER, True)
    torch_module.get_num_threads = guarded_get_num_threads

    def uninstall() -> None:
        if torch_module.get_num_threads is guarded_get_num_threads:
            torch_module.get_num_threads = original

    return uninstall


# ------------------------------------------------------------------------------------------------
# --self-check: measure both hazards and the helper, in an environment that has torch
# ------------------------------------------------------------------------------------------------
def _on_fresh_thread(fn: Callable[[], Any]) -> Any:
    box: dict[str, Any] = {}

    def run() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:  # re-raised on the calling thread below
            box["error"] = exc

    worker = threading.Thread(target=run, name="self-check-worker")
    worker.start()
    worker.join()
    if "error" in box:
        raise box["error"]
    return box["value"]


def self_check() -> dict[str, Any]:
    """Run the measurements the module's claims rest on. Every value is observed, none assumed."""
    import torch  # noqa: PLC0415

    report: dict[str, Any] = {"torch": torch.__version__, "blas_env": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")}}
    report["mapped_before_open"] = mapped_openmp_runtimes()
    omp = OpenMPRuntime()
    report["runtime"] = omp.describe()
    report["mapped_after_open"] = mapped_openmp_runtimes()

    # 1. The helper's read is passive: two reads on a fresh thread agree.
    report["fresh_thread_helper_reads"] = _on_fresh_thread(lambda: (omp.max_threads(), omp.max_threads()))

    # 2. The hazard the guard exists for: the raw getter re-pins a fresh thread.
    raw = torch.get_num_threads

    def getter_between() -> tuple[int, int, int]:
        before = omp.max_threads()
        reported = raw()
        return before, reported, omp.max_threads()

    report["fresh_thread_raw_getter"] = dict(zip(("icv_before", "getter_returned", "icv_after"), _on_fresh_thread(getter_between)))

    # 3. The main-thread premise: a getter call on main after import changes nothing.
    main_before = omp.max_threads()
    main_reported = raw()
    report["main_thread_raw_getter"] = {"icv_before": main_before, "getter_returned": main_reported, "icv_after": omp.max_threads()}

    # 4. The guard: raises on a fresh thread, passes on main, and the fresh thread's ICV is untouched.
    uninstall = install_torch_getter_guard(torch)
    try:

        def guarded_call() -> dict[str, Any]:
            before = omp.max_threads()
            try:
                torch.get_num_threads()
                outcome = "returned"
            except ThreadWidthHazard:
                outcome = "raised ThreadWidthHazard"
            return {"outcome": outcome, "icv_before": before, "icv_after": omp.max_threads()}

        report["guard_fresh_thread"] = _on_fresh_thread(guarded_call)
        report["guard_main_thread_returns"] = torch.get_num_threads()
        report["guard_idempotent"] = install_torch_getter_guard(torch) is not None and getattr(torch.get_num_threads, GUARD_MARKER, False)
    finally:
        uninstall()
    report["guard_uninstalled"] = torch.get_num_threads is raw

    fresh_raw = report["fresh_thread_raw_getter"]
    main_raw = report["main_thread_raw_getter"]
    guard = report["guard_fresh_thread"]
    report["verdicts"] = {
        "helper_opened_only_what_was_mapped": report["mapped_before_open"] == report["mapped_after_open"],
        "helper_read_is_passive": report["fresh_thread_helper_reads"][0] == report["fresh_thread_helper_reads"][1],
        "raw_getter_repins_a_fresh_thread": fresh_raw["icv_before"] != fresh_raw["icv_after"],
        "main_thread_getter_is_inert": main_raw["icv_before"] == main_raw["icv_after"],
        "guard_raises_off_main_and_leaves_icv": guard["outcome"] == "raised ThreadWidthHazard" and guard["icv_before"] == guard["icv_after"],
        "guard_uninstalls": report["guard_uninstalled"],
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Passive OpenMP width reads and the torch getter guard.")
    parser.add_argument("--self-check", action="store_true", help="measure both hazards and the helper (needs torch)")
    parser.add_argument("--json", action="store_true", help="print the self-check report as JSON")
    args = parser.parse_args(argv)
    if not args.self_check:
        print("mapped OpenMP runtimes:", mapped_openmp_runtimes() or "none")
        return 0
    report = self_check()
    if args.json:
        print(json.dumps(report, indent=1, default=str))
    else:
        print(f"torch {report['torch']}   runtime {report['runtime']['openmp_runtime']}   BLAS env {report['blas_env']}")
        for key in ("fresh_thread_helper_reads", "fresh_thread_raw_getter", "main_thread_raw_getter", "guard_fresh_thread", "guard_main_thread_returns"):
            print(f"  {key:<27} {report[key]}")
        for name, ok in report["verdicts"].items():
            if name == HAZARD_OBSERVATION:
                seen = "SEEN" if ok else "NOT SEEN -- a fresh thread's ICV already equals torch's global (e.g. OMP_NUM_THREADS set), so the re-pin is invisible here and still real where they differ"
                print(f"  obs  {name}: {seen}")
            else:
                print(f"  {'OK  ' if ok else 'FAIL'} {name}")
    # The raw-getter re-pin is the HAZARD, observed; it depends on the environment. The rest are
    # the helper's own claims, and only they decide the exit code.
    claims = {k: v for k, v in report["verdicts"].items() if k != HAZARD_OBSERVATION}
    return 0 if all(claims.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

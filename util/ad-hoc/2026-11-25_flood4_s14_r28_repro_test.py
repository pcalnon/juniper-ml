"""
pytest probe: reproduce, on demand and inside one test process, the event-loop gap that fails juniper-canopy's
test_relay_cascade_add_does_not_block_the_loop, by recreating the contention CI's process carried.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 builder r28

Copied into a juniper-canopy clone as src/tests/regression/test_r28_repro_relay_stall.py (beside the test it probes,
so ``import test_x7_sites_outside_main_gate`` resolves and canopy's conftest applies); never committed there.
Environment: R28_REPRO_OUT (JSONL out, required), R28_RUNS (measurements per cell and procedure, default 10),
R28_CELLS (comma list, default all), R28_PROCEDURES (comma list of relay,null,shape; default relay,null).

Every measurement runs in a fresh event loop on the main thread (as pytest-asyncio runs each test), with the relay's
lazily imported modules imported beforehand (as in CI's process). Revision 1 of this probe (2026-11-25, output
runs/repro/base_unpinned_cov.jsonl) reused one loop and imported inside patch.dict(sys.modules); revision 2 does not.

Cells (contention started in THIS process, stopped and joined at the end of the cell):
    none       nothing extra
    pyspin     one thread in a pure-Python loop (holds the GIL; yields only on the interpreter's forced switch)
    torchspin  one thread looping a tiny in-place torch op (releases and retakes the GIL around every op)
    demo1/2/3  1/2/3 DemoMode(update_interval=0.1).start() training threads -- what the leaking tests leave behind
Procedures:
    relay      the real test's procedure (its _Ticker, _FakeStream, _WSM, patches, constants) with the stub recording
               which thread ran it; records worst_gap, elapsed, whether the stub ran on the loop thread
    null       the same ticker around ``await asyncio.sleep(0.9)`` and nothing else: no relay, no stub, no thread
    shape      the shape-of-fix probe: a stub held on a threading.Event that only a coroutine on the loop releases;
               records whether the loop released it and how long that took (no pass/fail threshold here)
    sampled    the relay procedure with a sampler thread recording the loop thread's innermost frames every 10 ms;
               reports the frames seen inside the ticker's worst gap (where the loop thread was while it did not tick)
    held       the fix's own _HeldCall (fixed tree only), offloaded with asyncio.to_thread: whether the loop released
               it and the release latency (entry to return) -- the distribution HOLD_SECONDS is set against
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import threading
import time
import importlib
import types
from unittest.mock import MagicMock, patch

import pytest
import test_x7_sites_outside_main_gate as x7  # noqa: E402 - the harness under test, imported from beside this probe

OUT = os.environ.get("R28_REPRO_OUT", "")
RUNS = int(os.environ.get("R28_RUNS", "10"))
CELLS = [c for c in os.environ.get("R28_CELLS", "none,pyspin,torchspin,demo1,demo2,demo3").split(",") if c]
PROCEDURES = [p for p in os.environ.get("R28_PROCEDURES", "relay,null").split(",") if p]


def _write(row: dict) -> None:
    with open(OUT, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


class _Contention:
    def __init__(self, cell: str) -> None:
        self.cell = cell
        self.stop = threading.Event()
        self.threads: list[threading.Thread] = []
        self.demos = []

    def __enter__(self):
        if self.cell == "pyspin":
            self.threads.append(threading.Thread(target=self._pyspin, daemon=True, name="r28-pyspin"))
        elif self.cell == "torchspin":
            self.threads.append(threading.Thread(target=self._torchspin, daemon=True, name="r28-torchspin"))
        elif self.cell.startswith("demo"):
            from demo_mode import DemoMode

            for _ in range(int(self.cell[4:])):
                demo = DemoMode(update_interval=0.1)
                demo.start()
                self.demos.append(demo)
        for thread in self.threads:
            thread.start()
        time.sleep(0.5)  # let the contention reach its steady state before measuring
        return self

    def __exit__(self, *_exc):
        self.stop.set()
        for thread in self.threads:
            thread.join(timeout=10)
        for demo in self.demos:
            demo._stop.set()
            if demo.thread is not None:
                demo.thread.join(timeout=30)
        return False

    def demo_alive(self) -> int:
        return sum(1 for t in threading.enumerate() if t.name.endswith("(_training_loop)"))

    def _pyspin(self) -> None:
        while not self.stop.is_set():
            total = 0
            for i in range(2000):
                total += i * i

    def _torchspin(self) -> None:
        import torch

        a = torch.zeros(4)
        b = torch.ones(4)
        while not self.stop.is_set():
            a.add_(b)


async def _relay_once() -> dict:
    counter: list[int] = []
    where: dict = {}
    loop_thread = threading.get_ident()
    adapter = x7.CascorServiceAdapter(service_url="http://localhost:8200", client=MagicMock())

    def _stub(*_a, **_kw):
        counter.append(1)
        where["thread"] = threading.get_ident()
        time.sleep(x7.BLOCK_SECONDS)
        return {"nodes": ["n0"]}

    adapter.extract_network_topology = _stub
    first = x7._FakeStream(messages=[{"type": "cascade_add"}])
    cancel = x7._FakeStream(connect_exc=asyncio.CancelledError())
    wsm = x7._WSM()
    settings = types.SimpleNamespace(use_websocket_set_params=False, ws_relay_summary_interval_seconds=0.0)
    wsm_mod = types.ModuleType("communication.websocket_manager")
    wsm_mod.websocket_manager = wsm
    ticker = x7._Ticker()
    await ticker.start()
    started = time.perf_counter()
    with (
        patch(x7._CTS, x7._stream_factory(first, cancel)),
        patch.dict(sys.modules, {"communication.websocket_manager": wsm_mod}),
        patch(x7._SETTINGS, return_value=settings),
    ):
        await adapter.start_metrics_relay()
        await asyncio.wait_for(adapter._relay_task, timeout=30)
    elapsed = time.perf_counter() - started
    await ticker.stop()
    return {"worst_gap": ticker.worst_gap, "elapsed": elapsed, "ticks": len(ticker.ticks), "stub_calls": len(counter), "stub_on_loop_thread": where.get("thread") == loop_thread, "topology_broadcast": any(p.get("type") == "topology" for p in wsm.payloads)}


async def _sampled_once() -> dict:
    """The relay procedure with a sampler thread recording the loop thread's innermost frames every 10 ms."""
    main_ident = threading.get_ident()
    samples: list[tuple[float, list[str]]] = []
    done = threading.Event()

    def _sample() -> None:
        while not done.is_set():
            frame = sys._current_frames().get(main_ident)
            stack = []
            while frame is not None and len(stack) < 6:
                stack.append(f"{os.path.basename(frame.f_code.co_filename)}:{frame.f_lineno}:{frame.f_code.co_name}")
                frame = frame.f_back
            samples.append((time.perf_counter(), stack))
            time.sleep(0.01)

    sampler = threading.Thread(target=_sample, daemon=True, name="r28-sampler")
    sampler.start()
    try:
        row = await _relay_once_with_ticks()
    finally:
        done.set()
        sampler.join(timeout=5)
    ticks = row.pop("tick_times")
    gaps = [(ticks[i + 1] - ticks[i], ticks[i], ticks[i + 1]) for i in range(len(ticks) - 1)]
    worst, start, end = max(gaps) if gaps else (0.0, 0.0, 0.0)
    row["sampled_worst_gap"] = worst
    inside = [s for t, s in samples if start < t < end]
    counts: dict[str, int] = {}
    for stack in inside:
        key = " < ".join(stack[:4])
        counts[key] = counts.get(key, 0) + 1
    row["gap_samples"] = len(inside)
    row["gap_top_stacks"] = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    return row


async def _relay_once_with_ticks() -> dict:
    row = {}
    ticker_box: dict = {}
    original = x7._Ticker

    class _Keep(original):
        def __init__(self):
            super().__init__()
            ticker_box["t"] = self

    x7_ticker, x7._Ticker = x7._Ticker, _Keep
    try:
        row = await _relay_once()
    finally:
        x7._Ticker = x7_ticker
    row["tick_times"] = list(ticker_box["t"].ticks)
    return row


async def _null_once() -> dict:
    ticker = x7._Ticker()
    await ticker.start()
    started = time.perf_counter()
    await asyncio.sleep(0.9)
    elapsed = time.perf_counter() - started
    await ticker.stop()
    return {"worst_gap": ticker.worst_gap, "elapsed": elapsed, "ticks": len(ticker.ticks)}


async def _shape_once() -> dict:
    """The shape of the deterministic fix: the loop must run while the call is held."""
    loop = asyncio.get_running_loop()
    loop_thread = threading.get_ident()
    entered = threading.Event()
    release = threading.Event()
    seen: dict = {}

    def _held():
        seen["thread"] = threading.get_ident()
        entered.set()
        seen["released"] = release.wait(timeout=10)
        return {"nodes": ["n0"]}

    async def _releaser():
        while not entered.is_set():
            await asyncio.sleep(0.005)
        seen["entered_at"] = time.perf_counter()
        release.set()

    started = time.perf_counter()
    releaser = loop.create_task(_releaser())
    await asyncio.to_thread(_held)
    await releaser
    return {"released_by_loop": seen.get("released"), "off_loop": seen.get("thread") != loop_thread, "elapsed": time.perf_counter() - started}


async def _held_once() -> dict:
    """The fix's own harness (x7._HeldCall, present only in the fixed tree): how long the loop takes to release it."""
    stamps: dict = {}

    class _Timed(x7._HeldCall):
        def __call__(self, *args, **kwargs):
            stamps["entered"] = time.perf_counter()
            result = super().__call__(*args, **kwargs)
            stamps["returned"] = time.perf_counter()
            return result

    held = _Timed({"nodes": ["n0"]})
    async with held.released_by_the_loop():
        await asyncio.to_thread(held)
    return {"released_by_loop": held.released_by_loop, "off_loop": held.ran_on_loop_thread is False, "release_latency": stamps["returned"] - stamps["entered"]}


def _fresh_loop(coro_fn):
    """Run one measurement in a NEW event loop on this (the main) thread -- as pytest-asyncio runs each test.

    A new loop has no default executor, so the relay's first ``asyncio.to_thread`` builds one and starts its first
    worker thread, exactly as in CI's single run of the real test.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro_fn())
    finally:
        loop.run_until_complete(loop.shutdown_default_executor())
        loop.close()


@pytest.mark.timeout(1800)
@pytest.mark.parametrize("cell", CELLS)
def test_r28_contention_cell(cell):
    assert OUT, "R28_REPRO_OUT must name the JSONL output"
    # CI's process had imported these long before the real test ran (its frame-validation WARNING is logged in the
    # same millisecond as the connect), so import them here, outside every patch.dict(sys.modules) window.
    importlib.import_module("juniper_cascor_protocol.envelope")
    importlib.import_module("observability")

    with _Contention(cell) as contention:
        cpu0, wall0 = time.process_time(), time.perf_counter()
        for procedure in PROCEDURES:
            for run in range(RUNS):
                once = {"relay": _relay_once, "null": _null_once, "shape": _shape_once, "sampled": _sampled_once, "held": _held_once}[procedure]
                row = _fresh_loop(once)
                row.update({"cell": cell, "procedure": procedure, "run": run, "demo_threads_alive": contention.demo_alive(), "switchinterval": sys.getswitchinterval()})
                _write(row)
        cpu, wall = time.process_time() - cpu0, time.perf_counter() - wall0
        _write({"cell": cell, "procedure": "cpu", "process_cpu_seconds": cpu, "wall_seconds": wall, "cores_used": cpu / wall if wall else None})

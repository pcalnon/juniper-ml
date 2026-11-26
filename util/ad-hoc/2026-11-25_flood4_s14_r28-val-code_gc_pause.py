"""
Measure how long one full cyclic-GC pass holds the interpreter, by heap size, on the interpreter that runs this file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code

Usage:
    python <this file> [millions ...]      (default 1 2 4 8)

For each heap size: retain that many million empty lists (each GC-tracked), then time gc.collect() (full) three times,
and time how long a second thread is kept from running Python during one full pass (the whole-process stop a loop
thread would see). Prints one JSON line per size, then the interpreter identity.
"""

from __future__ import annotations

import gc
import json
import sys
import threading
import time


def blocked_during_collect() -> float:
    """Largest gap between a ticking thread's samples while the main thread runs one gc.collect()."""
    samples: list[float] = []
    stop = threading.Event()

    def _tick() -> None:
        while not stop.is_set():
            samples.append(time.perf_counter())
            time.sleep(0.001)

    ticker = threading.Thread(target=_tick, daemon=True)
    ticker.start()
    time.sleep(0.05)
    gc.collect()
    time.sleep(0.05)
    stop.set()
    ticker.join()
    return max(b - a for a, b in zip(samples, samples[1:]))


def main() -> int:
    sizes = [float(a) for a in sys.argv[1:]] or [1.0, 2.0, 4.0, 8.0]
    print(json.dumps({"python": sys.version, "executable": sys.executable, "base_prefix": sys.base_prefix}), flush=True)
    for millions in sizes:
        keep = [[] for _ in range(int(millions * 1_000_000))]
        gc.collect()
        passes = []
        for _ in range(3):
            started = time.perf_counter()
            gc.collect()
            passes.append(round(time.perf_counter() - started, 4))
        gap = round(blocked_during_collect(), 4)
        print(json.dumps({"heap_millions": millions, "full_collect_seconds": passes, "other_thread_max_gap_seconds": gap}), flush=True)
        del keep
        gc.collect()
    return 0


if __name__ == "__main__":
    sys.exit(main())

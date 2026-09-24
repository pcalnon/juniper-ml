"""Lane A1: is the per-character cost of _ENTITY_TAG_LIST flat (linear) or rising (super-linear)?

redos_offline.py showed the per-character cost at 1 MiB several times the cost at 8 KiB for
some shapes. That is either an algorithmic term or the backtracking stack outgrowing the
caches. This fits the log-log slope over doubling sizes, and records the peak traced memory
of one parse, so the two explanations can be told apart. Only sizes up to the cap matter to
the service; the larger ones exist to expose a term the cap would hide.
"""

import math
import sys
import time
import tracemalloc

SCRATCH = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1"
sys.path.insert(0, f"{SCRATCH}/tree-3a76a4c")
from juniper_data.api import http_cache as hc  # noqa: E402

assert hc.__file__.startswith(SCRATCH)
LIST = hc._ENTITY_TAG_LIST


def fit(unit, n):
    return (unit * (n // len(unit) + 1))[:n]


SHAPES = {
    "',' * n + x": lambda n: fit(",", n - 1) + "x",
    "', ' * k + x": lambda n: fit(", ", n - 1) + "x",
    "'\"\",' * k + x": lambda n: fit('"",', n - 1) + "x",
    "' ' * n + x": lambda n: fit(" ", n - 1) + "x",
}


def tmin(fn, reps):
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        best = min(best, time.perf_counter_ns() - t0)
    return best / 1e3


for name, build in SHAPES.items():
    pts = []
    print(f"\n{name}")
    for k in range(8, 21):
        n = 2**k
        s = build(n)
        us = tmin(lambda: LIST.fullmatch(s), 20 if n <= 16384 else 4)
        tracemalloc.start()
        LIST.fullmatch(s)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        pts.append((n, us))
        print(f"  n={n:8d}  {us:12.1f} us  {us * 1000 / n:7.1f} ns/char  peak_traced={peak / 1024:10.1f} KiB ({peak / n:6.1f} B/char)")
    # local slopes of log(time) vs log(n)
    slopes = [math.log(pts[i + 1][1] / pts[i][1]) / math.log(2) for i in range(len(pts) - 1)]
    print("  local log-log slopes:", " ".join(f"{s:.2f}" for s in slopes))
    capped = [s for (n, _), s in zip(pts, slopes) if n < 8192]
    print(f"  mean slope for n < 8192: {sum(capped) / len(capped):.2f}  (1.0 = linear, 2.0 = quadratic)")

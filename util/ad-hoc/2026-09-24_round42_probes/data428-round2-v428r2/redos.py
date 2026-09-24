"""Probe http_cache._ENTITY_TAG_LIST for catastrophic backtracking (validator scratch)."""

import sys
import time

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr")
from juniper_data.api.http_cache import _ENTITY_TAG_LIST  # noqa: E402


def t(label: str, s: str) -> float:
    t0 = time.perf_counter()
    r = _ENTITY_TAG_LIST.fullmatch(s)
    dt = time.perf_counter() - t0
    print(f"{label:40s} len={len(s):6d} match={r is not None} {dt * 1000:10.2f} ms", flush=True)
    return dt


# Pattern A: many ", " groups then a trailing garbage char
for k in (10, 14, 16, 18, 20, 22):
    t(f"', ' * {k} + 'x'", ", " * k + "x")
# Pattern B: long whitespace then garbage
for n in (1000, 4000, 8000):
    t(f"' ' * {n} + 'x'", " " * n + "x")
# Pattern C: more whitespace per group
for k in (6, 8, 10):
    t(f"',   ' * {k} + 'x'", ",   " * k + "x")

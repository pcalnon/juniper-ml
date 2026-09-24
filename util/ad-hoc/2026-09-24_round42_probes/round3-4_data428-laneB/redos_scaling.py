"""Lane B: asymptotic scaling of the shipped _ENTITY_TAG_LIST past the cap (regex alone)."""

from __future__ import annotations

import time

from juniper_data.api import http_cache as hc

rx = hc._ENTITY_TAG_LIST


def t(s: str, reps: int = 3) -> float:
    best = 1e9
    for _ in range(reps):
        t0 = time.perf_counter()
        rx.fullmatch(s)
        best = min(best, time.perf_counter() - t0)
    return best


for name, unit, tail in (("commas", ",", "x"), ("comma-space", ", ", "x"), ("spaces", " ", "x"), ("comma-tabs", ",\t\t", "x"), ("tabs-then-commas", None, None)):
    row = []
    for n in (8192, 16384, 32768, 65536, 131072):
        s = ("\t" * (n // 2) + "," * (n // 2 - 1) + "x") if unit is None else unit * (n // len(unit)) + tail
        row.append((n, t(s)))
    base = row[0][1]
    print(name.ljust(18), "  ".join(f"{n//1024}k={v*1e3:8.2f}ms(x{v/base:5.1f})" for n, v in row))

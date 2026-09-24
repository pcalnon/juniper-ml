"""Lane B: time the SHIPPED entity-tag grammar (3a76a4c) on hostile shapes, and check scaling.

Loads http_cache.py from the extracted tree (PYTHONPATH). For each shape, times the three public
predicates on inputs of growing length up to (and one over) the 8192 cap, and reports the
ratio t(8k)/t(1k): ~8 is linear, ~64 is quadratic. Also a random fuzz at the cap.
"""

from __future__ import annotations

import random
import time

from juniper_data.api import http_cache as hc

ETAG = hc.strong_etag("a" * 64)
CAP = hc.MAX_PRECONDITION_FIELD_LENGTH


def fit(unit: str, n: int, tail: str = "x") -> str:
    k = max(1, (n - len(tail)) // len(unit))
    return unit * k + tail


SHAPES = {
    "comma-space": lambda n: fit(", ", n),
    "spaces": lambda n: fit(" ", n),
    "comma-tabs": lambda n: fit(",\t\t", n),
    "space-comma-space": lambda n: fit(" , ", n),
    "unterminated-quote": lambda n: '"' + "a" * (n - 1),
    "W/-run": lambda n: fit("W/", n),
    "tags-no-commas": lambda n: fit('"a" ', n),
    "tag-wide-ws-comma": lambda n: fit('"a"' + " " * 50 + ",", n),
    "comma-W/": lambda n: fit(", W/", n, ""),
    "adjacent-tags": lambda n: fit('""', n, ""),
    "tags-then-open-quote": lambda n: fit('"a",', n, '"'),
    "commas": lambda n: fit(",", n),
    "tabs-then-commas": lambda n: "\t" * (n // 2) + "," * (n // 2 - 1) + "x",
    "ws-quote-ws": lambda n: fit(' " ', n),
    "W/-quote": lambda n: fit('W/"', n),
}


def time_all(field: str) -> float:
    t0 = time.perf_counter()
    hc.if_none_match_hits(field, ETAG)
    hc.if_match_fails(field, ETAG)
    hc.write_preconditions_hold(None, field, ETAG)
    hc.write_preconditions_hold(field, None, ETAG)
    return time.perf_counter() - t0


def best_of(field: str, reps: int = 5) -> float:
    return min(time_all(field) for _ in range(reps))


print(f"cap={CAP}")
worst = 0.0
for name, make in SHAPES.items():
    times = {n: best_of(make(n)) for n in (1024, 2048, 4096, CAP)}
    over = best_of(make(CAP + 1))
    ratio = times[CAP] / times[1024] if times[1024] else float("nan")
    worst = max(worst, times[CAP])
    print(f"{name:22s} 1k={times[1024]*1e3:7.3f}ms 2k={times[2048]*1e3:7.3f}ms 4k={times[4096]*1e3:7.3f}ms 8k={times[CAP]*1e3:7.3f}ms over-cap={over*1e3:7.3f}ms ratio8k/1k={ratio:5.1f}")

random.seed(20260924)
alphabet = [",", " ", "\t", '"', "W", "/", "a"]
fuzz_worst = 0.0
fuzz_worst_field = ""
for _ in range(400):
    f = "".join(random.choice(alphabet) for _ in range(CAP))
    t = time_all(f)
    if t > fuzz_worst:
        fuzz_worst, fuzz_worst_field = t, f
print(f"random fuzz at cap (400 fields): worst {fuzz_worst*1e3:.3f} ms; worst field starts {fuzz_worst_field[:40]!r}")
print(f"worst structured shape at cap: {worst*1e3:.3f} ms")

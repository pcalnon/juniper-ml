"""X-A (APD-CASCOR-008) probes against the merged tree, over real HTTP (scratch only)."""

from __future__ import annotations

import logging
import os
import sys
import threading
import time

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.ERROR)

from fakejd import FakeJD  # noqa: E402
from juniper_data_client import JuniperDataClient  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402

TG = M._TRUNCATABLE_GENERATORS
print("manager module:", M.__file__)


def reader_for(fake):
    return TG.reader(JuniperDataClient, source=fake.url, api_key=None)


def probe_failure_mode(mode, delay=0.0):
    fake = FakeJD()
    try:
        TG.reset()
        fake.gen_mode, fake.gen_delay = mode, delay
        t0 = time.monotonic()
        first = reader_for(fake)()
        dt = time.monotonic() - t0
        memo_after_fail = dict(TG._by_source)
        fake.gen_mode = "ok"
        second = reader_for(fake)()
        third = reader_for(fake)()
        print(f"[{mode:8s}] first={first!r} ({dt:.2f}s) memo_after_first={memo_after_fail!r} second={sorted(second) if second is not None else None} third_is_memo={third is second} gen_calls={fake.gen_calls}")
    finally:
        fake.close()


print("\n== 1. failure modes: never memoised, retried next call ==")
probe_failure_mode("delay", delay=7.0)
probe_failure_mode("500")
probe_failure_mode("badjson")
probe_failure_mode("empty")
probe_failure_mode("dict")
probe_failure_mode("noschema")

print("\n== 1b. a PARTIAL listing (equities lost its schema; others kept theirs) ==")
fake = FakeJD()
TG.reset()
fake.gen_mode = "partial"
r1 = reader_for(fake)()
fake.gen_mode = "ok"  # producer recovers
r2 = reader_for(fake)()
print(f"partial -> {sorted(r1) if r1 is not None else None}; after producer recovers -> {sorted(r2) if r2 is not None else None}; gen_calls={fake.gen_calls} (1 == memoised the partial read)")
fake.close()

print("\n== 1c. connection refused (nothing listening) ==")
TG.reset()
t0 = time.monotonic()
r = TG.reader(JuniperDataClient, source="http://127.0.0.1:9", api_key=None)()
print(f"refused -> {r!r} in {time.monotonic() - t0:.2f}s; memo={dict(TG._by_source)!r}")

print("\n== 2. concurrent first requests on a cold memo (1.0 s listing) ==")
fake = FakeJD()
TG.reset()
fake.gen_mode, fake.gen_delay = "delay", 1.0
results = []
barrier = threading.Barrier(8)


def worker():
    barrier.wait()
    results.append(reader_for(fake)())


ts = [threading.Thread(target=worker) for _ in range(8)]
t0 = time.monotonic()
[t.start() for t in ts]
[t.join() for t in ts]
print(f"8 concurrent cold reads: gen_calls={fake.gen_calls}, distinct results={len({r for r in results})}, all equal={len({r for r in results}) == 1}, wall={time.monotonic() - t0:.2f}s, memo keys={list(TG._by_source)}")
fake.close()

print("\n== 2b. concurrent: one read fails, one succeeds -- is the failure ever stored? ==")
fake = FakeJD()
TG.reset()
seq = iter(["500", "ok"])
orig = fake.gen_mode


class Flip:
    pass


results2 = []


def w2(mode):
    fake.gen_mode = mode
    results2.append((mode, reader_for(fake)()))


fake.gen_mode = "500"
w2("500")
w2("ok")
print("sequence results:", [(m, sorted(r) if r else r) for m, r in results2], "memo:", {k: sorted(v) for k, v in TG._by_source.items()})
fake.close()

"""Lane B live probe against a uvicorn juniper-data server built from 3a76a4c.

Usage: live_probe.py <base-url> <storage-dir>
The API key is the scratch-only key serve.sh configured; nothing real is used.
"""

from __future__ import annotations

import statistics
import sys
import threading
import time
from pathlib import Path

import httpx

BASE = sys.argv[1]
STORE = Path(sys.argv[2])
H = {"X-API-Key": "lane-b-scratch-key"}
CAP = 8192


def create(seed: int) -> str:
    r = httpx.post(f"{BASE}/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True}, headers=H, timeout=30)
    assert r.status_code == 201, r.text
    return r.json()["dataset_id"]


def health_latency_during(fn, n_health: int = 20) -> tuple[float, list[float]]:
    """Run fn() in a thread; meanwhile time /v1/health calls. Return (fn duration, health latencies)."""
    lat: list[float] = []
    done = threading.Event()
    dur = {}

    def work():
        t0 = time.perf_counter()
        fn()
        dur["d"] = time.perf_counter() - t0
        done.set()

    th = threading.Thread(target=work)
    th.start()
    with httpx.Client(timeout=30) as c:
        while not done.is_set() and len(lat) < n_health:
            t0 = time.perf_counter()
            c.get(f"{BASE}/v1/health")
            lat.append(time.perf_counter() - t0)
    th.join()
    return dur["d"], lat


did = create(11)
etag = httpx.get(f"{BASE}/v1/datasets/{did}", headers=H).headers["etag"]
print("dataset", did, "etag", etag[:16])

# ---------------------------------------------------------------- ReDoS, live
print("\n== ReDoS: worst shapes at the cap, on the event loop (GET) and under _version_lock (PATCH)")
shapes = {
    "r2-original-45B": ", " * 22 + "x",
    "comma-space@cap": (", " * (CAP // 2))[: CAP - 1] + "x",
    "commas@cap": "," * (CAP - 1) + "x",
    "comma-spaces@cap": "," + " " * (CAP - 2) + "x",
    "comma-tabs-commas@cap": "," + "\t" * (CAP // 2) + "," * (CAP // 2 - 2) + "x",
}
with httpx.Client(timeout=60) as c:
    for name, field in shapes.items():
        assert len(field) <= CAP, (name, len(field))
        t0 = time.perf_counter()
        g = c.get(f"{BASE}/v1/datasets/{did}", headers={**H, "If-None-Match": field})
        tg = time.perf_counter() - t0
        t0 = time.perf_counter()
        g2 = c.get(f"{BASE}/v1/datasets/{did}", headers={**H, "If-Match": field})
        tg2 = time.perf_counter() - t0
        t0 = time.perf_counter()
        p = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": ["redos"]}, headers={**H, "If-Match": field})
        tp = time.perf_counter() - t0
        print(f"   {name:24s} len={len(field):5d}  GET INM -> {g.status_code} in {tg*1e3:6.1f} ms | GET IM -> {g2.status_code} in {tg2*1e3:6.1f} ms | PATCH IM -> {p.status_code} in {tp*1e3:6.1f} ms")
    # Health latency while 50 worst-case GETs run back to back.
    worst = "," * (CAP - 1) + "x"

    def burst():
        with httpx.Client(timeout=60) as cc:
            for _ in range(50):
                cc.get(f"{BASE}/v1/datasets/{did}", headers={**H, "If-None-Match": worst})

    d, lat = health_latency_during(burst, n_health=200)
    base_lat = []
    for _ in range(20):
        t0 = time.perf_counter()
        c.get(f"{BASE}/v1/health")
        base_lat.append(time.perf_counter() - t0)
    print(f"   50 worst-case GETs took {d:.2f} s; /v1/health during: median {statistics.median(lat)*1e3:.1f} ms max {max(lat)*1e3:.1f} ms (n={len(lat)}); idle median {statistics.median(base_lat)*1e3:.1f} ms")
    over = "," * CAP + "x"
    r = c.get(f"{BASE}/v1/datasets/{did}", headers={**H, "If-None-Match": over})
    r2 = c.get(f"{BASE}/v1/datasets/{did}", headers={**H, "If-Match": over})
    r3 = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": ["over"]}, headers={**H, "If-None-Match": over})
    print(f"   over-cap ({len(over)}): GET INM -> {r.status_code}, GET IM -> {r2.status_code}, PATCH INM -> {r3.status_code}")
    big = '"' + "a" * 20000 + '"'
    r4 = c.get(f"{BASE}/v1/datasets/{did}", headers={**H, "If-None-Match": big})
    print(f"   20 KB field: GET INM -> {r4.status_code}")

# ---------------------------------------------------------------- empty fields
print("\n== Empty precondition fields (C3/C4 survived: nothing pins these)")
with httpx.Client(timeout=30) as c:
    for hdr in ("If-Match", "If-None-Match"):
        g = c.get(f"{BASE}/v1/datasets/{did}", headers={**H, hdr: ""})
        a = c.get(f"{BASE}/v1/datasets/{did}/artifact", headers={**H, hdr: ""})
        p = c.patch(f"{BASE}/v1/datasets/{did}/tags", json={"add_tags": [f"empty-{hdr}"]}, headers={**H, hdr: ""})
        print(f"   {hdr}: '' -> GET {g.status_code}, artifact {a.status_code}, PATCH {p.status_code}")

# ---------------------------------------------------------------- orphan, live
print("\n== Orphaned artifact on the live LocalFS store")
orphan = create(12)
(STORE / f"{orphan}.meta.json").unlink()
with httpx.Client(timeout=30) as c:
    for hdrs in ({}, {"If-Match": "*"}, {"If-Match": '"nope"'}, {"If-None-Match": "*"}, {"If-None-Match": '"nope"'}, {"If-Match": "*", "If-None-Match": "*"}, {"If-Match": '"nope"', "If-None-Match": "*"}):
        r = c.get(f"{BASE}/v1/datasets/{orphan}/artifact", headers={**H, **hdrs})
        print(f"   {hdrs} -> {r.status_code} bytes={len(r.content)} etag={r.headers.get('etag')} cc={r.headers.get('cache-control')}")
    r = c.get(f"{BASE}/v1/datasets/{orphan}", headers=H)
    print(f"   GET metadata of the orphan -> {r.status_code}")
    r = c.patch(f"{BASE}/v1/datasets/{orphan}/tags", json={"add_tags": ["x"]}, headers={**H, "If-Match": "*"})
    print(f"   PATCH tags of the orphan (If-Match: *) -> {r.status_code}")
print("   files for the orphan now:", sorted(p.name for p in STORE.iterdir() if p.name.startswith(orphan)))

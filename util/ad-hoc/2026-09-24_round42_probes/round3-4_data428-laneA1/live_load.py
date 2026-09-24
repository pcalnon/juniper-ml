"""Lane A1: event-loop latency under concurrent worst-case-under-cap requests (tasks 4 and 7).

Goal: does one caller sending large-but-legal precondition fields (<= the 8192 cap) to the
conditional routes degrade the latency the SERVER gives other callers? The 8192 cap bounds a
single parse to a few milliseconds; this asks whether many such requests in flight serialise
behind each other on the event loop / the per-dataset lock and push the health endpoint's
response time up.

Design:
* A latency sampler in its OWN process issues GET /v1/health on one keep-alive connection
  once every 20 ms and records each round-trip. It measures the server, not the generator.
* A small number of concurrent client coroutines (default 3 processes x 8 connections) issue
  ONE scenario's request back-to-back for a fixed duration. Requests are pre-built as bytes.
* Baseline health latency (idle) is sampled first, then re-sampled during each scenario.

Usage: live_load.py <port> <dataset_id> <scenario|all>
Appends one JSON record per scenario to live_load_results.jsonl.
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import statistics
import subprocess
import sys
import time

HERE = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1"
sys.path.insert(0, HERE)
from rawhttp import KEY  # noqa: E402

PY = sys.executable
CAP = 8192
DURATION = float(os.environ.get("LANE_A1_DURATION", "10"))
PROCS = int(os.environ.get("LANE_A1_PROCS", "3"))
CONNS = int(os.environ.get("LANE_A1_CONNS", "8"))


def raw(method: str, path: str, header_lines: list[tuple[str, str]], body: bytes | None) -> bytes:
    lines = [f"{method} {path} HTTP/1.1", "Host: 127.0.0.1", f"X-API-Key: {KEY}"]
    for k, v in header_lines:
        lines.append(f"{k}: {v}")
    if body is not None:
        lines.append("Content-Type: application/json")
        lines.append(f"Content-Length: {len(body)}")
    head = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")
    return head + (body or b"")


def max_tags_then(last: str, unit: str = '"",') -> str:
    return unit * ((CAP - len(last)) // len(unit)) + last


def build_scenarios(dsid: str, etag: str) -> dict[str, bytes]:
    meta, art, tags = f"/v1/datasets/{dsid}", f"/v1/datasets/{dsid}/artifact", f"/v1/datasets/{dsid}/tags"
    inm_miss = max_tags_then('""')            # ~2730 tags, well-formed, names nothing
    im_hold = max_tags_then(etag)             # holds; current tag last of the max count
    garbage = (", " * (CAP // 2))[: CAP - 1] + "x"  # malformed, fails at the very end
    return {
        "get_meta_worstcase": raw("GET", meta, [("If-Match", im_hold), ("If-None-Match", inm_miss)], None),
        "get_meta_garbage": raw("GET", meta, [("If-None-Match", garbage)], None),
        "get_artifact_worstcase": raw("GET", art, [("If-Match", im_hold), ("If-None-Match", inm_miss)], None),
        "patch_tags_worstcase": raw("PATCH", tags, [("If-Match", im_hold), ("If-None-Match", inm_miss)], b'{"add_tags":["z"]}'),
        "patch_tags_garbage": raw("PATCH", tags, [("If-None-Match", garbage)], b'{"add_tags":["z"]}'),
        "baseline_get_meta_plain": raw("GET", meta, [], None),
    }


# ---- worker process: one scenario, back-to-back on keep-alive connections ----------------
WORKER = r'''
import asyncio, os, sys, time
PORT=int(sys.argv[1]); DUR=float(sys.argv[2]); CONNS=int(sys.argv[3])
payload=open(sys.argv[4],"rb").read()
async def one():
    n=0
    reader,writer=await asyncio.open_connection("127.0.0.1",PORT)
    end=time.perf_counter()+DUR
    try:
        while time.perf_counter()<end:
            writer.write(payload); await writer.drain()
            # read one full response (Content-Length or chunked or close); keep-alive assumed
            hdr=b""
            while b"\r\n\r\n" not in hdr:
                c=await reader.read(65536)
                if not c: return n
                hdr+=c
            head,rest=hdr.split(b"\r\n\r\n",1)
            L=[l for l in head.split(b"\r\n") if l[:15].lower()==b"content-length:"]
            if L:
                need=int(L[0].split(b":")[1]);
                while len(rest)<need:
                    c=await reader.read(65536)
                    if not c: break
                    rest+=c
            elif b"transfer-encoding: chunked" in head.lower():
                while not rest.endswith(b"0\r\n\r\n"):
                    c=await reader.read(65536)
                    if not c: break
                    rest+=c
            n+=1
    finally:
        writer.close()
    return n
async def main():
    r=await asyncio.gather(*[one() for _ in range(CONNS)])
    print(sum(r))
asyncio.run(main())
'''


async def sample_health(port: int, seconds: float, label: str) -> list[float]:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    req = raw("GET", "/v1/health", [], None)
    lat: list[float] = []
    end = time.perf_counter() + seconds
    try:
        while time.perf_counter() < end:
            t0 = time.perf_counter()
            writer.write(req)
            await writer.drain()
            hdr = b""
            while b"\r\n\r\n" not in hdr:
                c = await reader.read(65536)
                if not c:
                    return lat
                hdr += c
            head, rest = hdr.split(b"\r\n\r\n", 1)
            cl = [l for l in head.split(b"\r\n") if l[:15].lower() == b"content-length:"]
            need = int(cl[0].split(b":")[1]) if cl else 0
            while len(rest) < need:
                c = await reader.read(65536)
                if not c:
                    break
                rest += c
            lat.append((time.perf_counter() - t0) * 1000.0)
            await asyncio.sleep(0.02)
    finally:
        writer.close()
    return lat


def pct(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    return s[min(len(s) - 1, int(p / 100.0 * len(s)))]


def summ(xs: list[float]) -> dict:
    return {"n": len(xs), "min": round(min(xs), 2), "median": round(statistics.median(xs), 2), "p95": round(pct(xs, 95), 2), "p99": round(pct(xs, 99), 2), "max": round(max(xs), 2)} if xs else {"n": 0}


async def run_scenario(port: int, name: str, payload: bytes) -> dict:
    path = f"{HERE}/_scn_{name}.bin"
    with open(path, "wb") as fh:
        fh.write(payload)
    procs = [subprocess.Popen([PY, "-s", "-c", WORKER, str(port), str(DURATION), str(CONNS), path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(PROCS)]
    await asyncio.sleep(0.4)  # let the workers ramp
    health = await sample_health(port, DURATION - 1.0, name)
    counts, errs = [], []
    for pr in procs:
        out, err = pr.communicate(timeout=DURATION + 30)
        counts.append(int(out.strip()) if out.strip().isdigit() else 0)
        if err.strip():
            errs.append(err.strip()[:200])
    total = sum(counts)
    rec = {"scenario": name, "duration_s": DURATION, "procs": PROCS, "conns_per_proc": CONNS, "requests_served": total, "throughput_rps": round(total / DURATION, 1), "health_ms": summ(health), "worker_errors": errs}
    print(f"{name:26s} served={total:6d} ({rec['throughput_rps']:7.1f} rps)  health {rec['health_ms']}")
    return rec


async def main() -> None:
    port, dsid, which = int(sys.argv[1]), sys.argv[2], sys.argv[3]
    # fetch a current etag for the max-tags-that-hold field
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(raw("GET", f"/v1/datasets/{dsid}", [], None))
    await writer.drain()
    hdr = b""
    while b"\r\n\r\n" not in hdr:
        hdr += await reader.read(65536)
    etag = [l.split(b":", 1)[1].strip().decode() for l in hdr.split(b"\r\n") if l[:5].lower() == b"etag:"][0]
    writer.close()
    scenarios = build_scenarios(dsid, etag)
    idle = await sample_health(port, 3.0, "idle")
    print(f"idle health baseline: {summ(idle)}")
    names = list(scenarios) if which == "all" else [which]
    out = [{"scenario": "idle_baseline", "health_ms": summ(idle)}]
    for name in names:
        out.append(await run_scenario(port, name, scenarios[name]))
        await asyncio.sleep(1.0)  # let the server settle between scenarios
    with open(f"{HERE}/live_load_results.jsonl", "a") as fh:
        for rec in out:
            fh.write(json.dumps(rec) + "\n")
    print("appended", len(out), "records to live_load_results.jsonl")


if __name__ == "__main__":
    asyncio.run(main())

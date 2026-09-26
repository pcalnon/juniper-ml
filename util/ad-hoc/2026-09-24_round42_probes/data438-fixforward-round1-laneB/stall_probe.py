"""Lane B (r42d): measure the event-loop stall a create's save causes through record_access.

For each tree and scenario, against a live uvicorn server over LocalFS:
  1. create a small dataset D0;
  2. start a LARGE create (gaussian, unnamed or named) in a thread;
  3. wait until its save has begun (the save's temp metadata file appears -- LocalFS writes it
     first, then compresses the arrays);
  4. optionally GET /v1/datasets/D0, which schedules record_access on the event loop;
  5. probe GET /v1/health every 20 ms until the create returns, recording each latency.
At main an UNNAMED save holds no lock, so record_access runs at once. At head every save holds
the process-global _version_lock, and record_access waits for it ON THE LOOP.

Usage: python stall_probe.py <n_samples_per_class> <n_features>
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from common import S, fresh_dir, server  # noqa: E402

N_PER_CLASS = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
N_FEATURES = int(sys.argv[2]) if len(sys.argv) > 2 else 100


def one(tree: str, scenario: str, seed: int) -> dict:
    storage = fresh_dir(S / "stall" / f"{tree}-{scenario}")
    log = S / "out" / f"stall-server-{tree}-{scenario}.log"
    with server(tree, 18700, storage, log) as (base, _proc):
        with httpx.Client(base_url=base, timeout=300) as c:
            d0 = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 1}, "persist": True})
            assert d0.status_code == 201, d0.text
            d0_id = d0.json()["dataset_id"]
            body = {"generator": "gaussian", "params": {"n_classes": 2, "n_samples_per_class": N_PER_CLASS, "n_features": N_FEATURES, "seed": seed}, "persist": True}
            if scenario.startswith("named"):
                body["name"] = "big"
            result: dict = {}

            def big() -> None:
                with httpx.Client(base_url=base, timeout=600) as c2:
                    r = c2.post("/v1/datasets", json=body)
                    result["status"] = r.status_code
                    result["t_done"] = time.monotonic()

            t0 = time.monotonic()
            th = threading.Thread(target=big)
            th.start()
            t_save = None
            while th.is_alive():
                if list(storage.glob("*.meta.json.*.tmp")):
                    t_save = time.monotonic()
                    break
                time.sleep(0.002)
            if t_save is None:
                return {"tree": tree, "scenario": scenario, "error": "never saw the save start", **result}
            read_latency = None
            if scenario.endswith("+read"):
                tr = time.monotonic()
                rr = c.get(f"/v1/datasets/{d0_id}")
                read_latency = time.monotonic() - tr
                assert rr.status_code == 200, rr.text
            lat: list[tuple[float, float]] = []
            with httpx.Client(base_url=base, timeout=300) as hc:
                while th.is_alive():
                    ts = time.monotonic()
                    h = hc.get("/v1/health")
                    assert h.status_code == 200
                    lat.append((round(ts - t_save, 3), round(time.monotonic() - ts, 3)))
                    time.sleep(0.02)
            th.join()
            access = c.get(f"/v1/datasets/{d0_id}/access").json()
            return {
                "tree": tree,
                "scenario": scenario,
                "create_status": result.get("status"),
                "generate_s": round(t_save - t0, 3),
                "save_s": round(result["t_done"] - t_save, 3),
                "read_latency_s": None if read_latency is None else round(read_latency, 3),
                "health_probes": len(lat),
                "health_max_latency_s": max((x[1] for x in lat), default=None),
                "health_p50_latency_s": sorted(x[1] for x in lat)[len(lat) // 2] if lat else None,
                "first_slow_probe": next(({"sent_after_save_start_s": x[0], "latency_s": x[1]} for x in lat if x[1] > 0.25), None),
                "d0_access_count": access.get("access_count"),
            }


def main() -> None:
    rows = []
    seed = 100
    for tree in ("main", "head"):
        for scenario in ("unnamed+read", "unnamed-control", "named+read"):
            seed += 1
            row = one(tree, scenario, seed)
            print(json.dumps(row), flush=True)
            rows.append(row)
    (S / "out" / "stall_probe.json").write_text(json.dumps(rows, indent=2))
    # scratch storage is large: remove it
    import shutil

    shutil.rmtree(S / "stall", ignore_errors=True)


if __name__ == "__main__":
    main()

"""Lane B (r42d): the event-loop stall, with /v1/health probed CONCURRENTLY with the read.

For each tree: a LARGE unnamed create; once its save has begun (its temp metadata file
appears), a health prober starts (every 20 ms, each request timed), and 0.5 s later ONE read of
an unrelated small dataset D0 -- a metadata GET, or an artifact download -- is sent. That read
schedules record_access on the event loop. Reports the save's length, the read's latency and the
longest health latency, plus how long after the read the first slow probe was sent.

Usage: python stall_probe2.py <n_samples_per_class> <n_features>
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


def one(tree: str, reader: str, seed: int) -> dict:
    storage = fresh_dir(S / "stall" / f"{tree}-{reader}")
    log = S / "out" / f"stall2-server-{tree}-{reader}.log"
    with server(tree, 18720, storage, log) as (base, _proc):
        with httpx.Client(base_url=base, timeout=300) as c:
            d0 = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 1}, "persist": True})
            assert d0.status_code == 201, d0.text
            d0_id = d0.json()["dataset_id"]
            body = {"generator": "gaussian", "params": {"n_classes": 2, "n_samples_per_class": N_PER_CLASS, "n_features": N_FEATURES, "seed": seed}, "persist": True}
            done = threading.Event()
            result: dict = {}

            def big() -> None:
                with httpx.Client(base_url=base, timeout=600) as c2:
                    r = c2.post("/v1/datasets", json=body)
                    result["status"] = r.status_code
                    result["t_done"] = time.monotonic()
                done.set()

            th = threading.Thread(target=big)
            th.start()
            t_save = None
            while not done.is_set():
                if list(storage.glob("*.meta.json.*.tmp")):
                    t_save = time.monotonic()
                    break
                time.sleep(0.002)
            if t_save is None:
                th.join()
                return {"tree": tree, "reader": reader, "error": "never saw the save start"}
            lat: list[tuple[float, float]] = []

            def prober() -> None:
                with httpx.Client(base_url=base, timeout=300) as hc:
                    while not done.is_set():
                        ts = time.monotonic()
                        h = hc.get("/v1/health")
                        assert h.status_code == 200
                        lat.append((round(ts - t_save, 3), round(time.monotonic() - ts, 3)))
                        time.sleep(0.02)

            pt = threading.Thread(target=prober)
            pt.start()
            time.sleep(0.5)
            t_read = time.monotonic()
            url = f"/v1/datasets/{d0_id}" if reader == "metadata" else f"/v1/datasets/{d0_id}/artifact"
            rr = c.get(url)
            read_latency = time.monotonic() - t_read
            assert rr.status_code == 200, rr.text
            th.join()
            pt.join()
            slow = [x for x in lat if x[1] > 0.5]
            return {
                "tree": tree,
                "reader": reader,
                "create_status": result.get("status"),
                "save_s": round(result["t_done"] - t_save, 3),
                "read_sent_after_save_start_s": round(t_read - t_save, 3),
                "read_latency_s": round(read_latency, 3),
                "health_probes": len(lat),
                "health_max_latency_s": max((x[1] for x in lat), default=None),
                "health_probes_over_0.5s": len(slow),
                "first_slow_probe": ({"sent_after_save_start_s": slow[0][0], "latency_s": slow[0][1]} if slow else None),
            }


def main() -> None:
    rows = []
    seed = 200
    for tree in ("main", "head"):
        for reader in ("metadata", "artifact"):
            seed += 1
            row = one(tree, reader, seed)
            print(json.dumps(row), flush=True)
            rows.append(row)
    (S / "out" / "stall_probe2.json").write_text(json.dumps(rows, indent=2))
    import shutil

    shutil.rmtree(S / "stall", ignore_errors=True)


if __name__ == "__main__":
    main()

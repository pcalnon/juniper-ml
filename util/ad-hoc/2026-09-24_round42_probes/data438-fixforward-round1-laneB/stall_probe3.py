"""Lane B (r42d): two large unnamed creates back to back, and one read -- does the loop wait for BOTH saves?

Create A starts; create B starts 1 s later, so B's save_versioned is queued on _version_lock while
A saves. A read of D0 is sent once B is queued. _version_lock is not FIFO, so the loop's
record_access can lose the lock to B and wait out B's save too. Health is probed throughout.
Usage: python stall_probe3.py <n_samples_per_class> <n_features>
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


def one(tree: str) -> dict:
    storage = fresh_dir(S / "stall" / f"{tree}-two")
    log = S / "out" / f"stall3-server-{tree}.log"
    with server(tree, 18740, storage, log) as (base, _proc):
        with httpx.Client(base_url=base, timeout=300) as c:
            d0 = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 1}, "persist": True}).json()["dataset_id"]
            done: dict[str, float] = {}
            t_start = time.monotonic()

            def big(label: str, seed: int) -> None:
                with httpx.Client(base_url=base, timeout=600) as c2:
                    r = c2.post("/v1/datasets", json={"generator": "gaussian", "params": {"n_classes": 2, "n_samples_per_class": N_PER_CLASS, "n_features": N_FEATURES, "seed": seed}, "persist": True})
                    assert r.status_code == 201, r.text
                    done[label] = round(time.monotonic() - t_start, 3)

            ta = threading.Thread(target=big, args=("A", 301))
            ta.start()
            time.sleep(1.0)
            tb = threading.Thread(target=big, args=("B", 302))
            tb.start()
            # wait until A is saving, then give B time to finish generating and queue on the lock
            while not list(storage.glob("*.meta.json.*.tmp")):
                time.sleep(0.002)
            t_a_save = round(time.monotonic() - t_start, 3)
            time.sleep(3.0)
            lat: list[tuple[float, float]] = []
            stop = threading.Event()

            def prober() -> None:
                with httpx.Client(base_url=base, timeout=300) as hc:
                    while not stop.is_set():
                        ts = time.monotonic()
                        hc.get("/v1/health")
                        lat.append((round(ts - t_start, 3), round(time.monotonic() - ts, 3)))
                        time.sleep(0.02)

            pt = threading.Thread(target=prober)
            pt.start()
            time.sleep(0.2)
            t_read = time.monotonic()
            c.get(f"/v1/datasets/{d0}")
            read_latency = round(time.monotonic() - t_read, 3)
            ta.join()
            tb.join()
            stop.set()
            pt.join()
            return {
                "tree": tree,
                "A_save_started_s": t_a_save,
                "read_sent_s": round(t_read - t_start, 3),
                "read_latency_s": read_latency,
                "A_done_s": done.get("A"),
                "B_done_s": done.get("B"),
                "health_max_latency_s": max((x[1] for x in lat), default=None),
            }


def main() -> None:
    rows = [one("main"), one("head")]
    for r in rows:
        print(json.dumps(r), flush=True)
    (S / "out" / "stall_probe3.json").write_text(json.dumps(rows, indent=2))
    import shutil

    shutil.rmtree(S / "stall", ignore_errors=True)


if __name__ == "__main__":
    main()

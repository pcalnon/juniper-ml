"""Lane B (r42d): false contention across processes -- another process's lock on an UNRELATED id.

A second process holds the cross-process lock for an absent id H for 5 s. At head, H is chosen to
share a stripe with dataset T; at main each id has its own lock file. While H is held:
  1. DELETE T (a different dataset) -- its thread takes _version_lock, then waits on the flock;
  2. 0.3 s later, GET R (a third dataset, on another stripe) -- whose record_access runs on the loop;
  3. /v1/health is probed throughout.
Usage: python xproc_stall_probe.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from common import S, TREES, fresh_dir, server  # noqa: E402

HOLD_S = 5.0


def stripe(i: str) -> int:
    return int(hashlib.sha256(i.encode()).hexdigest(), 16) % 16


def one(tree: str) -> dict:
    storage = fresh_dir(S / "xstall" / tree / "storage")
    log = S / "out" / f"xstall-server-{tree}.log"
    with server(tree, 18760, storage, log) as (base, _proc):
        with httpx.Client(base_url=base, timeout=120) as c:
            ids = [c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": s}, "persist": True}).json()["dataset_id"] for s in range(11, 31)]
            target = ids[0]
            reader = next(i for i in ids[1:] if stripe(i) != stripe(target))
            holder = next(f"holder-{n:05d}" for n in range(100000) if stripe(f"holder-{n:05d}") == stripe(target))
            ready = S / "xstall" / tree / "ready"
            hold = subprocess.Popen(["bash", str(S / "scripts" / "run_in_tree.bash"), str(TREES[tree]), str(S / "scripts" / "stripe_holder.py"), str(storage), holder, str(HOLD_S), str(ready)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            t0 = time.monotonic()
            while not ready.exists():
                if hold.poll() is not None or time.monotonic() - t0 > 60:
                    raise SystemExit(f"holder failed: {hold.communicate()}")
                time.sleep(0.01)
            t_held = time.monotonic()
            res: dict = {}

            def delete() -> None:
                with httpx.Client(base_url=base, timeout=120) as c2:
                    ts = time.monotonic()
                    r = c2.delete(f"/v1/datasets/{target}")
                    res["delete_status"] = r.status_code
                    res["delete_latency_s"] = round(time.monotonic() - ts, 3)

            lat: list[float] = []
            stop = threading.Event()

            def prober() -> None:
                with httpx.Client(base_url=base, timeout=120) as hc:
                    while not stop.is_set():
                        ts = time.monotonic()
                        hc.get("/v1/health")
                        lat.append(round(time.monotonic() - ts, 3))
                        time.sleep(0.02)

            td = threading.Thread(target=delete)
            tp = threading.Thread(target=prober)
            tp.start()
            td.start()
            time.sleep(0.3)
            ts = time.monotonic()
            rr = c.get(f"/v1/datasets/{reader}")
            read_latency = round(time.monotonic() - ts, 3)
            td.join()
            hold.wait(30)
            stop.set()
            tp.join()
            return {
                "tree": tree,
                "holder_lock_file": ready.read_text().split("/")[-1],
                "target_stripe": stripe(target),
                "reader_stripe": stripe(reader),
                "delete_sent_after_hold_s": round(ts - t_held - 0.3, 3),
                **res,
                "read_status": rr.status_code,
                "read_latency_s": read_latency,
                "health_max_latency_s": max(lat) if lat else None,
            }


def main() -> None:
    rows = [one("main"), one("head")]
    for r in rows:
        print(json.dumps(r), flush=True)
    (S / "out" / "xproc_stall_probe.json").write_text(json.dumps(rows, indent=2))
    import shutil

    shutil.rmtree(S / "xstall", ignore_errors=True)


if __name__ == "__main__":
    main()

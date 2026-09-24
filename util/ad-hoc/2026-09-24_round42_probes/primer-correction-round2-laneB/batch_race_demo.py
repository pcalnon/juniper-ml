#!/usr/bin/env python3
"""Are ALL of juniper-data's tag updates atomic, as Appendix E.2 says #263 made them? Tests the batch route.

Scratch instrument for round-2 Lane B. Usage:
    python batch_race_demo.py <juniper-data tree> <scratch store dir> [rounds]

Bare FastAPI app with ONLY the datasets router (no settings, no auth, no secrets) over a LocalFS store.
Per round, on a fresh dataset:
  A. 12 threads, each PATCH /v1/datasets/batch-tags adding one distinct tag   -> survivors /12
  B. 12 threads, each PATCH /v1/datasets/{id}/tags adding one distinct tag    -> survivors /12 (control)
  C. 6 single-route PATCHes carrying If-Match (the conditional path) interleaved with 6 batch PATCHes
     -> how many conditional writes that answered 200 were then erased by a batch writer
  D. GET-undo: batch PATCH interleaved with GETs of the same dataset (record_access fires per GET)
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path


def main() -> int:
    root, store_dir = sys.argv[1], sys.argv[2]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    sys.path.insert(0, root)
    import juniper_data
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from juniper_data.api.routes import datasets
    from juniper_data.storage.local_fs import LocalFSDatasetStore

    print("juniper_data imported from:", Path(juniper_data.__file__).parent)
    datasets.set_store(LocalFSDatasetStore(Path(store_dir)))
    app = FastAPI()
    app.include_router(datasets.router, prefix="/v1")
    c = TestClient(app)

    def fresh(seed: int) -> str:
        r = c.post("/v1/datasets", json={"generator": "spiral", "params": {"seed": seed}, "tags": ["baseline"]})
        assert r.status_code in (200, 201), r.text[:200]
        return r.json()["dataset_id"]

    def run(fns) -> None:
        barrier = threading.Barrier(len(fns))

        def wrap(f):
            barrier.wait()
            f()

        ts = [threading.Thread(target=wrap, args=(f,)) for f in fns]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

    tot = {"A": 0, "B": 0, "C_ok": 0, "C_lost": 0, "D_lost": 0}
    for r in range(rounds):
        # A: batch route only
        d = fresh(1000 + r)
        run([lambda i=i: c.patch("/v1/datasets/batch-tags", json={"dataset_ids": [d], "add_tags": [f"a{i:02d}"], "remove_tags": []}) for i in range(12)])
        tags = c.get(f"/v1/datasets/{d}").json()["tags"]
        a = sum(t.startswith("a") for t in tags)
        tot["A"] += a
        # B: single route only (control)
        d = fresh(2000 + r)
        run([lambda i=i: c.patch(f"/v1/datasets/{d}/tags", json={"add_tags": [f"s{i:02d}"]}) for i in range(12)])
        tags = c.get(f"/v1/datasets/{d}").json()["tags"]
        b = sum(t.startswith("s") for t in tags)
        tot["B"] += b
        # C: ONE conditional single PATCH (If-Match read before the race) vs 11 batch writers
        d = fresh(3000 + r)
        ok: list[str] = []
        etag = c.get(f"/v1/datasets/{d}").headers.get("etag")

        def cond(d=d, etag=etag) -> None:
            resp = c.patch(f"/v1/datasets/{d}/tags", json={"add_tags": ["cond"]}, headers={"If-Match": etag} if etag else {})
            if resp.status_code == 200:
                ok.append("cond")

        run([cond] + [lambda i=i: c.patch("/v1/datasets/batch-tags", json={"dataset_ids": [d], "add_tags": [f"x{i:02d}"], "remove_tags": []}) for i in range(11)])
        tags = set(c.get(f"/v1/datasets/{d}").json()["tags"])
        lost = [t for t in ok if t not in tags]
        tot["C_ok"] += len(ok)
        tot["C_lost"] += len(lost)
        # D: batch edit racing plain GETs (record_access rewrites the whole document)
        d = fresh(4000 + r)
        run([lambda: c.patch("/v1/datasets/batch-tags", json={"dataset_ids": [d], "add_tags": ["dtag"], "remove_tags": []})] + [lambda: c.get(f"/v1/datasets/{d}") for _ in range(11)])
        # record_access is scheduled with call_soon; give it a moment to run, then read the document
        import time

        time.sleep(0.5)
        tags = c.get(f"/v1/datasets/{d}").json()["tags"]
        tot["D_lost"] += int("dtag" not in tags)
        print(f"round {r}: A batch {a}/12 | B single {b}/12 | C conditional 200s {len(ok)}, erased afterwards {len(lost)} | D batch edit undone by a GET: {'dtag' not in tags}")
    print("TOTALS", tot, f"over {rounds} rounds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

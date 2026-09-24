#!/usr/bin/env python3
"""Does juniper-data's tag PATCH lose an update WITHOUT If-Match? Tests v2's "until juniper-data#428" claim.

Scratch instrument for round-2 Lane B. Usage:
    python lost_update_demo.py <juniper-data tree> <scratch store dir>

Builds a bare FastAPI app holding ONLY the datasets router (no settings, no auth middleware, no
secrets read) over a LocalFS store in <scratch store dir>, then:

  1. SEQUENTIAL: the II.11 headline interleaving translated to juniper-data's add/remove body:
     A GET, B GET, A PATCH add ["approved"], B PATCH add ["rejected"] -- no precondition -- then GET.
     The toy's claim is that without If-Match "B's write ... silently erases A's change".
  2. CONCURRENT, threads: 12 threads each add one distinct tag through the route.
  3. CONCURRENT, processes: 12 processes each call store.update_tags(add=[pN]) on the same LocalFS dir.
Prints the surviving tags; a lost update shows as a missing tag.
"""
from __future__ import annotations

import multiprocessing as mp
import sys
import threading
from pathlib import Path


def _proc_add(root: str, store_dir: str, dataset_id: str, tag: str, barrier) -> None:
    sys.path.insert(0, root)
    from juniper_data.storage.local_fs import LocalFSDatasetStore

    store = LocalFSDatasetStore(Path(store_dir))
    barrier.wait()
    if hasattr(store, "update_tags"):
        store.update_tags(dataset_id, [tag], [])
    else:
        # Before juniper-data#263 there was no update_tags: replay the route's own two-hop
        # read-modify-write (routes/datasets.py:785-794 at 9e8b7ef4) verbatim.
        meta = store.get_meta(dataset_id)
        current = set(meta.tags)
        current.update([tag])
        meta.tags = sorted(current)
        store.update_meta(dataset_id, meta)


def main() -> int:
    root, store_dir = sys.argv[1], sys.argv[2]
    sys.path.insert(0, root)
    import juniper_data
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from juniper_data.api.routes import datasets
    from juniper_data.storage.local_fs import LocalFSDatasetStore

    print("juniper_data imported from:", Path(juniper_data.__file__).parent)
    store = LocalFSDatasetStore(Path(store_dir))
    datasets.set_store(store)
    app = FastAPI()
    app.include_router(datasets.router, prefix="/v1")
    c = TestClient(app)

    r = c.post("/v1/datasets", json={"generator": "spiral", "params": {}, "tags": ["baseline"]})
    assert r.status_code in (200, 201), (r.status_code, r.text[:300])
    dsid = r.json()["dataset_id"]
    print("created", dsid, r.status_code)

    # 1. sequential headline interleaving, no precondition
    a = c.get(f"/v1/datasets/{dsid}")
    b = c.get(f"/v1/datasets/{dsid}")
    wa = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["approved"]})
    wb = c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["rejected"]})
    final = c.get(f"/v1/datasets/{dsid}").json()["tags"]
    print(f"1 SEQUENTIAL: A read {a.json()['tags']} B read {b.json()['tags']}; A PATCH {wa.status_code}, B PATCH {wb.status_code}; final tags {final}")
    print("  A's change survived:", "approved" in final)

    # 2. concurrent threads through the route
    barrier_t = threading.Barrier(12)

    def t_add(i: int) -> None:
        barrier_t.wait()
        c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": [f"t{i:02d}"]})

    ts = [threading.Thread(target=t_add, args=(i,)) for i in range(12)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    tags = c.get(f"/v1/datasets/{dsid}").json()["tags"]
    got = sorted(t for t in tags if t.startswith("t"))
    print(f"2 THREADS: {len(got)}/12 thread tags survived")

    # 3. concurrent processes on the same LocalFS directory
    ctx = mp.get_context("spawn")
    barrier_p = ctx.Barrier(12)
    ps = [ctx.Process(target=_proc_add, args=(root, store_dir, dsid, f"p{i:02d}", barrier_p)) for i in range(12)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    tags = LocalFSDatasetStore(Path(store_dir)).get_meta(dsid).tags
    got = sorted(t for t in tags if t.startswith("p"))
    print(f"3 PROCESSES: {len(got)}/12 process tags survived; exit codes {[p.exitcode for p in ps]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

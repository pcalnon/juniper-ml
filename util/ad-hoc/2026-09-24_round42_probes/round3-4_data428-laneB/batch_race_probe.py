"""Lane B: does ``PATCH /batch-tags`` (no lock) defeat the conditional PATCH's documented guarantee?

Docs at 3a76a4c: "The check runs against the current metadata inside the same lock as the write,
so it cannot pass and then lose the race" (docs/api/JUNIPER_DATA_API.md, PATCH /v1/datasets/{id}/tags).

Deterministic interleaving on the REAL LocalFS store and the REAL routes. The only instrumentation
widens an existing window: ``update_meta`` sleeps 0.3 s before doing its real work, so the
conditional PATCH sits between its (passed) precondition and its write long enough for a second
request to land. ``batch_update_tags`` in the route takes neither ``_version_lock`` nor the flock,
so it is not held back. A control run uses a second SINGLE-dataset PATCH instead of batch-tags;
that one takes the lock, so it must wait and then get its turn.

Also: a DELETE landing in the same window -- does the conditional PATCH answer 200 with an ETag
for a dataset that no longer exists?
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from fastapi.testclient import TestClient

from juniper_data.api.app import create_app
from juniper_data.api.routes import datasets
from juniper_data.api.settings import Settings
from juniper_data.storage.local_fs import LocalFSDatasetStore

root = Path(sys.argv[1])


def fresh(sub: str):
    storage = root / sub
    storage.mkdir(parents=True, exist_ok=True)
    store = LocalFSDatasetStore(storage)
    app = create_app(settings=Settings(storage_path=str(storage)))
    datasets.set_store(store)
    client = TestClient(app)
    r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 7}, "persist": True})
    assert r.status_code == 201, r.text
    return client, store, r.json()["dataset_id"]


def slow_writes(store: LocalFSDatasetStore, delay: float, only_first: bool = True) -> None:
    real = store.update_meta
    state = {"n": 0}

    def slowed(dataset_id, meta):
        state["n"] += 1
        if not only_first or state["n"] == 1:
            time.sleep(delay)
        return real(dataset_id, meta)

    store.update_meta = slowed  # type: ignore[method-assign]


def scenario(name: str, second) -> None:
    client, store, did = fresh(name)
    etag = client.get(f"/v1/datasets/{did}").headers["etag"]
    slow_writes(store, 0.3)
    out: dict = {}

    def conditional():
        r = client.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["conditional"]}, headers={"If-Match": etag})
        out["cond"] = (r.status_code, r.headers.get("etag"), r.json().get("tags") if r.status_code == 200 else r.text[:80])

    t = threading.Thread(target=conditional)
    t.start()
    time.sleep(0.1)  # the conditional PATCH has passed its precondition and is inside update_meta's delay
    t0 = time.perf_counter()
    out["second"] = second(client, did)
    out["second_latency_s"] = round(time.perf_counter() - t0, 3)
    t.join()
    final = client.get(f"/v1/datasets/{did}")
    out["final_status"] = final.status_code
    out["final_tags"] = final.json().get("tags") if final.status_code == 200 else None
    out["final_etag"] = final.headers.get("etag")
    print(f"--- {name}")
    for k, v in out.items():
        print(f"    {k}: {v}")


def batch(client, did):
    r = client.patch("/v1/datasets/batch-tags", json={"dataset_ids": [did], "add_tags": ["batch"]})
    return (r.status_code, r.json())


def single(client, did):
    r = client.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["single"]})
    return (r.status_code, r.json().get("tags"))


def delete(client, did):
    r = client.delete(f"/v1/datasets/{did}")
    return r.status_code


scenario("control-single-patch", single)
scenario("batch-tags-in-the-window", batch)
scenario("delete-in-the-window", delete)

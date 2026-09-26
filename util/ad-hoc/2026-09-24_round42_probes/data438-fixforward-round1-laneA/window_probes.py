#!/usr/bin/env python3
"""Lane A: the qualified and disclosed windows the changed docs describe, forced.

P1  N1: a removal landing between LocalFS update_meta's existence check and its rename -> 200 + ETag,
    and the metadata is resurrected without its artifact. Control: the same removal one step earlier
    (after the precondition, before update_meta) -> 404.
P2  L5, as widened here: an UNNAMED create's slow save holds _version_lock; a GET of another dataset
    schedules record_access on the event loop; how long does an unrelated GET /v1/datasets then take?
P3  L7: two store instances stand in for two workers; A's metadata snapshot shows X expired; B deletes
    X and re-creates it with no TTL; A's delete_expired inside the snapshot TTL deletes the new X.
    Control: the same deletion and re-creation through A itself.
"""

import datetime as dt
import json
import os
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

import juniper_data

assert Path(juniper_data.__file__).resolve().is_relative_to(Path(os.environ["EXPECTED_TREE"]).resolve())
from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.core.models import DatasetMeta  # noqa: E402
from juniper_data.storage import local_fs  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

WORK = Path(tempfile.mkdtemp(prefix="window-probes-"))


def meta(dataset_id, **kw):
    return DatasetMeta(dataset_id=dataset_id, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=dt.datetime(2026, 9, 1, tzinfo=dt.UTC), checksum="ab" * 32, **kw)


ARR = {"X_train": np.zeros((2, 2), dtype=np.float32)}

# ------------------------------------------------------------------------------ P1
print("== P1: removal inside update_meta's own window vs. one step earlier")
for where in ("inside update_meta (after its exists check)", "before update_meta (after the precondition)"):
    store = LocalFSDatasetStore(WORK / f"p1-{len(where)}")
    app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
    datasets.set_store(store)
    client = TestClient(app, raise_server_exceptions=False)
    store.save("victim", meta("victim", tags=["t0"]), ARR)
    etag = client.patch("/v1/datasets/victim/tags", json={"add_tags": ["t1"]}).headers["etag"]

    def remove_by_hand():
        (store.base_path / "victim.meta.json").unlink()
        (store.base_path / "victim.npz").unlink()

    real_dumps = local_fs.json.dumps
    real_update_meta = store.update_meta
    armed = {"on": True}
    if where.startswith("inside"):

        def dumps_then_remove(*a, **k):
            if armed["on"]:
                armed["on"] = False
                remove_by_hand()
            return real_dumps(*a, **k)

        local_fs.json.dumps = dumps_then_remove
    else:

        def remove_then_update_meta(dataset_id, m):
            if armed["on"]:
                armed["on"] = False
                remove_by_hand()
            return real_update_meta(dataset_id, m)

        store.update_meta = remove_then_update_meta
    try:
        r = client.patch("/v1/datasets/victim/tags", json={"add_tags": ["t2"]}, headers={"If-Match": etag})
    finally:
        local_fs.json.dumps = real_dumps
        store.update_meta = real_update_meta
    print(f"  {where}: PATCH {r.status_code} etag={'yes' if r.headers.get('etag') else 'no'}; meta file now: {(store.base_path / 'victim.meta.json').exists()}; npz now: {(store.base_path / 'victim.npz').exists()}")

# ------------------------------------------------------------------------------ P2
print("\n== P2: an unnamed create's slow save vs. an unrelated read on the event loop")
store = LocalFSDatasetStore(WORK / "p2")
store.save("other", meta("other"), ARR)
app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
SAVE_SECONDS = 1.5
with TestClient(app, raise_server_exceptions=False) as client:
    datasets.set_store(store)
    client.get("/v1/datasets")  # warm
    entered = threading.Event()
    real_save = store.save

    def slow_save(dataset_id, m, arrays):
        entered.set()
        time.sleep(SAVE_SECONDS)
        return real_save(dataset_id, m, arrays)

    store.save = slow_save
    out = {}
    t = threading.Thread(target=lambda: out.__setitem__("create", client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 31}, "persist": True})))
    t.start()
    assert entered.wait(20)
    t0 = time.monotonic()
    g = client.get("/v1/datasets/other")  # schedules record_access on the loop
    t1 = time.monotonic()
    lst = client.get("/v1/datasets")
    t2 = time.monotonic()
    t.join(20)
    store.save = real_save
    print(f"  GET /other: {g.status_code} in {t1 - t0:.3f}s; then GET /v1/datasets: {lst.status_code} in {t2 - t1:.3f}s (save held {SAVE_SECONDS}s); create: {out['create'].status_code}")

# ------------------------------------------------------------------------------ P3
print("\n== P3: expired-dataset cleanup decides on a snapshot")
for who in ("another store instance (a second worker)", "the same store instance"):
    root = WORK / f"p3-{len(who)}"
    a = LocalFSDatasetStore(root)
    b = a if who.startswith("the same") else LocalFSDatasetStore(root)
    past = dt.datetime(2026, 9, 1, tzinfo=dt.UTC)
    a.save("x", meta("x", ttl_seconds=60, expires_at=past), ARR)
    snap = a._list_all_metadata_cached()
    b.delete_under_lock("x")
    b.save("x", meta("x", tags=["recreated-no-ttl"]), ARR)
    deleted = a.delete_expired()
    print(f"  re-created through {who}: A.delete_expired() -> {deleted}; the re-created x still exists: {a.get_meta('x') is not None}")

import shutil  # noqa: E402

shutil.rmtree(WORK, ignore_errors=True)

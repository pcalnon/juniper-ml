#!/usr/bin/env python3
"""Lane A extra probes.

B  (base's per-id lock) a dangling symlink planted at <id>.meta.json.lock, then delete_under_lock:
   outside file created? its mode? dataset deleted?  At head the same planting is at the STRIPE.
C  a CORRUPT metadata document (not a containment fault): status per route -- is it still the caller's 400?
E  how long LocalFS.save -- which a create now runs under the process-global _version_lock -- takes for a
   large artifact (random float32, as incompressible as real market data gets).
"""

import datetime as dt
import os
import stat
import tempfile
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
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

WORK = Path(tempfile.mkdtemp(prefix="extra-probes-"))
HEAD = hasattr(LocalFSDatasetStore, "_open_lock_stripe")


def meta(dataset_id, **kw):
    return DatasetMeta(dataset_id=dataset_id, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=dt.datetime(2026, 9, 1, tzinfo=dt.UTC), checksum="ab" * 32, **kw)


ARR = {"X_train": np.zeros((2, 2), dtype=np.float32)}

print("== B: a dangling symlink planted at the lock file, then delete_under_lock")
store = LocalFSDatasetStore(WORK / "b" / "storage")
store.save("guarded", meta("guarded"), ARR)
outside = WORK / "b" / "outside" / "planted.lock"
outside.parent.mkdir(parents=True)
lock_path = store._lock_path("guarded")
lock_path.parent.mkdir(exist_ok=True)
lock_path.unlink(missing_ok=True)
lock_path.symlink_to(outside)
print(f"  lock path planted: {lock_path.relative_to(store.base_path)}")
try:
    result = store.delete_under_lock("guarded")
    print(f"  delete_under_lock returned {result}")
except OSError as exc:
    print(f"  delete_under_lock raised {type(exc).__name__} errno={exc.errno}")
print(f"  outside file created: {outside.exists()}" + (f", mode {oct(stat.S_IMODE(outside.stat().st_mode))}" if outside.exists() else ""))
print(f"  dataset still stored: {store.get_meta('guarded') is not None}")

print("\n== C: a corrupt metadata document (garbage JSON), not a containment fault")
store = LocalFSDatasetStore(WORK / "c" / "storage")
app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
datasets.set_store(store)
client = TestClient(app, raise_server_exceptions=False)
r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 41}, "persist": True})
dataset_id = r.json()["dataset_id"]
(store.base_path / f"{dataset_id}.meta.json").write_text("{not json", encoding="utf-8")
for label, call in (
    ("GET /{id}", lambda: client.get(f"/v1/datasets/{dataset_id}")),
    ("GET /filter", lambda: client.get("/v1/datasets/filter")),
    ("GET /stats", lambda: client.get("/v1/datasets/stats")),
    ("PATCH /{id}/tags", lambda: client.patch(f"/v1/datasets/{dataset_id}/tags", json={"add_tags": ["x"]})),
    ("GET /{id}/artifact", lambda: client.get(f"/v1/datasets/{dataset_id}/artifact")),
):
    resp = call()
    print(f"  {label:18} {resp.status_code} {resp.text[:70]}")

print("\n== E: LocalFS.save time for a large artifact (the create now holds _version_lock throughout)")
store = LocalFSDatasetStore(WORK / "e" / "storage")
rng = np.random.default_rng(0)
for mib in (16, 64):
    n = mib * 1024 * 1024 // 4
    arrays = {"X_train": rng.standard_normal(n, dtype=np.float32).reshape(-1, 16)}
    t0 = time.monotonic()
    store.save(f"big-{mib}", meta(f"big-{mib}"), arrays)
    elapsed = time.monotonic() - t0
    size = (store.base_path / f"big-{mib}.npz").stat().st_size
    print(f"  {mib} MiB of float32: save {elapsed:.2f} s, npz {size / 1048576:.1f} MiB on disk")
    store.delete(f"big-{mib}")

import shutil  # noqa: E402

shutil.rmtree(WORK, ignore_errors=True)

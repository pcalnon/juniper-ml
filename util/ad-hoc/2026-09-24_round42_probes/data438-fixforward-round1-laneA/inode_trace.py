#!/usr/bin/env python3
"""Lane A: run the three delete paths through the real routes, bracketed by marker syscalls, for strace.

Run under ``strace -f -e trace=%file,%desc``; inode_trace_parse.py then lists every syscall between
the markers that could allocate an inode (open/openat/openat2 with O_CREAT, creat, mkdir, mknod,
link, symlink). A delete path that issues none cannot need a free inode.
"""

import datetime as dt
import os
import sys
import tempfile
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

work = Path(tempfile.mkdtemp(prefix="inode-trace-"))
store = LocalFSDatasetStore(work / "storage")
app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
datasets.set_store(store)
client = TestClient(app, raise_server_exceptions=False)
expired = dt.datetime(2026, 9, 1, tzinfo=dt.UTC)
# warm every code path once on throwaway datasets, so lazy imports happen before the markers
for name in ("warm-1", "warm-2", "warm-3"):
    meta = DatasetMeta(dataset_id=name, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=expired, checksum="ab" * 32, expires_at=expired if name == "warm-3" else None)
    store.save(name, meta, {"X_train": np.zeros((2, 2), dtype=np.float32)})
client.delete("/v1/datasets/warm-1")
client.post("/v1/datasets/batch-delete", json={"dataset_ids": ["warm-2"]})
client.post("/v1/datasets/cleanup-expired")
# the datasets the marked phase deletes, created AFTER the warm-up so cleanup has one to delete
for name in ("doomed-delete", "doomed-batch", "doomed-expired"):
    meta = DatasetMeta(dataset_id=name, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=expired, checksum="ab" * 32, expires_at=expired if name == "doomed-expired" else None)
    store.save(name, meta, {"X_train": np.zeros((2, 2), dtype=np.float32)})
before = sorted(p.name for p in store.base_path.iterdir())
os.path.exists("/LANE_A_MARKER_BEGIN")
r1 = client.delete("/v1/datasets/doomed-delete")
r2 = client.post("/v1/datasets/batch-delete", json={"dataset_ids": ["doomed-batch"]})
r3 = client.post("/v1/datasets/cleanup-expired")
os.path.exists("/LANE_A_MARKER_END")
after = sorted(p.name for p in store.base_path.iterdir())
print("storage dir:", work / "storage", file=sys.stderr)
print("responses:", r1.status_code, r2.status_code, r2.json(), r3.status_code, r3.json(), file=sys.stderr)
print("top-level before:", before, file=sys.stderr)
print("top-level after: ", after, file=sys.stderr)

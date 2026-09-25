#!/usr/bin/env python3
"""Lane A: a dataset whose .meta.json is a symlink out of the storage root; download its artifact 3 times.

Prints the status of each download and counts log records at WARNING+ whose formatted text
(traceback included) carries the dataset id, split by logger. Imports nothing a release may lack.
"""

import logging
import os
import tempfile
from pathlib import Path

import juniper_data

assert Path(juniper_data.__file__).resolve().is_relative_to(Path(os.environ["EXPECTED_TREE"]).resolve())
from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

records = []


class Keep(logging.Handler):
    def emit(self, record):
        records.append(record)


work = Path(tempfile.mkdtemp(prefix="symlink-meta-"))
store = LocalFSDatasetStore(work / "storage")
app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
datasets.set_store(store)
with TestClient(app, raise_server_exceptions=False) as client:
    # attached AFTER the lifespan ran: the app's configure_logging replaces the root handlers
    root = logging.getLogger()
    root.addHandler(Keep(level=logging.DEBUG))
    root.setLevel(logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.DEBUG)
    datasets.set_store(store)
    r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 21}, "persist": True})
    dataset_id = r.json()["dataset_id"]
    meta_path = store.base_path / f"{dataset_id}.meta.json"
    outside = work / "outside"
    outside.mkdir()
    (outside / meta_path.name).write_bytes(meta_path.read_bytes())
    meta_path.unlink()
    meta_path.symlink_to(outside / meta_path.name)
    records.clear()
    statuses = [client.get(f"/v1/datasets/{dataset_id}/artifact").status_code for _ in range(3)]
    statuses.append(client.get(f"/v1/datasets/{dataset_id}/artifact", headers={"If-None-Match": "*"}).status_code)
fmt = logging.Formatter("%(message)s")
naming = [rec for rec in records if rec.levelno >= logging.WARNING and dataset_id in fmt.format(rec)]
print("statuses (3 plain downloads, then If-None-Match: *):", statuses)
print("WARNING+ records carrying the id:", len(naming), sorted({f"{rec.name}:{rec.levelname}" for rec in naming}))
print("asyncio 'Exception in callback' records:", sum(1 for rec in records if rec.name == "asyncio" and "Exception in callback" in rec.getMessage()))

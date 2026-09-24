"""Lane B: a VALID dataset whose .meta.json is a symlink out of the storage root, whose .npz is a
normal file. What does GET /artifact answer, and what is logged? Portable across trees (no import
of InvalidDatasetIdError)."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from juniper_data.api.app import create_app
from juniper_data.api.routes import datasets
from juniper_data.api.settings import Settings
from juniper_data.storage.local_fs import LocalFSDatasetStore

root = Path(sys.argv[1])
storage = root / "store"
outside = root / "outside"
storage.mkdir(parents=True, exist_ok=True)
outside.mkdir(parents=True, exist_ok=True)
(outside / "elsewhere.meta.json").write_text('{"not": "metadata"}')
store = LocalFSDatasetStore(storage)
app = create_app(settings=Settings(storage_path=str(storage)))
datasets.set_store(store)
client = TestClient(app)

valid = "spiral-3.0.0-symlinked0000000"
np.savez(storage / f"{valid}.npz", X_train=np.zeros((2, 2), dtype=np.float32))
link = storage / f"{valid}.meta.json"
if not link.exists():
    os.symlink(outside / "elsewhere.meta.json", link)

records: list[logging.LogRecord] = []


class Grab(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        records.append(record)


logging.getLogger("juniper_data").addHandler(Grab(level=logging.DEBUG))
logging.getLogger("juniper_data").setLevel(logging.DEBUG)
for hdrs in ({}, {"If-None-Match": "*"}):
    records.clear()
    r = client.get(f"/v1/datasets/{valid}/artifact", headers=hdrs)
    loud = [f"{rec.levelname}:{rec.getMessage()[:90]}" for rec in records if rec.levelno >= logging.DEBUG and rec.name.startswith("juniper_data.api")]
    print(f"GET artifact {hdrs} -> {r.status_code} bytes={len(r.content)} etag={r.headers.get('etag')} logs={loud}")

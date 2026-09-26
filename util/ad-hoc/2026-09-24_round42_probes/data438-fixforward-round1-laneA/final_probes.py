#!/usr/bin/env python3
"""Lane A final probes.

PA  the PATCH route's OpenAPI description carries the new scope sentences.
PC  one metadata file that leads out of the root: what named creates, /versions and /latest answer.
PD  cross-process stripe sharing: this process holds a slow create of A (the file lock held for the
    whole save); a CHILD process runs record_access on B, a different EXISTING dataset -- on the same
    stripe at head. How long does the child wait?  (At base the lock file is per id.)
PE  MAX_PRECONDITION_FIELD_LENGTH (A1 F2 of data428-round3-laneA1-security.md: out of scope, untouched).
"""

import datetime as dt
import hashlib
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

import juniper_data

assert Path(juniper_data.__file__).resolve().is_relative_to(Path(os.environ["EXPECTED_TREE"]).resolve())
from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.http_cache import MAX_PRECONDITION_FIELD_LENGTH  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.core.models import DatasetMeta  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

WORK = Path(tempfile.mkdtemp(prefix="final-probes-"))
HEAD = hasattr(LocalFSDatasetStore, "_open_lock_stripe")


def meta(dataset_id, **kw):
    return DatasetMeta(dataset_id=dataset_id, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=dt.datetime(2026, 9, 1, tzinfo=dt.UTC), checksum="ab" * 32, **kw)


ARR = {"X_train": np.zeros((2, 2), dtype=np.float32)}

if len(sys.argv) > 1 and sys.argv[1] == "child-record-access":
    store = LocalFSDatasetStore(Path(sys.argv[2]))
    print("ready", flush=True)
    sys.stdin.readline()  # "go": the parent now holds A's lock
    t0 = time.time()
    store.record_access(sys.argv[3])
    print(f"{t0:.3f} {time.time():.3f}", flush=True)
    sys.exit(0)

print("== PA: OpenAPI description of PATCH /v1/datasets/{dataset_id}/tags")
store = LocalFSDatasetStore(WORK / "a")
app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
datasets.set_store(store)
client = TestClient(app, raise_server_exceptions=False)
desc = client.get("/openapi.json").json()["paths"]["/v1/datasets/{dataset_id}/tags"]["patch"]["description"]
flat = " ".join(desc.split())
for needle in ("every route that creates, edits or deletes a dataset takes the same locks", "It does not hold for ``CachedDatasetStore``", "unless, on LocalFS, the removal lands between the write's own existence check and its rename"):
    print(f"  contains {needle[:60]!r}...: {needle in flat}")

print("\n== PC: one metadata file leads out of the root -- named create, /versions, /latest")
store = LocalFSDatasetStore(WORK / "c")
app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
datasets.set_store(store)
client = TestClient(app, raise_server_exceptions=False)
r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 51}, "persist": True, "name": "nm"})
bad = r.json()["dataset_id"]
mp = store.base_path / f"{bad}.meta.json"
out = WORK / "c-outside"
out.mkdir()
(out / mp.name).write_bytes(mp.read_bytes())
mp.unlink()
mp.symlink_to(out / mp.name)
store._invalidate_metadata_cache()
for label, call in (
    ("POST named create (other params)", lambda: client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 52}, "persist": True, "name": "nm"})),
    ("POST unnamed create (other params)", lambda: client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 53}, "persist": True})),
    ("GET /versions?name=nm", lambda: client.get("/v1/datasets/versions", params={"name": "nm"})),
    ("GET /latest?name=nm", lambda: client.get("/v1/datasets/latest", params={"name": "nm"})),
):
    resp = call()
    print(f"  {label:36} {resp.status_code} {resp.text[:60]}")

print("\n== PD: cross-process sharing of a lock file")
root = WORK / "d"
store = LocalFSDatasetStore(root)


def stripe(i):
    return int(hashlib.sha256(i.encode()).hexdigest(), 16) % 16


a = "spiral-3.0.0-aaaaaaaaaaaaaaa0"
b = next(f"spiral-3.0.0-bbbbbbbbbbbbb{n:03d}" for n in range(1000) if stripe(f"spiral-3.0.0-bbbbbbbbbbbbb{n:03d}") == stripe(a))
print(f"  A={a} stripe {stripe(a):x}; B={b} stripe {stripe(b):x}")
store.save(b, meta(b), ARR)
entered, release = threading.Event(), threading.Event()
real_save = store.save


def slow_save(did, m, arrays):
    if did == a:
        entered.set()
        release.wait(20)
    return real_save(did, m, arrays)


store.save = slow_save
proc = subprocess.Popen([sys.executable, __file__, "child-record-access", str(root), b], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=os.environ.copy())
assert proc.stdout.readline().strip() == "ready"
t = threading.Thread(target=lambda: store.save_versioned(a, meta(a), ARR))
t.start()
assert entered.wait(20)
proc.stdin.write("go\n")
proc.stdin.flush()
time.sleep(2.0)
waiting = proc.poll() is None
t_release = time.time()
release.set()
t.join(20)
out_line = proc.stdout.readline().strip().split()
proc.wait(20)
t0, t1 = float(out_line[0]), float(out_line[1])
print(f"  child record_access(B) started {t0 - t_release:+.2f} s rel. release; still running 2 s into A's held save: {waiting}; took {t1 - t0:.2f} s, finished {t1 - t_release:+.2f} s after A's save was released")

print(f"\n== PE: MAX_PRECONDITION_FIELD_LENGTH = {MAX_PRECONDITION_FIELD_LENGTH}")
import shutil  # noqa: E402

shutil.rmtree(WORK, ignore_errors=True)

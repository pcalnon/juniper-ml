"""Lane B (r42d): dynamic deadlock hunt -- does any route nest two stripe locks, or re-enter _version_lock?

Instruments (class-level, so every store instance is covered):
  * LocalFSDatasetStore._meta_write_lock -- per-thread depth; any depth > 1 is recorded with both ids
    and whether they share a stripe (a same-stripe nest self-deadlocks: flock is per open file
    description, so a second open of one stripe blocks even in the same thread);
  * DatasetStore._version_lock -- a same-thread re-acquire (non-reentrant: a self-deadlock) is recorded
    and raised instead of hanging.
Then every dataset route is driven through the app over (1) LocalFS, (2) Cached(LocalFS, LocalFS),
(3) Cached(LocalFS, InMemory). Also: 12 processes open a fresh storage dir at once; and locks/ removed
mid-run. Run inside a tree: run_in_tree.bash <tree> nesting_probe.py <workdir>
"""

import contextlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import juniper_data

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__

import juniper_data.api.settings as settings_module  # noqa: E402

settings_module.get_secret = lambda _name: None

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.base import DatasetStore  # noqa: E402
from juniper_data.storage.cached import CachedDatasetStore  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

WORK = Path(sys.argv[1])
events: list[dict] = []
depth = threading.local()
real_mwl = LocalFSDatasetStore._meta_write_lock


@contextlib.contextmanager
def probing_mwl(self, dataset_id):
    stack = getattr(depth, "stack", None)
    if stack is None:
        stack = depth.stack = []
    if stack:
        outer_store, outer_id = stack[-1]
        events.append({"nested_file_lock": [outer_id, dataset_id], "same_stripe": outer_store._lock_path(outer_id) == self._lock_path(dataset_id)})
    stack.append((self, dataset_id))
    try:
        with real_mwl(self, dataset_id):
            yield
    finally:
        stack.pop()


class ReentryDetectingLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._owner = None

    def __enter__(self):
        if self._owner == threading.get_ident():
            events.append({"version_lock_reentry": True})
            raise RuntimeError("same-thread re-acquire of _version_lock (would deadlock)")
        self._lock.acquire()
        self._owner = threading.get_ident()
        return self

    def __exit__(self, *exc):
        self._owner = None
        self._lock.release()

    def locked(self):
        return self._lock.locked()


LocalFSDatasetStore._meta_write_lock = probing_mwl
DatasetStore._version_lock = ReentryDetectingLock()


def drive(store) -> dict:
    client = TestClient(create_app(settings=Settings(storage_path=str(WORK / "unused"), rate_limit_enabled=False, api_keys=None, _env_file=None)), raise_server_exceptions=False)
    datasets.set_store(store)
    statuses = {}
    mk = lambda seed, **kw: {"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True, **kw}  # noqa: E731
    r = client.post("/v1/datasets", json=mk(1))
    a = r.json()["dataset_id"]
    statuses["create"] = r.status_code
    statuses["create-named"] = client.post("/v1/datasets", json=mk(2, name="n")).status_code
    statuses["create-again"] = client.post("/v1/datasets", json=mk(1)).status_code
    br = client.post("/v1/datasets/batch-create", json={"datasets": [mk(3), mk(4, name="n"), mk(1)]})
    statuses["batch-create"] = br.status_code
    b = [x["dataset_id"] for x in br.json()["results"]][0]
    statuses["ttl-create"] = client.post("/v1/datasets", json=mk(5, ttl_seconds=1)).status_code
    g = client.get(f"/v1/datasets/{a}")
    statuses["get"] = g.status_code
    statuses["get-304"] = client.get(f"/v1/datasets/{a}", headers={"If-None-Match": g.headers.get("etag", '"x"')}).status_code
    art = client.get(f"/v1/datasets/{a}/artifact")
    statuses["artifact"] = art.status_code
    statuses["artifact-304"] = client.get(f"/v1/datasets/{a}/artifact", headers={"If-None-Match": art.headers.get("etag", '"x"')}).status_code
    statuses["patch"] = client.patch(f"/v1/datasets/{a}/tags", json={"add_tags": ["t"]}).status_code
    etag = client.get(f"/v1/datasets/{a}").headers.get("etag")
    statuses["patch-if-match"] = client.patch(f"/v1/datasets/{a}/tags", json={"add_tags": ["u"]}, headers={"If-Match": etag}).status_code
    statuses["batch-tags"] = client.patch("/v1/datasets/batch-tags", json={"dataset_ids": [a, b, "absent-1"], "add_tags": ["v"]}).status_code
    statuses["batch-export"] = client.post("/v1/datasets/batch-export", json={"dataset_ids": [a, b]}).status_code
    statuses["filter"] = client.get("/v1/datasets/filter").status_code
    statuses["stats"] = client.get("/v1/datasets/stats").status_code
    statuses["versions"] = client.get("/v1/datasets/versions", params={"name": "n"}).status_code
    statuses["latest"] = client.get("/v1/datasets/latest", params={"name": "n"}).status_code
    time.sleep(1.2)
    statuses["cleanup"] = client.post("/v1/datasets/cleanup-expired").status_code
    statuses["batch-delete"] = client.post("/v1/datasets/batch-delete", json={"dataset_ids": [b, "absent-2"]}).status_code
    statuses["delete"] = client.delete(f"/v1/datasets/{a}").status_code
    client.get("/v1/health")
    return statuses


def concurrent_init() -> dict:
    target = WORK / "concurrent"
    go = WORK / "go"
    code = (
        "import sys, time\nfrom pathlib import Path\nfrom juniper_data.storage.local_fs import LocalFSDatasetStore\n"
        "go = Path(sys.argv[2])\n(go.parent / ('ready.' + sys.argv[3])).write_text('1')\n"
        "while not go.exists():\n    pass\nLocalFSDatasetStore(Path(sys.argv[1]))\nprint('ok')\n"
    )
    env = {**os.environ, "PYTHONPATH": str(TREE)}
    procs = [subprocess.Popen([sys.executable, "-c", code, str(target), str(go), str(i)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(12)]
    while len(list(WORK.glob("ready.*"))) < 12:
        time.sleep(0.01)
    go.write_text("1")
    outs = [p.communicate(timeout=120) for p in procs]
    failures = [err[-200:] for (out, err), p in zip(outs, procs) if p.returncode != 0]
    return {"processes": 12, "failures": failures, "stripes": sorted(p.name for p in (target / "locks").iterdir()), "stray": sorted(p.name for p in target.iterdir() if p.name != "locks")}


def locks_removed_mid_run() -> dict:
    store = LocalFSDatasetStore(WORK / "rm")
    client_store = store
    from juniper_data.core.models import DatasetMeta
    import numpy as np

    meta = DatasetMeta(dataset_id="v", generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime.now(UTC))
    x = np.zeros((2, 2), dtype=np.float32)
    client_store.save("v", meta, {"X_train": x, "y_train": x, "X_test": x, "y_test": x})
    shutil.rmtree(WORK / "rm" / "locks")
    ok = client_store.update_tags("v", ["after-rm"], []) is not None
    return {"update_tags_after_rm_locks": ok, "locks_now": sorted(p.name for p in (WORK / "rm" / "locks").iterdir())}


out = {}
for label, factory in (
    ("LocalFS", lambda: LocalFSDatasetStore(WORK / "s1")),
    ("Cached(LocalFS,LocalFS)", lambda: CachedDatasetStore(LocalFSDatasetStore(WORK / "s2p"), LocalFSDatasetStore(WORK / "s2c"))),
    ("Cached(LocalFS,LocalFS same dir)", lambda: CachedDatasetStore(LocalFSDatasetStore(WORK / "s3"), LocalFSDatasetStore(WORK / "s3"))),
    ("Cached(LocalFS,InMemory)", lambda: CachedDatasetStore(LocalFSDatasetStore(WORK / "s4"), InMemoryDatasetStore())),
):
    events.clear()
    statuses = drive(factory())
    out[label] = {"statuses": statuses, "nesting_or_reentry_events": list(events)}
out["concurrent_init"] = concurrent_init()
out["locks_removed_mid_run"] = locks_removed_mid_run()
print(json.dumps(out, indent=1))

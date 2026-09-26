#!/usr/bin/env python3
"""Lane A: force create-if-absent interleavings through the REAL routes and across processes.

S1  POST A checks (absent) and is held in generation; POST B creates the same id; a conditional
    PATCH (If-Match = B's ETag) passes its check and is held inside its write; A is released.
    Does A's save land inside the PATCH's window?  What does A's 201 promise, what is stored?
S2  Two POSTs of one id, both past the route's existence check (held in generation until both
    arrive), then released together. How many saves?  Does each 201 describe what is stored?
S3  A conditional update_tags held inside its locks in THIS process; a child PROCESS calls
    save_versioned on the same id (unnamed, then named). Does the child wait, and write?
S4  Two child processes save_versioned one id: the first sleeps 2 s inside its save, the second
    starts 0.5 s later. Does the second wait and write nothing?
No monkeypatching of get_meta: the route's own existence check is what the creates pass.
"""

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

import juniper_data

EXPECTED = Path(os.environ["EXPECTED_TREE"]).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(EXPECTED), juniper_data.__file__
print("juniper_data from:", juniper_data.__file__)

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.routes.generators import GENERATOR_REGISTRY  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.core.models import DatasetMeta  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

WORK = Path(tempfile.mkdtemp(prefix="create-race-"))
SPIRAL = GENERATOR_REGISTRY["spiral"]["generator"]
REAL_GENERATE = SPIRAL.__dict__["generate"]
WAIT = 20


def client_for(store):
    app = create_app(settings=Settings(storage_path=str(store.base_path), rate_limit_enabled=False))
    datasets.set_store(store)
    return TestClient(app, raise_server_exceptions=False)


BODY = {"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 7}, "persist": True}


def stored(store, dataset_id):
    m = store.get_meta(dataset_id)
    # JSON mode, so a datetime renders exactly as the API renders it ('Z', not '+00:00')
    return None if m is None else {"tags": sorted(m.tags), "description": m.description, "expires_at": m.model_dump(mode="json")["expires_at"]}


def described(resp):
    m = resp.json()["meta"]
    return {"tags": sorted(m["tags"]), "description": m.get("description"), "expires_at": m.get("expires_at")}


# ------------------------------------------------------------------------------------------ S1
def s1():
    print("\n== S1: a create released while a conditional PATCH is held in its window (real routes)")
    store = LocalFSDatasetStore(WORK / "s1")
    client = client_for(store)
    gen_entered, gen_release = threading.Event(), threading.Event()
    calls = {"n": 0}
    lock = threading.Lock()

    def gated_generate(params):
        with lock:
            calls["n"] += 1
            mine = calls["n"]
        if mine == 1:  # request A only
            gen_entered.set()
            gen_release.wait(WAIT)
        return REAL_GENERATE.__func__(params)

    SPIRAL.generate = staticmethod(gated_generate)
    try:
        out = {}
        ta = threading.Thread(target=lambda: out.__setitem__("A", client.post("/v1/datasets", json={**BODY, "tags": ["from-A"], "description": "A", "ttl_seconds": 3600})))
        ta.start()
        assert gen_entered.wait(WAIT)
        b = client.post("/v1/datasets", json={**BODY, "tags": ["from-B"], "description": "B"})
        dataset_id = b.json()["dataset_id"]
        print(f"  B: {b.status_code}; stored now {stored(store, dataset_id)}")
        etag = client.patch(f"/v1/datasets/{dataset_id}/tags", json={"add_tags": ["before"]}).headers["etag"]
        in_window, release = threading.Event(), threading.Event()
        real_update_meta = store.update_meta

        def held_update_meta(target, meta):
            if "cond" in meta.tags:
                in_window.set()
                release.wait(WAIT)
            return real_update_meta(target, meta)

        store.update_meta = held_update_meta
        tp = threading.Thread(target=lambda: out.__setitem__("P", client.patch(f"/v1/datasets/{dataset_id}/tags", json={"add_tags": ["cond"]}, headers={"If-Match": etag})))
        tp.start()
        assert in_window.wait(WAIT), "PATCH never reached its write"
        gen_release.set()
        ta.join(3.0)
        a_done_in_window = not ta.is_alive()
        print(f"  with the PATCH held (3 s after A was released): A finished = {a_done_in_window}; stored = {stored(store, dataset_id)}")
        release.set()
        tp.join(WAIT)
        ta.join(WAIT)
        store.update_meta = real_update_meta
        a, p = out["A"], out["P"]
        print(f"  PATCH: {p.status_code} etag={p.headers.get('etag')}")
        print(f"  A: {a.status_code} describes {described(a)}")
        final = stored(store, dataset_id)
        print(f"  final stored: {final}")
        g = client.get(f"/v1/datasets/{dataset_id}")
        print(f"  PATCH's ETag is current: {g.headers.get('etag') == p.headers.get('etag')}; A's 201 matches what is stored: {described(a) == final}")
    finally:
        SPIRAL.generate = REAL_GENERATE


# ------------------------------------------------------------------------------------------ S2
def s2():
    print("\n== S2: two creates of one id, both past the route's existence check")
    store = LocalFSDatasetStore(WORK / "s2")
    client = client_for(store)
    barrier = threading.Barrier(2, timeout=WAIT)

    def gated_generate(params):
        barrier.wait()
        return REAL_GENERATE.__func__(params)

    saves = []
    real_save = store.save

    def counting_save(dataset_id, meta, arrays):
        saves.append(sorted(meta.tags))
        time.sleep(0.2)
        return real_save(dataset_id, meta, arrays)

    store.save = counting_save
    SPIRAL.generate = staticmethod(gated_generate)
    try:
        out = {}
        t1 = threading.Thread(target=lambda: out.__setitem__("one", client.post("/v1/datasets", json={**BODY, "params": {**BODY["params"], "seed": 8}, "tags": ["one"], "ttl_seconds": 3600})))
        t2 = threading.Thread(target=lambda: out.__setitem__("two", client.post("/v1/datasets", json={**BODY, "params": {**BODY["params"], "seed": 8}, "tags": ["two"]})))
        t1.start()
        t2.start()
        t1.join(WAIT)
        t2.join(WAIT)
    finally:
        SPIRAL.generate = REAL_GENERATE
        store.save = real_save
    dataset_id = out["one"].json()["dataset_id"]
    final = stored(store, dataset_id)
    print(f"  saves: {saves}")
    for k in ("one", "two"):
        print(f"  {k}: {out[k].status_code} describes {described(out[k])}; matches stored: {described(out[k]) == final}")
    print(f"  final stored: {final}")


# ------------------------------------------------------------------------------------------ S3/S4
def child(storage, dataset_id, tag, named, sleep_s, out):
    return subprocess.Popen([sys.executable, str(Path(__file__).with_name("create_child.py")), str(storage), dataset_id, tag, "1" if named else "0", str(sleep_s), str(out)], env=os.environ.copy())


def meta_for(dataset_id, tags):
    return DatasetMeta(dataset_id=dataset_id, generator="spiral", generator_version="3.0.0", params={}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=dt.datetime(2026, 9, 1, tzinfo=dt.UTC), checksum="ab" * 32, tags=tags)


def s3(named):
    print(f"\n== S3 ({'named' if named else 'unnamed'}): a child PROCESS creates while this process holds a conditional update_tags in its window")
    store = LocalFSDatasetStore(WORK / f"s3-{int(named)}")
    dataset_id = "spiral-3.0.0-s3probe00000000" + str(int(named))
    store.save(dataset_id, meta_for(dataset_id, ["orig"]), {"X_train": np.zeros((2, 2), dtype=np.float32)})
    # The child models a create whose ROUTE-level existence check ran before the dataset existed
    # (seconds earlier, before generating): it calls save_versioned directly, so the only check
    # left is the one save_versioned makes -- under the locks at head, none at base.
    in_window, release = threading.Event(), threading.Event()
    result = {}

    def hold(current):
        in_window.set()
        release.wait(WAIT)
        return True

    t = threading.Thread(target=lambda: result.__setitem__("edit", store.update_tags(dataset_id, ["cond"], [], precondition=hold)))
    t.start()
    assert in_window.wait(WAIT)
    out = WORK / f"s3-{int(named)}-child.json"
    t_release_at = None
    proc = child(store.base_path, dataset_id, "child", named, 0, out)
    time.sleep(2.5)
    child_done_in_window = proc.poll() is not None
    on_disk_in_window = stored(store, dataset_id)
    t_release_at = time.time()
    release.set()
    t.join(WAIT)
    proc.wait(WAIT)
    rec = json.loads(out.read_text())
    print(f"  child finished while the edit was held: {child_done_in_window}; on disk then: {on_disk_in_window}")
    print(f"  child entered save: {rec['saved']}; child finished {rec['t_end'] - t_release_at:+.2f} s after the release; child's returned tags: {rec['returned_tags']}")
    print(f"  edit result tags: {sorted(result['edit'].tags) if result.get('edit') else result.get('edit')}; final stored: {stored(store, dataset_id)}")


def s3_absent(named):
    print(f"\n== S3b ({'named' if named else 'unnamed'}): the dataset is ABSENT; this process holds the file lock via save_versioned (slow save); a child creates the same id")
    store = LocalFSDatasetStore(WORK / f"s3b-{int(named)}")
    dataset_id = "spiral-3.0.0-s3bprobe0000000" + str(int(named))
    real_save = store.save
    entered, release = threading.Event(), threading.Event()

    def held_save(did, meta, arrays):
        entered.set()
        release.wait(WAIT)
        return real_save(did, meta, arrays)

    store.save = held_save
    result = {}
    m = meta_for(dataset_id, ["parent"])
    if named:
        m.dataset_name = "probe-name"
    t = threading.Thread(target=lambda: result.__setitem__("parent", store.save_versioned(dataset_id, m, {"X_train": np.zeros((2, 2), dtype=np.float32)})))
    t.start()
    assert entered.wait(WAIT)
    out = WORK / f"s3b-{int(named)}-child.json"
    proc = child(store.base_path, dataset_id, "child", named, 0, out)
    time.sleep(2.5)
    child_done = proc.poll() is not None
    t_rel = time.time()
    release.set()
    t.join(WAIT)
    proc.wait(WAIT)
    store.save = real_save
    rec = json.loads(out.read_text())
    print(f"  child finished while the parent's create was held: {child_done}; child saved: {rec['saved']}; child finished {rec['t_end'] - t_rel:+.2f} s after release; child returned tags {rec['returned_tags']}")
    print(f"  final stored: {stored(store, dataset_id)}")


def s4():
    print("\n== S4: two child processes create one id; the first sleeps 2 s inside its save")
    base_dir = WORK / "s4"
    LocalFSDatasetStore(base_dir)
    dataset_id = "spiral-3.0.0-s4probe000000000"
    o1, o2 = WORK / "s4-c1.json", WORK / "s4-c2.json"
    p1 = child(base_dir, dataset_id, "c1", False, 2.0, o1)
    time.sleep(0.8)
    p2 = child(base_dir, dataset_id, "c2", False, 0, o2)
    p1.wait(WAIT)
    p2.wait(WAIT)
    r1, r2 = json.loads(o1.read_text()), json.loads(o2.read_text())
    store = LocalFSDatasetStore(base_dir)
    print(f"  c1 saved={r1['saved']} returned {r1['returned_tags']}; c2 saved={r2['saved']} returned {r2['returned_tags']}; c2 ended {r2['t_end'] - r1['t_end']:+.2f} s relative to c1")
    print(f"  final stored: {stored(store, dataset_id)}")


s1()
s2()
s3(False)
s3(True)
s3_absent(False)
s3_absent(True)
s4()
import shutil  # noqa: E402

shutil.rmtree(WORK, ignore_errors=True)
print("\ndone")

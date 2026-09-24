"""Lane B: deterministic interleavings of the conditional PATCH with the three OTHER writers.

Docs at 3a76a4c (docs/api/JUNIPER_DATA_API.md, PATCH /v1/datasets/{id}/tags): "The check runs
against the current metadata inside the same lock as the write, so it cannot pass and then lose
the race". CHANGELOG [0.16.0]: "sent back as If-Match, a stale copy gets 412 and nothing is written."

Real LocalFS store, real routes, ONE TestClient portal (context-managed) so requests interleave on
one event loop. Instrumentation only WIDENS an existing window: the conditional PATCH's own
update_meta call (recognised by the tag it writes) blocks on an Event until the second request has
finished. Every store call is logged in order, so the interleaving is shown, not inferred.

  A. control: a second SINGLE-dataset PATCH (takes the lock) -> must wait; no loss.
  B. PATCH /batch-tags lands in the window (takes no lock).
  C. DELETE lands in the window (takes no lock).
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
MARK = "conditional-edit"


def run(name: str, second) -> None:
    storage = root / name
    storage.mkdir(parents=True, exist_ok=True)
    store = LocalFSDatasetStore(storage)
    app = create_app(settings=Settings(storage_path=str(storage)))
    log: list[str] = []
    t0 = time.perf_counter()

    def note(s: str) -> None:
        log.append(f"{time.perf_counter() - t0:7.3f}s {s}")

    in_window = threading.Event()
    release = threading.Event()
    real_update_meta = store.update_meta
    real_get_meta = store.get_meta

    def update_meta(dataset_id, meta):
        if MARK in meta.tags:
            note(f"conditional PATCH: precondition PASSED, about to write tags={meta.tags}; window open")
            in_window.set()
            release.wait(timeout=10)
            ok = real_update_meta(dataset_id, meta)
            note(f"conditional PATCH: update_meta wrote tags={meta.tags} -> returned {ok}")
            return ok
        ok = real_update_meta(dataset_id, meta)
        note(f"other writer: update_meta tags={meta.tags} -> {ok}")
        return ok

    def get_meta(dataset_id):
        m = real_get_meta(dataset_id)
        note(f"get_meta -> {None if m is None else m.tags} (version_lock held: {store._version_lock.locked()})")
        return m

    with TestClient(app) as client:
        datasets.set_store(store)  # AFTER the lifespan, which wires its own store
        r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 7}, "persist": True})
        did = r.json()["dataset_id"]
        etag = client.get(f"/v1/datasets/{did}").headers["etag"]
        time.sleep(0.2)  # let the GET's call_soon(record_access) finish before instrumenting
        store.update_meta = update_meta  # type: ignore[method-assign]
        store.get_meta = get_meta  # type: ignore[method-assign]
        note(f"--- scenario {name}: client holds If-Match {etag[:14]}...\"")
        out: dict = {}

        def conditional():
            resp = client.patch(f"/v1/datasets/{did}/tags", json={"add_tags": [MARK]}, headers={"If-Match": etag})
            out["conditional PATCH"] = (resp.status_code, (resp.headers.get("etag") or "")[:14], resp.json().get("tags") if resp.status_code == 200 else None)

        th = threading.Thread(target=conditional)
        th.start()
        assert in_window.wait(timeout=10), "conditional PATCH never reached its write"

        def second_req():
            out["second request"] = second(client, did)
            note(f"second request finished: {out['second request']}")

        th2 = threading.Thread(target=second_req)
        th2.start()
        th2.join(timeout=1.5)  # a lock-taking request cannot finish while the window is open
        note(f"second request finished inside the window: {not th2.is_alive()}")
        release.set()
        th.join()
        th2.join()
        final = client.get(f"/v1/datasets/{did}")
        out["final GET"] = (final.status_code, final.json().get("tags") if final.status_code == 200 else None)
    print(f"=== {name}")
    for line in log:
        print("   ", line)
    for k, v in out.items():
        print(f"    RESULT {k}: {v}")


def single(client, did):
    resp = client.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["single-edit"]})
    return (resp.status_code, resp.json().get("tags"))


def batch(client, did):
    resp = client.patch("/v1/datasets/batch-tags", json={"dataset_ids": [did], "add_tags": ["batch-edit"]})
    return (resp.status_code, resp.json())


def delete(client, did):
    return client.delete(f"/v1/datasets/{did}").status_code


run("A-control-single-patch", single)
run("B-batch-tags", batch)
run("C-delete", delete)

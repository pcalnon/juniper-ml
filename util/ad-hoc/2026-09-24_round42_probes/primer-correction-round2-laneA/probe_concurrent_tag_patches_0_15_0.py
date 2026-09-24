#!/usr/bin/env python3
"""Lane A r2: are concurrent UNCONDITIONAL tag PATCHes lost on juniper-data main (1afc3484)?

Tests the II.11 rewrite at primer L5362-5364 ("two clients that read the same dataset and both
PATCHed it produced a silent lost update -- until juniper-data#428 made that PATCH conditional").
N concurrent PATCH {"add_tags": [tag_i]} WITHOUT If-Match through the real route, LocalFS store.
  REAL      : main's store.update_tags (RMW under _version_lock since #263, + flock since #282)
  NEG-CTRL  : the route's pre-#263 shape re-created -- get_meta, a yield, set arithmetic,
              update_meta, in two thread hops with no lock (da2be273's removed lines)
If REAL keeps all N tags and NEG-CTRL loses some, the instrument can see a lost update and the
lost update was closed WITHOUT any precondition, i.e. not by #428.
"""
import asyncio
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / "pypi" / "wheel_0_15_0"
sys.path.insert(0, str(TREE))

import juniper_data.core.secrets as _secrets  # noqa: E402

_secrets.get_secret = lambda *a, **k: None

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from juniper_data.api.routes import datasets as ds_routes  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

N = 12


def pre263_update_tags(store):
    def update_tags(dataset_id, add_tags, remove_tags, precondition=None):
        meta = store.get_meta(dataset_id)           # hop 1 (no lock)
        if meta is None:
            return None
        time.sleep(0.02)                              # the window between the two hops
        tags = set(meta.tags)
        tags.update(add_tags)
        tags -= set(remove_tags)
        meta.tags = sorted(tags)
        store.update_meta(dataset_id, meta)          # hop 2 (no lock)
        return meta
    return update_tags


async def run(label, patch_store):
    path = HERE / f"tmp_conc_{label}"
    shutil.rmtree(path, ignore_errors=True)
    store = LocalFSDatasetStore(path)
    if patch_store:
        store.update_tags = pre263_update_tags(store)
    ds_routes.set_store(store)
    app = FastAPI()
    app.include_router(ds_routes.router, prefix="/v1")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://jd") as c:
        did = (await c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_points_per_spiral": 20, "seed": 5}, "tags": ["base"]})).json()["dataset_id"]
        rs = await asyncio.gather(*[c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": [f"t{i:02d}"]}) for i in range(N)])
        final = (await c.get(f"/v1/datasets/{did}")).json()["tags"]
    shutil.rmtree(path, ignore_errors=True)
    kept = sorted(t for t in final if t.startswith("t"))
    print(f"{label:9s} statuses={sorted({r.status_code for r in rs})} kept {len(kept)}/{N} tags -> {'NO LOSS' if len(kept) == N else 'LOST ' + str(N - len(kept))}")


async def main():
    await run("REAL", False)
    await run("NEG-CTRL", True)


asyncio.run(main())

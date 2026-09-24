#!/usr/bin/env python3
"""Lane A r2 negative control: headers the PUBLISHED juniper-data 0.15.0 wheel actually sends.

Imports juniper_data from the wheel extracted under pypi/wheel_0_15_0 (sha256 matched PyPI's
digest), mounts only its datasets router on a bare app, creates a spiral dataset in an in-memory
store, and prints the response headers of GET /{id}, GET /{id}/artifact (with and without an
If-None-Match) and PATCH /tags. `get_secret` is stubbed so no secret file is read.
"""
import asyncio
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / "pypi" / "wheel_0_15_0"
sys.path.insert(0, str(TREE))

import juniper_data.core.secrets as _secrets  # noqa: E402

_secrets.get_secret = lambda *a, **k: None

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402

import juniper_data  # noqa: E402
from juniper_data.api.routes import datasets as ds_routes  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

assert str(TREE) in juniper_data.__file__, juniper_data.__file__
WATCH = ("etag", "cache-control", "content-location", "last-modified", "vary")


async def main() -> None:
    ds_routes.set_store(InMemoryDatasetStore())
    app = FastAPI()
    app.include_router(ds_routes.router, prefix="/v1")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://jd") as c:
        did = (await c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_points_per_spiral": 40, "seed": 7}})).json()["dataset_id"]
        meta = await c.get(f"/v1/datasets/{did}")
        art = await c.get(f"/v1/datasets/{did}/artifact")
        art_inm = await c.get(f"/v1/datasets/{did}/artifact", headers={"If-None-Match": "*"})
        patch = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["x"]})
        for label, r in (("GET meta", meta), ("GET artifact", art), ("GET artifact INM:*", art_inm), ("PATCH tags", patch)):
            print(f"{label:20s} status={r.status_code} watched={ {k: r.headers[k] for k in WATCH if k in r.headers} } body_len={len(r.content)}")
        print("meta body has access_count:", "access_count" in meta.json())
    print("juniper_data version from wheel:", getattr(juniper_data, "__version__", "?"))


asyncio.run(main())

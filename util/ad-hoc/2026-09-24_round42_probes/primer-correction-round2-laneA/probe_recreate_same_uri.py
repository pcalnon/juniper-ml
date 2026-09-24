#!/usr/bin/env python3
"""Lane A r2: live test of E.1 item 2 -- "the artifact is not content-addressed".

juniper-data main (scratch tree 1afc3484), datasets router only, LocalFS store in scratch.
csv_import reads an upstream file whose content is NOT part of the request, so the id (a hash of
generator, version and params) cannot see it changing:
  1. write data.csv v1; POST csv_import -> id1, checksum1, artifact bytes b1
  2. DELETE id1
  3. rewrite data.csv (v2: different numbers, same shape); POST the SAME request -> id2
Expect id2 == id1 (same URI) and checksum2 != checksum1 (different data at that URI).
Negative control: step 3 WITHOUT rewriting the file must give the same checksum.
get_secret is stubbed before import; Settings is built explicitly with import_dir in scratch.
"""
import asyncio
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / "jd_main_1afc3484"
sys.path.insert(0, str(TREE))

import juniper_data.core.secrets as _secrets  # noqa: E402

_secrets.get_secret = lambda *a, **k: None

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402

import juniper_data.generators.csv_import.generator as csv_gen  # noqa: E402
from juniper_data.api.routes import datasets as ds_routes  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

IMPORTS = HERE / "tmp_imports"
STORE = HERE / "tmp_recreate_store"


def write_csv(offset: float) -> None:
    rows = ["x1,x2,label"] + [f"{i * 0.1 + offset:.3f},{(i % 7) * 0.5 - offset:.3f},{i % 2}" for i in range(40)]
    (IMPORTS / "data.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


async def cycle(c, mutate: bool, offset: float):
    req = {"generator": "csv_import", "params": {"file_path": "data.csv", "label_column": "label"}}
    r1 = await c.post("/v1/datasets", json=req)
    assert r1.status_code == 201, (r1.status_code, r1.text[:300])
    id1 = r1.json()["dataset_id"]
    ck1 = r1.json()["meta"]["checksum"]
    b1 = (await c.get(f"/v1/datasets/{id1}/artifact")).content
    d = await c.delete(f"/v1/datasets/{id1}")
    if mutate:
        write_csv(offset)
    r2 = await c.post("/v1/datasets", json=req)
    id2 = r2.json()["dataset_id"]
    ck2 = r2.json()["meta"]["checksum"]
    b2 = (await c.get(f"/v1/datasets/{id2}/artifact")).content
    await c.delete(f"/v1/datasets/{id2}")
    return {"mutated_upstream": mutate, "delete_status": d.status_code, "recreate_status": r2.status_code, "same_uri": id1 == id2, "id": id1,
            "checksum_changed": ck1 != ck2, "served_bytes_changed": b1 != b2, "sha_b1": hashlib.sha256(b1).hexdigest()[:16], "sha_b2": hashlib.sha256(b2).hexdigest()[:16]}


async def main():
    for p in (IMPORTS, STORE):
        shutil.rmtree(p, ignore_errors=True)
    IMPORTS.mkdir()
    settings = Settings(import_dir=str(IMPORTS))
    csv_gen.get_settings = lambda: settings
    ds_routes.set_store(LocalFSDatasetStore(STORE))
    app = FastAPI()
    app.include_router(ds_routes.router, prefix="/v1")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://jd") as c:
        write_csv(0.0)
        control = await cycle(c, mutate=False, offset=0.0)
        write_csv(0.0)
        test = await cycle(c, mutate=True, offset=0.25)
    print("control (upstream unchanged):", control)
    print("test    (upstream changed)  :", test)
    for p in (IMPORTS, STORE):
        shutil.rmtree(p, ignore_errors=True)


asyncio.run(main())

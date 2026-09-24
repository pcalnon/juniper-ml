#!/usr/bin/env python3
"""Lane A r2: in-process HTTP probe of juniper-data (scratch tree of origin/main 1afc3484) for Appendix E.

Mounts ONLY juniper_data.api.routes.datasets.router at /v1 on a bare FastAPI app (no Settings, no
auth middleware), drives it with httpx.ASGITransport, and records raw observed values -- not just
booleans -- so every check can be seen to be capable of the other answer.

Stores exercised: LocalFSDatasetStore (scratch dir), InMemoryDatasetStore, and CachedDatasetStore
(primary LocalFS, cache InMemory, write_through=False) across its two cache states.

`juniper_data.core.secrets.get_secret` is stubbed to return None BEFORE any juniper_data import that
could instantiate Settings, so no secret file is ever read. Nothing here prints env or secrets.
Run: /opt/miniforge3/envs/JuniperData/bin/python probe_jd_http.py
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / "jd_main_1afc3484"
sys.path.insert(0, str(TREE))

import juniper_data.core.secrets as _secrets  # noqa: E402

_secrets.get_secret = lambda *a, **k: None  # never read a secret file

import httpx  # noqa: E402
import numpy as np  # noqa: E402
from fastapi import FastAPI  # noqa: E402

import juniper_data  # noqa: E402
from juniper_data.api.routes import datasets as ds_routes  # noqa: E402
from juniper_data.core.artifacts import compute_checksum  # noqa: E402
from juniper_data.storage.cached import CachedDatasetStore  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

assert str(TREE) in juniper_data.__file__, juniper_data.__file__

REQ = {"generator": "spiral", "params": {"n_points_per_spiral": 40, "seed": 7}, "tags": ["baseline"], "name": "lanea-r2-probe"}
RESULTS: dict = {"juniper_data_file": juniper_data.__file__, "stores": {}}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def zip_info(b: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        return {"names": z.namelist(), "compress_types": sorted({i.compress_type for i in z.infolist()}), "date_times": sorted({i.date_time for i in z.infolist()})}


def app_for(store) -> FastAPI:
    ds_routes.set_store(store)
    app = FastAPI()
    app.include_router(ds_routes.router, prefix="/v1")
    return app


async def drive(label: str, store) -> dict:
    r: dict = {}
    app = app_for(store)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://jd") as c:
        created = await c.post("/v1/datasets", json=REQ)
        r["create_status"] = created.status_code
        did = created.json()["dataset_id"]
        r["dataset_id"] = did
        meta = await c.get(f"/v1/datasets/{did}")
        mj = meta.json()
        checksum = mj["checksum"]
        r["checksum"] = checksum
        # ---- metadata GET: strong ETag == sha256(body), private,no-cache, counters absent
        r["meta_etag"] = meta.headers.get("etag")
        r["meta_sha_body"] = '"' + sha(meta.content) + '"'
        r["meta_etag_is_sha_body"] = r["meta_etag"] == r["meta_sha_body"]
        r["meta_cache_control"] = meta.headers.get("cache-control")
        r["meta_has_access_count"] = "access_count" in mj or "last_accessed_at" in mj
        m304 = await c.get(f"/v1/datasets/{did}", headers={"If-None-Match": r["meta_etag"]})
        r["meta_inm_current"] = [m304.status_code, len(m304.content), m304.headers.get("etag"), m304.headers.get("cache-control")]
        # ---- artifact GET
        art = await c.get(f"/v1/datasets/{did}/artifact")
        body = art.content
        r["art_status"] = art.status_code
        r["art_etag"] = art.headers.get("etag")
        r["art_etag_is_weak_checksum"] = r["art_etag"] == f'W/"{checksum}"'
        r["art_cache_control"] = art.headers.get("cache-control")
        r["art_sha_body"] = sha(body)
        r["art_sha_body_eq_checksum"] = r["art_sha_body"] == checksum
        with np.load(io.BytesIO(body)) as npz:
            arrays = {k: npz[k] for k in npz.files}
        r["recomputed_checksum_from_served_arrays"] = compute_checksum(arrays)
        r["recomputed_eq_checksum"] = r["recomputed_checksum_from_served_arrays"] == checksum
        r["art_zip"] = zip_info(body)
        r["_body"] = body  # dropped before JSON dump
        # conditional artifact reads
        cases = {
            "INM weak W/checksum": {"If-None-Match": f'W/"{checksum}"'},
            "INM strong-form checksum": {"If-None-Match": f'"{checksum}"'},
            "INM other": {"If-None-Match": '"other"'},
            "IM weak W/checksum": {"If-Match": f'W/"{checksum}"'},
            "IM strong-form checksum": {"If-Match": f'"{checksum}"'},
            "IM sha(served bytes)": {"If-Match": f'"{r["art_sha_body"]}"'},
            "IM *": {"If-Match": "*"},
        }
        r["art_conditional"] = {}
        for k, h in cases.items():
            resp = await c.get(f"/v1/datasets/{did}/artifact", headers=h)
            r["art_conditional"][k] = [resp.status_code, len(resp.content)]
        # ---- /access
        acc = await c.get(f"/v1/datasets/{did}/access")
        r["access"] = [acc.status_code, acc.headers.get("cache-control"), sorted(acc.json().keys())]
        # ---- /latest
        lat = await c.get("/v1/datasets/latest", params={"name": REQ["name"]})
        r["latest"] = [lat.status_code, lat.headers.get("content-location"), lat.headers.get("cache-control"), lat.headers.get("etag") == '"' + sha(lat.content) + '"']
        # ---- PATCH tags
        before = await c.get(f"/v1/datasets/{did}")
        e0 = before.headers["etag"]
        p_nopre = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["np"]})
        r["patch_no_precondition"] = [p_nopre.status_code, p_nopre.json().get("tags"), p_nopre.headers.get("content-location")]
        r["patch_no_precondition_etag_is_sha_body"] = p_nopre.headers.get("etag") == '"' + sha(p_nopre.content) + '"'
        p_stale = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["stale"]}, headers={"If-Match": e0})
        after_stale = await c.get(f"/v1/datasets/{did}")
        r["patch_stale_if_match"] = [p_stale.status_code, "stale" in after_stale.json()["tags"]]
        cur = after_stale.headers["etag"]
        p_cur = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["cur"]}, headers={"If-Match": cur})
        r["patch_current_if_match"] = [p_cur.status_code, p_cur.headers.get("etag") == '"' + sha(p_cur.content) + '"', p_cur.headers.get("etag") != cur, p_cur.json().get("tags")]
        p_art = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["x"]}, headers={"If-Match": r["art_etag"]})
        r["patch_if_match_artifact_tag"] = p_art.status_code
        p_inm = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["y"]}, headers={"If-None-Match": "*"})
        r["patch_if_none_match_star"] = p_inm.status_code
        # delta semantics: two stale deltas (no precondition) both survive -- no erase
        g = await c.get(f"/v1/datasets/{did}")
        base_tags = set(g.json()["tags"])
        a = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["gold"]})
        b = await c.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["archive"]})
        final = set((await c.get(f"/v1/datasets/{did}")).json()["tags"])
        r["two_unconditional_deltas_both_survive"] = [a.status_code, b.status_code, {"gold", "archive"} <= final, sorted(final - base_tags)]
    return r


async def main() -> None:
    tmp = HERE / "tmp_localfs_store"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp2 = HERE / "tmp_cached_primary"
    shutil.rmtree(tmp2, ignore_errors=True)
    stores = {
        "LocalFS": LocalFSDatasetStore(tmp),
        "InMemory": InMemoryDatasetStore(),
    }
    bodies = {}
    for label, st in stores.items():
        res = await drive(label, st)
        bodies[label] = res.pop("_body")
        RESULTS["stores"][label] = res
    # Cached store: primary LocalFS, cache InMemory, populate-on-read
    cached = CachedDatasetStore(primary=LocalFSDatasetStore(tmp2), cache=InMemoryDatasetStore(), write_through=False)
    app = app_for(cached)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://jd") as c:
        did = (await c.post("/v1/datasets", json=REQ)).json()["dataset_id"]
        first = await c.get(f"/v1/datasets/{did}/artifact")
        second = await c.get(f"/v1/datasets/{did}/artifact")
    RESULTS["cached_two_states"] = {
        "dataset_id": did,
        "first_read_sha": sha(first.content), "first_zip_names": zip_info(first.content)["names"], "first_etag": first.headers.get("etag"),
        "second_read_sha": sha(second.content), "second_zip_names": zip_info(second.content)["names"], "second_etag": second.headers.get("etag"),
        "bytes_differ": first.content != second.content, "same_etag": first.headers.get("etag") == second.headers.get("etag"),
    }
    lf, im = RESULTS["stores"]["LocalFS"], RESULTS["stores"]["InMemory"]
    RESULTS["cross_store"] = {
        "same_dataset_id": lf["dataset_id"] == im["dataset_id"],
        "same_checksum": lf["checksum"] == im["checksum"],
        "served_bytes_differ": bodies["LocalFS"] != bodies["InMemory"],
        "LocalFS_zip_names": lf["art_zip"]["names"], "InMemory_zip_names": im["art_zip"]["names"],
    }
    out = HERE / "probe_jd_http.json"
    out.write_text(json.dumps(RESULTS, indent=1, default=str), encoding="utf-8")
    print(json.dumps(RESULTS, indent=1, default=str))
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

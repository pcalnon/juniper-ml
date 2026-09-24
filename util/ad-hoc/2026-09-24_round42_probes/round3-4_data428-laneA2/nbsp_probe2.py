"""NBSP/NEL-wrapped '*': function level, and through httpx.ASGITransport (raw header bytes kept)."""

import asyncio
import sys
import tempfile
from pathlib import Path

L = Path(__file__).resolve().parent
sys.path.insert(0, str(L / "trees" / "3a76a4c"))

import httpx  # noqa: E402

from juniper_data.api import http_cache as hc  # noqa: E402
from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

tag = hc.strong_etag("abc")
for f in ("\xa0*", "\x85*", "*"):
    print(f"function level {f!r}: _well_formed={hc._well_formed(f)} if_none_match_hits={hc.if_none_match_hits(f, tag)} if_match_fails={hc.if_match_fails(f, tag)} write_preconditions_hold={hc.write_preconditions_hold(f, None, tag)}")

seen: list = []


async def main() -> None:
    storage = Path(tempfile.mkdtemp(dir=str(L / "tmp"))) / "s"
    storage.mkdir()
    store = LocalFSDatasetStore(storage)
    app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False))
    datasets.set_store(store)

    async def spy(scope, receive, send):  # record the raw header bytes the app is handed
        if scope["type"] == "http":
            seen.append([v for k, v in scope["headers"] if k in (b"if-match", b"if-none-match")])
        await app(scope, receive, send)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=spy), base_url="http://t") as c:
        dsid = (await c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 4}, "persist": True})).json()["dataset_id"]
        for raw in (b"\xa0*", b"\x85*"):
            seen.clear()
            inm = await c.get(f"/v1/datasets/{dsid}", headers={"If-None-Match": raw})
            got = seen[-1]
            im = await c.get(f"/v1/datasets/{dsid}", headers={"If-Match": raw})
            art = await c.get(f"/v1/datasets/{dsid}/artifact", headers={"If-None-Match": raw})
            before = (await c.get(f"/v1/datasets/{dsid}")).json()["tags"]
            pat = await c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["nbsp"]}, headers={"If-Match": raw})
            print(f"ASGI {raw!r} (app received {got}): GET If-None-Match -> {inm.status_code} [docs: 200 full body]; GET If-Match -> {im.status_code} [docs: 412]; artifact If-None-Match -> {art.status_code} [docs: 200]; PATCH If-Match -> {pat.status_code} [docs: 412], tags {before} -> {pat.json().get('tags') if pat.status_code == 200 else 'unchanged'}")
            if pat.status_code == 200:
                await c.patch(f"/v1/datasets/{dsid}/tags", json={"remove_tags": ["nbsp"]})


asyncio.run(main())

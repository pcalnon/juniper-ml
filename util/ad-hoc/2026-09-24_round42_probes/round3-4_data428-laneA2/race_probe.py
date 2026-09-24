"""Does a conditional PATCH .../tags 'pass and then lose the race' against the documented write routes?

The docs (OpenAPI PATCH description, docs/api/JUNIPER_DATA_API.md 1057-1062, docs/REFERENCE.md 1313-1317)
say the If-Match check runs against the CURRENT representation inside the store's lock, so it cannot
pass and then lose a race to another writer (on one host). That holds only against writers that take
the lock. This probe orders two REAL HTTP requests on the service's store (LocalFS), in one process:

  A: PATCH /v1/datasets/{id}/tags  add 'mine'  If-Match: <E0>   (the conditional write)
  B: a second writer, issued while A holds update_tags' lock, after A has READ the metadata and
     before A's precondition runs and A writes.

The only hook is a wrapper on store.get_meta that, for A's locked read, waits (bounded) for B to
finish. It orders operations the code already permits; it adds no write of its own.

  case 1  B = PATCH /v1/datasets/batch-tags add 'batch'   (takes no lock)
  case 2  B = DELETE /v1/datasets/{id}                      (takes no lock)
  control B = PATCH /v1/datasets/{id}/tags add 'batch'      (takes the lock: must serialise)
"""

import asyncio
import sys
import tempfile
import threading
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(TREE))

import httpx  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

L = Path(__file__).resolve().parent


async def scenario(label: str, b_request) -> None:
    storage = Path(tempfile.mkdtemp(dir=str(L / "tmp"))) / "store"
    storage.mkdir(parents=True)
    store = LocalFSDatasetStore(storage)
    app = create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False))
    datasets.set_store(store)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as client:
        r = await client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 3}, "persist": True})
        dsid = r.json()["dataset_id"]
        e0 = (await client.get(f"/v1/datasets/{dsid}")).headers["etag"]

        b_go, b_done = threading.Event(), threading.Event()
        state = {"armed": True, "a_waited_for_b": None}
        real_get_meta = store.get_meta

        def get_meta(dataset_id):
            meta = real_get_meta(dataset_id)
            if state["armed"] and store._version_lock.locked():
                # A's read inside update_tags' lock: let B run now, then continue with what A read.
                state["armed"] = False
                b_go.set()
                state["a_waited_for_b"] = b_done.wait(3)
            return meta

        store.get_meta = get_meta

        async def run_a():
            return await client.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["mine"]}, headers={"If-Match": e0})

        async def run_b():
            await asyncio.to_thread(b_go.wait, 10)
            try:
                return await b_request(client, dsid)
            finally:
                b_done.set()

        ra, rb = await asyncio.gather(run_a(), run_b())
        del store.get_meta
        final = store.get_meta(dsid)
        meta_file = store._meta_path(dsid).exists()
        npz_file = store._npz_path(dsid).exists()
        print(f"[{label}]")
        print(f"   A (conditional PATCH, If-Match=E0): {ra.status_code}; B: {rb.status_code} {rb.text[:70]}")
        print(f"   A's locked read waited for B to finish: {state['a_waited_for_b']}")
        print(f"   final tags on disk: {final.tags if final else None}; meta file exists={meta_file}, npz exists={npz_file}")
        lost = []
        if final is not None and "batch" in getattr(rb, "_want", ["batch"]) and rb.status_code == 200 and "batch" not in final.tags:
            lost.append("B's 200 'batch' edit was overwritten by A")
        if ra.status_code == 200 and (final is None or "mine" not in final.tags):
            lost.append("A's 200 'mine' edit is gone")
        if rb.status_code == 204 and meta_file:
            lost.append("B's 204 DELETE was undone: A re-wrote the metadata of a deleted dataset")
        print(f"   lost updates: {lost or 'none'}")


async def batch_tags(client, dsid):
    return await client.patch("/v1/datasets/batch-tags", json={"dataset_ids": [dsid], "add_tags": ["batch"]})


async def delete(client, dsid):
    return await client.delete(f"/v1/datasets/{dsid}")


async def locked_patch(client, dsid):
    return await client.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["batch"]})


async def main():
    await scenario("case 1: B = PATCH /batch-tags (no lock)", batch_tags)
    await scenario("case 2: B = DELETE /{id} (no lock)", delete)
    await scenario("control: B = PATCH /{id}/tags (takes the lock)", locked_patch)


asyncio.run(main())

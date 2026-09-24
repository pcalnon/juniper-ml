#!/usr/bin/env python3
"""Lane A: APD-DATA-055 behaviour on juniper-data origin/main, in-process (no port), LocalFS in scratch.
A stale If-Match on DELETE and on PATCH /batch-tags, against the tag PATCH as the control."""
import os
import shutil
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
sys.path.insert(0, f"{S}/src/juniper-data")
for k in [k for k in os.environ if k.startswith("JUNIPER_DATA_")]:
    del os.environ[k]
store_dir = f"{S}/data055_store"
shutil.rmtree(store_dir, ignore_errors=True)
os.makedirs(store_dir)
os.environ["JUNIPER_DATA_STORAGE_PATH"] = store_dir

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402

app = create_app()
STALE = '"0000000000000000000000000000000000000000000000000000000000000000"'
with TestClient(app, raise_server_exceptions=False) as c:
    ids = []
    for seed in (1, 2):
        r = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_points_per_spiral": 20, "seed": seed}})
        ids.append(r.json()["dataset_id"])
    a, b = ids
    etag = c.get(f"/v1/datasets/{a}").headers.get("ETag")
    print("current ETag of A:", (etag or "")[:20] + "…")
    r = c.patch(f"/v1/datasets/{a}/tags", json={"add_tags": ["x"]}, headers={"If-Match": STALE})
    print("CONTROL tag PATCH with stale If-Match ->", r.status_code)
    r = c.patch("/v1/datasets/batch-tags", json={"dataset_ids": [a], "add_tags": ["batch"]}, headers={"If-Match": STALE})
    print("batch-tags with stale If-Match ->", r.status_code, "| tags now:", c.get(f"/v1/datasets/{a}").json().get("tags"))
    r = c.delete(f"/v1/datasets/{b}", headers={"If-Match": STALE})
    print("DELETE with stale If-Match ->", r.status_code, "| GET afterwards:", c.get(f"/v1/datasets/{b}").status_code)
shutil.rmtree(store_dir, ignore_errors=True)

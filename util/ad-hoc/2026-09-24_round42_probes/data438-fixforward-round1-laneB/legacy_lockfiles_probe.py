"""Lane B (r42d): per-id lock files from the OLD scheme, then the new store over the same directory.

Phase "old" (run in the main tree): create datasets through the API and read/tag them, so
record_access and update_tags leave <id>.meta.json.lock files; also lock two ABSENT ids.
Phase "new" (run in the head tree): open the same directory; enumerate, filter, stats, versions,
the readiness probe's count, and every write; report what is on disk before and after.
Run: run_in_tree.bash <tree> legacy_lockfiles_probe.py <old|new> <workdir>
"""

import json
import os
import sys
from pathlib import Path

import juniper_data

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__

import juniper_data.api.settings as settings_module  # noqa: E402

settings_module.get_secret = lambda _name: None

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets, health  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

phase, work = sys.argv[1], Path(sys.argv[2])
storage = work / "storage"
storage.mkdir(parents=True, exist_ok=True)
store = LocalFSDatasetStore(storage)
client = TestClient(create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False, api_keys=None, _env_file=None)))
datasets.set_store(store)
listing = lambda: sorted(p.relative_to(storage).as_posix() for p in storage.rglob("*"))  # noqa: E731
out: dict = {"phase": phase}
if phase == "old":
    ids = []
    for seed in (1, 2, 3):
        r = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": seed}, "persist": True, "name": "legacy"})
        ids.append(r.json()["dataset_id"])
    for did in ids:
        client.get(f"/v1/datasets/{did}")
        client.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["old"]})
    client.patch("/v1/datasets/absent-0001/tags", json={"add_tags": ["x"]})
    client.delete("/v1/datasets/absent-0002")
    client.get("/v1/health")
    out["ids"] = ids
    out["on_disk"] = listing()
else:
    before = listing()
    out["on_disk_before"] = before
    health._reset_probe_cache()
    out["list"] = client.get("/v1/datasets").json()
    out["filter_total"] = client.get("/v1/datasets/filter").json().get("total")
    out["stats_total"] = client.get("/v1/datasets/stats").json().get("total_datasets")
    out["versions_total"] = client.get("/v1/datasets/versions", params={"name": "legacy"}).json().get("total")
    out["ready"] = client.get("/v1/health/ready").json()
    did = out["list"][0]
    out["patch"] = client.patch(f"/v1/datasets/{did}/tags", json={"add_tags": ["new"]}).status_code
    out["delete"] = client.delete(f"/v1/datasets/{did}").status_code
    new = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 9}, "persist": True})
    out["create"] = new.status_code
    after = listing()
    out["removed_by_new_version"] = sorted(set(before) - set(after))
    out["added_by_new_version"] = sorted(set(after) - set(before))
    out["legacy_lock_files_left"] = sorted(p for p in after if p.endswith(".meta.json.lock"))
print(json.dumps(out, indent=1))

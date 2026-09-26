"""Lane B (r42d): can skipping record_access for "unreadable" metadata drop a LEGITIMATE access?

The artifact route's first get_meta fails ONCE, transiently (EMFILE: a descriptor limit hit for a
moment), and succeeds on every later call -- the metadata is perfectly readable. The download is
served; is the access counted?
Run inside a tree: run_in_tree.bash <tree> access_suppression_probe.py
"""

import errno
import json
import os
import tempfile
from pathlib import Path

import juniper_data

TREE = Path(os.getcwd()).resolve()
assert Path(juniper_data.__file__).resolve().is_relative_to(TREE), juniper_data.__file__

import juniper_data.api.settings as settings_module  # noqa: E402

settings_module.get_secret = lambda _name: None

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

work = Path(tempfile.mkdtemp(dir=os.environ.get("SURVEY_TMP")))
storage = work / "storage"
storage.mkdir()
store = LocalFSDatasetStore(storage)
client = TestClient(create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False, api_keys=None, _env_file=None)))
datasets.set_store(store)
created = client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 3}, "persist": True})
dataset_id = created.json()["dataset_id"]
before = client.get(f"/v1/datasets/{dataset_id}/access").json()["access_count"]
real = store.get_meta
fail_next = [True]


def flaky_get_meta(did):
    if fail_next:
        fail_next.clear()
        raise OSError(errno.EMFILE, os.strerror(errno.EMFILE))
    return real(did)


store.get_meta = flaky_get_meta
r = client.get(f"/v1/datasets/{dataset_id}/artifact")
client.get("/v1/health")  # let the loop run any scheduled callback
after = client.get(f"/v1/datasets/{dataset_id}/access").json()["access_count"]
print(json.dumps({"download_status": r.status_code, "etag_sent": "etag" in r.headers, "access_count_before": before, "access_count_after": after, "access_recorded": after == before + 1}))

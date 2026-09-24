"""HEAD, orphan artifact + failing If-Match, and malformed If-None-Match on PATCH (validator scratch)."""

import sys
import tempfile
from pathlib import Path

ROOT = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr"
sys.path.insert(0, ROOT)
SCRATCH = Path(ROOT).parent / "probes" / "rfc_tmp"
SCRATCH.mkdir(exist_ok=True)

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

storage = Path(tempfile.mkdtemp(dir=SCRATCH))
c = TestClient(create_app(settings=Settings(storage_path=str(storage), api_keys=None, rate_limit_enabled=False, metrics_enabled=False)))
store = LocalFSDatasetStore(storage)
datasets.set_store(store)
dsid = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 5}}).json()["dataset_id"]
for path in (f"/v1/datasets/{dsid}", f"/v1/datasets/{dsid}/artifact", "/v1/datasets/latest?name=x"):
    print("HEAD", path, "->", c.head(path).status_code)
# Orphaned artifact (metadata gone, NPZ present): a FAILING If-Match is ignored and the body served
store._meta_path(dsid).unlink()
r = c.get(f"/v1/datasets/{dsid}/artifact", headers={"If-Match": '"definitely-not-current"'})
print("orphan artifact + failing If-Match ->", r.status_code, "bytes:", len(r.content))

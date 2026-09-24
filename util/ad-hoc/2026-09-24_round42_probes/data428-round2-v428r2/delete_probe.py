"""Does DELETE /v1/datasets/{id} honour If-Match now that its GET emits a strong ETag? (validator scratch)"""

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
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

storage = Path(tempfile.mkdtemp(dir=SCRATCH))
c = TestClient(create_app(settings=Settings(storage_path=str(storage), api_keys=None, rate_limit_enabled=False, metrics_enabled=False)))
store = InMemoryDatasetStore()
datasets.set_store(store)
dsid = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 7}}).json()["dataset_id"]
stale = c.get(f"/v1/datasets/{dsid}").headers["etag"]
c.patch(f"/v1/datasets/{dsid}/tags", json={"add_tags": ["someone-else"]})
r = c.delete(f"/v1/datasets/{dsid}", headers={"If-Match": stale})
print("DELETE with stale If-Match ->", r.status_code, "| dataset still exists:", store.exists(dsid))
dsid2 = c.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 8}}).json()["dataset_id"]
r = c.patch("/v1/datasets/batch-tags", json={"dataset_ids": [dsid2], "add_tags": ["x"]}, headers={"If-Match": '"stale"'})
print("PATCH /batch-tags with stale If-Match ->", r.status_code)

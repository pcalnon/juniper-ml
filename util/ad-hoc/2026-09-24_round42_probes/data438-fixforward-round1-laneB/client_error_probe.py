"""Lane B (r42d): caller mistakes on /filter and create -- 400 or 500? (head vs main)

Run inside a tree: run_in_tree.bash <tree> client_error_probe.py
"""

import base64
import json
import logging
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

logging.disable(logging.CRITICAL)
work = Path(tempfile.mkdtemp(dir=os.environ.get("SURVEY_TMP")))
storage = work / "storage"
storage.mkdir()
store = LocalFSDatasetStore(storage)
client = TestClient(create_app(settings=Settings(storage_path=str(storage), rate_limit_enabled=False, api_keys=None, _env_file=None)), raise_server_exceptions=False)
datasets.set_store(store)
client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_spirals": 2, "n_points_per_spiral": 20, "seed": 3}, "persist": True})
naive_cursor = base64.urlsafe_b64encode(b"2026-01-01T00:00:00|zzz").decode()
cases = {
    "filter cursor not base64": ("GET", "/v1/datasets/filter", {"params": {"cursor": "%%%"}}),
    "filter cursor naive datetime": ("GET", "/v1/datasets/filter", {"params": {"cursor": naive_cursor}}),
    "filter created_after naive": ("GET", "/v1/datasets/filter", {"params": {"created_after": "2026-01-01T00:00:00"}}),
    "create params rejected by generator": ("POST", "/v1/datasets", {"json": {"generator": "spiral", "params": {"n_spirals": 99}, "persist": True}}),
    "GET malformed id": ("GET", "/v1/datasets/..bad", {}),
    "DELETE malformed id": ("DELETE", "/v1/datasets/-bad", {}),
}
out = {}
for label, (method, url, kw) in cases.items():
    r = client.request(method, url, **kw)
    out[label] = {"status": r.status_code, "detail": str(r.json().get("detail"))[:100] if r.headers.get("content-type", "").startswith("application/json") else None}
print(json.dumps(out, indent=1))

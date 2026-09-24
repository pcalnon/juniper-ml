"""Conditional PATCH matrix with headers computed against the CURRENT etag each time (validator scratch)."""

import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr"
sys.path.insert(0, ROOT)
SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/probes/rfc_tmp")
SCRATCH.mkdir(exist_ok=True)

import numpy as np  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.core.models import DatasetMeta  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402


def arrays():
    x = np.arange(8, dtype=np.float32).reshape(4, 2)
    y = np.eye(2, dtype=np.float32)[[0, 1, 0, 1]]
    return {"X_train": x[:2], "y_train": y[:2], "X_val": x[:1], "y_val": y[:1], "X_test": x[2:], "y_test": y[2:]}


for label, store in (("memory", InMemoryDatasetStore()), ("localfs", LocalFSDatasetStore(Path(tempfile.mkdtemp(dir=SCRATCH))))):
    storage = SCRATCH / f"pm{label}"
    storage.mkdir(exist_ok=True)
    c = TestClient(create_app(settings=Settings(storage_path=str(storage), api_keys=None, rate_limit_enabled=False, metrics_enabled=False)))
    datasets.set_store(store)
    store.save("d1", DatasetMeta(dataset_id="d1", generator="spiral", generator_version="3.0.0", params={"seed": 1}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime(2026, 9, 22, tzinfo=UTC), checksum="ab" * 32), arrays())
    print(f"== {label}")
    cases = [
        ("IM current", lambda e: {"If-Match": e}, 200),
        ("IM *", lambda e: {"If-Match": "*"}, 200),
        ("IM stale", lambda e: {"If-Match": '"stale"'}, 412),
        ("IM W/current", lambda e: {"If-Match": "W/" + e}, 412),
        ("IM list incl current", lambda e: {"If-Match": f'"a", {e}'}, 200),
        ("INM stale", lambda e: {"If-None-Match": '"stale"'}, 200),
        ("INM current", lambda e: {"If-None-Match": e}, 412),
        ("INM W/current", lambda e: {"If-None-Match": "W/" + e}, 412),
        ("INM *", lambda e: {"If-None-Match": "*"}, 412),
        ("IM current + INM stale", lambda e: {"If-Match": e, "If-None-Match": '"stale"'}, 200),
        ("IM current + INM current", lambda e: {"If-Match": e, "If-None-Match": e}, 412),
        ("IM stale + INM stale", lambda e: {"If-Match": '"stale"', "If-None-Match": '"stale2"'}, 412),
        ("IM malformed", lambda e: {"If-Match": "garbage"}, 412),
        ("INM malformed", lambda e: {"If-None-Match": "garbage"}, 200),
        ("IM empty", lambda e: {"If-Match": ""}, 412),
        ("INM empty", lambda e: {"If-None-Match": ""}, 200),
    ]
    for i, (note, make, want) in enumerate(cases):
        e = c.get("/v1/datasets/d1").headers["etag"]
        before = list(store.get_meta("d1").tags)
        r = c.patch("/v1/datasets/d1/tags", json={"add_tags": [f"t{i}"]}, headers=make(e))
        after = list(store.get_meta("d1").tags)
        ok = "OK " if r.status_code == want and (r.status_code == 200) == (before != after) else "BAD"
        print(f"  {ok} {note:26} -> {r.status_code} (want {want}) wrote={before != after}")

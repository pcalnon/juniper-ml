"""What does an invalid (caller-controlled) id on /artifact log? Run against a tree given as argv[1]."""

import logging
import sys
import tempfile
from pathlib import Path

ROOT = sys.argv[1]
sys.path.insert(0, ROOT)
SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/probes/rfc_tmp")
SCRATCH.mkdir(exist_ok=True)

from fastapi.testclient import TestClient  # noqa: E402

import juniper_data  # noqa: E402
from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

print("tree:", juniper_data.__file__)
records: list[logging.LogRecord] = []


class Grab(logging.Handler):
    def emit(self, record):
        records.append(record)


logging.getLogger().addHandler(Grab())
logging.getLogger().setLevel(logging.DEBUG)
storage = Path(tempfile.mkdtemp(dir=SCRATCH))
c = TestClient(create_app(settings=Settings(storage_path=str(storage), api_keys=None, rate_limit_enabled=False, metrics_enabled=False)))
datasets.set_store(LocalFSDatasetStore(storage))
for path in ("/v1/datasets/CALLER$CONTROLLED/artifact", "/v1/datasets/CALLER$CONTROLLED"):
    records.clear()
    resp = c.get(path)
    print(path, "->", resp.status_code)
    for rec in records:
        if rec.name.startswith("juniper_data"):
            exc = logging.Formatter().formatException(rec.exc_info) if rec.exc_info else ""
            print(f"  {rec.levelname:8} {rec.getMessage()[:90]!r} exc_info={'yes' if exc else 'no'} caller-string-in-record={'CALLER$CONTROLLED' in rec.getMessage() + exc}")

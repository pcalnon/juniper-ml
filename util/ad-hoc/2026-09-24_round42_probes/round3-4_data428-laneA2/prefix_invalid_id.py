"""At a given tree: an invalid id on the artifact route -- status, and any WARNING (with or without traceback)."""

import logging
import sys
import tempfile
from pathlib import Path

L = Path(__file__).resolve().parent
tree = sys.argv[1]
sys.path.insert(0, str(L / "trees" / tree))

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402

records: list[logging.LogRecord] = []


class Grab(logging.Handler):
    def emit(self, record):
        records.append(record)


lg = logging.getLogger("juniper_data")
lg.addHandler(Grab(level=logging.DEBUG))
lg.setLevel(logging.DEBUG)
storage = Path(tempfile.mkdtemp(dir=str(L / "tmp"))) / "s"
storage.mkdir()
kwargs = {"storage_path": str(storage)}
if "rate_limit_enabled" in Settings.model_fields:
    kwargs["rate_limit_enabled"] = False
app = create_app(settings=Settings(**kwargs))
datasets.set_store(LocalFSDatasetStore(storage))
r = TestClient(app).get("/v1/datasets/CALLER$CONTROLLED/artifact")
warn = [x for x in records if x.levelno >= logging.WARNING]
print(f"[{tree}] status={r.status_code} body={r.text} warnings={[(w.getMessage()[:80], w.exc_info is not None) for w in warn]}")
print(f"[{tree}] caller id in a WARNING record (message or traceback): {any('CALLER$CONTROLLED' in logging.Formatter('%(message)s').format(w) for w in warn)}")

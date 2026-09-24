"""Small checks: old grammar at k=22 (the docs' '~1.8 s'); InMemory answers an odd id with 404."""

import re
import sys
import tempfile
import time
from pathlib import Path

L = Path(__file__).resolve().parent
sys.path.insert(0, str(L / "trees" / "3a76a4c"))

OLD = re.compile(r'[ \t]*(?:(?:W/)?"[^"]*")?[ \t]*(?:,[ \t]*(?:(?:W/)?"[^"]*")?[ \t]*)*')
for k in (20, 22):
    t = time.perf_counter()
    OLD.fullmatch(", " * k + "x")
    print(f"old ', ' * {k} + 'x': {time.perf_counter() - t:.3f} s")

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

app = create_app(settings=Settings(storage_path=tempfile.mkdtemp(dir=str(L / "tmp")), rate_limit_enabled=False))
datasets.set_store(InMemoryDatasetStore())
c = TestClient(app)
print("InMemory, id CALLER$CONTROLLED:", {p: c.get(p).status_code for p in ("/v1/datasets/CALLER$CONTROLLED", "/v1/datasets/CALLER$CONTROLLED/artifact")})

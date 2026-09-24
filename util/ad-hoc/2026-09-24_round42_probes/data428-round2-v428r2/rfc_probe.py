"""RFC 9110 behaviour probe for PR #428's conditional requests (validator scratch)."""

import hashlib
import json
import logging
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr"
sys.path.insert(0, ROOT)
SCRATCH = Path(ROOT).parent / "probes" / "rfc_tmp"
SCRATCH.mkdir(exist_ok=True)

import numpy as np  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.http_cache import if_match_fails, if_none_match_hits, strong_etag  # noqa: E402
from juniper_data.api.routes import datasets  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402
from juniper_data.core.models import DatasetMeta, PublicDatasetMeta  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

E = strong_etag("abc")
print("== grammar (If-None-Match hits / If-Match fails) against current", E)
for field in ['W/abc', '"abc', 'W/ "abc"', 'w/"abc"', '"abc" "def"', '"abc",', ',"abc"', ",", "*, \"abc\"", '"*"', '"a b"', '"abc"\t,\t"x"', ' "abc" ', '"x", W/"abc"', 'W/"abc"W/"x"', '"ab"c"', "\"abc\"\x00", '"abc", *']:
    print(f"  {field!r:22} INM-hit={if_none_match_hits(field, E)!s:5}  IM-fail={if_match_fails(field, E)}")


def app_with(store):
    storage = SCRATCH / f"st{id(store)}"
    storage.mkdir(exist_ok=True)
    app = create_app(settings=Settings(storage_path=str(storage), api_keys=None, rate_limit_enabled=False, metrics_enabled=False))
    datasets.set_store(store)
    return TestClient(app)


def arrays():
    x = np.arange(8, dtype=np.float32).reshape(4, 2)
    y = np.eye(2, dtype=np.float32)[[0, 1, 0, 1]]
    return {"X_train": x[:2], "y_train": y[:2], "X_val": x[:1], "y_val": y[:1], "X_test": x[2:], "y_test": y[2:]}


def meta(dsid, **kw):
    f = dict(dataset_id=dsid, generator="spiral", generator_version="3.0.0", params={"seed": 1}, n_samples=4, n_features=2, n_train=2, n_test=2, created_at=datetime(2026, 9, 22, 20, 0, tzinfo=UTC), checksum="ab" * 32)
    f.update(kw)
    return DatasetMeta(**f)


for label, store in (("memory", InMemoryDatasetStore()), ("localfs", LocalFSDatasetStore(Path(tempfile.mkdtemp(dir=SCRATCH))))):
    c = app_with(store)
    print(f"\n== store={label}")
    tricky = meta(
        "tricky-1",
        params={"noise": 1e-07, "big": 1e22, "neg0": -0.0, "tiny": 5e-324, "i": 2**63, "nan": float("nan"), "inf": float("inf"), "s": "é 💥", "nested": {"b": 1, "a": [1.5, None]}},
        description="héllo \"quoted\" \\ back",
        created_at=datetime(2026, 9, 22, 20, 0, 0, 123456, tzinfo=UTC),
        expires_at=datetime(2026, 9, 30, 1, 2, 3),
        tags=["zeta", "alpha"],
    )
    store.save("tricky-1", tricky, arrays())
    r = c.get("/v1/datasets/tricky-1")
    print("  GET", r.status_code, "etag==sha256(wire):", r.headers.get("etag") == '"' + hashlib.sha256(r.content).hexdigest() + '"')
    ref = FastAPI()

    @ref.get("/m", response_model=PublicDatasetMeta)
    def _m() -> DatasetMeta:
        return store.get_meta("tricky-1")

    refbody = TestClient(ref).get("/m").content
    print("  bytes identical to FastAPI response_model rendering:", refbody == r.content)
    if refbody != r.content:
        print("   route:", r.content[:300])
        print("   ref  :", refbody[:300])
    print("  body sample:", r.content[:160])
    et = r.headers["etag"]
    r304 = c.get("/v1/datasets/tricky-1", headers={"If-None-Match": et})
    print("  304:", r304.status_code, dict(r304.headers))
    # PATCH then GET: same etag (LocalFS round trip)
    p = c.patch("/v1/datasets/tricky-1/tags", json={"add_tags": ["new"]}, headers={"If-Match": et})
    g = c.get("/v1/datasets/tricky-1")
    print("  PATCH", p.status_code, "PATCH etag == next GET etag:", p.headers.get("etag") == g.headers.get("etag"), "| body equal:", p.content == g.content)
    if p.content != g.content:
        print("   patch:", p.content[:400])
        print("   get  :", g.content[:400])
    # conditional PATCH matrix
    cur = g.headers["etag"]
    for hdrs, note in (
        ({"If-Match": "*"}, "IM *"),
        ({"If-None-Match": '"stale"'}, "INM stale"),
        ({"If-None-Match": cur}, "INM current"),
        ({"If-None-Match": "W/" + cur}, "INM W/current"),
        ({"If-Match": "W/" + cur}, "IM W/current"),
        ({"If-Match": cur, "If-None-Match": '"other"'}, "IM cur + INM other"),
    ):
        before = store.get_meta("tricky-1").tags
        rr = c.patch("/v1/datasets/tricky-1/tags", json={"add_tags": ["probe-" + note.replace(" ", "_")]}, headers=hdrs)
        after = store.get_meta("tricky-1").tags
        print(f"  PATCH {note:22} -> {rr.status_code} wrote={before != after}")
        if rr.status_code == 200:
            cur = rr.headers["etag"]
    # nonexistent targets
    for path, hdrs in (("/v1/datasets/nope", {"If-Match": "*"}), ("/v1/datasets/nope", {"If-None-Match": "*"}), ("/v1/datasets/nope/artifact", {"If-Match": "*"}), ("/v1/datasets/latest?name=nope", {"If-None-Match": "*"})):
        print(f"  GET {path} {hdrs} -> {c.get(path, headers=hdrs).status_code}")
    print("  PATCH nope If-Match:* ->", c.patch("/v1/datasets/nope/tags", json={"add_tags": ["x"]}, headers={"If-Match": "*"}).status_code)
    # artifact: strong form of checksum in INM (weak comparison -> 304), in IM (strong -> 412)
    a = c.get("/v1/datasets/tricky-1/artifact")
    ck = store.get_meta("tricky-1").checksum
    print("  artifact etag:", a.headers.get("etag"), "sha256(served)==checksum:", hashlib.sha256(a.content).hexdigest() == ck)
    print("  artifact INM strong-form ->", c.get("/v1/datasets/tricky-1/artifact", headers={"If-None-Match": f'"{ck}"'}).status_code)
    print("  artifact IM strong-form ->", c.get("/v1/datasets/tricky-1/artifact", headers={"If-Match": f'"{ck}"'}).status_code)
    r304a = c.get("/v1/datasets/tricky-1/artifact", headers={"If-None-Match": a.headers["etag"]})
    print("  artifact 304 headers:", r304a.status_code, dict(r304a.headers))
    acc = c.get("/v1/datasets/tricky-1/access")
    print("  /access:", acc.status_code, acc.json(), acc.headers.get("cache-control"))

# LocalFS: an invalid (caller-controlled) id on the artifact route -- what is logged, at what level?
print("\n== LocalFS invalid id on /artifact: log records")
records: list[logging.LogRecord] = []


class Grab(logging.Handler):
    def emit(self, record):
        records.append(record)


root = logging.getLogger()
root.addHandler(Grab())
root.setLevel(logging.DEBUG)
store = LocalFSDatasetStore(Path(tempfile.mkdtemp(dir=SCRATCH)))
c = app_with(store)
logging.getLogger().setLevel(logging.DEBUG)
records.clear()
resp = c.get("/v1/datasets/CALLER$CONTROLLED%0Afake-log-line/artifact")
print("  status:", resp.status_code, resp.text[:120])
for rec in records:
    if rec.levelno >= logging.DEBUG and rec.name.startswith("juniper_data"):
        text = rec.getMessage()
        exc = logging.Formatter().formatException(rec.exc_info) if rec.exc_info else ""
        print(f"  {rec.levelname:8} {rec.name}: {text!r} | exc_info carries caller string: {'CALLER$CONTROLLED' in exc}")
        if exc:
            print("     last exc line:", exc.strip().splitlines()[-1][:160])

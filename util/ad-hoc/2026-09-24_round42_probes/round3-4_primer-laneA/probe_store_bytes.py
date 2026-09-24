#!/usr/bin/env python3
"""Lane A, claims 2-3 for the stores the HTTP probe could not run (no Redis / Postgres server, and the
``redis`` / ``psycopg2`` packages are absent from the JuniperData env).

Runs each store's REAL ``save`` + ``get_artifact_bytes`` code in-process, with the network client
replaced by an in-memory fake (constructors bypassed via ``object.__new__``), then asks: is
sha256(served bytes) == compute_checksum(arrays)? is the NPZ DEFLATE-compressed? are keys sorted?

Also: (a) LocalFS with the SAME arrays in two dict orders -> different served bytes, same checksum;
(b) CachedDatasetStore(LocalFS primary, InMemory cache) serving ONE dataset as two different byte
strings depending on cache state; (c) HF / Kaggle stores are pure delegates to their cache_store.
Everything is written under this script's scratch directory.
"""

from __future__ import annotations

import hashlib
import io
import shutil
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "jd-main"))

import numpy as np  # noqa: E402

import juniper_data  # noqa: E402
from juniper_data.core.artifacts import compute_checksum  # noqa: E402
from juniper_data.core.meta import pop_data_quality_meta, pop_scaling_meta, pop_truncation_meta  # noqa: E402
from juniper_data.core.models import DatasetMeta  # noqa: E402
from juniper_data.generators.spiral.generator import SpiralGenerator  # noqa: E402
from juniper_data.generators.spiral.params import SpiralParams  # noqa: E402
from juniper_data.storage.cached import CachedDatasetStore  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402
from juniper_data.storage.postgres_store import PostgresDatasetStore  # noqa: E402
from juniper_data.storage.redis_store import RedisDatasetStore  # noqa: E402

assert "/scratchpad/r42/primer-laneA/jd-main/" in juniper_data.__file__

WORK = HERE / "store-probe"
shutil.rmtree(WORK, ignore_errors=True)
WORK.mkdir()

arrays = SpiralGenerator.generate(SpiralParams(n_spirals=2, n_points_per_spiral=60, seed=1234))
pop_scaling_meta(arrays)
pop_truncation_meta(arrays)
pop_data_quality_meta(arrays)
checksum = compute_checksum(arrays)
print("arrays keys (generator order):", list(arrays))
print("checksum:", checksum)


def meta_for(dsid: str) -> DatasetMeta:
    return DatasetMeta(dataset_id=dsid, generator="spiral", generator_version="3.0.0", params={}, n_samples=120, n_features=2, n_train=1, n_test=1, created_at=datetime.now(UTC), checksum=checksum)


def describe(label: str, body: bytes) -> str:
    zf = zipfile.ZipFile(io.BytesIO(body))
    names = [i.filename for i in zf.infolist()]
    methods = sorted({i.compress_type for i in zf.infolist()})
    sha = hashlib.sha256(body).hexdigest()
    verdict = "EQUAL" if sha == checksum else "differs"
    print(f"{label:48s} sha256={sha[:16]}... vs checksum: {verdict}; zip methods={methods} (8=DEFLATED); keys sorted={names == sorted(names)}")
    return sha


# ---- Redis: real save/get with a fake client ------------------------------------------------
class FakePipe:
    def __init__(self, store: dict) -> None:
        self.store, self.ops = store, []

    def set(self, k, v):
        self.ops.append((k, v))

    def setex(self, k, ttl, v):
        self.ops.append((k, v))

    def execute(self):
        for k, v in self.ops:
            self.store[k] = v


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict = {}

    def pipeline(self):
        return FakePipe(self.data)

    def get(self, k):
        return self.data.get(k)

    def exists(self, k):
        return int(k in self.data)


redis_store = object.__new__(RedisDatasetStore)
redis_store._client = FakeRedis()
redis_store._key_prefix = "lanea:"
redis_store._default_ttl = None
redis_store.save("ds-redis", meta_for("ds-redis"), arrays)
sha_redis = describe("RedisDatasetStore (real save/get, fake client)", redis_store.get_artifact_bytes("ds-redis"))


# ---- Postgres: real save/get with a fake connection -------------------------------------------
class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.last = sql

    def fetchone(self):
        return None


class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def cursor(self, **kw):
        return FakeCursor()

    def commit(self):
        pass


pg = object.__new__(PostgresDatasetStore)
pg._artifact_path = WORK / "pg"
pg._artifact_path.mkdir()
pg._get_connection = lambda: FakeConn()  # type: ignore[method-assign]
pg.save("ds-pg", meta_for("ds-pg"), arrays)
sha_pg = describe("PostgresDatasetStore (real save/get, fake conn)", pg.get_artifact_bytes("ds-pg"))

# ---- LocalFS and InMemory directly ---------------------------------------------------------------
lfs = LocalFSDatasetStore(WORK / "lfs")
lfs.save("ds-a", meta_for("ds-a"), arrays)
sha_lfs = describe("LocalFSDatasetStore (generator key order)", lfs.get_artifact_bytes("ds-a"))
reordered = {k: arrays[k] for k in sorted(arrays)}
lfs.save("ds-b", meta_for("ds-b"), reordered)
sha_lfs_sorted = describe("LocalFSDatasetStore (SAME arrays, sorted order)", lfs.get_artifact_bytes("ds-b"))
print(f"  -> same arrays, same checksum ({compute_checksum(reordered) == checksum}), different served bytes: {sha_lfs != sha_lfs_sorted}")
mem = InMemoryDatasetStore()
mem.save("ds-m", meta_for("ds-m"), arrays)
sha_mem = describe("InMemoryDatasetStore", mem.get_artifact_bytes("ds-m"))

# ---- CachedDatasetStore: one dataset, two byte strings -----------------------------------------------
cached = CachedDatasetStore(LocalFSDatasetStore(WORK / "cached-primary"), InMemoryDatasetStore(), write_through=False)
cached.save("ds-c", meta_for("ds-c"), arrays)
first = cached.get_artifact_bytes("ds-c")  # cache miss -> primary's bytes (and populates the cache)
second = cached.get_artifact_bytes("ds-c")  # cache hit -> in-memory re-serialization (sorted)
s1 = describe("CachedDatasetStore read #1 (cache miss -> primary)", first)
s2 = describe("CachedDatasetStore read #2 (cache hit -> InMemory)", second)
print(f"  -> ONE dataset, ONE checksum, two served byte strings: {s1 != s2}")

# ---- HF / Kaggle: delegates ---------------------------------------------------------------------------
from juniper_data.storage.hf_store import HuggingFaceDatasetStore  # noqa: E402
from juniper_data.storage.kaggle_store import KaggleDatasetStore  # noqa: E402

for cls in (HuggingFaceDatasetStore, KaggleDatasetStore):
    s = object.__new__(cls)
    s._cache_store = InMemoryDatasetStore()
    s._cache_store.save("ds-x", meta_for("ds-x"), arrays)
    describe(f"{cls.__name__} (delegates to cache_store)", s.get_artifact_bytes("ds-x"))

all_differ = all(h != checksum for h in (sha_redis, sha_pg, sha_lfs, sha_lfs_sorted, sha_mem, s1, s2))
print("\nsha256(served bytes) != checksum for every store exercised:", all_differ)

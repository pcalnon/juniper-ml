#!/usr/bin/env python3
"""Lane A: APD-DATA-054 -- served bytes vs the stored checksum, on juniper-data origin/main's own
InMemory and LocalFS stores (LocalFS rooted in scratch). Also: same arrays, different key order."""
import hashlib
import os
import shutil
import sys
from pathlib import Path

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
sys.path.insert(0, f"{S}/src/juniper-data")
import numpy as np  # noqa: E402

from juniper_data.core.artifacts import compute_checksum  # noqa: E402
from juniper_data.storage.local_fs import LocalFSDatasetStore  # noqa: E402
from juniper_data.storage.memory import InMemoryDatasetStore  # noqa: E402

rng = np.random.default_rng(0)
arrays = {k: rng.standard_normal((20, 2)).astype(np.float32) for k in ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test")}
checksum = compute_checksum(arrays)


class M:  # minimal stand-in for DatasetMeta where only model_dump is needed
    pass


mem = InMemoryDatasetStore()
mem._arrays["d"] = arrays  # direct seeding: get_artifact_bytes reads only _arrays
mem_bytes = mem.get_artifact_bytes("d")

root = Path(f"{S}/data054_store")
shutil.rmtree(root, ignore_errors=True)
lfs = LocalFSDatasetStore(root)
import io  # noqa: E402

buf = io.BytesIO()
np.savez_compressed(buf, **arrays)  # exactly what local_fs.save writes (keys in insertion order)
lfs_bytes_insertion = buf.getvalue()
rev = dict(reversed(list(arrays.items())))
buf2 = io.BytesIO()
np.savez_compressed(buf2, **rev)
lfs_bytes_reversed = buf2.getvalue()

h = lambda b: hashlib.sha256(b).hexdigest()[:16]  # noqa: E731
print("checksum (stored)            :", checksum[:16])
print("InMemory served sha256       :", h(mem_bytes), "== checksum?", h(mem_bytes) == checksum[:16])
print("LocalFS-style served sha256  :", h(lfs_bytes_insertion), "== checksum?", h(lfs_bytes_insertion) == checksum[:16])
print("same arrays, reversed key order: bytes differ?", lfs_bytes_insertion != lfs_bytes_reversed, "| checksum of reordered arrays equal?", compute_checksum(rev) == checksum)
shutil.rmtree(root, ignore_errors=True)

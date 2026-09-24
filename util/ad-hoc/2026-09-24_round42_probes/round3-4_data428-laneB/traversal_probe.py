"""Lane B: does LocalFS at 3a76a4c still refuse every traversal, and with which exception class?

Runs each hostile id against every LocalFS entry point that builds a path, and through the HTTP
routes (TestClient, LocalFS wired), including percent-encoded forms. Also the symlink case the
containment check exists for: a VALID id whose .meta.json is a symlink out of the storage root.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from juniper_data.api.app import create_app
from juniper_data.api.routes import datasets
from juniper_data.api.settings import Settings
from juniper_data.storage.base import InvalidDatasetIdError
from juniper_data.storage.local_fs import LocalFSDatasetStore

root = Path(sys.argv[1])
storage = root / "store"
outside = root / "outside"
storage.mkdir(parents=True, exist_ok=True)
outside.mkdir(parents=True, exist_ok=True)
(outside / "secret.meta.json").write_text('{"not": "metadata"}')
store = LocalFSDatasetStore(storage)

HOSTILE = [
    "..", "../x", "..\\x", "a/../b", "/etc/passwd", "a/b", "a\\b", "%2e%2e", "%2e%2e%2fx", "..%2f",
    "x\x00y", "x\ny", "abc\n", " abc", "abc ", ".hidden", "-rf", "_x", "a" * 129, "",
    "．．", "․․", "a／b", "a∕b", "a⁄b", "аbc",  # fullwidth dot, one-dot leader, fullwidth solidus, division slash, fraction slash, cyrillic a
    "a..b", "a.", "a-", "...",
]

ops = {
    "get_meta": lambda i: store.get_meta(i),
    "exists": lambda i: store.exists(i),
    "open_artifact_stream": lambda i: store.open_artifact_stream(i),
    "get_artifact_bytes": lambda i: store.get_artifact_bytes(i),
    "delete": lambda i: store.delete(i),
    "update_meta": lambda i: store.update_meta(i, None),  # refused before meta is touched, if at all
    "record_access": lambda i: store.record_access(i),
    "update_tags": lambda i: store.update_tags(i, ["t"], []),
}

accepted = []
for hid in HOSTILE:
    results = {}
    for name, op in ops.items():
        try:
            op(hid)
            results[name] = "ACCEPTED"
        except InvalidDatasetIdError:
            results[name] = "InvalidDatasetIdError"
        except ValueError as exc:
            results[name] = f"ValueError({type(exc).__name__})"
        except Exception as exc:  # noqa: BLE001
            results[name] = f"{type(exc).__name__}"
    kinds = set(results.values())
    if "ACCEPTED" in kinds:
        accepted.append((hid, results))
    print(f"{hid!r:28.28} -> {sorted(kinds)}")

print("\nids ACCEPTED by some op:", [(h, [k for k, v in r.items() if v == 'ACCEPTED']) for h, r in accepted])

# Files created outside the storage root? (would be a traversal that landed)
created_outside = sorted(p.name for p in outside.iterdir())
print("files in the outside dir:", created_outside)
print("files in storage:", sorted(p.name for p in storage.iterdir()))

# HTTP layer, LocalFS wired.
app = create_app(settings=Settings(storage_path=str(storage)))
datasets.set_store(store)
client = TestClient(app)
paths = ["/v1/datasets/..%2F..%2Fetc%2Fpasswd/artifact", "/v1/datasets/%2e%2e/artifact", "/v1/datasets/..%5Cx/artifact", "/v1/datasets/x%00y/artifact",
         "/v1/datasets/%EF%BC%8E%EF%BC%8E/artifact", "/v1/datasets/a%E2%88%95b/artifact", "/v1/datasets/.hidden/artifact", "/v1/datasets/%20abc/artifact"]
for p in paths:
    for hdrs in ({}, {"If-None-Match": "*"}, {"If-Match": '"x"'}):
        r = client.get(p, headers=hdrs)
        print(f"GET {p} {hdrs} -> {r.status_code} {r.text[:60]!r}")
    r = client.patch(p.replace("/artifact", "/tags"), json={"add_tags": ["t"]}, headers={"If-Match": "*"})
    print(f"PATCH {p.replace('/artifact', '/tags')} If-Match:* -> {r.status_code}")

# The symlink case: a VALID id whose metadata file points outside the root.
valid = "spiral-3.0.0-symlinked0000000"
import numpy as np  # noqa: E402

np.savez(storage / f"{valid}.npz", X_train=np.zeros((2, 2), dtype=np.float32))
os.symlink(outside / "secret.meta.json", storage / f"{valid}.meta.json")
logging.basicConfig(level=logging.WARNING)
for hdrs in ({}, {"If-None-Match": "*"}):
    r = client.get(f"/v1/datasets/{valid}/artifact", headers=hdrs)
    print(f"symlinked-meta GET artifact {hdrs} -> {r.status_code} {r.text[:60]!r} len={len(r.content)}")
r = client.get(f"/v1/datasets/{valid}")
print(f"symlinked-meta GET metadata -> {r.status_code} {r.text[:60]!r}")
try:
    store.get_meta(valid)
except Exception as exc:  # noqa: BLE001
    print("store.get_meta(symlinked) raises", type(exc).__name__, "isinstance InvalidDatasetIdError:", isinstance(exc, InvalidDatasetIdError))

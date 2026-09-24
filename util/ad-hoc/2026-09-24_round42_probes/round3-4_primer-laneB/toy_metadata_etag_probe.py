#!/usr/bin/env python3
"""Lane B probe: does II.11's `metadata_etag` digest the bytes the toy actually sends?

Replicates, verbatim in logic, the primer's II.11 example (primer lines 5470-5477 canonical_json,
5523-5533 Dataset.metadata, 5536-5543 metadata_etag) and Starlette's JSONResponse.render
(ensure_ascii=False, allow_nan=False, indent=None, separators=(",", ":"), no sort_keys), which is
what the toy's GET /v1/datasets/{id} sends (primer line 5722). No FastAPI needed.
"""
import hashlib
import json


def canonical_json(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def starlette_render(content):
    return json.dumps(content, ensure_ascii=False, allow_nan=False, indent=None, separators=(",", ":")).encode("utf-8")


def metadata(ds):
    return {
        "id": ds["id"],
        "generator": ds["generator"],
        "version": ds["version"],
        "params": ds["params"],
        "tags": sorted(ds["tags"]),
        "n_samples": ds["n_samples"],
        "size_bytes": ds["size_bytes"],
        "created_at": ds["created_at"],
    }


for label, tags in (("fixture SPIRAL tags", ["baseline"]), ("non-ASCII tag", ["métier"])):
    ds = {"id": "spiral-v1-0123456789abcdef", "generator": "spiral", "version": 1,
          "params": {"n_samples": 512, "noise": 0.05, "seed": 42}, "tags": tags,
          "n_samples": 512, "size_bytes": 512, "created_at": 1790000000.123}
    md = metadata(ds)
    etag_digest = hashlib.sha256(canonical_json(md).encode("utf-8")).hexdigest()[:32]
    sent = starlette_render(md)
    sent_digest = hashlib.sha256(sent).hexdigest()[:32]
    print(f"{label}: ETag digest={etag_digest}  sha256(sent body)={sent_digest}  equal={etag_digest == sent_digest}")
    print(f"   canonical bytes == sent bytes: {canonical_json(md).encode('utf-8') == sent}")

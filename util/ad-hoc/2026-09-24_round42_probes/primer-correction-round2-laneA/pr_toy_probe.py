#!/usr/bin/env python3
"""
Prove the API primer's II.11 toy sends exactly the bytes its strong metadata ETag hashes.

Project: juniper-ml
Sub-Project: ad-hoc tooling (documentation verification)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- verification for the primer's Appendix E correction
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

`metadata_etag` in the primer's `conditional_datasets.py` example calls itself "a *strong* validator:
a hash of the exact representation we would send". Before the 2026-09-24 correction the routes sent
`JSONResponse(dataset.metadata())` -- insertion order, FastAPI's own separators -- while the ETag
hashed `canonical_json(...)` (sorted keys, compact), so the body and the hash disagreed. The
correction makes the four metadata responses send `canonical_json(...)` itself.

This extracts the example from a primer file by the harness's own convention (the
`<!-- example-file: conditional_datasets.py -->` marker), drives the POST (create and reuse), GET and
PATCH routes in-process, and checks `ETag == '"' + sha256(body)[:32] + '"'` on each. Run it on the
corrected primer (expect 4/4 MATCH) and on `git show HEAD:<primer>` before the correction (expect
MISMATCH): the second run is the negative control that shows the check can fail.

Usage: <python with fastapi + httpx> 2026-09-24_primer_toy_etag_matches_body.py <primer.md>
"""

import asyncio
import hashlib
import importlib.util
import re
import sys
import tempfile
from pathlib import Path


def extract(doc: str, name: str) -> str:
    m = re.search(r"<!-- example-file: " + re.escape(name) + r" -->\n```python\n(.*?)\n```", doc, re.S)
    if not m:
        raise SystemExit(f"no example-file block named {name}")
    return m.group(1) + "\n"


async def probe(mod) -> "list[tuple[str, bool]]":
    import httpx

    app = mod.create_app()
    transport = httpx.ASGITransport(app=app)
    results = []
    async with httpx.AsyncClient(transport=transport, base_url="http://toy") as client:
        body = {"generator": "spiral", "version": 1, "params": {"n_samples": 64, "seed": 7}, "tags": ["a"]}
        created = await client.post("/v1/datasets", json=body)
        reused = await client.post("/v1/datasets", json=body)
        dataset_id = created.json()["id"]
        got = await client.get(f"/v1/datasets/{dataset_id}")
        patched = await client.patch(f"/v1/datasets/{dataset_id}/tags", json={"tags": ["a", "b"]}, headers={"If-Match": got.headers["etag"]})
        for label, resp in (("POST create", created), ("POST reuse", reused), ("GET", got), ("PATCH", patched)):
            want = '"' + hashlib.sha256(resp.content).hexdigest()[:32] + '"'
            results.append((f"{label} {resp.status_code}", resp.headers.get("etag") == want))
    return results


def main(argv: "list[str]") -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    code = extract(Path(argv[1]).read_text(encoding="utf-8"), "conditional_datasets.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "conditional_datasets.py"
        path.write_text(code, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("conditional_datasets", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["conditional_datasets"] = mod  # @dataclass needs the module registered
        spec.loader.exec_module(mod)
        results = asyncio.run(probe(mod))
    for label, ok in results:
        print(f"  {'MATCH   ' if ok else 'MISMATCH'} {label}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

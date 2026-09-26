#!/usr/bin/env python3
"""Lane B: drive the II.11 toy (conditional_datasets.py) extracted from a primer file with inputs the
fix-forward's probe does not send, and print status + content-type + a body excerpt.

Usage: <venv python> toy_attack.py <primer.md> [label]
Never sends an n_samples that would allocate memory: only values that overflow before allocating.
"""
import asyncio
import base64
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

A = "application/json"


def extract(doc: str, name: str) -> str:
    m = re.search(r"<!-- example-file: " + re.escape(name) + r" -->\n```python\n(.*?)\n```", doc, re.S)
    return m.group(1) + "\n"


POSTS = [
    ("n_samples 1.5 (non-integer number)", b'{"generator": "spiral", "params": {"n_samples": 1.5}}'),
    ("n_samples 64.0 (integral float)", b'{"generator": "spiral", "params": {"n_samples": 64.0}}'),
    ("n_samples \"512\" (numeric string)", b'{"generator": "spiral", "params": {"n_samples": "512"}}'),
    ("n_samples true (bool)", b'{"generator": "spiral", "params": {"n_samples": true}}'),
    ("noise \"0.1\" (string, not n_samples)", b'{"generator": "spiral", "params": {"noise": "0.1"}}'),
    ("seed null (not n_samples)", b'{"generator": "spiral", "params": {"seed": null}}'),
    ("nested object param", b'{"generator": "spiral", "params": {"opts": {"a": 1}}}'),
    ("string param (algorithm)", b'{"generator": "spiral", "params": {"algorithm": "fast"}}'),
    ("n_samples -5 (negative)", b'{"generator": "spiral", "params": {"n_samples": -5}}'),
    ("n_samples 10**30 (declared omission)", b'{"generator": "spiral", "params": {"n_samples": 1000000000000000000000000000000}}'),
    ("n_samples 1e300 (finite float)", b'{"generator": "spiral", "params": {"n_samples": 1e300}}'),
    ("noise 1e309 (JSON number -> inf)", b'{"generator": "spiral", "params": {"noise": 1e309}}'),
    ("generator NaN", b'{"generator": NaN}'),
    ("version NaN", b'{"generator": "spiral", "version": NaN}'),
    ("tags [NaN]", b'{"generator": "spiral", "tags": [NaN]}'),
    ("extra key NaN", b'{"generator": "spiral", "zz": NaN}'),
    ("5000-digit integer", b'{"generator": "spiral", "params": {"n_samples": ' + b"9" * 5000 + b"}}"),
    ("invalid JSON", b'{"generator": '),
    ("empty body", b""),
]


async def drive(module) -> None:
    import httpx

    app = module.create_app()
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for label, body in POSTS:
            r = await client.post("/v1/datasets", content=body, headers={"Content-Type": A})
            ctype = r.headers.get("content-type", "")
            excerpt = r.text[:160].replace("\n", " ")
            print(f"  POST {label:40} {r.status_code} {ctype:32} {excerpt}")
        # non-JSON content type
        r = await client.post("/v1/datasets", content=b"generator=spiral", headers={"Content-Type": "text/plain"})
        print(f"  POST {'text/plain body':40} {r.status_code} {r.headers.get('content-type', ''):32} {r.text[:120]}")
        # routing errors FastAPI generates
        for method, url in (("GET", "/v1/nope"), ("DELETE", "/v1/datasets/x"), ("PUT", "/v1/datasets")):
            r = await client.request(method, url)
            print(f"  {method} {url:44} {r.status_code} {r.headers.get('content-type', ''):32} {r.text[:120]}")
        # a cursor that decodes to deeply nested JSON
        raw = ("[" * 10000 + "]" * 10000).encode()
        cur = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        r = await client.get("/v1/datasets", params={"cursor": cur})
        print(f"  GET {'deeply nested cursor':45} {r.status_code} {r.headers.get('content-type', ''):32} {r.text[:120]}")
        # PATCH tags with a NaN
        c = await client.post("/v1/datasets", json={"generator": "spiral", "params": {"n_samples": 8}})
        did = c.json()["id"]
        r = await client.patch(f"/v1/datasets/{did}/tags", content=b'{"tags": [NaN]}', headers={"Content-Type": A, "If-Match": c.headers["etag"]})
        print(f"  PATCH {'tags [NaN]':43} {r.status_code} {r.headers.get('content-type', ''):32} {r.text[:160]}")
        # the NaN echo, in full
        r = await client.post("/v1/datasets", content=b'{"generator": "spiral", "params": {"noise": NaN}}', headers={"Content-Type": A})
        print("  NaN echo errors:", json.dumps(r.json().get("errors"))[:400])


def main() -> None:
    src = extract(Path(sys.argv[1]).read_text(encoding="utf-8"), "conditional_datasets.py")
    print("==", sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "conditional_datasets.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("conditional_datasets", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        asyncio.run(drive(mod))


if __name__ == "__main__":
    main()

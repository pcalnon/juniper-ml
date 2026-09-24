#!/usr/bin/env python3
"""Compare the II.11 toy's responses route by route between the base and head primers.

Scratch instrument for round-2 Lane B. Usage: <python with fastapi+httpx> toy_routes_compare.py
Extracts conditional_datasets.py from primer_base.md and primer_head.md (harness convention), drives
each app in-process, and prints per route: status, content-type, content-length == len(body),
ETag == sha256(body)[:32], body parses as strict JSON, and whether base/head bodies are equal as JSON.
Also sends one non-standard JSON body containing NaN, where canonical_json (allow_nan=True) and
JSONResponse (allow_nan=False) diverge.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(doc: Path, tag: str):
    text = doc.read_text(encoding="utf-8")
    m = re.search(r"<!-- example-file: conditional_datasets.py -->\n```python\n(.*?)\n```", text, re.S)
    tmp = Path(tempfile.mkdtemp(dir=HERE / "tmp"))
    p = tmp / "conditional_datasets.py"
    p.write_text(m.group(1) + "\n", encoding="utf-8")
    name = f"cd_{tag}"
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def strict_json(b: bytes):
    def bad(x):
        raise ValueError(f"non-standard constant {x}")

    return json.loads(b, parse_constant=bad)


async def drive(mod) -> dict:
    import httpx

    out = {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mod.create_app()), base_url="http://t") as c:
        body = {"generator": "spiral", "version": 1, "params": {"n_samples": 64, "seed": 7, "label": "café"}, "tags": ["b", "a"]}
        r1 = await c.post("/v1/datasets", json=body)
        r2 = await c.post("/v1/datasets", json=body)
        did = r1.json()["id"]
        r3 = await c.get(f"/v1/datasets/{did}")
        r4 = await c.get(f"/v1/datasets/{did}", headers={"If-None-Match": r3.headers["etag"]})
        r5 = await c.patch(f"/v1/datasets/{did}/tags", json={"tags": ["z"]}, headers={"If-Match": r3.headers["etag"]})
        r6 = await c.patch(f"/v1/datasets/{did}/tags", json={"tags": ["y"]}, headers={"If-Match": r3.headers["etag"]})
        r7 = await c.patch(f"/v1/datasets/{did}/tags", json={"tags": ["y"]})
        r8 = await c.get(f"/v1/datasets/{did}/artifact")
        r9 = await c.get("/v1/datasets")
        try:
            rn = await c.post("/v1/datasets", content=b'{"generator":"spiral","params":{"noise":NaN},"tags":[]}', headers={"content-type": "application/json"})
            try:
                strict_json(rn.content)
                verdict = "strict JSON"
            except Exception as e:  # noqa: BLE001
                verdict = f"NOT JSON ({e})"
            nan = (rn.status_code, rn.headers.get("content-type"), verdict, rn.content[rn.content.find(b'"params"'):][:40])
        except Exception as e:  # noqa: BLE001 - scratch probe: report whatever the app raises
            nan = ("raised", type(e).__name__, str(e)[:120])
        for label, r in (("POST create", r1), ("POST reuse", r2), ("GET", r3), ("GET 304", r4), ("PATCH ok", r5), ("PATCH 412", r6), ("PATCH 428", r7), ("GET artifact", r8), ("GET list", r9)):
            et = r.headers.get("etag")
            want = '"' + hashlib.sha256(r.content).hexdigest()[:32] + '"'
            try:
                parsed = strict_json(r.content) if r.content else None
                pj = "json-ok"
            except Exception:  # noqa: BLE001
                parsed, pj = None, "not-json" if r.headers.get("content-type", "").startswith("application/octet") else "INVALID-JSON"
            out[label] = (r.status_code, r.headers.get("content-type"), r.headers.get("content-length") == str(len(r.content)), (et == want) if et else None, pj, parsed)
        out["NaN POST"] = nan
    return out


def main() -> int:
    base = asyncio.run(drive(load(HERE / "primer_base.md", "base")))
    head = asyncio.run(drive(load(HERE / "primer_head.md", "head")))
    def scrub(v):
        if isinstance(v, dict):
            return {k: scrub(x) for k, x in v.items() if k != "created_at"}
        if isinstance(v, list):
            return [scrub(x) for x in v]
        return v

    for k in base:
        if k == "NaN POST":
            continue
        b, h = base[k], head[k]
        same_json = "n/a" if b[5] is None else (scrub(b[5]) == scrub(h[5]))
        print(f"{k:13s} base: {b[0]} {b[1]!s:28s} len-ok={b[2]} etag==sha(body)={b[3]!s:5s} {b[4]:12s} | head: {h[0]} {h[1]!s:28s} len-ok={h[2]} etag==sha(body)={h[3]!s:5s} {h[4]:12s} | same JSON value: {same_json}")
    print("NaN POST base:", base["NaN POST"])
    print("NaN POST head:", head["NaN POST"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

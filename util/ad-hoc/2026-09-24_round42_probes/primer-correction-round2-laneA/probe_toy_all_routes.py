#!/usr/bin/env python3
"""Lane A r2: independent check of the II.11 toy -- EVERY response that carries an ETag.

Extracts conditional_datasets.py from a primer by locating the example-file marker line and the
next closing fence (own parser, not the PR's regex), imports it, and drives every route:
POST create/reuse, GET metadata (200 and 304), GET artifact (200 and 304), PATCH (200, 412, 428),
list. For each 200 carrying an ETag it compares the tag with '"' + sha256(body)[:32] + '"'.
Usage: <python with fastapi+httpx> probe_toy_all_routes.py <primer.md>
"""
import asyncio
import hashlib
import importlib.util
import sys
from pathlib import Path


def extract(doc: str, name: str) -> str:
    lines = doc.split("\n")
    start = lines.index(f"<!-- example-file: {name} -->")
    assert lines[start + 1].startswith("```"), "marker not followed by fence"
    end = next(i for i in range(start + 2, len(lines)) if lines[i].strip() == "```")
    return "\n".join(lines[start + 2:end]) + "\n"


async def drive(mod):
    import httpx

    rows = []

    def rec(label, r, strong_expected=True):
        et = r.headers.get("etag")
        want = '"' + hashlib.sha256(r.content).hexdigest()[:32] + '"'
        rows.append((label, r.status_code, et, (et == want) if (et and r.status_code == 200) else None, len(r.content), r.headers.get("cache-control")))

    app = mod.create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://toy") as c:
        body = {"generator": "spiral", "version": 1, "params": {"n_samples": 300, "seed": 3, "note": "café"}, "tags": ["b", "a"]}
        cr = await c.post("/v1/datasets", json=body); rec("POST create", cr)
        ru = await c.post("/v1/datasets", json=body); rec("POST reuse", ru)
        did = cr.json()["id"]
        g = await c.get(f"/v1/datasets/{did}"); rec("GET meta", g)
        g304 = await c.get(f"/v1/datasets/{did}", headers={"If-None-Match": g.headers["etag"]}); rec("GET meta INM", g304)
        a = await c.get(f"/v1/datasets/{did}/artifact"); rec("GET artifact", a)
        a304 = await c.get(f"/v1/datasets/{did}/artifact", headers={"If-None-Match": a.headers["etag"]}); rec("GET artifact INM", a304)
        p428 = await c.patch(f"/v1/datasets/{did}/tags", json={"tags": ["z"]}); rec("PATCH no If-Match", p428)
        p412 = await c.patch(f"/v1/datasets/{did}/tags", json={"tags": ["z"]}, headers={"If-Match": '"stale"'}); rec("PATCH stale", p412)
        p200 = await c.patch(f"/v1/datasets/{did}/tags", json={"tags": ["z"]}, headers={"If-Match": g.headers["etag"]}); rec("PATCH current", p200)
        g2 = await c.get(f"/v1/datasets/{did}"); rec("GET meta after PATCH", g2)
        lst = await c.get("/v1/datasets"); rec("GET list", lst)
        rows.append(("PATCH etag == next GET etag", None, None, p200.headers.get("etag") == g2.headers.get("etag"), None, None))
    return rows


def main():
    code = extract(Path(sys.argv[1]).read_text(encoding="utf-8"), "conditional_datasets.py")
    out = Path(__file__).resolve().parent / "_toy_extracted_conditional_datasets.py"
    out.write_text(code, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("conditional_datasets", out)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["conditional_datasets"] = mod
    spec.loader.exec_module(mod)
    for row in asyncio.run(drive(mod)):
        print("  %-28s status=%-4s etag_eq_sha_body=%-5s len=%-5s cc=%s etag=%s" % (row[0], row[1], row[3], row[4], row[5], row[2]))
    out.unlink()


if __name__ == "__main__":
    main()

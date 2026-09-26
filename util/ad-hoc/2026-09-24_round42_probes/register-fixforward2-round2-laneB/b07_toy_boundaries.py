#!/usr/bin/env python3
"""Lane B r2: drive the II.11 toy at one primer revision through every boundary the delta's sentences make claims about.

Usage: <venv python> b07_toy_boundaries.py <primer.md> <label>

Runs under RLIMIT_AS = 2 GiB so no case can exhaust the host's memory (the host's swap is nearly full).
Each case prints: status, content-type, and a short body. Nothing is asserted here; the comparison across
revisions is read by hand (b08 tabulates it).
"""
import asyncio
import base64
import importlib.util
import json
import re
import resource
import sys
import tempfile
from pathlib import Path

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))

H = {"Content-Type": "application/json"}


def extract(doc: str) -> str:
    m = re.search(r"<!-- example-file: conditional_datasets\.py -->\n```python\n(.*?)\n```", doc, re.S)
    return m.group(1) + "\n"


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def post(params_json: str, extra: str = "") -> bytes:
    return ('{"generator": "spiral", "params": ' + params_json + extra + "}").encode("utf-8")


POSTS = [
    # --- n_samples: what int() rejects vs accepts (9880's clause) ---
    ("ns int 64 (control)", post('{"n_samples": 64}')),
    ("ns 1.5", post('{"n_samples": 1.5}')),
    ("ns -5", post('{"n_samples": -5}')),
    ("ns 0", post('{"n_samples": 0}')),
    ('ns "512"', post('{"n_samples": "512"}')),
    ('ns " 512 " (int() strips)', post('{"n_samples": " 512 "}')),
    ('ns "5_12" (int() accepts)', post('{"n_samples": "5_12"}')),
    ('ns arabic-indic digits', post('{"n_samples": "\\u0665\\u0661\\u0662"}')),
    ("ns true", post('{"n_samples": true}')),
    ("ns false", post('{"n_samples": false}')),
    ("ns null", post('{"n_samples": null}')),
    ('ns "abc"', post('{"n_samples": "abc"}')),
    ('ns "1e3"', post('{"n_samples": "1e3"}')),
    ("ns lone surrogate", post('{"n_samples": "\\ud800"}')),
    ("ns NaN", post('{"n_samples": NaN}')),
    ("ns 1e400 (=inf)", post('{"n_samples": 1e400}')),
    ("ns 1e8 (100 MB, allocatable)", post('{"n_samples": 100000000}')),
    ("ns 1e17", post('{"n_samples": 1e17}')),
    ("ns 1e19", post('{"n_samples": 1e19}')),
    ("ns 1e300", post('{"n_samples": 1e300}')),
    ("ns 10**30 (JSON int)", post('{"n_samples": 1000000000000000000000000000000}')),
    # --- other params (5346's divergence, 9880's "any other non-number") ---
    ('seed null', post('{"n_samples": 64, "seed": null}')),
    ('noise "0.1"', post('{"n_samples": 64, "noise": "0.1"}')),
    ('mode "fast"', post('{"n_samples": 64, "mode": "fast"}')),
    ("grid [1,2]", post('{"n_samples": 64, "grid": [1, 2]}')),
    ("nested {a:1}", post('{"n_samples": 64, "nested": {"a": 1}}')),
    ("flag true", post('{"n_samples": 64, "flag": true}')),
    ("string param lone surrogate", post('{"n_samples": 64, "s": "\\ud800"}')),
    ("grid [1, NaN]", post('{"n_samples": 64, "grid": [1, NaN]}')),
    # --- other fields: validation errors whose echo holds something unusual ---
    ("tag lone surrogate", b'{"generator": "spiral", "params": {"n_samples": 64}, "tags": ["\\ud800"]}'),
    ("generator lone surrogate", b'{"generator": "\\ud800", "params": {}}'),
    ("tag NaN", b'{"generator": "spiral", "params": {}, "tags": [NaN]}'),
    ("extra key lone surrogate", b'{"generator": "spiral", "params": {}, "x\\ud800": 1}'),
    # --- body-level ---
    ("body 5000-digit int", b'{"generator": "spiral", "params": {"n_samples": ' + b"1" * 5000 + b"}}"),
    ("body not JSON", b"{not json"),
    ("body JSON list", b"[]"),
    ("body empty", b""),
]


async def main(primer: Path, label: str) -> None:
    import httpx

    src = extract(primer.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "conditional_datasets.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("conditional_datasets", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    rows = []

    def rec(name, r):
        body = r.content[:150].decode("utf-8", "replace").replace("\n", " ")
        rows.append({"case": name, "status": r.status_code, "ctype": r.headers.get("content-type", ""), "body": body})

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mod.create_app(), raise_app_exceptions=False), base_url="http://t") as c:
        for name, body in POSTS:
            rec(name, await c.post("/v1/datasets", content=body, headers=H))
        rec("POST text/plain body", await c.post("/v1/datasets", content=post('{"n_samples": 64}'), headers={"Content-Type": "text/plain"}))
        # ids: is 1.0 a different dataset from 1? (never coerced)
        a = await c.post("/v1/datasets", content=post('{"n_samples": 64, "k": 1}'), headers=H)
        b = await c.post("/v1/datasets", content=post('{"n_samples": 64, "k": 1.0}'), headers=H)
        rows.append({"case": "k:1 vs k:1.0 same id?", "status": f"{a.status_code}/{b.status_code}", "ctype": "", "body": str(a.json().get("id") == b.json().get("id")) if a.status_code < 300 and b.status_code < 300 else "n/a"})
        # --- framework-generated errors (5377-5378, 5433-5434) ---
        rec("GET unknown route", await c.get("/v1/nope"))
        rec("DELETE dataset (405)", await c.delete("/v1/datasets/x"))
        rec("OPTIONS /v1/datasets", await c.options("/v1/datasets"))
        rec("GET limit=abc", await c.get("/v1/datasets?limit=abc"))
        rec("GET limit=0", await c.get("/v1/datasets?limit=0"))
        # --- decode_cursor (5600) ---
        cursors = {
            "cursor deep 10000 balanced": b64(b"[" * 10000 + b"]" * 10000),
            "cursor deep 10000 dict": b64(b'{"a":' * 10000 + b"1" + b"}" * 10000),
            "cursor deep 5000 balanced": b64(b"[" * 5000 + b"]" * 5000),
            "cursor 20000 deep": b64(b"[" * 20000 + b"]" * 20000),
            "cursor non-ascii": "éééé",
            "cursor NaN": b64(b"NaN"),
            "cursor after null": b64(b'{"after": null}'),
            "cursor after lone surrogate": b64(b'{"after": "\\ud800"}'),
            "cursor 5000-digit int": b64(b"1" * 5000),
            "cursor invalid utf-8": b64(b"\xff\xfe\xfd"),
            "cursor utf-16 json": b64('{"after": "x"}'.encode("utf-16")),
            "cursor list": b64(b"[1]"),
            "cursor valid": b64(b'{"after": "spiral-v1-0"}'),
        }
        for name, cur in cursors.items():
            try:
                rec(name, await c.get("/v1/datasets", params={"cursor": cur}))
            except Exception as exc:  # client-side refusal, not the app's answer
                rows.append({"case": name, "status": "client-refused", "ctype": "", "body": repr(exc)[:120]})
    print(json.dumps({"label": label, "rows": rows}))


asyncio.run(main(Path(sys.argv[1]), sys.argv[2]))

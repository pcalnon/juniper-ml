#!/usr/bin/env python3
"""Lane A: what the II.11 toy actually does with create-params inputs the repo probe does not try.

Extracts conditional_datasets.py from a primer (the `<!-- example-file: ... -->` marker the harness uses) and
POSTs each body in-process with raise_app_exceptions=False, printing status, content-type, and for a 201 the
stored n_samples and artifact length. Tests the primer's line-9880 wording "NaN, Infinity or a non-integer
`n_samples` is a 422 problem where it had been a plain-text 500" case by case, at base and head.
Huge values are chosen so the failing arithmetic overflows BEFORE any allocation (no memory is requested).

usage: <venv python> a13_toy_params_edge_probe.py <primer.md> [<primer.md> ...]
"""
import asyncio
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

CASES = [
    ("control n_samples 64", b'{"generator": "spiral", "params": {"n_samples": 64, "noise": 0.05, "seed": 1}}'),
    ("n_samples 2.5 (non-integer number)", b'{"generator": "spiral", "params": {"n_samples": 2.5}}'),
    ("n_samples 64.0 (integral float)", b'{"generator": "spiral", "params": {"n_samples": 64.0}}'),
    ('n_samples "512" (numeric string)', b'{"generator": "spiral", "params": {"n_samples": "512"}}'),
    ('n_samples "abc" (non-numeric)', b'{"generator": "spiral", "params": {"n_samples": "abc"}}'),
    ("n_samples true (bool)", b'{"generator": "spiral", "params": {"n_samples": true}}'),
    ("n_samples -1 (negative)", b'{"generator": "spiral", "params": {"n_samples": -1}}'),
    ("n_samples 1e19 (finite, huge)", b'{"generator": "spiral", "params": {"n_samples": 1e19}}'),
    ("n_samples 1e300 (finite, huge)", b'{"generator": "spiral", "params": {"n_samples": 1e300}}'),
    ("n_samples 10**30 (int, huge)", b'{"generator": "spiral", "params": {"n_samples": 1000000000000000000000000000000}}'),
    ("n_samples 1e400 (parses to inf)", b'{"generator": "spiral", "params": {"n_samples": 1e400}}'),
    ('param "mode": "fast" (string)', b'{"generator": "spiral", "params": {"mode": "fast"}}'),
    ('param "shape": [2, 3] (list)', b'{"generator": "spiral", "params": {"shape": [2, 3]}}'),
    ("param seed 10**30 (int, huge)", b'{"generator": "spiral", "params": {"seed": 1000000000000000000000000000000}}'),
]


def extract(doc: str, name: str) -> str:
    m = re.search(r"<!-- example-file: " + re.escape(name) + r" -->\n```python\n(.*?)\n```", doc, re.S)
    if not m:
        raise SystemExit(f"no example-file block named {name}")
    return m.group(1) + "\n"


async def drive(module):
    import httpx

    app = module.create_app()
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for label, body in CASES:
            r = await client.post("/v1/datasets", content=body, headers={"Content-Type": "application/json"})
            extra = ""
            if r.status_code in (200, 201):
                j = r.json()
                ds = app.state.datasets.get(j.get("id"))
                extra = f"stored n_samples={getattr(ds, 'n_samples', '?')!r} params={getattr(ds, 'params', '?')!r} artifact_len={len(ds.artifact) if ds else '?'}"
            elif r.status_code == 422:
                try:
                    extra = "; ".join(f"{e.get('type')}@{'.'.join(map(str, e.get('loc', [])))}" for e in r.json().get("errors", []))[:120]
                except Exception as exc:  # noqa: BLE001
                    extra = f"(body not JSON: {exc})"
            print(f"  {label:36} {r.status_code} {r.headers.get('content-type', ''):28} {extra}")


for doc in sys.argv[1:]:
    print(f"== {doc}")
    src = extract(Path(doc).read_text(encoding="utf-8"), "conditional_datasets.py")
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "conditional_datasets.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("conditional_datasets", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        asyncio.run(drive(mod))
        del sys.modules[spec.name]

#!/usr/bin/env python3
"""Lane A: what does the head toy's 422 body say for NaN / Infinity / -Infinity params? (line 5631's comment)

usage: <venv python> a15_nan_echo_body.py <primer.md>
"""
import asyncio
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

src = re.search(r"<!-- example-file: conditional_datasets.py -->\n```python\n(.*?)\n```", Path(sys.argv[1]).read_text(encoding="utf-8"), re.S).group(1)


async def main(mod):
    import httpx

    app = mod.create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t") as c:
        for lit in (b"NaN", b"Infinity", b"-Infinity"):
            r = await c.post("/v1/datasets", content=b'{"generator": "spiral", "params": {"noise": ' + lit + b"}}", headers={"Content-Type": "application/json"})
            body = r.json()
            inputs = [e.get("input") for e in body.get("errors", [])]
            print(lit.decode(), r.status_code, r.headers["content-type"], "inputs:", json.dumps(inputs), "raw-has-bare-NaN:", b": NaN" in r.content or b":NaN" in r.content)


with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "conditional_datasets.py"
    p.write_text(src + "\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("conditional_datasets", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    asyncio.run(main(mod))

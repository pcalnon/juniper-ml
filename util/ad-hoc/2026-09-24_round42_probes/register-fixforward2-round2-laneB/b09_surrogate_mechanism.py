#!/usr/bin/env python3
"""Lane B r2: WHY a lone surrogate escapes as a plain-text 500 at head, and whether a stored one poisons the list.

Usage: <venv python> b09_surrogate_mechanism.py <primer.md>

1. Drives POST n_samples="\\ud800" with raise_app_exceptions=True to capture the real exception and its frame.
2. Creates a NEW dataset whose tag is a lone surrogate (tags are list[str], which accepts one), then lists.
3. Shows the one-line remedy: rendering the problem body with json.dumps' default ensure_ascii=True.
"""
import asyncio
import importlib.util
import json
import re
import resource
import sys
import tempfile
import traceback
from pathlib import Path

resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
H = {"Content-Type": "application/json"}


def load(primer: Path, patch_render: bool = False):
    src = re.search(r"<!-- example-file: conditional_datasets\.py -->\n```python\n(.*?)\n```", primer.read_text(encoding="utf-8"), re.S).group(1) + "\n"
    if patch_render:
        old = "        return JSONResponse(body, status_code=self.status, media_type=PROBLEM_JSON, headers=self.headers)"
        assert src.count(old) == 1
        src = src.replace(old, "        return Response(json.dumps(body, allow_nan=False), status_code=self.status, media_type=PROBLEM_JSON, headers=self.headers)")
    tmp = tempfile.mkdtemp(dir=Path(__file__).parent / "tmp")
    p = Path(tmp) / "conditional_datasets.py"
    p.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(f"cd_{patch_render}", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


async def main(primer: Path) -> None:
    import httpx

    mod = load(primer)
    # 1. the mechanism
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mod.create_app(), raise_app_exceptions=True), base_url="http://t") as c:
        try:
            r = await c.post("/v1/datasets", content=b'{"generator": "spiral", "params": {"n_samples": "\\ud800"}}', headers=H)
            print("1. n_samples lone surrogate:", r.status_code, r.headers.get("content-type"))
        except Exception as exc:
            tb = traceback.extract_tb(exc.__traceback__)
            frames = [f"{Path(f.filename).name}:{f.lineno} {f.name}" for f in tb][-4:]
            print("1. n_samples lone surrogate raised:", type(exc).__name__, str(exc)[:110])
            print("   innermost frames:", " <- ".join(reversed(frames)))
    # 2. a stored lone-surrogate tag, then the list
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=mod.create_app(), raise_app_exceptions=False), base_url="http://t") as c:
        made = await c.post("/v1/datasets", content=b'{"generator": "two_moons", "params": {"n_samples": 8}, "tags": ["\\ud800"]}', headers=H)
        print("2. create with a lone-surrogate tag:", made.status_code, made.headers.get("content-type"))
        one = await c.get(f"/v1/datasets/{made.json()['id']}") if made.status_code < 300 else None
        print("   GET that dataset:", one.status_code if one else "n/a", one.headers.get("content-type") if one else "")
        lst = await c.get("/v1/datasets")
        print("   GET /v1/datasets (the list):", lst.status_code, lst.headers.get("content-type"), lst.content[:40])
    # 3. the remedy: to_response renders with ensure_ascii=True
    fixed = load(primer, patch_render=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=fixed.create_app(), raise_app_exceptions=False), base_url="http://t") as c:
        for label, body in (("n_samples", b'{"generator": "spiral", "params": {"n_samples": "\\ud800"}}'), ("string param", b'{"generator": "spiral", "params": {"s": "\\ud800"}}'), ("generator", b'{"generator": "\\ud800"}')):
            r = await c.post("/v1/datasets", content=body, headers=H)
            print(f"3. remedy, lone surrogate in {label}:", r.status_code, r.headers.get("content-type"), json.loads(r.content)["errors"][0]["input"].encode("unicode_escape")[:20])


asyncio.run(main(Path(sys.argv[1])))

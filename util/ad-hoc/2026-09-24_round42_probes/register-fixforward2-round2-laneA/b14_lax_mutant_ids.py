#!/usr/bin/env python3
"""Lane A round 2: under the "lax union" mutant (line 5502 -> dict[str, int | float]) of the head primer, does
"512" become 512 (same dataset id as 512) and true become 1 (same id as 1)? Run with the pinned venv's python."""
import asyncio
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

import httpx

P = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")
lines = P.read_text(encoding="utf-8").split("\n")
lines[5502 - 1] = "    params: dict[str, int | float] = Field(default_factory=dict)"
doc = "\n".join(lines)
src = re.search(r"<!-- example-file: conditional_datasets\.py -->\n```python\n(.*?)\n```", doc, re.S).group(1) + "\n"
d = tempfile.mkdtemp()
f = Path(d) / "conditional_datasets.py"
f.write_text(src, encoding="utf-8")
spec = importlib.util.spec_from_file_location("conditional_datasets", f)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
shutil.rmtree(d)


async def main():
    tr = httpx.ASGITransport(app=m.create_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=tr, base_url="http://t") as c:
        for body in ({"generator": "spiral", "params": {"n_samples": "512"}}, {"generator": "spiral", "params": {"n_samples": 512}},
                     {"generator": "spiral", "params": {"n_samples": True}}, {"generator": "spiral", "params": {"n_samples": 1}}):
            r = await c.post("/v1/datasets", json=body)
            j = r.json()
            print(body["params"], "->", r.status_code, j.get("id"), "stored params", j.get("params"))


asyncio.run(main())

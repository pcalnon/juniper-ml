#!/usr/bin/env python3
"""Lane B: show what the lax-union mutant (head's primer with line 5502 as `dict[str, int | float]`)
does with the inputs the strict schema exists to refuse, next to head's strict schema.

Usage: <venv python> lax_mutant_behaviour.py
"""
import asyncio
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

S = Path(__file__).resolve().parent
PRIMER = S / "head/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
LAX = "    params: dict[str, int | float] = Field(default_factory=dict)"
CASES = [
    ("n_samples \"512\"", b'{"generator": "spiral", "params": {"n_samples": "512"}}'),
    ("n_samples 512", b'{"generator": "spiral", "params": {"n_samples": 512}}'),
    ("n_samples true", b'{"generator": "spiral", "params": {"n_samples": true}}'),
    ("n_samples 1", b'{"generator": "spiral", "params": {"n_samples": 1}}'),
    ("noise NaN", b'{"generator": "spiral", "params": {"noise": NaN}}'),
]


def load(src: str, tag: str):
    # A TemporaryDirectory (not mkdtemp): the module is fully executed before the directory goes.
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "conditional_datasets.py"
        p.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location(f"conditional_datasets_{tag}", p)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    return mod


async def drive(mod, tag):
    import httpx

    app = mod.create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t") as c:
        for label, body in CASES:
            r = await c.post("/v1/datasets", content=body, headers={"Content-Type": "application/json"})
            j = r.json() if r.headers.get("content-type", "").startswith("application/") else {}
            print(f"  {tag:6} {label:18} {r.status_code} id={j.get('id', '-')} params={j.get('params', '-')}")


def main():
    lines = PRIMER.read_text(encoding="utf-8").split("\n")
    doc_strict = "\n".join(lines)
    lines[5502 - 1] = LAX
    doc_lax = "\n".join(lines)
    rx = re.compile(r"<!-- example-file: conditional_datasets.py -->\n```python\n(.*?)\n```", re.S)
    for tag, doc in (("strict", doc_strict), ("lax", doc_lax)):
        mod = load(rx.search(doc).group(1) + "\n", tag)
        asyncio.run(drive(mod, tag))


if __name__ == "__main__":
    main()

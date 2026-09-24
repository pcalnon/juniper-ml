#!/usr/bin/env python3
"""
Probe the API primer's II.11 toy for client-input errors that escape its RFC 9457 error model as a 500.

Project: juniper-ml
Sub-Project: ad-hoc tooling (documentation verification)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- verification for the second round-42 fix-forward of the register and primer
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The II.11 example's module docstring promises "RFC 9457 problem details on every error path". The
post-merge refutation lane of juniper-ml#2080 / #2075
(reports/2026-09-24_defect-register-round-42/ml2080-round1-laneB-refute.md, L4) found that a POST whose
params carry NaN or Infinity -- which Python's JSON parser accepts -- reaches `canonical_json(...,
allow_nan=False)` unrefused and escapes as a text/plain 500.

This extracts `conditional_datasets.py` from a primer file by the harness's own convention (the
`<!-- example-file: conditional_datasets.py -->` marker), POSTs each client-input case in-process with
`raise_app_exceptions=False` (so an unhandled exception is observed as the 500 a real server sends), and
checks that every one is answered 422 with `application/problem+json`. The valid POST is the control and
must be answered 201.

Run it on the primer before the fix (expect the escapes) and after it (expect every case REFUSED).

Usage: <python with fastapi + httpx> 2026-09-24_primer_toy_error_paths_probe.py <primer.md>
"""

import asyncio
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

# (label, raw JSON body). Python's json module parses NaN / Infinity / -Infinity; so does Starlette.
CASES = [
    ("NaN in params", b'{"generator": "spiral", "params": {"noise": NaN}}'),
    ("Infinity in params", b'{"generator": "spiral", "params": {"noise": Infinity}}'),
    ("-Infinity in params", b'{"generator": "spiral", "params": {"noise": -Infinity}}'),
    ("NaN nested in params", b'{"generator": "spiral", "params": {"grid": [1.0, NaN]}}'),
    ("non-integer n_samples", b'{"generator": "spiral", "params": {"n_samples": "abc"}}'),
    ("list n_samples", b'{"generator": "spiral", "params": {"n_samples": [512]}}'),
    ("null n_samples", b'{"generator": "spiral", "params": {"n_samples": null}}'),
]
CONTROL = b'{"generator": "spiral", "params": {"n_samples": 64, "noise": 0.05, "seed": 1}}'


def extract(doc: str, name: str) -> str:
    m = re.search(r"<!-- example-file: " + re.escape(name) + r" -->\n```python\n(.*?)\n```", doc, re.S)
    if not m:
        raise SystemExit(f"no example-file block named {name}")
    return m.group(1) + "\n"


async def drive(module) -> "int | None":
    """Return how many cases escaped, or None when the control POST was not created."""
    import httpx

    app = module.create_app()
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    escaped = 0
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Content-Type": "application/json"}
        control = await client.post("/v1/datasets", content=CONTROL, headers=headers)
        print(f"  {'control (valid POST)':24} {control.status_code} {control.headers.get('content-type', '')}")
        if control.status_code != 201:
            return None
        for label, body in CASES:
            r = await client.post("/v1/datasets", content=body, headers=headers)
            ctype = r.headers.get("content-type", "")
            ok = r.status_code == 422 and ctype.startswith("application/problem+json")
            escaped += not ok
            print(f"  {label:24} {r.status_code} {ctype:28} {'REFUSED' if ok else 'ESCAPED'}")
    return escaped


def main(argv: "list[str]") -> int:
    if len(argv) != 2:
        raise SystemExit(__doc__.split("Usage: ")[1])
    source = extract(Path(argv[1]).read_text(encoding="utf-8"), "conditional_datasets.py")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "conditional_datasets.py"
        path.write_text(source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("conditional_datasets", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        escaped = asyncio.run(drive(module))
    if escaped is None:
        print("RESULT: the control POST was not created, so the probe shows nothing")
        return 2
    print("RESULT:", "every client-input error is a 422 problem" if escaped == 0 else f"{escaped} of {len(CASES)} escaped the error model")
    return 1 if escaped else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

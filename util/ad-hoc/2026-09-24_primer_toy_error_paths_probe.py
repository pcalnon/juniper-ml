#!/usr/bin/env python3
"""
Probe the API primer's II.11 toy: does each client-input case get the answer the primer now says it gets?

Project: juniper-ml
Sub-Project: ad-hoc tooling (documentation verification)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- verification for the second round-42 fix-forward of the register and primer
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The II.11 example's module docstring promised "RFC 9457 problem details on every error path". The
post-merge refutation lane of juniper-ml#2080 / #2075
(reports/2026-09-24_defect-register-round-42/ml2080-round1-laneB-refute.md, L4) found that a POST whose
params carry NaN or Infinity -- which Python's JSON parser accepts -- reached `canonical_json(...,
allow_nan=False)` unrefused and escaped as a text/plain 500.

The second fix-forward restricts `params` to JSON numbers, never coerced, and makes the 422 handler able to
echo a refused NaN. Its pre-PR validation found this probe's first version overclaimed: it tried seven cases
and printed "every client-input error is a 422 problem", while `n_samples: 1.5` is still accepted
(truncated) and a huge `n_samples` still escapes as a plain-text 500. So each case now carries the answer
the corrected primer SAYS it gets, the known limitations included, and the probe checks exactly that. The
deep-cursor case pins the same fix-forward's `RecursionError` catch in `decode_cursor`, which the primer's
own suite has no line to test without moving one.

This extracts `conditional_datasets.py` from a primer file by the harness's own convention (the
`<!-- example-file: conditional_datasets.py -->` marker) and drives each case in-process with
`raise_app_exceptions=False`, so an unhandled exception is observed as the plain-text 500 a real server
sends. The valid POST is the control and must be answered 201.

Run it on the primer after the fix (expect every case AS EXPECTED) and before it (expect mismatches: the
negative control).

Usage: <python with fastapi + httpx> 2026-09-24_primer_toy_error_paths_probe.py <primer.md>
"""

import asyncio
import base64
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

PROBLEM = "application/problem+json"
PLAIN = "text/plain"
JSON = "application/json"

# (label, method, target, raw JSON body or None, expected status, expected content-type prefix).
# Python's json module parses NaN / Infinity / -Infinity; so does Starlette.
# The deep cursor must be BALANCED and 10,000 deep: on CPython 3.13 the C scanner parses a 5,000-deep
# array, and an unbalanced one fails as a JSONDecodeError before it recurses that far (measured
# 2026-09-24). Its URL is about 26.7 KB, which uvicorn's h11 parser refuses before the app sees it; an
# in-process client, or a server without that limit, reaches decode_cursor.
_DEEP_CURSOR = base64.urlsafe_b64encode(b"[" * 10000 + b"]" * 10000).decode("ascii").rstrip("=")
CASES = [
    ("NaN in params", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"noise": NaN}}', 422, PROBLEM),
    ("Infinity in params", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"noise": Infinity}}', 422, PROBLEM),
    ("-Infinity in params", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"noise": -Infinity}}', 422, PROBLEM),
    ("NaN nested in params", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"grid": [1.0, NaN]}}', 422, PROBLEM),
    ("non-numeric n_samples", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": "abc"}}', 422, PROBLEM),
    ("list n_samples", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": [512]}}', 422, PROBLEM),
    ("null n_samples", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": null}}', 422, PROBLEM),
    ("numeric-string n_samples", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": "512"}}', 422, PROBLEM),
    ("boolean n_samples", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": true}}', 422, PROBLEM),
    ("string param", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"mode": "fast"}}', 422, PROBLEM),
    # Known limitations the corrected primer states (lines 5377-5378, 9880): n_samples itself is unchecked.
    ("fractional n_samples (truncated)", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": 1.5}}', 201, JSON),
    ("huge n_samples (known 500)", "POST", "/v1/datasets", b'{"generator": "spiral", "params": {"n_samples": 1e19}}', 500, PLAIN),
    ("cursor nested past the limit", "GET", f"/v1/datasets?cursor={_DEEP_CURSOR}", None, 400, PROBLEM),
]
CONTROL = b'{"generator": "spiral", "params": {"n_samples": 64, "noise": 0.05, "seed": 1}}'


def extract(doc: str, name: str) -> str:
    m = re.search(r"<!-- example-file: " + re.escape(name) + r" -->\n```python\n(.*?)\n```", doc, re.S)
    if not m:
        raise SystemExit(f"no example-file block named {name}")
    return m.group(1) + "\n"


async def drive(module) -> "int | None":
    """Return how many cases were answered other than expected, or None when the control POST was not created."""
    import httpx

    app = module.create_app()
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    unexpected = 0
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Content-Type": "application/json"}
        control = await client.post("/v1/datasets", content=CONTROL, headers=headers)
        print(f"  {'control (valid POST)':34} {control.status_code} {control.headers.get('content-type', '')}")
        if control.status_code != 201:
            return None
        for label, method, target, body, want_status, want_ctype in CASES:
            if method == "GET":
                r = await client.get(target)
            else:
                r = await client.post(target, content=body, headers=headers)
            ctype = r.headers.get("content-type", "")
            ok = r.status_code == want_status and ctype.startswith(want_ctype)
            unexpected += not ok
            print(f"  {label:34} {r.status_code} {ctype:28} {'AS EXPECTED' if ok else f'UNEXPECTED (want {want_status} {want_ctype})'}")
    return unexpected


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
        unexpected = asyncio.run(drive(module))
    if unexpected is None:
        print("RESULT: the control POST was not created, so the probe shows nothing")
        return 2
    print("RESULT:", f"all {len(CASES)} probed cases answered as the primer says" if unexpected == 0 else f"{unexpected} of {len(CASES)} probed cases answered otherwise")
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

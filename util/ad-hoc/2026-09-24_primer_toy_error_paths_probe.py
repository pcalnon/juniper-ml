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
echo a refused NaN. Round 1 of its pre-PR validation found this probe's first version overclaimed: it tried
seven cases and printed "every client-input error is a 422 problem", while `n_samples: 1.5` was still
accepted (truncated) and a huge `n_samples` still escaped as a plain-text 500. Round 2
(register-fixforward2-round2-laneA-reprobe.md, register-fixforward2-round2-laneB-refute.md) found those
limitations better fixed than documented, and found a lone surrogate -- valid JSON, and a valid Python
`str` -- turning the 422 itself into a plain-text 500, because Starlette's `JSONResponse` renders with
`ensure_ascii=False`. The toy now bounds `n_samples` to an integer from 1 to 1,000,000 and renders every
problem body, and the list, ASCII-escaped.

So each case carries the answer the corrected primer SAYS it gets, and the probe checks exactly that. The
primer's own suite pins some of them (lines 6084-6087 and 6117-6120: the deep cursor, "512", `true`, `null`,
1.5, NaN and an echoed surrogate); this keeps those too and adds the ones the suite cannot hold without
moving a line: the bound's edges, surrogates in other fields, and a surrogate STORED in a tag and then
listed, which made every later list a plain-text 500 on `main` as well.

This extracts `conditional_datasets.py` from a primer file by the harness's own convention (the
`<!-- example-file: conditional_datasets.py -->` marker) and drives each case in-process, in order, on one
app, with `raise_app_exceptions=False`, so an unhandled exception is observed as the plain-text 500 a real
server sends. The valid POST is the control and must be answered 201.

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
JSON = "application/json"

# 15,000 balanced levels. CPython 3.13's C JSON scanner raises RecursionError somewhere between 9,000 and
# 10,000 levels, balanced or not; sys.getrecursionlimit()'s 1,000 is not the limit that applies (both
# round-2 lanes measured this on 3.13.13). The suite builds the same cursor without an import, as
# "W1tb" * 5000 + "XV1d" * 5000. Whether a real server delivers a URL this long depends on the server:
# round 2's lane A saw uvicorn with h11 accept a 26.7 KB request written in one piece and refuse it
# written in 8 KB pieces. In-process, the app always sees it.
_DEEP_CURSOR = base64.urlsafe_b64encode(b"[" * 15000 + b"]" * 15000).decode("ascii")
_P = "/v1/datasets"
CASES = [
    # Non-numbers in params: refused by the schema (lines 5498 and 5502), never coerced.
    ("NaN in params", "POST", _P, b'{"generator": "spiral", "params": {"noise": NaN}}', 422, PROBLEM),
    ("Infinity in params", "POST", _P, b'{"generator": "spiral", "params": {"noise": Infinity}}', 422, PROBLEM),
    ("-Infinity in params", "POST", _P, b'{"generator": "spiral", "params": {"noise": -Infinity}}', 422, PROBLEM),
    ("NaN nested in params", "POST", _P, b'{"generator": "spiral", "params": {"grid": [1.0, NaN]}}', 422, PROBLEM),
    ("non-numeric n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": "abc"}}', 422, PROBLEM),
    ("list n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": [512]}}', 422, PROBLEM),
    ("null n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": null}}', 422, PROBLEM),
    ("numeric-string n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": "512"}}', 422, PROBLEM),
    ("boolean n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": true}}', 422, PROBLEM),
    ("string param", "POST", _P, b'{"generator": "spiral", "params": {"mode": "fast"}}', 422, PROBLEM),
    ("null seed", "POST", _P, b'{"generator": "spiral", "params": {"seed": null}}', 422, PROBLEM),
    ("boolean seed", "POST", _P, b'{"generator": "spiral", "params": {"seed": true}}', 422, PROBLEM),
    # n_samples out of range or not an integer: refused by the route's bound (lines 5658-5659).
    ("fractional n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 1.5}}', 422, PROBLEM),
    ("integral-float n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 512.0}}', 422, PROBLEM),
    ("zero n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 0}}', 422, PROBLEM),
    ("negative n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": -5}}', 422, PROBLEM),
    ("n_samples one past the bound", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 1000001}}', 422, PROBLEM),
    ("huge integer n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 10000000000000000000}}', 422, PROBLEM),
    ("huge float n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 1e19}}', 422, PROBLEM),
    ("n_samples at the lower bound", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 1}}', 201, JSON),
    # A lone surrogate: echoed in a 422 (lines 5455, 5464, 5618, 5622), or stored in a tag and listed (5682, 5699).
    ("lone surrogate in a string param", "POST", _P, b'{"generator": "spiral", "params": {"s": "\\ud800"}}', 422, PROBLEM),
    ("lone surrogate as n_samples", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": "\\ud800"}}', 422, PROBLEM),
    ("lone surrogate as generator", "POST", _P, b'{"generator": "\\ud800"}', 422, PROBLEM),
    ("lone surrogate in an extra key", "POST", _P, b'{"generator": "spiral", "x\\ud800": 1}', 422, PROBLEM),
    ("lone surrogate stored in a tag", "POST", _P, b'{"generator": "spiral", "params": {"n_samples": 8}, "tags": ["\\ud800"]}', 201, JSON),
    ("the list after it", "GET", _P, None, 200, JSON),
    # A cursor nested past what the JSON parser allows (line 5600).
    ("cursor nested 15,000 deep", "GET", f"{_P}?cursor={_DEEP_CURSOR}", None, 400, PROBLEM),
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
        control = await client.post(_P, content=CONTROL, headers=headers)
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

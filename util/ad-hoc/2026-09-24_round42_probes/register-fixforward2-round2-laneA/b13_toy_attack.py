#!/usr/bin/env python3
"""Lane A round 2: my own in-process attack on the II.11 toy, for each primer given.

Run with the pinned venv's python:  <venv>/bin/python b13_toy_attack.py <label=primer.md> [<label=primer.md> ...]
Prints a table: case | status + content-type (+ a short body excerpt) per primer.
"""
import asyncio
import base64
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

import httpx

J = {"Content-Type": "application/json"}


def extract(doc: str) -> str:
    m = re.search(r"<!-- example-file: conditional_datasets\.py -->\n```python\n(.*?)\n```", doc, re.S)
    return m.group(1) + "\n"


def deep(n):
    return b"[" * n + b"]" * n


CASES = [
    # (label, method, path, body bytes or None, headers)
    ("control valid", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":64,"noise":0.05,"seed":1}}', J),
    ("seed null", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":64,"seed":null}}', J),
    ("noise \"0.1\"", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"noise":"0.1"}}', J),
    ("nested list [1,2]", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"grid":[1,2]}}', J),
    ("nested object", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"opts":{"a":1}}}', J),
    ("string param", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"mode":"fast"}}', J),
    ("bool param (not n_samples)", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"shuffle":true}}', J),
    ("n_samples \"512\"", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":"512"}}', J),
    ("n_samples \" 512 \"", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":" 512 "}}', J),
    ("n_samples \"1_000\"", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":"1_000"}}', J),
    ("n_samples \"1.5\"", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":"1.5"}}', J),
    ("n_samples true", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":true}}', J),
    ("n_samples false", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":false}}', J),
    ("n_samples \"abc\"", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":"abc"}}', J),
    ("n_samples null", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":null}}', J),
    ("n_samples [512]", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":[512]}}', J),
    ("n_samples {}", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":{}}}', J),
    ("n_samples NaN", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":NaN}}', J),
    ("n_samples 1e400 (inf)", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":1e400}}', J),
    ("n_samples 1.5", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":1.5}}', J),
    ("n_samples -1.5", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":-1.5}}', J),
    ("n_samples 0", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":0}}', J),
    ("n_samples -5", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":-5}}', J),
    ("n_samples 10000000 (10 MB)", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":10000000}}', J),
    ("n_samples 1e19", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":1e19}}', J),
    ("n_samples 1e300", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":1e300}}', J),
    ("n_samples 10**30 int", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":1000000000000000000000000000000}}', J),
    ("noise Infinity", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"noise":Infinity}}', J),
    ("deep list 3000 in params", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"x":' + deep(3000) + b'}}', J),
    ("NaN in tags", "POST", "/v1/datasets", b'{"generator":"spiral","tags":[NaN]}', J),
    ("5000-digit int (body-parse)", "POST", "/v1/datasets", b'{"generator":"spiral","params":{"n_samples":' + b"9" * 5000 + b'}}', J),
    ("invalid UTF-8 body", "POST", "/v1/datasets", b'{"generator":"\xff"}', J),
    ("invalid JSON", "POST", "/v1/datasets", b'{"generator": ', J),
    ("text/plain content-type", "POST", "/v1/datasets", b'{"generator":"spiral"}', {"Content-Type": "text/plain"}),
    ("GET unknown path", "GET", "/v1/nope", None, {}),
    ("DELETE dataset", "DELETE", "/v1/datasets/x", None, {}),
    ("PUT collection", "PUT", "/v1/datasets", None, {}),
    ("GET missing dataset (route 404)", "GET", "/v1/datasets/nope", None, {}),
    ("PATCH tags no If-Match", "PATCH", "/v1/datasets/__ID__/tags", b'{"tags":["a"]}', J),
    ("PATCH tags stale If-Match", "PATCH", "/v1/datasets/__ID__/tags", b'{"tags":["a"]}', {**J, "If-Match": '"stale"'}),
    ("list limit=99999", "GET", "/v1/datasets?limit=99999", None, {}),
    ("bad cursor", "GET", "/v1/datasets?cursor=%%%", None, {}),
    ("cursor nested 10000", "GET", "/v1/datasets?cursor=" + base64.urlsafe_b64encode(deep(10000)).decode().rstrip("="), None, {}),
    ("cursor nested dict+list 10000", "GET", "/v1/datasets?cursor=" + base64.urlsafe_b64encode(b'{"":[' * 5000 + b"1" + b"]}" * 5000).decode().rstrip("="), None, {}),
]


async def run(module):
    app = module.create_app()
    out = {}
    tr = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=tr, base_url="http://t") as c:
        ctl = await c.post("/v1/datasets", content=CASES[0][3], headers=J)
        did = ctl.json().get("id") if ctl.status_code in (200, 201) else "x"
        for label, method, path, body, headers in CASES:
            path = path.replace("__ID__", did)
            r = await c.request(method, path, content=body, headers=headers)
            ct = r.headers.get("content-type", "")
            excerpt = r.text[:90].replace("\n", " ")
            extra = ""
            if r.status_code in (200, 201) and ct.startswith("application/json"):
                try:
                    d = r.json()
                    extra = f" n_samples={d.get('n_samples')} size={d.get('size_bytes')} params={json.dumps(d.get('params'))[:60]}"
                except Exception:
                    pass
            out[label] = f"{r.status_code} {ct.split(';')[0]}{extra}" + ("" if extra else f" | {excerpt}")
    return out


def load(path):
    src = extract(Path(path).read_text(encoding="utf-8"))
    d = tempfile.mkdtemp()
    f = Path(d) / "conditional_datasets.py"
    f.write_text(src, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("conditional_datasets", f)
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    import shutil
    shutil.rmtree(d)
    return m


results = {}
labels = []
for arg in sys.argv[1:]:
    label, path = arg.split("=", 1)
    labels.append(label)
    results[label] = asyncio.run(run(load(path)))
    sys.modules.pop("conditional_datasets", None)

for case in [c[0] for c in CASES]:
    print(f"== {case}")
    for lb in labels:
        print(f"   {lb:9} {results[lb][case]}")

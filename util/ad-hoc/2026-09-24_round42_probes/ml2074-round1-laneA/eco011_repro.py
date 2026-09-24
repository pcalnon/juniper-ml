#!/usr/bin/env python3
"""Lane A: APD-ECO-011 -- canopy (origin/main) in DEMO mode, auth off, in-process TestClient (no port).
A cross-site "simple" POST (Content-Type text/plain, foreign Origin) to /api/dataset/generate.
Upstreams are pointed at a closed port so nothing live is touched."""
import os
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
for k in [k for k in os.environ if k.startswith(("JUNIPER_CANOPY_", "CANOPY_", "JUNIPER_CASCOR", "JUNIPER_DATA", "CASCOR_"))]:
    del os.environ[k]
os.environ.update({
    "JUNIPER_CANOPY_DEMO_MODE": "true",
    "JUNIPER_CANOPY_JUNIPER_DATA_URL": "http://127.0.0.1:1",
    "JUNIPER_CANOPY_RECURRENCE_SERVICE_URL": "",
    "JUNIPER_CANOPY_REQUIRE_AUTH": "false",
})
src = f"{S}/src/juniper-canopy/src"
sys.path.insert(0, src)
os.chdir(src)

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

print("main from", main.__file__)
with TestClient(main.app, raise_server_exceptions=False) as c:
    print("backend_type:", main.backend.backend_type, "| auth enabled:", main.api_key_auth.enabled)
    before = c.get("/api/dataset")
    b = before.json() if before.status_code == 200 else {}
    print("GET /api/dataset before:", before.status_code, {k: (len(v) if isinstance(v, list) else v) for k, v in list(b.items())[:6]})
    r = c.post("/api/dataset/generate", content=b'{"n_samples": 40, "n_spirals": 3}', headers={"Content-Type": "text/plain", "Origin": "https://evil.example"})
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text[:120]
    print("cross-site text/plain POST ->", r.status_code, {k: (len(v) if isinstance(v, list) else v) for k, v in (body.items() if isinstance(body, dict) else [])} if isinstance(body, dict) else body)
    after = c.get("/api/dataset")
    a = after.json() if after.status_code == 200 else {}
    print("GET /api/dataset after:", after.status_code, {k: (len(v) if isinstance(v, list) else v) for k, v in list(a.items())[:6]})
    r2 = c.post("/api/dataset/generate", content=b"not json at all", headers={"Content-Type": "text/plain", "Origin": "https://evil.example"})
    print("non-JSON text/plain POST ->", r2.status_code)

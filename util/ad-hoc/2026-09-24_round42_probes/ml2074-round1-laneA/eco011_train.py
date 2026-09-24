#!/usr/bin/env python3
"""Lane A: in canopy's auth-off demo profile, are the /api/train/* POSTs Origin-checked? In-process only."""
import os
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
for k in [k for k in os.environ if k.startswith(("JUNIPER_CANOPY_", "CANOPY_", "JUNIPER_CASCOR", "JUNIPER_DATA", "CASCOR_"))]:
    del os.environ[k]
os.environ.update({"JUNIPER_CANOPY_DEMO_MODE": "true", "JUNIPER_CANOPY_JUNIPER_DATA_URL": "http://127.0.0.1:1"})
src = f"{S}/src/juniper-canopy/src"
sys.path.insert(0, src)
os.chdir(src)
from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

with TestClient(main.app, raise_server_exceptions=False) as c:
    print("auth enabled:", main.api_key_auth.enabled, "| backend:", main.backend.backend_type)
    for path in ("/api/train/pause", "/api/train/resume", "/api/train/stop"):
        r = c.post(path, content=b"", headers={"Content-Type": "text/plain", "Origin": "https://evil.example"})
        print(f"cross-site text/plain POST {path} ->", r.status_code, r.text[:80])

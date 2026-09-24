"""Lane A: hunk 13 item (3) -- in canopy's auth-off profile, a cross-site "simple" text/plain POST to
/api/dataset/generate regenerates the dataset. Runs the real app (lifespan on, demo backend) with NO
key configured, sends the POST with a foreign Origin and Content-Type text/plain, and reports the
status plus whether the dataset actually changed (n_samples read back from GET /api/dataset).
Usage: canopy_textplain_probe.py <canopy tree>   (JuniperCanopy1 interpreter, libtorch override unset)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

tree = Path(sys.argv[1]).resolve()
src = tree / "src"
for var in ("CANOPY_API_KEY", "CANOPY_API_KEY_FILE", "JUNIPER_CANOPY_REQUIRE_AUTH"):
    os.environ.pop(var, None)
os.chdir(src)
sys.path.insert(0, str(src))

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

cm = TestClient(main.app, raise_server_exceptions=False)
client = cm.__enter__()
print("auth enabled:", main.api_key_auth.enabled)


def sample_count():
    r = client.get("/api/dataset")
    try:
        d = r.json()
    except Exception:
        return r.status_code, None
    for key in ("num_samples", "n_samples", "samples"):
        if isinstance(d, dict) and key in d:
            return r.status_code, d[key]
    if isinstance(d, dict) and isinstance(d.get("inputs"), list):
        return r.status_code, len(d["inputs"])
    return r.status_code, sorted(d)[:8] if isinstance(d, dict) else type(d).__name__


print("before:", sample_count())
resp = client.post(
    "/api/dataset/generate",
    content=json.dumps({"n_samples": 40, "generator": "spiral"}),
    headers={"Content-Type": "text/plain", "Origin": "https://attacker.example"},
)
print("cross-site text/plain POST /api/dataset/generate ->", resp.status_code)
print("after :", sample_count())
try:
    cm.__exit__(None, None, None)
except Exception as exc:
    print("lifespan exit:", type(exc).__name__)
os._exit(0)

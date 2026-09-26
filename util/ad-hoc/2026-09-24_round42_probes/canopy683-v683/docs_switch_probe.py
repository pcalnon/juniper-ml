"""Print _docs_enabled, auth state and /openapi.json status (keyless and keyed) for the tree on PYTHONPATH."""

import os

import main
from fastapi.testclient import TestClient

key = os.environ.get("PROBE_KEY", "")
with TestClient(main.app) as c:
    anon = c.get("/openapi.json").status_code
    keyed = c.get("/openapi.json", headers={"X-API-Key": key}).status_code if key else None
    status_anon = c.get("/api/status").status_code
print(f"docs_enabled={main._docs_enabled} auth_enabled={main.api_key_auth.enabled} /openapi.json keyless={anon} keyed={keyed} /api/status keyless={status_anon}")

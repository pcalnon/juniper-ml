"""Feed juniper-data's REAL GET /v1/generators (via its own app + TestClient) to cascor's merged derive() (scratch)."""

import os
import sys

JD, CASCOR = sys.argv[1], sys.argv[2]
sys.path.insert(0, JD)
sys.path.insert(0, os.path.join(CASCOR, "src"))

import juniper_data  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from juniper_data.api.app import create_app  # noqa: E402

from api.lifecycle.manager import _TruncatableGenerators  # noqa: E402

print("juniper_data from:", juniper_data.__file__)
with TestClient(create_app()) as client:
    resp = client.get("/v1/generators")
    listing = resp.json()
print("status:", resp.status_code, "| entries:", len(listing), "| every entry has a dict 'schema':", all(isinstance(e.get("schema"), dict) for e in listing))
print("names:", [e["name"] for e in listing])
print("derived truncatable set:", sorted(_TruncatableGenerators.derive(listing)))
# is allow_truncation ever reached only through $ref/$defs (which derive() does not follow)?
for e in listing:
    s = e["schema"]
    top = "allow_truncation" in (s.get("properties") or {})
    nested = "allow_truncation" in str(s.get("$defs", {}))
    if top or nested:
        print(f"  {e['name']}: top-level={top} in-$defs={nested}")

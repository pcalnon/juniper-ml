"""Probe juniper-data's GET /v1/generators in-process and dump the JSON (read-only)."""
import json
import os
import sys

sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-data")
out = sys.argv[1]
from juniper_data.api.routes.generators import GENERATOR_REGISTRY  # noqa: E402

direct = {}
for name, info in GENERATOR_REGISTRY.items():
    sch = info["params_class"].model_json_schema()
    props = sch.get("properties") or {}
    direct[name] = "allow_truncation" in props
print("direct model_json_schema truncatable:", sorted(n for n, t in direct.items() if t))
print("registry size:", len(GENERATOR_REGISTRY), sorted(GENERATOR_REGISTRY))

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402

os.environ.pop("JUNIPER_DATA_API_KEYS", None)
app = create_app()
with TestClient(app) as c:
    r = c.get("/v1/generators")
    print("status", r.status_code)
    body = r.json()
    print("type", type(body).__name__, "len", len(body) if isinstance(body, list) else None)
    if isinstance(body, list):
        print("keys of first:", sorted(body[0].keys()))
        print("available flags:", {e["name"]: e.get("available") for e in body})
        print("with schema key:", sum(1 for e in body if "schema" in e), "with params_schema key:", sum(1 for e in body if "params_schema" in e))
    else:
        print(body)
    with open(out, "w") as fh:
        json.dump(body, fh)

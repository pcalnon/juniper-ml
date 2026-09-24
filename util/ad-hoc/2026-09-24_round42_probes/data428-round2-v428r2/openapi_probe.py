"""Inspect the published OpenAPI for the D-B routes (validator scratch)."""

import json
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr")
from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

app = create_app(settings=Settings(storage_path=sys.argv[1], api_keys=["k"], rate_limit_enabled=False, metrics_enabled=False))
spec = app.openapi()
for path in ("/v1/datasets/{dataset_id}", "/v1/datasets/latest", "/v1/datasets/{dataset_id}/artifact", "/v1/datasets/{dataset_id}/tags", "/v1/datasets/{dataset_id}/access"):
    for method, op in spec["paths"][path].items():
        print("=" * 20, method.upper(), path, op.get("operationId"))
        print("description mentions strong:", "strong" in (op.get("description") or "").lower(), "| weak:", "weak" in (op.get("description") or "").lower())
        for line in (op.get("description") or "").splitlines():
            if "ETag" in line or "strong" in line.lower():
                print("   desc:", line.strip())
        print("params:", [(p["name"], p["in"], p["schema"]) for p in op.get("parameters", [])])
        for code, resp in op["responses"].items():
            print("  ", code, resp.get("description"), list((resp.get("headers") or {}).keys()), list((resp.get("content") or {}).keys()))
print("components with counters:", [name for name, s in spec["components"]["schemas"].items() if "access_count" in json.dumps(s)])
print("DatasetMeta in components:", "DatasetMeta" in spec["components"]["schemas"], "| PublicDatasetMeta:", "PublicDatasetMeta" in spec["components"]["schemas"])

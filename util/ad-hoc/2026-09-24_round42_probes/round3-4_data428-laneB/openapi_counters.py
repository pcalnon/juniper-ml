"""Lane B: does the PublicDatasetMeta OpenAPI schema carry a counter PROPERTY, or only mention one?"""

import sys

from juniper_data.api.app import create_app
from juniper_data.api.settings import Settings

app = create_app(settings=Settings(storage_path=sys.argv[1], api_keys=["k"], rate_limit_enabled=False, metrics_enabled=False))
spec = app.openapi()
for name in ("PublicDatasetMeta", "DatasetAccessStats"):
    s = spec["components"]["schemas"][name]
    props = sorted(s.get("properties", {}))
    print(name, "counter properties:", [p for p in props if p in ("access_count", "last_accessed_at")])
    print("   description mentions access_count:", "access_count" in (s.get("description") or ""))

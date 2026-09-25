#!/usr/bin/env python3
"""In-process probe (no port, no lifespan) of the REAL juniper-data app: a lone surrogate in a typed body field.

Run with /opt/miniforge3/envs/JuniperData/bin/python -s. Imports juniper_data from the main checkout (read-only);
storage points at this lane's scratch directory; every Sentry DSN variable is set to "" before import.
"""
import asyncio
import os
import sys
from pathlib import Path

SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hv2/laneF2/datastore")
SCRATCH.mkdir(parents=True, exist_ok=True)
for var in ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN"):
    os.environ[var] = ""
os.environ["JUNIPER_DATA_STORAGE_PATH"] = str(SCRATCH)
os.environ["JUNIPER_DATA_METRICS_ENABLED"] = "false"
os.environ.pop("JUNIPER_DATA_API_KEYS", None)
sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-data")

import fastapi  # noqa: E402
import httpx  # noqa: E402
import starlette  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402


async def main():
    app = create_app(Settings())
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    print("fastapi", fastapi.__version__, "starlette", starlette.__version__)
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        for label, raw in (
            ("control ttl_seconds='abc'", b'{"generator": "spiral", "ttl_seconds": "abc"}'),
            ("surrogate ttl_seconds", b'{"generator": "spiral", "ttl_seconds": "\\ud800"}'),
        ):
            r = await c.post("/v1/datasets", content=raw, headers={"content-type": "application/json"})
            print(f"{label:28} {r.status_code} {r.headers.get('content-type')} {r.text[:90]!r}")


asyncio.run(main())

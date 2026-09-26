"""Lane P (round 2) read-only probe: does the serve script's interpreter give the same 422-echo outcome as data's locked pair?

The serve script (#2097, util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash) runs
/opt/miniforge3/envs/JuniperData/bin/python. Round 3 (handoff-2fba4397-round3-laneF-reprobe.md) measured
juniper-data on the LOCKED pair (fastapi 0.141.1 / starlette 1.6.0) in-process. This re-runs the same three
requests in-process under the serve script's interpreter. No port, no Sentry init, every DSN variable "".
Run with -B -s so no bytecode is written and no user site-packages leak in.
"""
import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE = HERE / "datastore"
STORE.mkdir(exist_ok=True)
for var in ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN"):
    os.environ[var] = ""
os.environ["JUNIPER_DATA_STORAGE_PATH"] = str(STORE)
os.environ["JUNIPER_DATA_METRICS_ENABLED"] = "false"
os.environ["JUNIPER_DATA_RATE_LIMIT_ENABLED"] = "false"
for var in ("JUNIPER_DATA_API_KEYS", "JUNIPER_DATA_API_KEYS_FILE", "JUNIPER_DATA_REQUIRE_AUTH"):
    os.environ.pop(var, None)
sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-data")

import fastapi  # noqa: E402
import httpx  # noqa: E402
import starlette  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

print("fastapi", fastapi.__version__, "starlette", starlette.__version__, "python", sys.version.split()[0])
print("juniper_data from", sys.modules["juniper_data"].__file__)


async def main() -> None:
    sur = b'"\\ud800"'
    app = create_app(Settings())
    t = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=t, base_url="http://t") as c:
        for label, raw in (
            ("data ctl ttl_seconds='abc'", b'{"generator": "spiral", "ttl_seconds": "abc"}'),
            ("data sur ttl_seconds=D800", b'{"generator": "spiral", "ttl_seconds": ' + sur + b"}"),
            ("data sur generator=D800", b'{"generator": ' + sur + b"}"),
        ):
            r = await c.post("/v1/datasets", content=raw, headers={"content-type": "application/json"})
            print(f"{label:30} {r.status_code} {r.headers.get('content-type')} {r.text[:70]!r}")


asyncio.run(main())

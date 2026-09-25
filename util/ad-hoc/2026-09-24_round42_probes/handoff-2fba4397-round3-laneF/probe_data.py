"""Lane D round-3 probe: the REAL juniper-data app, in-process (no port), with its lifespan.

Interpreter: the primer venv (CPython 3.13.13; fastapi 0.141.1 / starlette 1.6.0, data's locked pair).
Missing juniper-data deps come from JuniperCanopy1's site-packages, appended AFTER the venv's, and
cachetools (pure Python) from JuniperData's, appended last. juniper_data is imported from the main
checkout (HEAD 1afc348, whose api/app.py equals 0f0f7e0e's). Run with -B: no bytecode is written.

Sentry: every DSN variable is "" (so data's own configure_sentry is a no-op). The probe itself calls
sentry_sdk.init with a dummy localhost DSN and a CAPTURING transport, so nothing leaves the process,
and counts envelope items. A default-FastAPI 500 is the positive control for the harness.
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
os.environ.pop("JUNIPER_DATA_API_KEYS", None)
sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-data")
sys.path.append("/opt/miniforge3/envs/JuniperCanopy1/lib/python3.13/site-packages")
sys.path.append("/opt/miniforge3/envs/JuniperData/lib/python3.14t/site-packages")

import fastapi  # noqa: E402
import httpx  # noqa: E402
import sentry_sdk  # noqa: E402
import starlette  # noqa: E402
from sentry_sdk.transport import Transport  # noqa: E402

ITEMS: list[str] = []


class CaptureTransport(Transport):
    def capture_envelope(self, envelope):  # noqa: D401
        for item in envelope.items:
            ITEMS.append(item.type or item.headers.get("type", "?"))


sentry_sdk.init(dsn="https://public@127.0.0.1:9/1", transport=CaptureTransport, send_default_pii=False, enable_logs=True, traces_sample_rate=0.0)

from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

print("fastapi", fastapi.__version__, "starlette", starlette.__version__, "sentry_sdk", sentry_sdk.VERSION, "python", sys.version.split()[0])
print("juniper_data from", sys.modules["juniper_data"].__file__)


class B(BaseModel):
    n: int


def toy() -> FastAPI:
    app = FastAPI()

    @app.post("/x")
    async def x(b: B) -> dict:
        return {"ok": True}

    return app


def snap() -> dict:
    sentry_sdk.flush(timeout=2)
    out: dict[str, int] = {}
    for t in ITEMS:
        out[t] = out.get(t, 0) + 1
    return out


async def main() -> None:
    SUR = b'"\\ud800"'
    t = httpx.ASGITransport(app=toy(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=t, base_url="http://t") as c:
        r = await c.post("/x", content=b'{"n": ' + SUR + b"}", headers={"content-type": "application/json"})
        print(f"{'CONTROL toy default':30} {r.status_code} {r.headers.get('content-type')} {r.text[:50]!r} sentry={snap()}")
    ITEMS.clear()
    app = create_app(Settings())
    t = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=t, base_url="http://t") as c:
        snap()
        ITEMS.clear()
        for label, raw in (
            ("data ctl ttl_seconds='abc'", b'{"generator": "spiral", "ttl_seconds": "abc"}'),
            ("data sur ttl_seconds=D800", b'{"generator": "spiral", "ttl_seconds": ' + SUR + b"}"),
            ("data sur generator=D800", b'{"generator": ' + SUR + b"}"),
        ):
            r = await c.post("/v1/datasets", content=raw, headers={"content-type": "application/json"})
            print(f"{label:30} {r.status_code} {r.headers.get('content-type')} {r.text[:70]!r} sentry={snap()}")
            ITEMS.clear()
    sentry_sdk.capture_message("lane D harness positive control")
    print("harness control capture_message ->", snap())


asyncio.run(main())

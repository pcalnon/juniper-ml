"""Lane D round-3 probe: the REAL juniper-cascor app, in-process (no port), WITHOUT its lifespan.

Interpreter: JuniperCascor1 (its own env). cascor is imported from the main checkout (== origin/main 7f4a7213).
Run with -B: no bytecode written. JUNIPER_CASCOR_LOG_DIR points into this lane's scratch.
Every DSN variable is ""; the probe's own sentry_sdk.init uses a dummy localhost DSN and a capturing
transport (nothing leaves the process). A default-FastAPI 500 is the harness's positive control.
"""
import asyncio
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE / "cascorlogs"
LOGS.mkdir(exist_ok=True)
for var in ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN"):
    os.environ[var] = ""
os.environ["JUNIPER_CASCOR_LOG_DIR"] = str(LOGS)
sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-cascor/src")

import fastapi  # noqa: E402
import httpx  # noqa: E402
import sentry_sdk  # noqa: E402
import starlette  # noqa: E402
from sentry_sdk.transport import Transport  # noqa: E402

ITEMS: list[str] = []


class CaptureTransport(Transport):
    def capture_envelope(self, envelope):
        for item in envelope.items:
            ITEMS.append(item.type or "?")


sentry_sdk.init(dsn="https://public@127.0.0.1:9/1", transport=CaptureTransport, send_default_pii=False, traces_sample_rate=0.0)

from fastapi import FastAPI  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from api.app import create_app  # noqa: E402

print("fastapi", fastapi.__version__, "starlette", starlette.__version__, "sentry_sdk", sentry_sdk.VERSION, "python", sys.version.split()[0])


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
    ITEMS.clear()
    return out


async def main() -> None:
    SUR = b'"\\ud800"'
    t = httpx.ASGITransport(app=toy(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=t, base_url="http://t") as c:
        r = await c.post("/x", content=b'{"n": ' + SUR + b"}", headers={"content-type": "application/json"})
        print(f"{'CONTROL toy default':28} {r.status_code} {r.headers.get('content-type')} {r.text[:50]!r} sentry={snap()}")
    app = create_app()
    t = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=t, base_url="http://t") as c:
        for label, raw in (
            ("cascor ctl input_size='abc'", b'{"input_size": "abc"}'),
            ("cascor sur input_size=D800", b'{"input_size": ' + SUR + b"}"),
        ):
            r = await c.post("/v1/network", content=raw, headers={"content-type": "application/json"})
            print(f"{label:28} {r.status_code} {r.headers.get('content-type')} {r.text[:150]!r} sentry={snap()}")


asyncio.run(main())

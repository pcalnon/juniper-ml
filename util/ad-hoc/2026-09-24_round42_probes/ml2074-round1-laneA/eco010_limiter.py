#!/usr/bin/env python3
"""Lane A: APD-ECO-010 -- does a refused key reach canopy's rate limiter? In-process (TestClient,
no port), canopy origin/main's SecurityMiddleware + APIKeyAuth + real RateLimiter (limit 3/min)."""
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
sys.path.insert(0, f"{S}/src/juniper-canopy/src")

from starlette.applications import Starlette  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402
from starlette.routing import Route  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

import middleware  # noqa: E402
import security  # noqa: E402

print("from", middleware.__file__)


class CountingLimiter(security.RateLimiter):
    calls = 0

    async def __call__(self, request, api_key=None):  # same signature the middleware uses
        CountingLimiter.calls += 1
        return await super().__call__(request, api_key)


async def ok(request):
    return JSONResponse({"ok": True})


app = Starlette(routes=[Route("/api/thing", ok, methods=["GET"])])
limiter = CountingLimiter(requests_per_minute=3, window_seconds=60, enabled=True)
app.add_middleware(middleware.SecurityMiddleware, api_key_auth=security.APIKeyAuth(["right-key"]), rate_limiter=limiter)
c = TestClient(app)
wrong = [c.get("/api/thing", headers={"X-API-Key": f"wrong-{i}"}).status_code for i in range(10)]
print("10 wrong-key requests ->", wrong, "| limiter invoked:", CountingLimiter.calls)
missing = [c.get("/api/thing").status_code for _ in range(5)]
print("5 key-less requests   ->", missing, "| limiter invoked:", CountingLimiter.calls)
right = [c.get("/api/thing", headers={"X-API-Key": "right-key"}).status_code for _ in range(5)]
print("5 right-key requests  ->", right, "| limiter invoked:", CountingLimiter.calls)

"""Independent route sweep for the #678 CHANGELOG counts (validator's own, not the builder's).

Run with cwd = <tree>/src (runpy.sh does this). Env decides the key under test.

For every route in ``main.app.routes`` it records:
  * kind (http / websocket / mount), path template, methods;
  * the middleware tier, by calling SecurityMiddleware's OWN ``_is_exempt`` / ``_is_key_exempt``
    on a concrete path (so the classification is the code's, not a re-implementation);
  * an EMPIRICAL keyless request through TestClient with the real lifespan, and the status +
    detail it got. A 401 whose detail is the middleware's "Missing API key" string is the
    middleware refusing; anything else reached past the middleware.

Output: one JSON document on stdout.
"""

import json
import os
import re
import sys
import threading

os.environ.setdefault("JUNIPER_CANOPY_DEMO_MODE", "1")
os.environ.setdefault("JUNIPER_SKIP_DEP_FLOOR_CHECK", "1")

import main  # noqa: E402
from fastapi.routing import APIRoute, APIWebSocketRoute  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.routing import Mount, Route, WebSocketRoute  # noqa: E402

import middleware  # noqa: E402

mw = middleware.SecurityMiddleware.__new__(middleware.SecurityMiddleware)

PARAM = re.compile(r"\{([^}:]+)(?::([^}]+))?\}")


def concrete(path: str) -> str:
    def sub(m):
        conv = m.group(2) or "str"
        return "0" if conv in ("int", "float") else ("x/y" if conv == "path" else "x")

    return PARAM.sub(sub, path)


rows = []
for r in main.app.routes:
    if isinstance(r, (APIWebSocketRoute, WebSocketRoute)):
        rows.append({"kind": "websocket", "path": r.path, "methods": []})
        continue
    if isinstance(r, Mount):
        rows.append({"kind": "mount", "path": r.path, "methods": []})
        continue
    if isinstance(r, (APIRoute, Route)):
        methods = sorted(m for m in (r.methods or []) if m not in ("HEAD", "OPTIONS"))
        rows.append({"kind": "http", "path": r.path, "methods": methods, "api_route": isinstance(r, APIRoute)})
        continue
    rows.append({"kind": type(r).__name__, "path": getattr(r, "path", None), "methods": []})

pairs = []
for row in rows:
    if row["kind"] != "http":
        continue
    for m in row["methods"]:
        cpath = concrete(row["path"])
        tier = "exempt" if mw._is_exempt(cpath) else ("key_exempt" if mw._is_key_exempt(cpath) else "key_gated")
        pairs.append({"method": m, "path": row["path"], "concrete": cpath, "tier": tier, "parameterized": "{" in row["path"]})

results = {}


def probe(client, p):
    try:
        if p["method"] == "GET":
            resp = client.get(p["concrete"])
        elif p["method"] == "DELETE":
            resp = client.delete(p["concrete"])
        else:
            # An empty JSON object: routes with a body model 422 in validation, i.e. AFTER the
            # middleware, without running handler side effects.
            resp = client.request(p["method"], p["concrete"], json={})
        detail = None
        try:
            body = resp.json()
            detail = body.get("detail") if isinstance(body, dict) else None
        except Exception:  # noqa: BLE001
            pass
        if isinstance(detail, (list, dict)):
            detail = "<validation>"
        return resp.status_code, detail
    except Exception as exc:  # noqa: BLE001
        return "EXC", f"{type(exc).__name__}: {str(exc)[:120]}"


only_gated = os.environ.get("SWEEP_ONLY_GATED", "1") == "1"
with TestClient(main.app, raise_server_exceptions=False) as client:
    for p in pairs:
        if only_gated and p["tier"] != "key_gated":
            # still probe GETs of the other tiers; skip their state-changing calls
            if p["method"] != "GET":
                continue
        holder = {}

        def go():
            holder["r"] = probe(client, p)

        t = threading.Thread(target=go, daemon=True)
        t.start()
        t.join(20)
        results[f'{p["method"]} {p["path"]}'] = holder.get("r", ("TIMEOUT", None))

from security import get_api_key_auth  # noqa: E402

out = {
    "auth_enabled_main": main.api_key_auth.enabled,
    "auth_enabled_singleton": get_api_key_auth().enabled,
    "docs_enabled": main._docs_enabled,
    "routes": rows,
    "pairs": [dict(p, status=results.get(f'{p["method"]} {p["path"]}', (None, None))[0], detail=results.get(f'{p["method"]} {p["path"]}', (None, None))[1]) for p in pairs],
}
with open(os.environ["SWEEP_OUT"], "w") as fh:
    json.dump(out, fh, indent=1, default=str)

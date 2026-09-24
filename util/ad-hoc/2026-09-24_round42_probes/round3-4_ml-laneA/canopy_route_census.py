"""Lane A: re-derive the register's "55 method-path pairs, 27 of them state-changing, and the 25
parameterless GETs all 401 before the fix and 200 after" (hunk 13) from canopy's real app.

Usage: canopy_route_census.py <canopy tree>   (run with the JuniperCanopy1 interpreter)

Sets a whitespace-only CANOPY_API_KEY BEFORE importing the app, enumerates app.routes, classifies
each HTTP method-path pair with the SecurityMiddleware's OWN exemption predicates, then sends each
parameterless key-gated GET with no key through a TestClient (no lifespan) and tallies statuses.
"""

from __future__ import annotations

import collections
import os
import sys
from pathlib import Path

tree = Path(sys.argv[1]).resolve()
src = tree / "src"
os.environ["CANOPY_API_KEY"] = "   "
os.environ.pop("CANOPY_API_KEY_FILE", None)
os.environ.pop("JUNIPER_SKIP_AUTH_POSTURE_CHECK", None)
os.chdir(src)
sys.path.insert(0, str(src))

import main  # noqa: E402
from fastapi.routing import APIRoute  # noqa: E402
from starlette.routing import Route  # noqa: E402

import middleware as mw  # noqa: E402

app = main.app
print("security module :", sys.modules["security"].__file__)
print("auth enabled    :", main.api_key_auth.enabled if hasattr(main, "api_key_auth") else "n/a")

probe = mw.SecurityMiddleware.__new__(mw.SecurityMiddleware)
pairs = []
for r in app.routes:
    if isinstance(r, (APIRoute, Route)) and getattr(r, "methods", None):
        for m in sorted(r.methods):
            if m == "HEAD":
                continue
            exempt = probe._is_exempt(r.path)
            key_exempt = probe._is_key_exempt(r.path)
            pairs.append((m, r.path, exempt, key_exempt))

gated = [(m, p) for m, p, ex, kex in pairs if not ex and not kex]
state = [(m, p) for m, p in gated if m in ("POST", "PUT", "PATCH", "DELETE")]
gets = [(m, p) for m, p in gated if m == "GET"]
param_free_gets = [(m, p) for m, p in gets if "{" not in p]
print(f"HTTP method-path pairs (HEAD excluded): {len(pairs)}")
print(f"  exempt: {sum(1 for x in pairs if x[2])}, key-exempt: {sum(1 for x in pairs if (not x[2]) and x[3])}")
print(f"KEY-GATED pairs: {len(gated)}  | state-changing: {len(state)} | GET: {len(gets)} | parameterless GET: {len(param_free_gets)}")
print("methods:", dict(collections.Counter(m for m, _ in gated)))

from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)
tally = collections.Counter()
detail = []
for m, p in param_free_gets:
    try:
        resp = client.get(p)
        tally[resp.status_code] += 1
        detail.append((resp.status_code, p))
    except Exception as exc:  # pragma: no cover - diagnostic
        tally[type(exc).__name__] += 1
        detail.append((type(exc).__name__, p))
print("parameterless key-gated GET, no key, whitespace-only CANOPY_API_KEY:", dict(tally))
print("parameterless gated GET paths:", sorted(p for _, p in param_free_gets))
for status, p in sorted(detail, key=lambda t: str(t[0])):
    if status not in (200, 401):
        print("   non-200/401:", status, p)

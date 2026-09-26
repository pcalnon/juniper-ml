"""Does canopy main still raise on a non-ASCII key / CSRF token / internal header? (read-only probe)"""
import asyncio
import sys
import traceback

sys.path.insert(0, sys.argv[1])  # canopy src/

import security  # noqa: E402  canopy src/security.py
from starlette.requests import Request  # noqa: E402

print("canopy security from", security.__file__)

auth = security.APIKeyAuth(["real-configured-key"])
for presented in ["\xa0", "\x85", "real-configured-key\xa0", "ascii-wrong"]:
    try:
        print(f"APIKeyAuth.validate({presented!r}) -> {auth.validate(presented)}")
    except Exception as exc:  # noqa: BLE001
        tb = traceback.extract_tb(exc.__traceback__)[-1]
        print(f"APIKeyAuth.validate({presented!r}) RAISED {type(exc).__name__}: {exc}  at {tb.filename.rsplit('/', 1)[-1]}:{tb.lineno}")

# The X-Canopy-Internal compare in RateLimiter.__call__
limiter = security.RateLimiter(requests_per_minute=100, enabled=True)
scope = {"type": "http", "method": "GET", "path": "/api/x", "headers": [(security.INTERNAL_REQUEST_HEADER.lower().encode(), b"\xa0")], "client": ("1.2.3.4", 1)}
try:
    asyncio.run(limiter(Request(scope), None))
    print("RateLimiter(X-Canopy-Internal: \\xa0) -> no raise")
except Exception as exc:  # noqa: BLE001
    tb = traceback.extract_tb(exc.__traceback__)[-1]
    print(f"RateLimiter(X-Canopy-Internal: \\xa0) RAISED {type(exc).__name__}: {exc}  at {tb.filename.rsplit('/', 1)[-1]}:{tb.lineno}")

# CSRF store
import csrf  # noqa: E402

store = csrf.get_csrf_store() if hasattr(csrf, "get_csrf_store") else csrf.CSRFTokenStore()
minted = store.mint() if hasattr(store, "mint") else store.generate()
for token in ["\xe9", 1]:
    try:
        print(f"csrf.validate({token!r}) -> {store.validate(token)}")
    except Exception as exc:  # noqa: BLE001
        tb = traceback.extract_tb(exc.__traceback__)[-1]
        frame_locals = sorted(exc.__traceback__.tb_next.tb_frame.f_locals) if exc.__traceback__.tb_next else []
        print(f"csrf.validate({token!r}) RAISED {type(exc).__name__}: {exc}  at {tb.filename.rsplit('/', 1)[-1]}:{tb.lineno}; frame locals: {frame_locals}")

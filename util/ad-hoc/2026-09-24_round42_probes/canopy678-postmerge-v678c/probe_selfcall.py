"""Does a dashboard self-call survive a whitespace-only CANOPY_API_KEY? (requests header validation)"""

import os

import requests

from frontend import internal_api

for value in (" \t ", "", "\xa0"):
    os.environ["CANOPY_API_KEY"] = value
    internal_api._canopy_api_key.cache_clear()
    headers = internal_api.internal_api_headers()
    try:
        req = requests.Request("GET", "http://127.0.0.1:9/api/status", headers=headers).prepare()
        print(repr(value), "-> prepared OK; X-API-Key sent:", "X-API-Key" in req.headers)
    except Exception as exc:  # noqa: BLE001
        print(repr(value), "->", type(exc).__name__, str(exc)[:160])

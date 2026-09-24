"""Lane A launcher: serve juniper-data (the git-archive extraction of origin/main) on 127.0.0.1:<port>.

usage: serve_jd.py {localfs|memory} <port> <storage_dir>

``localfs`` is the service exactly as its lifespan builds it (LocalFSDatasetStore(storage_path)).
``memory`` swaps the lifespan's store factory for InMemoryDatasetStore -- the lifespan looks the
name up in the app module at startup, so patching the module attribute is enough.
No API keys, no auth requirement, no rate limit: the caller strips every JUNIPER* env var.
"""

import sys

mode, port, storage = sys.argv[1], int(sys.argv[2]), sys.argv[3]

import juniper_data  # noqa: E402
import juniper_data.api.app as appmod  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

assert "/scratchpad/r42/primer-laneA/jd-main/" in juniper_data.__file__, juniper_data.__file__

if mode == "memory":
    from juniper_data.storage.memory import InMemoryDatasetStore

    appmod.LocalFSDatasetStore = lambda _path: InMemoryDatasetStore()  # type: ignore[assignment]
elif mode != "localfs":
    raise SystemExit(f"unknown mode {mode!r}")

settings = Settings(storage_path=storage, api_keys=None, require_auth=False, rate_limit_enabled=False)
app = appmod.create_app(settings)

import uvicorn  # noqa: E402

uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

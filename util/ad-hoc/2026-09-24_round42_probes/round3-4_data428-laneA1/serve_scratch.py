"""Lane A1: serve juniper-data AS MERGED (3a76a4c, extracted with git archive) on a scratch port.

The JuniperData env has an EDITABLE install of the main juniper-data checkout, so a plain
``uvicorn juniper_data.api.app:get_app`` would serve whatever that checkout holds. This puts
the scratch tree first on sys.path and REFUSES to start unless the imported package is the
scratch copy. It runs uvicorn the way ``python -m juniper_data`` does (factory, defaults:
http=auto -> httptools, loop=auto -> uvloop, one worker, access log on), and prints the
interpreter's GIL state after httptools/uvloop are imported, because this env is a
free-threaded build and those extensions re-enable the GIL.

Settings come ONLY from the explicit environment the caller passes (run it under ``env -i``).
"""

import sys

TREE = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1/tree-3a76a4c"
sys.path.insert(0, TREE)

import juniper_data  # noqa: E402

if not juniper_data.__file__.startswith(TREE + "/"):
    raise SystemExit(f"refusing to serve: juniper_data imported from {juniper_data.__file__}")
import juniper_data.api.http_cache as hc  # noqa: E402

assert hc.__file__.startswith(TREE + "/"), hc.__file__
import httptools  # noqa: E402,F401
import uvicorn  # noqa: E402
import uvloop  # noqa: E402,F401

port = int(sys.argv[1])
print(f"[serve_scratch] juniper_data={juniper_data.__file__} http_cache={hc.__file__}", flush=True)
print(f"[serve_scratch] python={sys.version.split()[0]} gil_enabled={sys._is_gil_enabled()} uvicorn={uvicorn.__version__} httptools={httptools.__version__}", flush=True)
print(f"[serve_scratch] _ENTITY_TAG_LIST={hc._ENTITY_TAG_LIST.pattern} cap={hc.MAX_PRECONDITION_FIELD_LENGTH}", flush=True)
uvicorn.run("juniper_data.api.app:get_app", factory=True, host="127.0.0.1", port=port, log_level="info")

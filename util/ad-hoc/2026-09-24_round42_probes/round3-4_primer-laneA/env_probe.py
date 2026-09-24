"""Lane A env probe: which interpreter, numpy, zlib, and which juniper_data is imported."""

import importlib
import importlib.metadata as md
import sys
import zlib

print("python", sys.version.split()[0], sys.executable)
import numpy as np

print("numpy", np.__version__, "zlib", zlib.ZLIB_VERSION, "runtime", zlib.ZLIB_RUNTIME_VERSION)
for dist in ("juniper-data", "juniper-service-core", "fastapi", "starlette", "uvicorn", "httpx", "pydantic"):
    try:
        print(dist, md.version(dist))
    except md.PackageNotFoundError:
        print(dist, "NOT INSTALLED")
jd = importlib.import_module("juniper_data")
print("juniper_data imported from", jd.__file__, "version", getattr(jd, "__version__", "?"))

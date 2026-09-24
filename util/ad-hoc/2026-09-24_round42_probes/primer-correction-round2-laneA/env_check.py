#!/usr/bin/env python3
"""Lane A r2: report interpreter/library versions and confirm juniper_data imports from the scratch tree."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE / "jd_main_1afc3484"
sys.path.insert(0, str(TREE))

import fastapi  # noqa: E402
import httpx  # noqa: E402
import juniper_data  # noqa: E402
import numpy  # noqa: E402
import pydantic  # noqa: E402
import starlette  # noqa: E402
import zlib  # noqa: E402

print("python", sys.version.split()[0], sys.executable)
print("juniper_data from", juniper_data.__file__)
assert str(TREE) in juniper_data.__file__, "juniper_data did NOT import from the scratch tree"
print("numpy", numpy.__version__, "| zlib", zlib.ZLIB_RUNTIME_VERSION, "| fastapi", fastapi.__version__,
      "| starlette", starlette.__version__, "| pydantic", pydantic.__version__, "| httpx", httpx.__version__)

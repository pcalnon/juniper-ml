"""Item 11 (A-N4): re-measure canopy's ``equities`` seed at juniper-data origin/main (generator 5.0.0).

Replicates the service path of ``POST /v1/datasets`` exactly -- ``params_class(**request.params)``,
then ``bind_deployment_defaults``, then ``generate`` -- with canopy's EXACT ``default_params`` for
``equities``. Run with PYTHONPATH pointing at an origin/main tree and
JUNIPER_DATA_EQUITIES_CACHE_DIR pointing at a fresh directory (a fresh container). Scratch only.
"""

import datetime
import json
import os
import sys
import time

import numpy as np

from juniper_data.api.routes.generators import GENERATOR_REGISTRY
from juniper_data.generators.equities.defaults import EQUITIES_FEATURE_COLUMNS

CANOPY_SEED = json.loads(sys.argv[1])
info = GENERATOR_REGISTRY["equities"]
generator_class = info["generator"]
params_class = info["params_class"]

print("juniper_data tree:", sys.modules["juniper_data"].__file__)
print("registry version:", info["version"], "| class VERSION:", getattr(generator_class, "VERSION", "?"))
print("cache dir:", os.environ.get("JUNIPER_DATA_EQUITIES_CACHE_DIR"))
print("canopy seed:", CANOPY_SEED)
print("utc now:", datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"))

params = params_class(**CANOPY_SEED)
binder = getattr(generator_class, "bind_deployment_defaults", None)
if callable(binder):
    params = binder(params)
bound = params.model_dump()
print("bound max_symbols:", bound.get("max_symbols"), "| bound allow_truncation:", bound.get("allow_truncation"), "| start_date:", bound.get("start_date"), "| end_date:", bound.get("end_date"))

start = time.monotonic()
arrays = generator_class.generate(params)
elapsed = time.monotonic() - start
print(f"generate: {elapsed:.1f}s")
print("keys:", sorted(arrays))
for split in ("train", "val", "test"):
    X = arrays.get(f"X_{split}")
    y = arrays.get(f"y_{split}")
    if X is None:
        print(f"  {split}: ABSENT")
        continue
    xf = np.asarray(X, dtype=np.float64)
    nonfinite = int((~np.isfinite(xf)).sum())
    print(f"  X_{split} shape={tuple(X.shape)} dtype={X.dtype} nonfinite={nonfinite} | y_{split} shape={tuple(np.asarray(y).shape)} dtype={np.asarray(y).dtype}")
total = sum(int(np.asarray(arrays[f"X_{s}"]).shape[0]) for s in ("train", "val", "test") if f"X_{s}" in arrays)
print("total rows (train+val+test):", total)
print("feature columns (defaults):", len(EQUITIES_FEATURE_COLUMNS))
extra = sorted(k for k in arrays if not k.startswith(("X_", "y_")))
print("non-partition keys:", extra)

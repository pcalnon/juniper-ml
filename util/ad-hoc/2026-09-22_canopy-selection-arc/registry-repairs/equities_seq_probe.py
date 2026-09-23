"""Adjacent to item 11: does canopy's equities_seq evidence ("15,476 train windows of (64, 16)") still hold at 5.0.0?

Service path (params_class -> bind_deployment_defaults -> generate) with canopy's exact equities_seq seed. Scratch only.
"""

import json
import sys
import time

import numpy as np

from juniper_data.api.routes.generators import GENERATOR_REGISTRY

seed = json.loads(sys.argv[1])
info = GENERATOR_REGISTRY["equities_seq"]
params = info["generator"].bind_deployment_defaults(info["params_class"](**seed)) if hasattr(info["generator"], "bind_deployment_defaults") else info["params_class"](**seed)
t0 = time.monotonic()
arrays = info["generator"].generate(params)
print(f"version={info['version']} generate={time.monotonic() - t0:.1f}s")
for key in ("X_train", "X_val", "X_test", "y_train"):
    arr = np.asarray(arrays[key])
    print(f"  {key} shape={arr.shape} nonfinite={int((~np.isfinite(arr.astype(np.float64))).sum())}")

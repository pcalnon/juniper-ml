"""Item 11 stage 1: generate canopy's equities seed at juniper-data origin/main -> six-key NPZ.

Mirrors juniper-ml util/ad-hoc/2026-09-10_rank2_generate_artifacts.py but takes the SERVICE path
(params_class -> bind_deployment_defaults -> generate) and writes only the six contract keys.
Cases: the canopy seed exactly, and the seed without normalize_features (re-checks that key's
rationale). Scratch only; run in JuniperData with PYTHONPATH at an origin/main tree.
"""

import json
import sys
import time
from pathlib import Path

import numpy as np

from juniper_data.api.routes.generators import GENERATOR_REGISTRY

OUT = Path(sys.argv[1])
SEED = json.loads(sys.argv[2])
CASES = {
    "equities_canopy_seed": SEED,
    "equities_seed_without_normalize": {k: v for k, v in SEED.items() if k != "normalize_features"},
}
info = GENERATOR_REGISTRY["equities"]
OUT.mkdir(parents=True, exist_ok=True)
for case, overrides in CASES.items():
    params = info["params_class"](**overrides)
    params = info["generator"].bind_deployment_defaults(params)
    t0 = time.monotonic()
    arrays = info["generator"].generate(params)
    elapsed = time.monotonic() - t0
    payload = {k: np.asarray(arrays[k]) for k in ("X_train", "y_train", "X_val", "y_val", "X_test", "y_test")}
    np.savez_compressed(OUT / f"{case}.npz", **payload)
    shapes = {k: tuple(v.shape) for k, v in payload.items()}
    nonfinite = {k: int((~np.isfinite(v.astype(np.float64))).sum()) for k, v in payload.items() if k.startswith("X_")}
    print(f"{case}: version={info['version']} generate={elapsed:.1f}s shapes={shapes} nonfinite={nonfinite}")

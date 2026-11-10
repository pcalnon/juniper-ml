"""
Execute juniper-data's documented Sequence Windowing examples against the real code (flood-4 docs validator).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 juniper-data docs carrier validation (juniper-data #515, docs/REFERENCE.md § Sequence Windowing)

Usage (from a juniper-data checkout, with that repo's interpreter):
    python 2026-11-07_flood4_val_data_docs_seq_probe.py <juniper-data checkout>

Checks: the curl example's W; the documented defaults; the 400 detail for W < 3 and for a delay_product lag
at the window edge, through the real POST /v1/datasets route (FastAPI TestClient, in-memory storage).
"""

import sys

sys.path.insert(0, sys.argv[1])

from fastapi.testclient import TestClient  # noqa: E402

from juniper_data.generators.delay_product import DelayProductGenerator, DelayProductParams  # noqa: E402
from juniper_data.generators.multi_sine import MultiSineGenerator, MultiSineParams  # noqa: E402


def main():
    p = MultiSineParams(n_steps=64, lookback=8, horizon=1, seed=0)
    arrays = MultiSineGenerator.generate(p)
    w = sum(arrays[f"X_{s}"].shape[0] for s in ("train", "val", "test"))
    print("curl example W =", w, "shapes:", {k: v.shape for k, v in arrays.items() if hasattr(v, "shape")})
    print("keys:", sorted(k for k in arrays if not k.startswith("X_") and not k.startswith("y_")))
    d = MultiSineParams()
    print("defaults:", d.n_steps, d.lookback, d.horizon, d.sample_dt, d.train_ratio, d.val_ratio, d.seed, d.scaling)
    dp = DelayProductGenerator.generate(DelayProductParams(n_steps=200, lookback=16, seed=0))
    print("delay_product y_train shape:", dp["y_train"].shape, "X_train shape:", dp["X_train"].shape)

    from juniper_data.api.app import create_app  # noqa: E402

    cases = {
        "W<3": {"generator": "multi_sine", "params": {"n_steps": 10, "lookback": 8, "horizon": 1, "seed": 0}},
        "lag_edge": {"generator": "delay_product", "params": {"lookback": 8, "lag1": 8, "seed": 0}},
        "curl": {"generator": "multi_sine", "params": {"n_steps": 64, "lookback": 8, "horizon": 1, "seed": 0}},
    }
    # The context manager runs the app lifespan, which initialises storage.
    with TestClient(create_app()) as client:
        for name, body in cases.items():
            r = client.post("/v1/datasets", json=body)
            detail = r.json().get("detail") if r.headers.get("content-type", "").startswith("application/json") else r.text[:200]
            print(f"{name}: HTTP {r.status_code} detail={str(detail)[:260]}")


if __name__ == "__main__":
    main()

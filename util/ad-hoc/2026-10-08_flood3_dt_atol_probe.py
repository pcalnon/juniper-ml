#!/usr/bin/env python3
# Project:      Juniper
# Sub-Project:  juniper-ml
# Application:  ad-hoc evaluation helper (Cursor flood #3, "clients" slice)
# Author:       Paul Calnon
# Version:      0.1.0
# License:      MIT License
#
# Ad-hoc, single-use. juniper-data-client#228 documents that `t` and `dt` "must agree within
# dt_atol (default 1e-6)". The check is np.allclose(recon, dt, atol=dt_atol), whose default
# rtol=1e-5 also applies. This builds one artifact whose t/dt disagree by MORE than dt_atol and
# shows validate_npz_contract accepts it, then one that disagrees by more than atol+rtol*|dt|.
"""Usage: PYTHONPATH=<juniper-data-client worktree> python 2026-10-08_flood3_dt_atol_probe.py"""
import numpy as np

import juniper_data_client
from juniper_data_client import JuniperDataContractError, validate_npz_contract


def artifact(gap_error: float, gap: float = 1.0) -> dict:
    lookback = 3
    dt = np.array([[0.0, gap, gap]], dtype=np.float32)
    t = np.array([[0.0, gap + gap_error, 2 * gap + gap_error]], dtype=np.float64)
    return {
        "X_train": np.zeros((1, lookback, 2), np.float32),
        "y_train": np.zeros((1, 2), np.float32),
        "dt_train": dt,
        "t_train": t,
    }


print("imported from", juniper_data_client.__file__)
for gap, err in ((1.0, 9e-6), (1.0, 2e-5), (86400.0, 0.5)):
    try:
        kind = validate_npz_contract(artifact(err, gap))
        print(f"gap={gap:<8} |t-dt| error={err:<7} > dt_atol=1e-6: ACCEPTED ({kind})")
    except JuniperDataContractError as exc:
        print(f"gap={gap:<8} |t-dt| error={err:<7}: REJECTED ({exc})")

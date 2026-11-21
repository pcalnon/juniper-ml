#!/usr/bin/env python3
"""Re-derive the APD-DATA-041 claims about close/adj_close on the cached AAPL frame.

Checks, independently of lane B1: is the ratio monotone? how many distinct steps, at what
rounding? does a window ending before the download date still carry an adjustment?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-09
Status: ad-hoc — investigation (round-2 validation of the round-38 defect-register handoff)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: reports/2026-09-09_round-38-consensus/; see README.md in this directory for what each
         script settled and what it needs on disk to run.
"""
from __future__ import annotations

import pandas as pd

PKL = "/home/pcalnon/.cache/juniper_data/equities/ohlcv/AAPL_2000-01-01_2026-06-03.pkl"
df = pd.read_pickle(PKL)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ["_".join(str(p) for p in c if p) for c in df.columns]
print("columns:", list(df.columns)[:12])
close_col = next(c for c in df.columns if c.lower().startswith("close"))
adj_col = next(c for c in df.columns if "adj" in c.lower())
ratio = (df[close_col] / df[adj_col]).dropna()
print(f"rows: {len(ratio)}  first={ratio.iloc[0]:.6f}  last={ratio.iloc[-1]:.6f}")

d = ratio.diff().dropna()
print(f"strict increases: {(d > 0).sum()}   strict decreases: {(d < 0).sum()}   flat: {(d == 0).sum()}")
for tol in (0.0, 1e-9, 1e-6, 3e-6):
    print(f"  non-increasing within tol {tol:g}: {(d <= tol).all()}")

for dp in (6, 8, None):
    n = ratio.round(dp).nunique() if dp is not None else ratio.nunique()
    print(f"distinct values at {dp if dp else 'full'} dp: {n}")

# Economically real steps: drops bigger than a rounding wobble.
real = (d < -1e-6).sum()
print(f"down-steps beyond 1e-6: {real}")

# A window ending well before the download date still carries an adjustment.
for end in ("2023-12-29", "2020-12-31"):
    sub = ratio[ratio.index <= end]
    if len(sub):
        print(f"ratio on last row <= {end}: {sub.iloc[-1]:.6f}  => adjustment {100 * (sub.iloc[-1] - 1):.2f}%")

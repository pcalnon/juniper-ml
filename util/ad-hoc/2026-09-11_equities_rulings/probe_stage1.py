#!/usr/bin/env python3
"""
Probe stage 1 against the real 485-payload SEC cache: does the floor kill exactly the unusable
series, does the causal median keep the genuine ones, and does the restatement history survive?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-11_equities_rulings/stage1_fetch_shares.py
"""
from __future__ import annotations

import sys

W = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-causal-data-quality--20260911-2310--20cd6788"
sys.path.insert(0, W)

from juniper_data.generators.equities.generator import EquitiesGenerator  # noqa: E402

CASES = {
    "TAP  (all zero)": 24545,
    "CVNA (all zero)": 1690820,
    "DDOG (zero delivered)": 1561550,
    "FOX  (val=1)": 1754301,
    "PSKY (1000,1000,real)": 2041610,
    "BRK  (genuine Class-A)": 1067983,
    "NVR  (smallest ordinary)": 906163,
    "ADM  (restatement case)": 7084,
    "AAPL (healthy control)": 320193,
}

for label, cik in CASES.items():
    frame = EquitiesGenerator._fetch_shares(cik, True)
    if frame is None or not len(frame):
        print(f"{label:<26} -> None (unrescued)")
        continue
    lo = float(frame["shares"].min())
    hi = float(frame["shares"].max())
    ends = frame.index
    dup_ends = int(len(ends) - len(ends.unique()))
    print(f"{label:<26} -> rows={len(frame):>4} min={lo:>16,.0f} max={hi:>16,.0f} restated_ends={dup_ends}")

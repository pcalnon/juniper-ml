#!/usr/bin/env python3
"""Re-derive lane B1's three decisive claims independently.

1. Does `bind_deployment_defaults`' model_copy(update=...) destroy the omitted-vs-explicit-false
   distinction that a presence guard would need?
2. Does cascor ever CLEAR `_dataset_shortfall`?
3. How many cached shares payloads deliver a last as-of date older than 2025-06-01?

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

import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/juniper-data")

print("=== 1. model_fields_set through the binder ===")
try:
    from juniper_data.generators.equities.params import EquitiesParams
    from juniper_data.generators.equities.generator import bind_deployment_defaults
except Exception as exc:  # pragma: no cover
    print("  import failed:", exc)
else:
    omitted = EquitiesParams()
    explicit = EquitiesParams(allow_truncation=False)
    print(f"  BEFORE bind  omitted: {sorted(omitted.model_fields_set)}")
    print(f"  BEFORE bind  explicit-false: {sorted(explicit.model_fields_set)}")
    print(f"  distinguishable BEFORE: {('allow_truncation' in omitted.model_fields_set) != ('allow_truncation' in explicit.model_fields_set)}")
    try:
        bo = bind_deployment_defaults(omitted)
        be = bind_deployment_defaults(explicit)
        print(f"  AFTER  bind  omitted: {sorted(bo.model_fields_set)}")
        print(f"  AFTER  bind  explicit-false: {sorted(be.model_fields_set)}")
        same = ("allow_truncation" in bo.model_fields_set) == ("allow_truncation" in be.model_fields_set)
        print(f"  distinguishable AFTER: {not same}")
    except Exception as exc:
        print("  bind failed:", exc)

print()
print("=== 3. stale as-of dates in the delivered shares series ===")
CACHE = Path.home() / ".cache/juniper_data/equities/shares"
OUTLIER = 100.0


def delivered(payload):
    """Latest-filed fact per period end, then the whole-history median filter."""
    units = payload.get("units") or {}
    facts = []
    for arr in units.values():
        if isinstance(arr, list):
            facts.extend(arr)
    best = {}
    for f in facts:
        end, val, filed = f.get("end"), f.get("val"), f.get("filed", "")
        if end is None or val is None:
            continue
        prev = best.get(end)
        if prev is None or filed >= prev[0]:
            best[end] = (filed, float(val))
    pts = sorted((e, v) for e, (_, v) in best.items())
    if not pts:
        return []
    vals = sorted(v for _, v in pts)
    n = len(vals)
    med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
    if med > 0:
        lo, hi = med / OUTLIER, med * OUTLIER
        return [(e, v) for e, v in pts if lo <= v <= hi]
    return pts


stale, total, lasts = [], 0, []
for path in sorted(CACHE.glob("*.json")):
    try:
        pts = delivered(json.loads(path.read_text()))
    except Exception:
        continue
    if not pts:
        continue
    total += 1
    last_end = pts[-1][0]
    lasts.append(last_end)
    if last_end < "2025-06-01":
        stale.append((path.stem, last_end, pts[-1][1]))

print(f"  delivered series: {total}")
print(f"  last as-of before 2025-06-01: {len(stale)}")
print(f"  median last as-of: {sorted(lasts)[len(lasts) // 2] if lasts else 'n/a'}")
print(f"  predating 2015: {sum(1 for e in lasts if e < '2015-01-01')}")
for name, end, val in sorted(stale, key=lambda r: r[1])[:8]:
    print(f"    {name} last={end} val={val:,.0f}")

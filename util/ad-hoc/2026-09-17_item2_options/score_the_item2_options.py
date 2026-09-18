#!/usr/bin/env python3
"""What does each option for owner decision section 7 item 2 actually do to the instrument?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-17
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 7

Why
---
Item 2 asks whether the Sec 4 rows are re-scored. Presenting that choice needs the consequences
measured, not asserted -- and this arc has established that the consequences are NOT limited to
the headline rate: a downward re-score also desensitises the rung-3 area detector (the null for
the Bonferroni test is `1 - rate`) and raises the number of consecutive follows needed to reopen
a terminal study.

Runs each option through the REAL `analyse()` on a copy of the live ledger rather than
recomputing anything by hand. Writes nothing.
"""

from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"

P21 = "b57a72bb-11cc-46b7-875c-136eb77cd5d6"   # evidence: filename=1 (grep -rln, nothing read)
P24 = "eb3d9320-24f5-47cc-8190-01756107de4e"   # evidence: foreign=2 (a sibling repo's copy)

OPTIONS = [
    ("A  re-score BOTH", [P21, P24]),
    ("B  re-score NEITHER (status quo)", []),
    ("C  re-score P24 only (foreign)", [P24]),
    ("D  re-score P21 only (filename)", [P21]),
]


def load():
    spec = importlib.util.spec_from_file_location("sl", ROOT / "util" / "soak_ledger.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["sl"] = m
    spec.loader.exec_module(m)
    return m


def rescore_row(target: str, n: int) -> dict:
    return {"obs_id": f"sim-rs-{n}", "kind": "rescore", "ts": "2026-09-17T00:00:00Z",
            "rescores": target, "from_outcome": "follow",
            "to_outcome": "source-recovered", "reason": "simulation"}


def reopen_cost(m, k: int, n: int) -> int:
    """Consecutive additional follows needed to lift the Wilson upper back over 0.75."""
    for extra in range(0, 200):
        _, hi = m.wilson(k + extra, n + extra)
        if hi > m.DECISION_BOUNDARY:
            return extra
    return -1


def main() -> int:
    m = load()
    rows, _ = m.load_rows(LEDGER)

    print(f"boundary = {m.DECISION_BOUNDARY}    "
          f"AREA_MIN_MISSES = {m.AREA_MIN_MISSES}    "
          f"MIN_DISTINCT_PROBES = {m.MIN_DISTINCT_PROBES}\n")
    hdr = (f"{'option':<34}{'rate':>12}{'Wilson 95%':>22}{'margin':>9}"
           f"{'reopen':>8}{'verdict':>14}{'esc':>5}")
    print(hdr)
    print("-" * len(hdr))

    for label, targets in OPTIONS:
        sim = copy.deepcopy(rows) + [rescore_row(t, i) for i, t in enumerate(targets)]
        a = m.analyse(sim)
        s = a["seeded"]
        k, n = s["follows"], s["denom"]
        lo, hi = m.wilson(k, n)
        print(f"{label:<34}{f'{k}/{n} = {k/n:.1%}':>12}"
              f"{f'[{lo:.4f}, {hi:.4f}]':>22}"
              f"{m.DECISION_BOUNDARY - hi:>9.4f}"
              f"{reopen_cost(m, k, n):>8}"
              f"{a['verdict']:>14}"
              f"{len(a['escalations']):>5}")

    print("\n'reopen' = consecutive additional follows needed to lift the Wilson upper")
    print("back over the boundary. util/soak_run_probe.py refuses to generate them on a")
    print("terminal verdict without --force, so it is the real cost of entrenchment.\n")

    # The rung-3 desensitisation, measured rather than argued.
    print("Rung-3 area detector -- the Bonferroni null is `1 - rate`, so a LOWER rate")
    print("makes a systematic-area escalation LESS likely to fire:")
    try:
        from scipy.stats import binom                       # noqa: F401
        have = True
    except Exception:                                        # noqa: BLE001
        have = False
    for label, targets in OPTIONS:
        sim = copy.deepcopy(rows) + [rescore_row(t, i) for i, t in enumerate(targets)]
        a = m.analyse(sim)
        s = a["seeded"]
        pooled_miss = 1 - s["rate"]
        by_area = s.get("by_area_miss") or {}
        wt = by_area.get("worktrees")
        print(f"  {label:<34} pooled_miss={pooled_miss:.5f}   worktrees={wt}")
    if not have:
        print("  (scipy absent; p-values not recomputed here -- the pooled_miss column is")
        print("   the driver and is what moves.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

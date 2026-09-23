#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- owner decision D1 (the epoch-count debt)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py

Reduce the per-arm JSON records of ``2026-09-23_d1_epoch_count_sweep.py`` WITHOUT waiting for the
driver. The driver writes ``debt.json`` only at the very end; this reads whatever ``r<rep>-<arm>.json``
files exist, so an interim look is possible and a crashed sweep still yields its evidence.

For every arm record it prints, against the FIRST ``none`` record:
  * counts   -- hidden units, per-phase candidate ``epochs_completed``, output epochs, history length
                (the owner's criterion for the D1 flip);
  * numerics -- winning candidate per phase, best correlations, final loss (supplementary: explains
                the counts; bit-identity is stronger than count-identity).
and, per arm, whether its repeats agree with each other (determinism).

Usage::

    python3 util/ad-hoc/2026-09-23_d1_epoch_debt_reduce.py ~/.local/state/juniper-experiments/suites/d1-epoch-debt-20260923
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def counts(record: dict) -> tuple:
    return (
        record.get("hidden_units"),
        tuple(tuple(p["epochs_completed"]) for p in record.get("candidate_phases", [])),
        tuple(p["epochs_requested"] for p in record.get("output_passes", [])),
        record.get("outcome", {}).get("history_train_loss_len"),
    )


def numerics(record: dict) -> tuple:
    return (
        tuple(p["best_candidate_id"] for p in record.get("candidate_phases", [])),
        tuple(p["best_correlation"] for p in record.get("candidate_phases", [])),
        record.get("outcome", {}).get("final_train_loss"),
    )


def first_count_difference(a: tuple, b: tuple) -> str:
    for phase, (x, y) in enumerate(zip(a[1], b[1])):
        if x != y:
            return f"candidate phase {phase}: {list(x)} vs {list(y)}"
    if a[0] != b[0]:
        return f"hidden units {a[0]} vs {b[0]}"
    if len(a[1]) != len(b[1]):
        return f"phase count {len(a[1])} vs {len(b[1])}"
    return "output epochs / history length"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()

    records = {}
    for path in sorted(args.out_dir.glob("r*-*.json")):
        records[path.stem] = json.loads(path.read_text(encoding="utf-8"))
    if not records:
        print(f"no arm records under {args.out_dir}")
        return 2

    controls = [k for k in records if k.endswith("-none")]
    if not controls:
        print("no `none` arm yet -- nothing to compare against")
        return 2
    base_key = controls[0]
    base = records[base_key]
    base_c, base_n = counts(base), numerics(base)
    all_cands = [e for phase in base_c[1] for e in phase]
    budget = base.get("budgets", {}).get("candidate_epochs")
    below = sum(e < budget for e in all_cands) if budget else None
    print(f"reference: {base_key}  hidden={base_c[0]}  candidates={len(all_cands)}  below budget {budget}: {below}")
    print()
    print(f"{'record':<14}{'ok':<5}{'fit_s':>9}  {'icv in/out':<11}{'OMP':<5}{'counts==none':<14}{'numerics==none':<16}detail")
    by_arm: dict[str, list[tuple, tuple]] = {}
    for key, rec in records.items():
        c, n = counts(rec), numerics(rec)
        arm = key.split("-", 1)[1]
        by_arm.setdefault(arm, []).append((c, n))
        same_c, same_n = c == base_c, n == base_n
        detail = "" if same_c else first_count_difference(base_c, c)
        if same_c and not same_n:
            detail = f"final loss {n[2]} vs {base_n[2]}"
        icv = f"{rec['outcome'].get('icv_at_train_entry')}/{rec['outcome'].get('icv_at_exit')}"
        print(f"{key:<14}{str(rec['outcome'].get('ok')):<5}{rec['outcome'].get('fit_seconds'):>9}  {icv:<11}{str(rec['observed_blas_env'].get('OMP_NUM_THREADS')):<5}{str(same_c):<14}{str(same_n):<16}{detail}")
    print()
    for arm, rows in sorted(by_arm.items()):
        cs = {r[0] for r in rows}
        ns = {r[1] for r in rows}
        print(f"  {arm:<9} repeats={len(rows)}  counts deterministic={len(cs) == 1}  numerics deterministic={len(ns) == 1}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Plan v1.7.7: record that W5.2 landed (model half merged and cut as 0.6.0; service half open) and the R5 re-measurement.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.6 -> v1.7.7);
         juniper-recurrence#214 (W5.2 model half), #215 (service half), #216 (model 0.6.0 proposal); juniper-ml#2256 (driver);
         util/ad-hoc/2026-10-19_w5_2_eh_remeasure.py (the numbers quoted)

Usage
-----
    python3 util/ad-hoc/2026-10-19_plan_v1_7_7_w5_2_landed.py --release "<model 0.6.0 state>" [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

MODEL_PR = "juniper-recurrence#214, `b8728df7`"
SERVICE_PR = "juniper-recurrence#215"
DRIVER_PR = "juniper-ml#2256"
MEASURED = "re-measured on the trainval pool (1,522 windows; five expanding folds of 253 eval windows, embargo = look-back 64 per entity, `util/ad-hoc/2026-10-19_w5_2_eh_remeasure.py`): the bare 0.7.0 default (linear, GCV on the standardised block) **cv_r2 −0.298, cv_r2_std 0.281**; the recommended RFF / ridge 1.0 / 256 / median configuration **cv_r2 −0.111, cv_r2_std 0.041** — both inside the R5 band (`cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`)"


def edits(release: str) -> list[tuple[str, str]]:
    return [
        ("- **Version**: 1.7.6", "- **Version**: 1.7.7"),
        # Status line.
        (
            "— **0.7.0 is on PyPI and GHCR**). The v1.4.0 plan edits follow that record",
            f"— **0.7.0 is on PyPI and GHCR**); **W5.2 landed** (v1.7.7: the model half {MODEL_PR} — `SequenceData` carries `ticker_code` / `window_end_date`, a composed `trainval` view — {release}; the service half {SERVICE_PR} — the pool is `trainval`, a panel's folds are cut on the global date per entity, `embargo` defaults to the look-back, label-availability and `embargo_days` filters, a `folding` block on the response — open for recurrence 0.8.0; the driver {DRIVER_PR} omits `embargo` when the config omits it; the R5 band {MEASURED}). The v1.4.0 plan edits follow that record",
        ),
        # W5.2 row: header and acceptance cells.
        (
            "| W5.2 | F-P7, F-SCI2 | juniper-recurrence + juniper-model-core (integration) |",
            f"| W5.2 | F-P7, F-SCI2; **landed 2026-10-19** (model half {MODEL_PR}, model 0.6.0; service half {SERVICE_PR}, recurrence 0.8.0; driver {DRIVER_PR}) | juniper-recurrence + juniper-model-core (integration) |",
        ),
        (
            "| Four tests (chronology; lookback non-overlap; label availability; `test` excluded) — see Details. Bench gains a multi-ticker row. | L |",
            f"| Four tests (chronology; lookback non-overlap; label availability; `test` excluded) — see Details. Bench gains a multi-ticker row. **Done 2026-10-19** except the bench row: `juniper-recurrence/tests/test_crossval_folds.py` (10 tests) and the route test `test_crossval_pool_excludes_test_and_cuts_a_panel_on_the_date` pin the four; the E-H row {MEASURED}. **Owed**: the bench's multi-ticker row (`bench/run_benchmark.py` still cuts row-index folds). | L |",
        ),
        # W5.4 dependency row: the re-measurement is in hand.
        (
            "| W5.4 R5 band re-measured | W5.2 (the E-H row's population becomes train + val) | ORG | M | **Added 2026-10-05**: the band was measured on 1,698 windows incl. `test`; re-measure on 1,522 before encoding (numbers in `reconciler-rederive-b1r2.json` F10) |",
            f"| W5.4 R5 band re-measured | W5.2 (the E-H row's population becomes train + val) | ORG | M | **Added 2026-10-05**: the band was measured on 1,698 windows incl. `test`; re-measure on 1,522 before encoding (numbers in `reconciler-rederive-b1r2.json` F10). **Re-measured 2026-10-19** with W5.2's folds: {MEASURED} — the band holds; W5.4 can encode it |",
        ),
        # Progress block: one more bullet after the v1.7.6 one.
        (
            "  - **Next**: the juniper-ml `[recurrence]` extras and the Compose pin (both admit `<0.7.0`) are owner rulings again; W5.2 and W5.4 (round 3 of the CV-blowup note's review first); W5.7.",
            f"  - **W5.2 landed (later still)**: {MODEL_PR} (model 0.6.0 via juniper-recurrence#216; the follow-on ceiling PR #217 closed as superseded; {release}); {SERVICE_PR} open (its CI needs 0.6.0 on PyPI); {DRIVER_PR}. Design choice to note: an explicit `embargo` below the look-back is **honoured with a WARNING**, not refused — the E-G suite sweeps it and the W5.1 note's embargo-2 numbers remain reproducible; omitting it gives the plan's default. The R5 band {MEASURED}.\n  - **Next**: the `pypi` gate on model 0.6.0, then {SERVICE_PR} and recurrence 0.8.0; the juniper-ml `[recurrence]` extras and the Compose pin (both admit `<0.7.0`) are owner rulings; W5.4 (round 3 of the CV-blowup note's review first, then the facility and the band above); W5.7; the bench's multi-ticker row.",
        ),
    ]


_ROW_ANCHOR = "W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes. | Paul Calnon |\n"
_ROW = (
    "| 2026-10-19 | 1.7.7 | **W5.2 landed**: the model half ({model_pr}; model 0.6.0 proposed in juniper-recurrence#216, {release}); the service half ({service_pr}, open for recurrence 0.8.0, floor `>=0.6.0`); the driver ({driver_pr}) omits `embargo` when the config omits it. "
    "The CV pool is the `trainval` view (never `test`); a panel's folds are cut on the global `window_end_date` with a per-entity embargo defaulting to the look-back; a train window whose label crosses the cut is dropped; `embargo_days` is a duration gap; the response carries a `folding` block. "
    "The R5 band {measured}. "
    "Updated: Status line, W5.2 row (both cells), the W5.4 re-measurement dependency row, the Progress 2026-10-19 block. "
    "Owed: the gate and recurrence 0.8.0; the bench's multi-ticker row; the extras / Compose rulings; W5.4 (round 3 first); W5.7; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--release", required=True, help="model 0.6.0's state, e.g. 'Release juniper-recurrence-model-v0.6.0 cut at `2c5a419c`, publish run N at the owner's pypi gate'")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = _PLAN.read_text(encoding="utf-8")
    pending = []
    done = 0
    for old, new in edits(args.release):
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))
    row = _ROW.format(model_pr=MODEL_PR, release=args.release, service_pr=SERVICE_PR, driver_pr=DRIVER_PR, measured=MEASURED)
    row_pending = row not in text
    if row_pending and text.count(_ROW_ANCHOR) != 1:
        print(f"REFUSED: change-log anchor matched {text.count(_ROW_ANCHOR)} times (expected 1)")
        return 1
    if args.check:
        print(f"applied {done}, pending {len(pending)}, change-log row {'pending' if row_pending else 'present'}")
        return 0
    for old, new in pending:
        text = text.replace(old, new, 1)
    if row_pending:
        i = text.index(_ROW_ANCHOR) + len(_ROW_ANCHOR)
        text = text[:i] + row + text[i:]
    _PLAN.write_text(text, encoding="utf-8")
    print(f"applied {done + len(pending)} edits; change-log row {'added' if row_pending else 'already present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

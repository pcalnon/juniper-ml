#!/usr/bin/env python3
"""Plan v1.7.8: W5.4 landed (the acceptance facility and the R5 band), the 0.7.0 pins followed, the bench row opened.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.7 -> v1.7.8);
         juniper-ml#2262 (W5.4), juniper-ml#2260 (the [recurrence] extras), juniper-deploy#255 (the Compose pin),
         juniper-recurrence#219 (the bench row), juniper-recurrence#215 (its second commit: the [torch] extra fix);
         util/ad-hoc/2026-10-19_plan_v1_7_7_w5_2_landed.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-19_plan_v1_7_8_w5_4_landed.py --w54 "<juniper-ml#2262 state>" [--check]

``--w54`` is the state of the W5.4 PR at the time of the revision, e.g. "merged as `1a2b3c4d`" or "open, merge armed".
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

W54_PR = "juniper-ml#2262"
EXTRAS_PR = "juniper-ml#2260, `19c8999e`"
COMPOSE_PR = "juniper-deploy#255, `cade28d3`"
BENCH_PR = "juniper-recurrence#219"
TORCH_FIX = "the second commit on juniper-recurrence#215 (`25b75832`)"
FACILITY = (
    "`run_suite.py` gains `acceptance:` — a list of `{metric, min, max, mode}` bands on the suite or on an `include` row, validated at load; "
    "a `gate` miss makes a succeeded cell `failed` (exit 1), a `report` miss makes it `flagged` (a new terminal outcome, exit unchanged), "
    "an absent metric follows the mode and is distinct from `degraded`; `aggregate.csv` / `REPORT.md` gain an `acceptance` column (last) and a bands section; "
    "`tests/test_run_suite_acceptance.py` (20 tests)"
)
BAND = "the E-H equities row of `suites/p4/e-h-recurrence-real-data.yaml` carries R5 — `cv_r2 ∈ [−1.0, +0.5]` and `cv_r2_std ≤ 0.5`, both `gate`, row-scoped"
ROUND3 = "round 3 of the CV-blowup note's review was already recorded complete in `JUNIPER_2026-10-05_JUNIPER-RECURRENCE_EQUITIES-CV-BLOWUP-CONSENSUS-VALIDATION.md` (Lane A1-r3, 45 checks; the process terminated), so the precondition held"
TORCH = "juniper-recurrence 0.7.0's `[torch]` extra is unresolvable (`juniper-recurrence-model[torch]>=0.4.0,<0.5.0` against the base `>=0.5.0`; the W5.8 (B) floor raise missed that site and its CHANGELOG said otherwise)"


def edits(w54: str) -> list[tuple[str, str]]:
    return [
        ("- **Version**: 1.7.7", "- **Version**: 1.7.8"),
        # Status line: the v1.7.8 clause, and the stale "round 3 owed" tail corrected.
        (
            "both inside the R5 band (`cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`)). The v1.4.0 plan edits follow that record and are themselves not consensus-reviewed; round 3 of the note's review (one Lane A check of the new re-derivation keys) is still owed, and precedes W5.4's encoding of the R5 band.",
            f"both inside the R5 band (`cv_r2 ∈ [−1.0, +0.5]`, `cv_r2_std ≤ 0.5`)); **W5.4 landed and the 0.7.0 pins followed** (v1.7.8: {W54_PR}, {w54} — {FACILITY}; {BAND}; the juniper-ml `[recurrence]` extras moved to `juniper-recurrence>=0.7.0,<0.8.0` and `juniper-recurrence-model>=0.5.0,<0.6.0` ({EXTRAS_PR}) and the Compose image to `juniper-recurrence:0.7.0` ({COMPOSE_PR}); the bench's multi-ticker row is {BENCH_PR}, open behind juniper-recurrence#215; {TORCH}, fixed for 0.8.0 by {TORCH_FIX}). The v1.4.0 plan edits follow that record and are themselves not consensus-reviewed; {ROUND3}, and W5.4 encoded the R5 band on 2026-10-19.",
        ),
        # W5.4 row.
        (
            "| W5.4 | F-D3, F-SCI4 | juniper-ml | **No YAML `acceptance:` facility exists today** (`run_suite.py:742` is reporting-only). Build it: per-row schema `acceptance: {metric, min, max, mode: gate / report}`, parser, comparator over W0.4 keys, outcome semantics per R6, report columns; then encode the **R5** band for E-H. | Suite tests: `cv_r2 = −18081` → `failed` under `gate`, `flagged` under `report`; missing metric follows the mode (Details); schema error → suite refuses at load. | M–L |",
            f"| W5.4 | F-D3, F-SCI4; **landed 2026-10-19** ({W54_PR}) | juniper-ml | ~~No YAML `acceptance:` facility exists today~~ **Built** ({W54_PR}): {FACILITY}; then {BAND}, re-measured on W5.2's population first (v1.7.7). | Suite tests: `cv_r2 = −18081` → `failed` under `gate`, `flagged` under `report`; missing metric follows the mode (Details); schema error → suite refuses at load. **Done**: all three pinned in `tests/test_run_suite_acceptance.py`, plus row scoping (the control's 0.975 fails +0.5 only under a suite-level band), `flagged` complete for `--resume` and the exit code, the `acceptance` column last, bands outside the cell id, and the shipped E-H band. | M–L |",
        ),
        # W5.2 row: the bench row has a PR.
        (
            "**Owed**: the bench's multi-ticker row (`bench/run_benchmark.py` still cuts row-index folds). | L |",
            f"**The bench row is {BENCH_PR}** (opened 2026-10-19, behind juniper-recurrence#215 for the model 0.6.0 floor): `Dataset` carries `order` / `groups` / `embargo`, `equities_seq` pools the composed `trainval` view with `embargo = lookback`, `run_dataset` passes them to model-core and records a `folding` block, and an `equities_seq_panel` row (AAPL + MSFT) joins the single-ticker one; four stubbed bench tests, 41 pass. | L |",
        ),
        # P5 status row.
        (
            "| **P5** | Acceptance-band facility + E-H band (W5.4, R5, R6) | Planned | 5 | juniper-ml 0.11.0 |",
            f"| **P5** | Acceptance-band facility + E-H band (W5.4, R5, R6) | **Done 2026-10-19** ({W54_PR}; ships in 0.11.0) | 5 | juniper-ml 0.11.0 |",
        ),
        # R5 ruling line.
        (
            "- **R5: the amended recommendation is accepted** — `cv_r2 ∈ [−1.0, +0.5]` and `cv_r2_std ≤ 0.5`, both `gate`, row-scoped, re-measured on W5.2's population before W5.4 encodes it. Runbooks carry no r² interpretation until then.",
            f"- **R5: the amended recommendation is accepted** — `cv_r2 ∈ [−1.0, +0.5]` and `cv_r2_std ≤ 0.5`, both `gate`, row-scoped, re-measured on W5.2's population before W5.4 encodes it. Runbooks carry no r² interpretation until then. **Encoded 2026-10-19** ({W54_PR}): the band sits on the E-H row's `include` entry; a miss is `failed (acceptance: …)`.",
        ),
        # Progress block: the v1.7.7 Next bullet becomes a landing bullet + a new Next.
        (
            "  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 and recurrence 0.8.0; the juniper-ml `[recurrence]` extras and the Compose pin (both admit `<0.7.0`) are owner rulings; W5.4 (round 3 of the CV-blowup note's review first, then the facility and the band above); W5.7; the bench's multi-ticker row. The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes on the 0.6.1 image and the client-docstring follow-up stay open.",
            f"  - **W5.4 landed, the pins followed, the bench row opened (turing session 3, 2026-10-19)**: {W54_PR} ({w54}) — {FACILITY}; {BAND}; {ROUND3}. The two rulings 0.7.0 reopened were taken with the session's merge approval: {EXTRAS_PR} (both pins move together because 0.7.0 requires model 0.5.x; pre-flighted on real PyPI, `[recurrence]` 32 packages / `[all]` 76 on 3.12–3.14) and {COMPOSE_PR} (GHCR `0.7.0` / `0.7` / `latest` at index `sha256:8dbb693d…`, revision `5c576da4`; the smokes are owed at the next bring-up on a host whose Docker reaches GHCR). Found on the way: {TORCH}; fixed for 0.8.0 by {TORCH_FIX}, which also keeps the request's `embargo` off the WARNING line (CodeQL) and adds `tests/test_pyproject_floors.py`. The bench row is {BENCH_PR}, behind #215. Model 0.6.0 (run 39197693617) was still parked at the owner's `pypi` gate at the end of the session, so #215, 0.8.0 and #219 wait on it.\n  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 (re-run its failed lanes), recurrence 0.8.0, then {BENCH_PR}; the extras / Compose pins follow 0.8.0 (recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`, image `0.8.0`); W5.7 (juniper-data). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes (now on the 0.7.0 image) and the client-docstring follow-up stay open.",
        ),
    ]


_ROW_ANCHOR = "Owed: the gate and recurrence 0.8.0; the bench's multi-ticker row; the extras / Compose rulings; W5.4 (round 3 first); W5.7; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes. | Paul Calnon |\n"
_ROW = (
    "| 2026-10-19 | 1.7.8 | **W5.4 landed; the 0.7.0 pins followed; the bench row opened**: {w54_pr} ({w54}) — {facility}; {band}; {round3}. "
    "{extras_pr}: the juniper-ml `[recurrence]` extras move to `juniper-recurrence>=0.7.0,<0.8.0` **and** `juniper-recurrence-model>=0.5.0,<0.6.0` (0.7.0 requires model 0.5.x, so the old model cap `<0.5.0` would have left the extra unsatisfiable); {compose_pr}: the Compose image to `juniper-recurrence:0.7.0`. "
    "{bench_pr}: the bench's multi-ticker row (open, behind juniper-recurrence#215). Found: {torch}; fixed for 0.8.0 by {torch_fix}. "
    "Updated: Status line (the stale 'round 3 owed' tail corrected), W5.4 row (both cells), W5.2 row (the bench cell), P5 status row, the R5 ruling line, the Progress 2026-10-19 block. "
    "Owed: the gate, then #215 / 0.8.0 / #219 and the 0.8.0 pins; W5.7; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.7.0 image. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--w54", required=True, help="the W5.4 PR's state, e.g. 'merged as `1a2b3c4d`' or 'open, merge armed'")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = _PLAN.read_text(encoding="utf-8")
    pending = []
    done = 0
    for old, new in edits(args.w54):
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))
    row = _ROW.format(w54_pr=W54_PR, w54=args.w54, facility=FACILITY, band=BAND, round3=ROUND3, extras_pr=EXTRAS_PR, compose_pr=COMPOSE_PR, bench_pr=BENCH_PR, torch=TORCH, torch_fix=TORCH_FIX)
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

#!/usr/bin/env python3
"""Plan v1.7.9: W5.7 (the juniper-data producer guards: F-P5 / F-P6 / F-P8) built and opened as juniper-data#486.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.8 -> v1.7.9);
         juniper-data#486 (W5.7), util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py (what it applied);
         util/ad-hoc/2026-10-19_plan_v1_7_8_w5_4_landed.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-19_plan_v1_7_9_w5_7_opened.py --w57 "<juniper-data#486 state>" [--plan PATH] [--check]

``--w57`` is the state of the W5.7 PR at the time of the revision, e.g. "merged as `1a2b3c4d`" or "open, CI green".
``--plan`` points the script at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through
the API, so the upload is built on main's current file); the default is the repo's own copy.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

W57_PR = "juniper-data#486"
APPLY = "`util/ad-hoc/2026-10-19_apply_w5_7_producer_guards.py`"
SUMMARY = (
    "the two generators share one conditioning loop (`EquitiesGenerator._condition_universe`) that records every lost ticker with its reason; "
    "a lost **requested** symbol is refused with 422 under the shut `allow_truncation` gate (`rows_affected` 0; `incomplete_rows` not offered) and minted without it, "
    "recorded under `data_quality.dropped_symbols`, under the open one — a lost ticker of the default universe is recorded, never refused; "
    "for `equities_seq` a ticker with too few rows for one window is a loss too (it keeps its `ticker_vocab` slot, so existing ids keep their arrays); "
    "`_check_return_target_inputs` refuses `return` / `log_return` over a non-positive or non-finite `close` / `next_close` per ticker with a 400 naming the symbol, count and first session (`next_close` unguarded); "
    '`_condition_one` logs the `dividend` / `split_ratio` zero-fill at WARNING and records `data_quality.actions_present` (symbol → bool) — yfinance adds both columns under `actions=True`, so an absent one is an anomalous response the generator cannot tell from "no actions in range", hence recorded, never refused; '
    "`build_data_quality_meta` gains `dropped` / `actions_present`; the `equities_seq` docstring and `docs/REFERENCE.md` § Equities Data Quality Annotation document that `dataset_id` is request-addressed and the meta `checksum` is the content fingerprint; "
    "`generator_version` not bumped (as W1.8: a refused request mints nothing, every request that still mints emits the arrays it did); "
    "`tests/unit/test_equities_producer_guards.py` (35 tests), the OHLCV fixtures carry the two action columns"
)
TESTED = "250 passed over the nine equities-adjacent modules and 2182 / 1 environmental failure over the fast unit suite on turing; ruff clean"


def edits(w57: str) -> list[tuple[str, str]]:
    return [
        ("- **Version**: 1.7.8", "- **Version**: 1.7.9"),
        # Status line: the v1.7.9 clause.
        (
            "fixed for 0.8.0 by the second commit on juniper-recurrence#215 (`25b75832`)). The v1.4.0 plan edits follow that record",
            f"fixed for 0.8.0 by the second commit on juniper-recurrence#215 (`25b75832`)); **W5.7 built** (v1.7.9: {W57_PR}, {w57} — {SUMMARY}). The v1.4.0 plan edits follow that record",
        ),
        # F-P8 row: the guard exists.
        (
            "**accepted by the owner 2026-10-18** together with the W5.7 guard) |",
            f"**accepted by the owner 2026-10-18** together with the W5.7 guard; **guard built 2026-10-19**, {W57_PR}, {w57}) |",
        ),
        # W5.7 row.
        (
            "| W5.7 | F-P5, F-P6, **F-P8 (added v1.4.0)** | juniper-data | Record dropped-symbol list in `meta.data_quality`; refuse (or flag) when a **requested** symbol is lost; guard `close > 0` and finite before computing return targets. **F-P8 guard**: record whether yfinance's response carried the action columns (`actions_present` in meta), log the `dividend` / `split_ratio` zero-fill at WARNING, and document that `dataset_id` is request-addressed (refusal is a request-level choice — the generator cannot know whether actions exist in range). | Generator tests; a mint from a response without action columns carries `actions_present: false` and a WARNING. | S |",
            f'| W5.7 | F-P5, F-P6, **F-P8 (added v1.4.0)**; **built 2026-10-19** ({W57_PR}, {w57}) | juniper-data | Record dropped-symbol list in `meta.data_quality`; refuse (or flag) when a **requested** symbol is lost; guard `close > 0` and finite before computing return targets. **F-P8 guard**: record whether yfinance\'s response carried the action columns (`actions_present` in meta), log the `dividend` / `split_ratio` zero-fill at WARNING, and document that `dataset_id` is request-addressed (refusal is a request-level choice — the generator cannot know whether actions exist in range). **Built** ({W57_PR}, applied by {APPLY}): {SUMMARY}. Both halves of "refuse (or flag)" are taken: refuse for a named symbol under the shut gate, flag otherwise. | Generator tests; a mint from a response without action columns carries `actions_present: false` and a WARNING. **Done**: `TestActionColumns.test_seq_mint_without_action_columns_is_annotated_and_warns` pins that line; `TestLostRequestedSymbols` (11), `TestCloseGuard` (11), `TestDescriptorAndError` (6) pin the rest; {TESTED}. | S |',
        ),
        # P5 status row (the P5 of the P1-P5 roadmap: target summary, shared cache, producer guards).
        (
            "| **P5** | Target summary, shared cache, producer guards (W5.5–W5.7) | Planned | 5 | — |",
            f"| **P5** | Target summary, shared cache, producer guards (W5.5–W5.7) | **In progress** (W5.7 built 2026-10-19, {W57_PR}, {w57}; W5.5 / W5.6 planned) | 5 | — |",
        ),
        # Progress block: a W5.7 bullet before Next, and Next updated.
        (
            "  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 (re-run its failed lanes), recurrence 0.8.0, then juniper-recurrence#219; the extras / Compose pins follow 0.8.0 (recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`, image `0.8.0`); W5.7 (juniper-data). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes (now on the 0.7.0 image) and the client-docstring follow-up stay open.",
            f"  - **W5.7 built (turing session 3, later, 2026-10-19)**: {W57_PR} ({w57}; applied by {APPLY}) — {SUMMARY}. Verified on turing in a scratch venv (JuniperPython 3.14, pandas 3.0.1, yfinance 1.7.0): {TESTED}. Behaviour change to note for consumers: a multi-symbol request that loses a named symbol now gets 422 by default instead of a silently partial dataset (canopy's registry seeds and the E-H suite request `AAPL` alone, so they are unaffected); callers that relied on the silent shrink send `allow_truncation: true` and read `dropped_symbols`. It ships in juniper-data's next release (its `[Unreleased]`); the juniper-ml `[servers]` floor (`juniper-data>=0.17.0`) does not need to move for it. The model 0.6.0 `pypi` gate (run 39197693617) was still parked at the end of the session.\n  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 (re-run its failed lanes), recurrence 0.8.0, then juniper-recurrence#219; the extras / Compose pins follow 0.8.0 (recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`, image `0.8.0`); juniper-data's next release carries W5.7 (owner's cut). W5.5 / W5.6 (juniper-ml) are the remaining P5 rows. The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes (now on the 0.7.0 image) and the client-docstring follow-up stay open.",
        ),
    ]


_ROW_ANCHOR = "Owed: the gate, then #215 / 0.8.0 / #219 and the 0.8.0 pins; W5.7; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.7.0 image. | Paul Calnon |\n"
_ROW = (
    "| 2026-10-19 | 1.7.9 | **W5.7 built**: {w57_pr} ({w57}; applied by {apply}) — {summary}. Verified on turing: {tested}. "
    "Consumer note: a multi-symbol request that loses a named symbol now gets 422 by default (canopy's seeds and the E-H suite request `AAPL` alone); `allow_truncation: true` restores the partial mint, now annotated. "
    "Updated: Status line, F-P8 row, W5.7 row (both cells), the roadmap P5 status row, the Progress 2026-10-19 block. "
    "Owed: the model 0.6.0 gate, then #215 / 0.8.0 / #219 and the 0.8.0 pins; juniper-data's next release (W5.7); W5.5 / W5.6; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.7.0 image. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--w57", required=True, help="the W5.7 PR's state, e.g. 'merged as `1a2b3c4d`' or 'open, CI green'")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's copy)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    plan: Path = args.plan
    text = plan.read_text(encoding="utf-8")
    pending = []
    done = 0
    for old, new in edits(args.w57):
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))
    row = _ROW.format(w57_pr=W57_PR, w57=args.w57, apply=APPLY, summary=SUMMARY, tested=TESTED)
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
    plan.write_text(text, encoding="utf-8")
    print(f"applied {done + len(pending)} edits; change-log row {'added' if row_pending else 'already present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Consolidated development plan v1.15.0 -> v1.15.1: ml#2320's merge and re-check, ml#2330, and the owner's 0.11.2 ruling.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — one-off (a record revision of notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2210 / #2320 (merged f7a1442d); juniper-ml#2330; juniper-ml#2326 (R-ML-SERVERS floors, f823b0b7);
         util/ad-hoc/2026-10-25_apply_driver_budget_docs.py (the pattern this follows)

Why
---
v1.15.0 (ml#2325) landed while ml#2320 was merging. It names ml#2320 but not what it does, and it lists R-ML-SERVERS as
next. This revision records that session's work and the owner's ruling of 2026-10-25 that the next juniper-ml cut is
0.11.2, not the 0.12.0 ``util/release_train/detect.py`` proposes. The plan lands from turing as a whole file built from
a fresh ``origin/main`` copy, so every edit is anchored on text that must occur exactly once.

Usage
-----
    python3 util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py [--root DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found zero times or more than once refuses the
whole run before anything is written. ``--check`` writes nothing and exits 1 while an edit is pending.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    ("- **Version**: 1.15.0\n", "- **Version**: 1.15.1\n"),
    (
        "so no round checks v1.15.0, and each fact it adds names the probe or the record it came from. Every other path keeps v1.14.0's state and its staleness (Snapshot).\n",
        "so no round checks v1.15.0, and each fact it adds names the probe or the record it came from. Every other path keeps v1.14.0's state and its staleness (Snapshot).\n"
        "  - v1.15.1 (2026-10-25) records the P12 session that landed ml#2320 (ml#2210), and one owner ruling. ml#2320 merged and its post-merge re-check passed (XC-P12); its out-of-scope finding is ml#2330, asked in §6 Group C; R-ML-SERVERS's floors merged as ml#2326; and the owner ruled the next juniper-ml cut **0.11.2**, over the 0.12.0 that `util/release_train/detect.py` proposes (§5). Like v1.15.0, no round checks it.\n",
    ),
    (
        "The driver follow-ups filed on 2026-10-10 merged: ml#2211 as ml#2316, and ml#2210 as ml#2320.",
        "The driver follow-ups filed on 2026-10-10 merged: ml#2211 as ml#2316, and ml#2210 as ml#2320. ml#2316's post-merge re-check passed on `main` `899796d2`. "
        "ml#2320 (`f7a1442d`, 2026-10-25T18:12Z; v1.15.1) makes `run_suite` refuse a suite, before its first `--up`, whose `per_run_timeout_seconds` does not exceed a cell's worst-case driver budget. "
        "The driver's `worst_case_budget` sums the health waits, dataset creation, every wall-bounded phase and `save_model`, or cascor's teardown settle and `snapshot_at_end`. "
        "The nine recurrence suites, at 3900 s against 1200–1800, now carry 4500; the 20 cascor suites already cleared theirs. "
        "Its post-merge re-check passed on `main` `c86a5e5e`, four merges later. Its out-of-scope finding, E-C's wall budget, is ml#2330 (§6 Group C).",
    ),
    (
        "R-ML-SERVERS (§5), the recurrence-client 0.3.1 cut",
        "the juniper-ml 0.11.2 cut (§5; R-ML-SERVERS's floors merged as ml#2326; v1.15.1), the recurrence-client 0.3.1 cut",
    ),
    (
        "· W5.4 done · next: R-ML-SERVERS |",
        "· W5.4 done · R-ML-SERVERS's floors merged (ml#2326) · next: the juniper-ml 0.11.2 cut (owner ruling 2026-10-25) |",
    ),
    (
        "| **R-ML-SERVERS** (next; unblocked on 2026-10-25): a juniper-ml patch |",
        "| **R-ML-SERVERS** (floors merged as ml#2326, `f823b0b7`; the cut is juniper-ml **0.11.2** by the owner's ruling of 2026-10-25, over `detect.py`'s 0.12.0; v1.15.1): a juniper-ml patch |",
    ),
    (
        "; ml#2062's fix if it is ready |",
        "; ml#2062's fix if it is ready (ml#2333, open on 2026-10-25) |",
    ),
    (
        "7. R-ML-SERVERS, now that data 0.17.1 and cascor 0.12.0 are served. It waits on none of the steps above.\n",
        "7. R-ML-SERVERS: its floors merged as ml#2326 (2026-10-25), and the owner ruled the cut **0.11.2** (2026-10-25; `detect.py` proposed 0.12.0). The cut waits on none of the steps above (v1.15.1).\n",
    ),
    (
        "- **P10**: OD-7..OD-10.\n",
        "- **P10**: OD-7..OD-10.\n"
        "- **P12** (v1.15.1): ml#2330, E-C's wall budget against the R-6 gate's third contract. It fails only where juniper-cascor's `spiral-baseline.yaml` resolves, so CI never sees it. The options, from the issue:\n"
        "  1. raise E-C's budget, e.g. `execution.max_wall_seconds: 5400` (worst case 5850 s, under its 7200 s ceiling);\n"
        "  2. keep 3600 s and exempt E-C, on its own 517 s/cell measurement;\n"
        "  3. re-derive the cap threshold from post-#563 timings, which needs a fresh measurement.\n"
        "  Opened with the owner on 2026-10-25.\n",
    ),
    (
        "its facts cite the census, `util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py` and `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.7.16.\n",
        "its facts cite the census, `util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py` and `…EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` v1.7.16.\n"
        "  - v1.15.1 is a record of ml#2320's merge and re-check, ml#2330, ml#2326 and the owner's 0.11.2 ruling (2026-10-25). No round checks it (owner ruling 2026-10-24); its facts cite those PRs and `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_1_session_record.py`.\n",
    ),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = args.root / PLAN
    text = path.read_text(encoding="utf-8")
    pending = refused = 0
    for old, new in REPLACEMENTS:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new, 1)
        pending += 1
        print(f"  ~ {site}... {'pending' if args.check else 'applied now'}")

    if refused:
        print(f"REFUSED: {refused} anchor(s); nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

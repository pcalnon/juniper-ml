#!/usr/bin/env python
"""Record the 2026-09-23 replay-row verdicts (F-CANOPY-054, canopy#670) in the click-by-click matrix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 8);
         util/ad-hoc/2026-09-22_matrix_f053_rows.py (the pattern this follows)

Rewrites only the EXPECTED-RESULT cell (column 4) and the VERDICT cell (the last) of the seven replay
rows in ``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md``; every other cell
and row is left byte-for-byte. It refuses to run twice (the mark below), and it refuses when a row's
current verdict is not the one it was written against, so a concurrent edit cannot be clobbered.

Usage:  python3 util/ad-hoc/2026-09-23_matrix_f054_rows.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

MATRIX = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
MARK = "canopy#670"

PASS_658 = "PASS @ 2f2f5040 (canopy#658; 16 s settle)"
NOTE = (
    " **2026-09-23 on canopy#670's leg (`c0530279`), the replay block CLIENTSIDE (F-CANOPY-054):** re-driven at the 16 s settle"
    " (`util/ad-hoc/2026-09-08_replay_block_redrive.py`, store 116 rows); zero `replay-state` responses on the wire, the block no"
    " longer makes a round trip."
)
PASS_670 = "PASS @ c0530279 (canopy#670, clientside; 16 s settle; first PASS @ 2f2f5040, canopy#658)"

# row id -> (expected current verdict, text appended to the expected cell, new verdict)
EDITS = {
    "M-METRICS-11": (PASS_658, NOTE + " Start: `115 / 115 -> 0 / 115`.", PASS_670),
    "M-METRICS-12": (PASS_658, NOTE + " Step-back: `19 -> 18`, paused.", PASS_670),
    "M-METRICS-13": (
        "FAIL (F-CANOPY-054 on 2f2f5040; F-CANOPY-048 fixed by canopy#658)",
        NOTE
        + " Play `▶ -> ⏸` with the index advancing, then pause `⏸ -> ▶`, held. **The pause holds 3/3** in a store-series check"
        " (`util/ad-hoc/2026-09-23_f054_live_pause_check.py`: every replay-state write recorded; no `playing` write after the pause),"
        " against **F054-UNDONE 3/3 on the parent `2f973ca2`** in the same check (ledger Phase 8).",
        "PASS @ c0530279 (canopy#670; F-CANOPY-054 fixed; 16 s settle)",
    ),
    "M-METRICS-14": (PASS_658, NOTE + " Step-forward: `18 -> 19`, paused.", PASS_670),
    "M-METRICS-15": (PASS_658, NOTE + " End: `-> 115 / 115`.", PASS_670),
    "M-METRICS-16": (PASS_658, NOTE + " Speed: interval `1000 -> 500 -> 250 -> 1000` ms.", PASS_670),
    "M-METRICS-18": (PASS_658, NOTE + " Slider 9.6% -> position `11 / 115`, paused.", PASS_670),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    lines = MATRIX.read_text(encoding="utf-8").split("\n")
    done = set()
    for i, line in enumerate(lines):
        for rid, (want_verdict, add, new_verdict) in EDITS.items():
            if not line.startswith(f"| {rid} "):
                continue
            cells = line.split("|")
            verdict = cells[-2].strip()
            if MARK in cells[4] or MARK in verdict:
                print(f"REFUSED: {rid} already carries the {MARK} edit", file=sys.stderr)
                return 1
            if verdict != want_verdict:
                print(f"REFUSED: {rid} verdict is {verdict!r}, expected {want_verdict!r} -- re-read the matrix", file=sys.stderr)
                return 1
            cells[4] = cells[4].rstrip() + add + " "
            cells[-2] = f" {new_verdict} "
            lines[i] = "|".join(cells)
            done.add(rid)
            print(f"{rid}: {want_verdict!r} -> {new_verdict!r}")
    missing = set(EDITS) - done
    if missing:
        print(f"REFUSED: rows not found: {sorted(missing)}", file=sys.stderr)
        return 1
    if not args.dry_run:
        MATRIX.write_text("\n".join(lines), encoding="utf-8")
        print(f"wrote {MATRIX}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

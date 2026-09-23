#!/usr/bin/env python
"""Record the replay rows re-driven on canopy#670's REVISED fix (v2, 85415f3c) in the click-by-click matrix.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md (Phase 8, "Live verification of v2");
         util/ad-hoc/2026-09-23_matrix_f054_rows.py (the v1 edit this follows, and whose verdicts it expects)

Round 1 of review revised canopy#670 after the v1 verdicts were recorded. This appends the v2 evidence to
the EXPECTED-RESULT cell (column 4) of the seven replay rows and moves their VERDICT cell (the last) from
the v1 SHA to the v2 SHA. Every other cell and row is left byte-for-byte. It refuses to run twice (the mark
below), and it refuses when a row's verdict is not the v1 verdict it was written against.

Usage:  python3 util/ad-hoc/2026-09-23_matrix_f054_rows_v2.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

MATRIX = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
MARK = "85415f3c"

PASS_670 = "PASS @ c0530279 (canopy#670, clientside; 16 s settle; first PASS @ 2f2f5040, canopy#658)"
PASS_670_13 = "PASS @ c0530279 (canopy#670; F-CANOPY-054 fixed; 16 s settle)"
NOTE = (
    " **2026-09-23 on canopy#670's REVISED fix (`85415f3c`: events from values, after round 1 found a queued click could be"
    " dropped):** re-driven at the 16 s settle (`…_f054_v2_replay_block_redrive_8055_settle16.json`, store 116 rows), 7/7, zero"
    " `replay-state` responses on the wire."
)
PASS_V2 = "PASS @ 85415f3c (canopy#670 as revised; 16 s settle; first clientside PASS @ c0530279; first PASS @ 2f2f5040, canopy#658)"

EDITS = {
    "M-METRICS-11": (PASS_670, NOTE + " Start: `115 / 115 -> 0 / 115`.", PASS_V2),
    "M-METRICS-12": (PASS_670, NOTE + " Step-back: `20 -> 19`, paused.", PASS_V2),
    "M-METRICS-13": (
        PASS_670_13,
        NOTE
        + " Play `0 -> 8` advancing, pause held at 19. Clicks made DURING PLAYBACK applied 14 of 14 (5 pauses at 1x, 5 at 4x, 2 steps,"
        " 2 seeks; `util/ad-hoc/2026-09-23_f054_v2_live_check.py`), pause median 1.98 s.",
        "PASS @ 85415f3c (canopy#670 as revised; F-CANOPY-054 fixed; 16 s settle; first PASS @ c0530279)",
    ),
    "M-METRICS-14": (PASS_670, NOTE + " Step-forward: `19 -> 20`, paused.", PASS_V2),
    "M-METRICS-15": (PASS_670, NOTE + " End: `-> 115 / 115`.", PASS_V2),
    "M-METRICS-16": (PASS_670, NOTE + " Speed: interval `1000 -> 500 -> 250 -> 1000` ms.", PASS_V2),
    "M-METRICS-18": (PASS_670, NOTE + " Slider seeks during playback landed on their exact index (30% and 70%).", PASS_V2),
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

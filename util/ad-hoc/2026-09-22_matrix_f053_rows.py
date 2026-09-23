#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Record the 2026-09-22 row verdicts in the click-by-click matrix.

Rewrites only the EXPECTED-RESULT cell (column 4) and the VERDICT cell (the last) of the
named rows in ``notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md``;
every other cell, and every other row, is left byte-for-byte. It refuses to run twice, and
it refuses when a row's current verdict is not the one it was written against, so a
concurrent edit cannot be clobbered.

Why the expected results change as well as the verdicts. Round-2 review of F-CANOPY-053
found that M-CANDIDATES-01..06 state CONTENT ("Pool size; default '0'"), while the verdict
they carry ("PASS (re-validated @ f9defb4)") was scored on LIVENESS by the 2026-08-24
re-drive (badge Inactive->Training, pool 0->40). A mount default satisfies the text as
written. The criterion that was actually applied is made explicit here, and that is what
9bffaba1 fails.

Usage:  python3 util/ad-hoc/2026-09-22_matrix_f053_rows.py [--dry-run]
"""

import argparse
import sys
from pathlib import Path

MATRIX = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md"
MARK = "2026-09-22"
TRACK = " **Liveness (the criterion the 2026-08-24 re-drive scored): it TRACKS `/api/state` through a live candidate phase.**"
F053 = "FAIL @ 9bffaba1 (F-CANOPY-053; PASS on liveness @ f9defb4)"

# row id -> (expected current verdict, text appended to the expected cell, new verdict)
EDITS = {
    "M-CANDIDATES-01": ("PASS (re-validated @ f9defb4)", TRACK, F053),
    "M-CANDIDATES-02": ("PASS (re-validated @ f9defb4)", TRACK, F053),
    "M-CANDIDATES-03": ("PASS (re-validated @ f9defb4)", TRACK + " Pool size `0` against a server value of 8 fails it even at idle.", F053),
    "M-CANDIDATES-04": ("PASS (re-validated @ f9defb4)", TRACK,
                        "FAIL @ 9bffaba1 (INFERRED from F-CANOPY-053: the section was not read; PASS on liveness @ f9defb4)"),
    "M-CANDIDATES-06": ("PASS (re-validated @ f9defb4)", TRACK, F053),
    "M-CANDIDATES-07": ("FAIL",
                        " **Re-driven 2026-09-22 on `9bffaba1` with the row's own script (`util/ad-hoc/2026-09-22_m_candidates_07_row_check.py`):"
                        " RENDER PASS 4/4** (all 30 candidate points, 4.8-12.5 s after the tab opened; F-CANOPY-052 closed) **but THEME FAIL 3/3 at"
                        " F-CANOPY-004's 16 s interaction contract**: `theme-state` lands ~20 s after `#dark-mode-toggle`, and the figure re-themes at ~30 s.",
                        "FAIL @ 9bffaba1 (theme re-render outside F-CANOPY-004's contract; render PASS)"),
    "M-CANDIDATES-09": ("FAIL",
                        " **2026-09-22: cause attributed (INFERRED) to F-CANOPY-053**. The pool-history store is the second output of the same"
                        " writer, whose periodic writes never apply on `9bffaba1`; cards were not counted.",
                        "FAIL"),
}


REPLAY_NOTE = (" **2026-09-22 on `9bffaba1`: FAIL on F-CANOPY-048, with the store FULL** (80-95 rows). No replay-state write reached the wire"
                " across ten clicks in three runs, and the replay callbacks sat in the renderer's `requested` queue for the whole watch"
                " (the two-callback cycle; ledger Phase 7).")
F048 = "FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)"
REPLAY_EDITS = {rid: ("FAIL", REPLAY_NOTE, F048) for rid in ("M-METRICS-11", "M-METRICS-12", "M-METRICS-13", "M-METRICS-14", "M-METRICS-15", "M-METRICS-16")}
REPLAY_EDITS["M-METRICS-18"] = ("BLOCKED",
                                REPLAY_NOTE + " Lane A: keyboard and drag moved the slider 0 -> 10 -> 41, and `handle_replay_controls` never dispatched;"
                                " called directly it returns `9 / 94`. The gesture landed, so this is not BLOCKED (plan §9).",
                                "FAIL (F-CANOPY-048; was BLOCKED -- re-driven @ 9bffaba1 with the store full)")


F053_FAIL = "FAIL @ 9bffaba1 (F-CANOPY-053; PASS on liveness @ f9defb4)"
FIX_NOTE_657 = (" **Verified live on canopy#657's leg (`17588539`), a growth window 62 -> 68, one tab per browser: the DOM tracked"
                " `/api/state` with a ~10-20 s lag** (badge `Inactive -> Training -> Inactive`, pool size `0 -> 8`, progress `501/3000`,"
                " pool info -> top-2 table, history cards `0 -> 2 -> 6`).")
PASS_657 = "PASS @ 17588539 (canopy#657; was FAIL @ 9bffaba1 on F-CANOPY-053)"
FIX_NOTE_658 = (" **Verified live on canopy#658's leg (`2f2f5040`) at F-CANOPY-004's 16 s settle**: the control's write reaches the wire"
                " and applies (store 116 rows).")
PASS_658 = "PASS @ 2f2f5040 (canopy#658; 16 s settle)"
FIX_EDITS = {
    "M-CANDIDATES-01": (F053_FAIL, FIX_NOTE_657, PASS_657),
    "M-CANDIDATES-02": (F053_FAIL, FIX_NOTE_657, PASS_657),
    "M-CANDIDATES-03": (F053_FAIL, FIX_NOTE_657, PASS_657),
    "M-CANDIDATES-04": ("FAIL @ 9bffaba1 (INFERRED from F-CANOPY-053: the section was not read; PASS on liveness @ f9defb4)", FIX_NOTE_657,
                        "PASS @ 17588539 (canopy#657; read directly -- 501/3000 shown, then hidden)"),
    "M-CANDIDATES-06": (F053_FAIL, FIX_NOTE_657, PASS_657),
    "M-CANDIDATES-09": ("FAIL", FIX_NOTE_657 + " The `MAX_POOL_HISTORY_ENTRIES` cap was not exercised (6 entries).",
                        "PASS @ 17588539 (canopy#657; cards rendered 0 -> 2 -> 6; cap not exercised)"),
    "M-METRICS-11": ("FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)", FIX_NOTE_658 + " Start: `115 / 115 -> 0 / 115`.", PASS_658),
    "M-METRICS-12": ("FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)", FIX_NOTE_658 + " Step-back: `2 -> 1`, paused.", PASS_658),
    "M-METRICS-13": ("FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)",
                     FIX_NOTE_658 + " Play works (`▶ -> ⏸`, mode `playing`), but the PAUSE is undone or flickers when a late `replay_tick`"
                     " response computed from pre-click State lands after it (2 of 2 runs): **F-CANOPY-054**.",
                     "FAIL (F-CANOPY-054 on 2f2f5040; F-CANOPY-048 fixed by canopy#658)"),
    "M-METRICS-14": ("FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)", FIX_NOTE_658 + " Step-forward: `0 -> 1`, paused.", PASS_658),
    "M-METRICS-15": ("FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)", FIX_NOTE_658 + " End: `-> 115 / 115`.", PASS_658),
    "M-METRICS-16": ("FAIL (F-CANOPY-048; re-driven @ 9bffaba1 with the store full)", FIX_NOTE_658 + " Speed: interval `1000 -> 500 -> 250 -> 1000` ms.", PASS_658),
    "M-METRICS-18": ("FAIL (F-CANOPY-048; was BLOCKED -- re-driven @ 9bffaba1 with the store full)",
                     FIX_NOTE_658 + " Slider 9.6% -> position `11 / 115`, paused.", PASS_658),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--set", choices=("candidates", "replay", "fixes"), default="candidates")
    args = ap.parse_args()
    global EDITS, MARK
    if args.set == "replay":
        EDITS = REPLAY_EDITS
    elif args.set == "fixes":
        EDITS, MARK = FIX_EDITS, "Verified live on canopy#65"
    lines = MATRIX.read_text(encoding="utf-8").split("\n")
    done = set()
    for i, line in enumerate(lines):
        for rid, (want_verdict, add, new_verdict) in EDITS.items():
            if not line.startswith(f"| {rid} "):
                continue
            cells = line.split("|")
            # cells[0] == "" (before the first pipe), cells[-1] == "" (after the last)
            verdict = cells[-2].strip()
            if MARK in cells[4] or (EDITS is not FIX_EDITS and rid not in ("M-CANDIDATES-09",) and "9bffaba1" in verdict):
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

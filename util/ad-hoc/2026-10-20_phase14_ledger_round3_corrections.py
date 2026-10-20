#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : canopy E2E validation arc
# Author      : Paul Calnon
# License     : MIT License
# Created     : 2026-10-20
# Status      : ad-hoc — one-off correction pass; RETAINED as provenance (owner policy 2026-08-25)
# Retire when : RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related     : ledger Phase 14 (notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md);
#               util/ad-hoc/2026-10-20_phase14_ledger_round2_corrections.py (the pass this closes)
# ---------------------------------------------------------------------------
"""Round 3's closing pass on the ledger's Phase 14: the wording round 3 found, and the round-3 record.

Applied to the files as frozen for round 3 (local commit ``f5ebf4e7``). Round 3's two reports (Lanes 14-B and 14-C,
resumed on round 2's pass) are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round3.md``. Both state that nothing in
the round changes a number, a disposition, a rating, a count, an item or an action, which is §4's termination test;
the review ends with this pass, which changes wording only:

* [B1] run 2's clause names the writer firings its transcript does carry (second render 9.1 s after the mount render,
  the click 17.7 s after that), so "eleven arms" adds up while its after-reload delay stays unrecorded.
* [B2, C2] the window's lower bound was a guess: the one hit on the record is 7.9 s after the mount render, 2.8 s before
  its render; the fix direction and item 31 say so, and say that the driver's arms are fixed delays after the reload,
  so a re-drive needs a pin-delay knob (or reads each pin's position from the writer firings and repeats until the
  window is sampled).
* [B3] the round-2 record's "every round-1 defect answered" excepts the one Lane 14-C listed as not done (run 2's 27.9 s,
  fixed in round 2).
* [B] the handoff's Completed bullet still carried "8–9.5 s … which is the window"; it now carries round 2's reading.
* [C1] the round-1 record's Lane 14-A sentence gains a clause pointing at round 2's correction of its figures.

Usage:
    python3 util/ad-hoc/2026-10-20_phase14_ledger_round3_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"

LEDGER_SUBS = [
    # --- B1: run 2's firings ---
    (
        "> which stands here as a lead, not a fact); run 2 at the settled timing by design, unrecorded (both kept); run 3\n"
        "> settled at 27.9 s and early at\n",
        "> which stands here as a lead, not a fact); run 2 at the settled timing by design, its after-reload delay unrecorded\n"
        "> but its writer firings in the transcript (the second render 9.1 s after the mount render, the click 17.7 s after\n"
        "> that; both kept); run 3 settled at 27.9 s and early at\n",
    ),
    # --- B2, C2: the window's lower bound, and the driver ---
    (
        "> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix,\n"
        "> timing the pin BEFORE the second render (about 4–8 s after the mount render's writer firing; the render came\n"
        "> 7.9–10.7 s after it across eleven arms), with enough repeats to put a rate on it.\n",
        "> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix,\n"
        "> timing the pin BEFORE the second render: the render came 7.9–10.7 s after the mount render's writer firing\n"
        "> across eleven arms, and the one hit on the record was a pin 7.9 s after that firing, 2.8 s before its render;\n"
        "> where the band begins is not measured. The driver's arms are fixed delays after the reload, so a re-drive\n"
        "> needs a pin-delay knob, or reads each pin's position from `pin_requests_after_reload` and repeats until the\n"
        "> window is sampled, with enough hits to put a rate on it.\n",
    ),
    (
        "    the parent first with the pin timed BEFORE the second table render (about 4–8 s after the mount render's\n"
        "    writer firing; the render came 7.9–10.7 s after it across eleven arms, and every pin made after it survived)\n"
        "    to put a rate on the loss, which this phase measured once in eight.\n",
        "    the parent first with the pin timed BEFORE the second table render (it came 7.9–10.7 s after the mount\n"
        "    render's writer firing across eleven arms; every pin made after it survived, the one made 7.9 s after that\n"
        "    firing, 2.8 s before its render, was lost; where the band begins is not measured). The driver's arms are\n"
        "    fixed delays after the reload, so this needs a pin-delay knob in `2026-10-20_item30_fixwave_redrive.py`, or\n"
        "    repeats of the early arm with each pin's position read from `pin_requests_after_reload`, to put a rate on\n"
        "    the loss, which this phase measured once in eight.\n",
    ),
    # --- B3: the round-2 record's summary sentence ---
    (
        "  Both found every round-1 defect answered as the evidence demands and the replay byte-identical (Lane 14-C from\n",
        "  Both found every round-1 defect but one answered as the evidence demands (run 2's \"27.9 s\", Lane 14-C's, fixed\n"
        "  in this round) and the replay byte-identical (Lane 14-C from\n",
    ),
    # --- C1: the round-1 record's Lane 14-A sentence ---
    (
        "    arm). Every scored figure agreed. Its four f028 arms lost no pin, and all four show the second non-user\n"
        "    re-render 8–9.5 s after the mount render that `early#2` ran into.\n",
        "    arm). Every scored figure agreed. Its four f028 arms lost no pin, and all four show the second non-user\n"
        "    re-render 8–9.5 s after the mount render that `early#2` ran into (as round 1 wrote it; its table reads\n"
        "    7.9–9.1 s, and `early#2`'s render came 10.7 s after the mount render, after the click: round 2).\n",
    ),
    # --- the round-3 record ---
    (
        "- **Round 3**: two lanes on round 2's pass, by §4 (round 2 changed an action's parameter). _(filled by the round-3\n"
        "  script)_\n",
        "- **Round 3**: Lanes 14-B and 14-C resumed on the frozen `f5ebf4e7` (round 2's pass applied, the round-2 reports\n"
        "  archived), briefed on that pass alone (`reports/e2e-canopy-2026-09-02/drafts/lane14R3_phase14_ledger_brief.md`);\n"
        "  reports verbatim in `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round3.md`.\n"
        "  Both SOUND-WITH-FIXES; both recomputed the window from the record and Lane 14-A's table and found the three\n"
        "  sites' figures exact and consistent; both replayed all three passes from `3989fa83` byte for byte; **both state\n"
        "  that nothing in the round changes a number, a disposition, a rating, a count, an item or an action**, which is\n"
        "  §4's termination test, so the review ended here. The wording the round found is applied by\n"
        "  `util/ad-hoc/2026-10-20_phase14_ledger_round3_corrections.py` without a further round: run 2's clause names the\n"
        "  writer firings its transcript carries, so \"eleven arms\" adds up (Lane 14-B); the window's \"about 4–8 s\" was a\n"
        "  guess with one datum, 7.9 s, and the driver's arms are fixed delays after the reload, so item 31 now asks for a\n"
        "  pin-delay knob or a reading of each pin's position (Lanes 14-B and 14-C); the round-2 record's \"every round-1\n"
        "  defect answered\" excepts the one Lane 14-C had listed as not done (Lane 14-B); the handoff's Completed bullet\n"
        "  still carried round 1's \"8–9.5 s … which is the window\" (Lane 14-B); the round-1 record's Lane 14-A sentence\n"
        "  points at round 2's correction of its figures (Lane 14-C). The PR and branch the handoff names exist from the\n"
        "  landing on (Lane 14-C, carried from round 1).\n"
        "- **Iterations.** Three. Round 1 changed what the phase said about its own evidence (one of two F-CANOPY-028\n"
        "  losses unrecorded) and how the phase lands (the transcripts, the screenshots); round 2 changed the parameter of\n"
        "  one action (item 31's timing); round 3 changed wording. No disposition, rating or count changed in any round.\n",
    ),
]

HANDOFF_SUBS = [
    (
        "  `util/ad-hoc/2026-10-20_phase14_rebuild_shared_files_for_landing.py` (rebuilds the shared files from `origin/main`\n"
        "  by replaying the passes, for the API landing);\n",
        "  `util/ad-hoc/2026-10-20_phase14_rebuild_shared_files_for_landing.py` (rebuilds the shared files from `origin/main`\n"
        "  by replaying the passes, for the API landing); `util/ad-hoc/2026-10-20_push_signed_with_body_retry.py` (the\n"
        "  large files' signed commits, each with the session's trailer, retried through the link);\n",
    ),
    (
        "    canopy#533 did not address; a validator lane's four arms found the same second render 8–9.5 s after the\n"
        "    mount render, which is the window.\n",
        "    canopy#533 did not address; a validator lane's four arms and the reconciler's five kept arms show the same\n"
        "    second render 7.9–10.2 s after the mount render, and every pin made after it survived: the window is the\n"
        "    seconds before it.\n",
    ),
    (
        "conventions): SOUND / SOUND-WITH-FIXES / SOUND-WITH-FIXES; round 2, two lanes on the corrections, changed one\n"
        "action's parameter (item 31's pin window); round 3 on that pass (ledger Phase 14, Consensus record).\n",
        "conventions): SOUND / SOUND-WITH-FIXES / SOUND-WITH-FIXES; round 2, two lanes on the corrections, changed one\n"
        "action's parameter (item 31's pin window); round 3 on that pass changed wording only, so the review ended there\n"
        "(ledger Phase 14, Consensus record).\n",
    ),
]


def apply(text: str, subs: list, label: str) -> str:
    for old, new in subs:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"{label}: anchor occurs {n} times, expected 1: {old[:100]!r}")
        text = text.replace(old, new, 1)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    ledger = (root / LEDGER).read_text(encoding="utf-8")
    assert "- **Round 3**: Lanes 14-B and 14-C resumed" not in ledger, "round 3 already applied"
    out = {LEDGER: apply(ledger, LEDGER_SUBS, "ledger"), HANDOFF: apply((root / HANDOFF).read_text(encoding="utf-8"), HANDOFF_SUBS, "handoff")}
    if args.check:
        print("check OK: every anchor unique")
        return 0
    for rel, text in out.items():
        (root / rel).write_text(text, encoding="utf-8")
        print("corrected", rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

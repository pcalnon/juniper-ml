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
#               util/ad-hoc/2026-10-20_phase14_ledger_round1_corrections.py (the pass this corrects)
# ---------------------------------------------------------------------------
"""Round 2's correction pass on the ledger's Phase 14: what round 1's pass broke, and what it left.

Applied to the files as frozen for round 2 (local commit ``68278cf9``). Round 2's two reports (Lanes 14-B and 14-C,
resumed and briefed on the corrections) are archived verbatim in
``reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round2.md``. Every substitution is
anchored to occur exactly once and is credited to the lane that raised it; the reconciler re-derived each from the
record or the source before applying it. The pass also appends the round-2 record to Phase 14's consensus record.

What it changes (lane in brackets):

* MAJOR, an action's parameter [C1]: round 1 told item 31 to time the pin "8–10 s after the mount render", which is
  AFTER the second table render in most arms, where every pin survived; the one loss was a pin made BEFORE it. The
  blockquote, the fix direction and item 31 now say before the second render (about 4–8 s after the mount render's
  writer firing; the render came 7.9–10.7 s after it across eleven arms), and the phase's own five kept arms are
  credited with the same corroboration as Lane 14-A's four (second render 7.9–10.2 s after the mount render,
  0.9–18.5 s before each click). Lane 14-A's figure is restated from its table (7.9–9.1 s), not its prose.
* [C2] run 2's "27.9 s" has no record; it is the settled timing by design, unrecorded.
* [B1, C3] "3.4 s after the click" is read-to-read; now "within 3.4 s of the click" (blockquote, "cannot support",
  consensus record).
* [B2] "the capture keeps only the writer's own bodies" was wrong; it keeps every body naming the pin store, and misses
  a table render triggered by the params store alone.
* [B3, C4] "a click's render in 1.4–5.4 s" → the record's "first observable effect in 0.4–6.5 s".
* [B4] ``_merge_pinned_params`` is ``:7320-7348`` (round 1 over-corrected to 7349, a blank line).
* [B5, C6] the three screenshot cites say the files stay on turing.
* [B6, C7] the consensus record gains the §7 element it lacked, "what the evidence cannot support".
* [B7] "canopy's the supervisor's" → "canopy's log the supervisor's".
* [C5] ``create_callback_id`` runs ``:138-166`` in dash 3.x and ``:146-188`` in 4.4.1; ``callback_map`` is at
  ``_callback.py:311`` in 3.3.0 and ``:338`` in 4.4.1.
* [C8] the handoff's Created list names the landing helper ``2026-10-20_phase14_rebuild_shared_files_for_landing.py``.

Usage:
    python3 util/ad-hoc/2026-10-20_phase14_ledger_round2_corrections.py [--check] [--root DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LEDGER = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_canopy-phase14-item30-done-f069-dash3-inert.md"

LEDGER_SUBS = [
    # --- C1 (MAJOR): the window ---
    (
        "> made was gone, the card showing `Learning Rate 0.01` alone. A validator lane's four arms of the same drive (round\n"
        "> 1, Lane 14-A) lost no pin and show the same three firings each time: the mount render, **a second non-user\n"
        "> re-render 8–9.5 s after it**, and the click; in its arms the second render landed 0.8–10.8 s BEFORE the click,\n"
        "> carrying the set it was computed from, and nothing was lost. In `early#2` the click fell 7.9 s after the mount\n"
        "> render and the second render 2.8 s after the click. **The window is that second render**: a pin made in the\n"
        "> seconds before it is computed out of the table it rebuilds.\n",
        "> made was gone, the card showing `Learning Rate 0.01` alone. This phase's five kept arms show the same three\n"
        "> firings: the mount render, **a second non-user re-render 7.9–10.2 s after it**, and the click, which came\n"
        "> 0.9–18.5 s AFTER the second render in each of them, so the render carried the set it was computed from and the\n"
        "> click's writer wrote over it with both keys. A validator lane's four arms of the same drive (round 1, Lane 14-A)\n"
        "> lost no pin and show the same shape, its second render 7.9–9.1 s after the mount render and 0.8–10.8 s before\n"
        "> each click. In `early#2` alone the order was inverted: the click fell 7.9 s after the mount render and the second\n"
        "> render 2.8 s after the click. **The window is the seconds BEFORE that second render**: a pin made then is computed\n"
        "> out of the table it rebuilds; across the eleven arms every pin made after it survived, and the one made before\n"
        "> it was lost.\n",
    ),
    (
        "> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix,\n"
        "> timing the pin into the window (8–10 s after the mount render), with enough repeats to put a rate on it.\n",
        "> from a stale pin set after a toggle and asserts the store keeps the toggle. Re-drive the early arm on the fix,\n"
        "> timing the pin BEFORE the second render (about 4–8 s after the mount render's writer firing; the render came\n"
        "> 7.9–10.7 s after it across eleven arms), with enough repeats to put a rate on it.\n",
    ),
    (
        "    the parent first with the pin timed into the window (8–10 s after the mount render) to put a rate on the\n"
        "    loss, which this phase measured once in eight.\n",
        "    the parent first with the pin timed BEFORE the second table render (about 4–8 s after the mount render's\n"
        "    writer firing; the render came 7.9–10.7 s after it across eleven arms, and every pin made after it survived)\n"
        "    to put a rate on the loss, which this phase measured once in eight.\n",
    ),
    # --- C2: run 2's timing ---
    (
        "> which stands here as a lead, not a fact); run 2 at 27.9 s (both kept); run 3 settled at 27.9 s and early at\n",
        "> which stands here as a lead, not a fact); run 2 at the settled timing by design, unrecorded (both kept); run 3\n"
        "> settled at 27.9 s and early at\n",
    ),
    # --- B1, C3: read-to-read ---
    (
        "> eight second pins, by their delay after the reload: run 1 at ~10 s by the driver's design (its only surviving\n"
        "> read, 3.4 s after the click, has the SECOND pin absent, `store=['learning_rate']`, and its M-06 read the card\n",
        "> eight second pins, by their delay after the reload: run 1 at ~10 s by the driver's design (its only surviving\n"
        "> read, within 3.4 s of the click, has the SECOND pin absent, `store=['learning_rate']`, and its M-06 read the card\n",
    ),
    (
        "  was saved, and its transcript carries only a store read 3.4 s after the second pin, with that pin absent and\n",
        "  was saved, and its transcript carries only a store read within 3.4 s of the second pin, with that pin absent and\n",
    ),
    (
        "    artifact supports: the run-1 transcript reads the SECOND pin absent 3.4 s after the click, and the\n",
        "    artifact supports: the run-1 transcript reads the SECOND pin absent within 3.4 s of the click, and the\n",
    ),
    # --- B2: the capture sentence ---
    (
        "> pinned_set` from the pin set THAT callback received (`:114-118`). What triggers the second render is inferred,\n"
        "> not captured (the capture keeps only the writer's own bodies): the params store filling late on a fresh session\n",
        "> pinned_set` from the pin set THAT callback received (`:114-118`). What triggers the second render is inferred,\n"
        "> not captured (the capture keeps the bodies that name the pin store, so a table render triggered by the params\n"
        "> store alone is not in it): the params store filling late on a fresh session\n",
    ),
    # --- B3, C4 ---
    (
        "  sessions; the latencies here (a click's render in 1.4–5.4 s) fit F-CANOPY-004's contract and are not comparable\n",
        "  sessions; the latencies here (a click's first observable effect in 0.4–6.5 s) fit F-CANOPY-004's contract and are not comparable\n",
    ),
    # --- B4 ---
    (
        "> the two `[]` writes at mount in every drive are those), and `_merge_pinned_params` (`:7320-7349`) does what\n",
        "> the two `[]` writes at mount in every drive are those), and `_merge_pinned_params` (`:7320-7348`) does what\n",
    ),
    (
        "    `execute_restart` `:6478-6510`, `_merge_pinned_params` `:7320-7349`); the 3.1.1 wheel dropped from the list.\n",
        "    `execute_restart` `:6478-6510`, `_merge_pinned_params` `:7320-7348`); the 3.1.1 wheel dropped from the list.\n",
    ),
    # --- B5, C6: screenshot cites ---
    (
        "> `dashboard_manager.py:7350-7372` at `571743db`), holds live. Shots `reports/e2e-canopy-2026-09-02/item30-turing/shots/f001_dark.png`,\n"
        "> `f001_after_reload.png`.\n",
        "> `dashboard_manager.py:7350-7372` at `571743db`), holds live. Shots `reports/e2e-canopy-2026-09-02/item30-turing/shots/f001_dark.png`,\n"
        "> `f001_after_reload.png` (on turing, not landed: PNGs are LFS pointers in this repo).\n",
    ),
    (
        "> `reports/e2e-canopy-2026-09-02/item30-turing/service_leg_8064_dash441.json`, step `f012`; shots `reports/e2e-canopy-2026-09-02/item30-turing/shots/f012_*.png`). The editor's active block\n",
        "> `reports/e2e-canopy-2026-09-02/item30-turing/service_leg_8064_dash441.json`, step `f012`; shots `reports/e2e-canopy-2026-09-02/item30-turing/shots/f012_*.png`, on turing, not landed). The editor's active block\n",
    ),
    (
        "> confirm the edit\", now confirms what happened. Shots `reports/e2e-canopy-2026-09-02/item30-turing/shots/f013_append.png`, `f013_remove.png`.\n",
        "> confirm the edit\", now confirms what happened. Shots `reports/e2e-canopy-2026-09-02/item30-turing/shots/f013_append.png`, `f013_remove.png` (on turing, not landed).\n",
    ),
    # --- B7 ---
    (
        "> rejection per 30 s reconnect and canopy's the supervisor's disconnects): `/api/stream_health` read `overall: \"degraded\"` with the\n",
        "> rejection per 30 s reconnect and canopy's log the supervisor's disconnects): `/api/stream_health` read `overall: \"degraded\"` with the\n",
    ),
    # --- C5: cites ---
    (
        "The Python side is the same everywhere: `create_callback_id` (`dash/_utils.py:138-164` in 3.0.4, 3.2.0, 3.3.0 and\n"
        "3.4.0, `:146-186` in 4.4.1, which adds a branch for callbacks with no output and no inputs that does not touch\n"
        "this) suffixes an `allow_duplicate` output with `@sha256(\".\".join(str(x) for x in inputs))`, so two callbacks\n"
        "with the same output and the same inputs get the same id, and the server registers both (`callback_map` keyed by\n"
        "that id, `dash/_callback.py:311`, the second overwriting the first's entry; the dependency list served to the\n",
        "The Python side is the same everywhere: `create_callback_id` (`dash/_utils.py:138-166` in 3.0.4, 3.2.0, 3.3.0 and\n"
        "3.4.0, `:146-188` in 4.4.1, which adds a branch for callbacks with no output and no inputs that does not touch\n"
        "this) suffixes an `allow_duplicate` output with `@sha256(\".\".join(str(x) for x in inputs))`, so two callbacks\n"
        "with the same output and the same inputs get the same id, and the server registers both (`callback_map` keyed by\n"
        "that id, `dash/_callback.py:311` in 3.3.0 and `:338` in 4.4.1, the second overwriting the first's entry; the dependency list served to the\n",
    ),
    (
        "(`dash/_utils.py:138-164` in 3.0.4, 3.2.0, 3.3.0 and 3.4.0, `:146-186` in 4.4.1; the `allow_duplicate` suffix is\n",
        "(`dash/_utils.py:138-166` in 3.0.4, 3.2.0, 3.3.0 and 3.4.0, `:146-188` in 4.4.1; the `allow_duplicate` suffix is\n",
    ),
    (
        "callback registry is a dict keyed by the id, `_callback.py:311`, and the second registration overwrites the\n",
        "callback registry is a dict keyed by the id, `_callback.py:311` in 3.3.0 and `:338` in 4.4.1, and the second registration overwrites the\n",
    ),
    (
        "    population figure marked as unarchived and the contract's; line cites (`_utils.py:138-164` / `:146-186`,\n",
        "    population figure marked as unarchived and the contract's; line cites (`_utils.py:138-164` / `:146-186`, both\n"
        "    corrected again in round 2,\n",
    ),
    # --- B6, C7 + the round-2 record ---
    (
        "  The instrument reads DOM, store, request and cascor state; it cannot score a VIS half here, and it could have\n"
        "  produced a different answer only on the f028 race, which is timing-dependent by its nature.\n",
        "  The instrument reads DOM, store, request and cascor state; it cannot score a VIS half here, and it could have\n"
        "  produced a different answer only on the f028 race, which is timing-dependent by its nature.\n"
        "- **What the evidence cannot support** is \"What this phase cannot support\" above, as the rounds left it: one host,\n"
        "  dash 4.4.1 not 4.2.0, no VIS half, this host's latencies, F-CANOPY-028's first loss unrecorded and its rate\n"
        "  unmeasured (item 31), F-CANOPY-032 closed on a reading, F-CANOPY-069's dash 4 behaviour unmeasured (item 32).\n"
        "- **Round 2**: Lanes 14-B and 14-C resumed on the frozen `68278cf9` (round 1's pass applied, the round-1 reports\n"
        "  archived, the 20 screenshots withdrawn and the transcripts force-added), briefed on the corrections alone\n"
        "  (`reports/e2e-canopy-2026-09-02/drafts/lane14R2_phase14_ledger_brief.md`); reports verbatim in\n"
        "  `reports/e2e-canopy-2026-09-02/consensus/2026-10-20_validator_reports_phase14_round2.md`. Both SOUND-WITH-FIXES.\n"
        "  Both found every round-1 defect answered as the evidence demands and the replay byte-identical (Lane 14-C from\n"
        "  `3989fa83`, Lane 14-B from `5a383ae1`), and both state that nothing changes a disposition, a rating, a count or\n"
        "  an item. **What round 2 changed** (`util/ad-hoc/2026-10-20_phase14_ledger_round2_corrections.py`): Lane 14-C's\n"
        "  MAJOR, the parameter of an action: round 1's pass told item 31 to time the pin 8–10 s after the mount render,\n"
        "  which is after the second table render in most arms, where every pin survived; the loss on the record was the\n"
        "  pin made before it (7.9 s, the render at 10.7 s). The blockquote, the fix direction and item 31 now say before\n"
        "  the second render, about 4–8 s after the mount render's writer firing, and the phase's own five kept arms carry\n"
        "  the corroboration round 1 credited to Lane 14-A alone (second render 7.9–10.2 s after the mount render,\n"
        "  0.9–18.5 s before each click), Lane 14-A's figure being restated from its table (7.9–9.1 s). The minors: run 2's\n"
        "  \"27.9 s\" has no record (Lane 14-C); \"3.4 s after the click\" is read-to-read, now \"within 3.4 s\" (both); the\n"
        "  capture keeps every body naming the pin store, not only the writer's (Lane 14-B); \"a click's render in\n"
        "  1.4–5.4 s\" is now the record's 0.4–6.5 s (both); `_merge_pinned_params` ends at `:7348` (Lane 14-B; round 1 had\n"
        "  followed an off-by-one); `create_callback_id` runs `:138-166` and `:146-188`, `callback_map` at `:311` and\n"
        "  `:338` (Lane 14-C); the three screenshot cites say the files stay on turing (both); this record's missing §7\n"
        "  element (both); a grammar slip (Lane 14-B); the handoff's Created list names the landing helper (Lane 14-C).\n"
        "- **Round 3**: two lanes on round 2's pass, by §4 (round 2 changed an action's parameter). _(filled by the round-3\n"
        "  script)_\n",
    ),
]

HANDOFF_SUBS = [
    (
        "  `util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py`; `util/ad-hoc/2026-10-20_phase14_item30_apply.py`;\n",
        "  `util/ad-hoc/2026-10-20_cascor_leg_prepare_investigating.py`; `util/ad-hoc/2026-10-20_phase14_item30_apply.py`;\n"
        "  `util/ad-hoc/2026-10-20_phase14_rebuild_shared_files_for_landing.py` (rebuilds the shared files from `origin/main`\n"
        "  by replaying the passes, for the API landing);\n",
    ),
    (
        "**Consensus**: round 1 on 2026-10-20, three lanes (measurement re-creation, adversarial analysis, replay and\n"
        "conventions): SOUND / SOUND-WITH-FIXES / SOUND-WITH-FIXES; round 2 on the corrections (ledger Phase 14, Consensus record).\n",
        "**Consensus**: round 1 on 2026-10-20, three lanes (measurement re-creation, adversarial analysis, replay and\n"
        "conventions): SOUND / SOUND-WITH-FIXES / SOUND-WITH-FIXES; round 2, two lanes on the corrections, changed one\n"
        "action's parameter (item 31's pin window); round 3 on that pass (ledger Phase 14, Consensus record).\n",
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
    assert "- **Round 2**: Lanes 14-B and 14-C resumed" not in ledger, "round 2 already applied"
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

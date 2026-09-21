#!/usr/bin/env python3
"""Two APD-CASCOR-005 sentences the close's whole-file sweep caught by READING, not grepping.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#659, juniper-ml#1974, and 2026-09-21_register_close_cascor005.py

THIS SCRIPT IS THE PROTOCOL WORKING. The close protocol says: run a whole-file
``grep -n 'APD-<ID>'`` and **read every hit** -- and records why reading, not grepping, is the
requirement (a closure once left a sentence standing because the grep found it and the author
skimmed past). Both fixes below were found that way, and the first is a defect the closing script
itself introduced.

1. §4.3's routing note. The close prepended a SUPERSEDED marker anchored on a phrase in the
   MIDDLE of the paragraph, so the note still OPENED with "This row is an **owner decision, not a
   task**" as present fact, and the marker then said "The routing below was correct" while
   pointing at text ABOVE it. A reader scanning for the row's status would have read the stale
   first sentence and stopped. The marker moves to the head of the note, and the mid-paragraph
   insert is reverted to the sentence it displaced.

2. §6's Confidence note lists the `Low`-confidence entries "to triage before being actioned", and
   marks the closed ones with a strikethrough plus the PR -- ``~~`APD-DATA-033`~~ (fixed,
   data#297)``. `APD-CASCOR-005` is now closed and was still listed bare, so the list asserted it
   was awaiting triage. Following the convention that is already there beats inventing a second
   one.

Neither is caught by any count-based check: both sentences make a claim about the row's status
while the row's own marker says FIXED, which is exactly the "register disagrees with itself while
every count-based check still passes" failure the five-touch protocol exists to prevent.
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

_CASCOR_PR = "[juniper-cascor#659](https://github.com/pcalnon/juniper-cascor/pull/659)"
_ML_PR = "[juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974)"

# --- 1a: revert the mid-paragraph insert back to the sentence it displaced -----------------
MIDPARA_OLD = (
    "**SUPERSEDED 2026-09-21.** The routing below was correct while the row awaited a ruling. The owner "
    "ruled on 2026-09-09 (port the `matched`-flag loop; rejected: accept and document the residual leak) "
    f"and it shipped as {_CASCOR_PR} + "
    f"{_ML_PR}. Note also that \"the three copies\" "
    "is itself wrong — there are four; see the row. The original instruction, left standing because it is "
    "what the ruling overrode: **Do not unify the three copies unilaterally.**"
)
MIDPARA_NEW = "**Do not unify the three copies unilaterally.**"

# --- 1b: put the marker where a reader meets it first --------------------------------------
HEAD_OLD = "**`APD-CASCOR-005` routing.** This row is an **owner decision, not a task**."
HEAD_NEW = (
    "**`APD-CASCOR-005` routing — SUPERSEDED 2026-09-21. The row is FIXED.** The owner ruled on "
    f"2026-09-09 (port juniper-data's explicit `matched`-flag loop; rejected: accept and document the "
    f"residual leak) and it shipped as {_CASCOR_PR} + {_ML_PR}. Two things in the note below are now "
    "known wrong and are kept because they are what the ruling overrode: it routes the row as a decision "
    "rather than a task, and it says \"the three copies\" when there are **four** — "
    "`juniper-canopy/src/security.py` is a fourth, still unfixed, and "
    "`juniper-ml/tests/test_service_fork_drift.py` cannot express a canopy guard at all. **The routing as "
    "written:** This row is an **owner decision, not a task**."
)

# --- 2: follow the strikethrough convention already used in the same sentence --------------
CONF_OLD = "`APD-SVCCORE-007`, `APD-SVCCORE-013`, `APD-CASCOR-005`, `APD-ML-001`)"
CONF_NEW = "`APD-SVCCORE-007`, `APD-SVCCORE-013`, ~~`APD-CASCOR-005`~~ (fixed, cascor#659 + ml#1974), `APD-ML-001`)"

REPLACEMENTS = (
    ("§4.3 routing note — revert the mid-paragraph insert", MIDPARA_OLD, MIDPARA_NEW),
    ("§4.3 routing note — marker to the head", HEAD_OLD, HEAD_NEW),
    ("§6 Confidence note — strikethrough the closed row", CONF_OLD, CONF_NEW),
)


def main() -> int:
    text = REGISTER.read_text(encoding="utf-8")

    for label, old, _new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            print(f"REFUSED  {label}: anchor found {count} times, wanted exactly 1")
            print(f"         anchor: {old[:110]}")
            return 2

    for label, old, new in REPLACEMENTS:
        text = text.replace(old, new, 1)
        print(f"applied  {label}")

    REGISTER.write_text(text, encoding="utf-8")
    print(f"\nwrote {REGISTER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

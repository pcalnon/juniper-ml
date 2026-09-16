#!/usr/bin/env python3
"""Correct an unsupported closure claim I wrote into the register the same day.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: round-39 round-2 validation lane B2, which refuted it;
         [[register_file_data_052_truncation_optout]] (the script that introduced the claim)

``util/ad-hoc/register_file_data_052_truncation_optout.py`` closed the 4.9 preamble's
"two of them are in neither" gap by asserting that the second of the two -- the ``val_ratio`` /
``INFRASTRUCTURE_FIELDS`` drift -- "was closed by juniper-canopy#605 and belongs to the canopy
ledger". Half of that is wrong and the other half is imprecise:

* **No canopy ledger row exists.** ``grep -rln "INFRASTRUCTURE_FIELDS\\|val_ratio"`` returns
  nothing across ``juniper-canopy/notes/`` and every ``JUNIPER-CANOPY`` note in juniper-ml.
  Saying a finding "belongs to" a ledger it is not in describes an intention, not a location, and
  reads as a citation.
* **The code IS consistent now** -- ``val_ratio`` sits in ``INFRASTRUCTURE_FIELDS`` at
  ``juniper-canopy/src/dataset_schema.py:114``, so the drift the round-38 handoff described is
  gone. But the round-38 handoff's own point was that the DIRECTION was a real choice: excluding
  ``val_ratio`` makes the set consistent and removes the only sidebar control over the in-loop
  selection split. That choice was made and shipped, and is recorded nowhere.

So the gap is narrower than the original text and wider than my replacement for it.
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

text = REGISTER.read_text()

OLD = (
    "**Two of them were in neither, and that was a gap, not a\n"
    "decision** (noted 2026-09-09; **the gap is closed 2026-09-15** — the truncation defect is now\n"
    "`APD-DATA-052` below, and the `val_ratio` / `INFRASTRUCTURE_FIELDS` drift was closed by\n"
    "juniper-canopy#605 and belongs to the canopy ledger, so neither is handoff-only any more): the\n"
)
NEW = (
    "**Two of them were in neither, and that was a gap, not a\n"
    "decision** (noted 2026-09-09; **one of the two is closed 2026-09-15** — the truncation defect\n"
    "is now `APD-DATA-052` below. The other, the `val_ratio` / `INFRASTRUCTURE_FIELDS` drift, is\n"
    "**resolved in the code and unrecorded as a decision**: `val_ratio` now sits in\n"
    "`INFRASTRUCTURE_FIELDS` (`juniper-canopy/src/dataset_schema.py:114`), so the sidebar treats the\n"
    "three ratio fields alike — but that direction was the non-obvious half. Excluding `val_ratio`\n"
    "makes the set consistent **and removes the only sidebar control over the in-loop selection\n"
    "split**, and no canopy note or ledger row records the choice; a search for\n"
    "`INFRASTRUCTURE_FIELDS` across `juniper-canopy/notes/` and juniper-ml's `JUNIPER-CANOPY` notes\n"
    "returns nothing. An earlier draft of this sentence said it \"was closed by juniper-canopy#605\n"
    "and belongs to the canopy ledger\"; the second clause named an intention as though it were a\n"
    "location, and round-2 validation refused it): the\n"
)

if text.count(OLD) != 1:
    sys.exit(f"FAIL: found {text.count(OLD)} occurrences of the preamble sentence")

REGISTER.write_text(text.replace(OLD, NEW, 1))
print("  ok  corrected the val_ratio / INFRASTRUCTURE_FIELDS closure claim")
print(f"\nregister updated: {REGISTER}")

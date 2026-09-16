#!/usr/bin/env python3
"""Add the row-level park/actionable sentences for APD-DATA-050 and APD-DATA-051.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#404; [[register_round39_head_typo]] (the sibling script that filed the rows)

A row filed without a sentence in this block is a row with no stated status, which is the
condition the block exists to prevent. The APD-DATA-047 bullet is also re-pointed: its subject
moved from 1e13 to 1e11 when #404 made the bound load-bearing.
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

text = REGISTER.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} occurrences of:\n{old[:220]}")
    text = text.replace(old, new, 1)
    print(f"  ok  {label}")


OLD_047 = """- `APD-DATA-047` — **owner decision owed: ratify or remove.** It was added by the session
  implementing the `-043` ruling, not by a ruling, and a bound nobody chose is exactly the kind
  of thing that becomes load-bearing by accident. Removing it re-opens the early-typo blind
  spot the causal median created; keeping it needs the number owned.
"""

NEW_047 = """- `APD-DATA-047` — **owner decision owed: ratify or remove.** It was added by the session
  implementing the `-043` ruling, not by a ruling, and a bound nobody chose is exactly the kind
  of thing that becomes load-bearing by accident. Removing it re-opens the early-typo blind
  spot the causal median created; keeping it needs the number owned.
  **Re-pointed 2026-09-15**: the number to ratify is now **1e11**, not 1e13, and "load-bearing by
  accident" stopped being a hypothetical — at 1e13 the bound was nearly inert and a first-filing
  typo went out the door as `APD-DATA-050`. [juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404)
  re-sited it against the data rather than against headroom, which is the ratifiable form; the
  decision itself is still owed.
- `APD-DATA-050` — **CLOSED 2026-09-15** by
  [juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404), no ruling needed. A
  delivered value 990× wrong is a defect on its face, and the remedy restores an invariant the
  `-043` ruling already implies: a point must not vote on its own plausibility. The one thing a
  reader should carry forward is the **bounded** part — Berkshire's two share classes are now
  filtered as a scale error, which is `APD-DATA-046`'s deferred class-aware lookup coming due.
- `APD-DATA-051` — **actionable, and cheap.** No contract question: either the predicates behind
  the quoted numerators are recovered and the figures restated against 486 payloads, or the
  comments stop quoting counts. What must not happen is a denominator bump on its own, which is
  why #404 renumbered nothing.
"""
sub(OLD_047, NEW_047, "park sentences for -047 (re-pointed), -050, -051")

REGISTER.write_text(text)
print(f"\nregister updated: {REGISTER}")

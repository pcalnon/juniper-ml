#!/usr/bin/env python3
"""Close APD-DATA-047 as RATIFIED — the owner ruled the share-count ceiling stays at 1e11.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: APD-DATA-047; juniper-data#404 (merged 2026-09-16, squash 1bbb6976)

THE RULING. Put to the owner 2026-09-21 as three options -- ratify at 1e11, remove the ceiling,
ratify at some other value -- with the siting evidence and the overlap argument attached.
**Ratified at 1e11.** The deciding consideration: the ceiling is the only instrument that reaches
a typo in a series' FIRST filing (APD-DATA-050's EOG case, position 0), which no relative test can
see, so removing it re-opens that hole outright.

This is a DECISION close, not a code change. Nothing in juniper-data moves -- 1e11 is already what
juniper-data#404 shipped. What closes is the row's actual subject, which was never "is the code
wrong" but "nobody chose this number". Now someone has.

FOUR TOUCHES, NOT FIVE. The close protocol in the register's "Closing a row -- the five touches"
section is explicit that a row with no §3 detail entry needs four. APD-DATA-047 has none, so:
§4 table row, §5.1 verification row, §2 status paragraph, header date. The §4.9 rulings bullet is
touched as well -- not as a fifth touch but because it currently reads "owner decision owed", and
the protocol's whole-file `grep -n 'APD-<ID>'` sweep requires every hit be read and reconciled.

Every replacement below is verbatim and asserted exactly once. The script fails loudly rather than
patching a near-miss, because a silent partial close is the failure mode the protocol exists to
prevent -- the register would then disagree with itself while every count-based check still passed.
"""

from __future__ import annotations

import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

_RATIFIED = (
    "**FIXED (RATIFIED by the owner, 2026-09-21 — the ceiling STAYS, at `1e11` as sited by "
    "[juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404); no code change, because "
    "`1e11` is already what #404 shipped)** — the row asked for a decision, not a repair, and the "
    "decision is taken. Ratified against the evidence below rather than against comfort: the bound "
    "sits between the largest genuine count in the cache (Citigroup, 2.92e10) and the smallest "
    "demonstrated typo in it (AIZ, 1.168e11), 3.4× of headroom. **Why not remove it:** it is the "
    "only instrument that reaches a typo in a series' *first* filing — `APD-DATA-050`'s EOG case at "
    "position 0 — because a relative test has no prior basis there; removing it re-opens that hole "
    "outright. **Why not tighten it:** the four largest values that PASS it are themselves typos "
    "(Pentair 9.84e10, Packaging Corp 8.99e10, Regency Centers 8.19e10, Mid-America 7.50e10) and "
    "the relative filter already delivers all four correctly, so tightening to reach them would "
    "cross Citigroup's genuine 2.92e10 and delete real mega-cap history — the two populations "
    "overlap across any absolute bound, which is what makes this a judgement and not a calculation. "
    "Both rejected options are recorded here so a later reader can tell a decision from a drift. — "
)

# --- Touch 1: the §4 table row -------------------------------------------------------------
T1_OLD = "| APD-DATA-047 | An absolute share-count **ceiling** was added by"
T1_NEW = "| APD-DATA-047 | " + _RATIFIED + "An absolute share-count **ceiling** was added by"

# --- Touch 3: the §5.1 verification row ----------------------------------------------------
# Anchored on the END of the APD-DATA-050 §5.1 row so the new row lands directly after it.
T3_ANCHOR = "whose handoff is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`. |"
T3_NEW = T3_ANCHOR + (
    "\n| APD-DATA-047 | An absolute share-count ceiling was added by a fix rather than by a ruling, and nobody had chosen the number "
    "| **No PR — a decision, ratified 2026-09-21.** The value it ratifies was shipped by "
    "[juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404) "
    "| **Ratified at `1e11`, unchanged.** Verified that the code already carries the ratified value rather than assuming it: "
    "`git -C …/juniper-data show origin/main:juniper_data/generators/equities/generator.py` gives "
    "`_SHARES_ABSOLUTE_CEILING = 1.0e11` at `:123` and `VERSION = \"5.0.0\"` at `:58`. "
    "**What was ratified is the bound, not a claim that it is optimal** — the owner was shown that the two populations overlap "
    "across any absolute bound, that the four largest passing values are themselves typos which the relative filter catches, "
    "and that tightening far enough to reach them would delete Citigroup's genuine 2.92e10. Removing it was offered and "
    "rejected: nothing relative reaches a typo in a series' first filing, so the ceiling is the sole instrument for "
    "`APD-DATA-050`'s EOG case. **What this close does NOT establish:** that `1e11` is correct for a universe wider than the "
    "486-payload bundled cache it was sited against — a future symbol with a genuine count above `1e11`, or a typo below it, "
    "would need the number revisited, and the close protocol's own instruction is to re-derive rather than to inherit. |"
)

# --- Touch 4: the §2 status paragraph ------------------------------------------------------
T4A_OLD = "and (2026-09-15) `APD-DATA-050` ([juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404)) — and eight are open — **25 open in all**, 17 primer + 8 post-primer."
T4A_NEW = "and (2026-09-15) `APD-DATA-050` ([juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404)) and (2026-09-21, RATIFIED — a decision, no PR) `APD-DATA-047` — and seven are open — **24 open in all**, 17 primer + 7 post-primer."

T4B_OLD = "Four of those seven were FILED BY a fix for the others (an unratified bound, a capability the ruling's framing did not notice it removed, an orphaned cache, and comment figures that cannot be reproduced)"
T4B_NEW = "Four were FILED BY a fix for the others (an unratified bound, a capability the ruling's framing did not notice it removed, an orphaned cache, and comment figures that cannot be reproduced) — of which the first, `APD-DATA-047`, closed on 2026-09-21 when the owner ratified it, leaving three of the four open"

# --- Touch 5: the header date --------------------------------------------------------------
T5_OLD = "**Last Updated**: 2026-09-15"
T5_NEW = "**Last Updated**: 2026-09-21"

# --- Sweep reconciliation: the §4.9 rulings bullet still says the decision is owed ----------
T6_OLD = """- `APD-DATA-047` — **owner decision owed: ratify or remove.** It was added by the session"""
T6_NEW = """- `APD-DATA-047` — **RULED 2026-09-21: RATIFIED at `1e11`. The ceiling stays.** Removing it was
  offered and rejected, as was re-siting it to another value; the rejected options and the reasoning
  are recorded at the row's §4 entry and its §5.1 verification row. With this ruling **no row in
  this register is awaiting an owner decision** — every open row is implementation work.
  The original framing, left standing because it is what the ruling was taken against:
  **owner decision owed: ratify or remove.** It was added by the session"""

REPLACEMENTS = (
    ("§4 table row", T1_OLD, T1_NEW),
    ("§5.1 verification row", T3_ANCHOR, T3_NEW),
    ("§2 status paragraph (enumeration + counts)", T4A_OLD, T4A_NEW),
    ("§2 status paragraph (the 'four of those' sentence)", T4B_OLD, T4B_NEW),
    ("header Last Updated", T5_OLD, T5_NEW),
    ("§4.9 rulings bullet", T6_OLD, T6_NEW),
)


def main() -> int:
    text = REGISTER.read_text(encoding="utf-8")

    for label, old, _new in REPLACEMENTS:
        count = text.count(old)
        if count != 1:
            print(f"REFUSED  {label}: anchor found {count} times, wanted exactly 1")
            print(f"         anchor: {old[:110]}...")
            return 2

    for label, old, new in REPLACEMENTS:
        text = text.replace(old, new, 1)
        print(f"applied  {label}")

    REGISTER.write_text(text, encoding="utf-8")
    print(f"\nwrote {REGISTER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Close APD-CASCOR-005 — the non-short-circuiting key walk is on main in both forks.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#659 (MERGED, squash 435d6069), juniper-ml#1974 (MERGED, squash 968b9e9e)

STATUS IS VERIFIED, NOT INHERITED. This close was withheld until both halves were confirmed by
CONTENT on origin/main rather than by a MERGED badge:

    git -C .../juniper-cascor show origin/main:src/api/security.py    -> matched = False :68, return matched :72
    git show origin/main:juniper-service-core/juniper_service_core/security.py -> :73, :77
    git show origin/main:tests/test_service_fork_drift.py             -> guard row :155

FIVE TOUCHES. Unlike APD-DATA-047, this row HAS a §3 detail entry, so it takes all five: §4 table
row, §3 Status field, §5.1 verification row, §2 status paragraph, header date. The §3 Status is
located by walking forward from the (unique) §3 heading rather than by matching
``| **Status**     | OPEN`` directly -- that string occurs once per open §3 entry, and a
whitespace-padded blind replace would close an arbitrary other row.

THREE CORRECTIONS RIDE ALONG, all of them the same defect. The row was written as "two of three
copies". A source-tree census on 2026-09-21 -- run as an independent consensus lane that was
denied this register and the handoff, and which reached the number with nothing to reproduce --
found **four** copies. juniper-canopy/src/security.py is the fourth. So:

  - the §3 heading changes, and line 23's in-document anchor link changes with it or the
    Documentation Links check fails. Swept ecosystem-wide first: that anchor has exactly one
    referrer, line 23 of this same file.
  - the §4 row's summary text changes.
  - §4.3's "routing" note says "Do not unify the three copies unilaterally", which was correct
    while the row awaited a ruling and is now both ruled and implemented.

WHAT THIS CLOSE DELIBERATELY DOES NOT CLAIM. canopy is NOT fixed by juniper-cascor#659 /
juniper-ml#1974, and this row is not closed on canopy's behalf. The reason canopy cannot simply be
added to the drift guard is structural and is recorded in the row: tests/test_service_fork_drift.py
declares _FORK_REPOS = ("juniper-data", "juniper-cascor") and asserts every guard site's repo is a
member, so a canopy site is rejected by the gate's own well-formedness check. Widening that tuple
has its own blast radius and is left as follow-up rather than smuggled into a close.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REGISTER = Path(__file__).resolve().parents[2] / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

OLD_HEADING = "### APD-CASCOR-005 — API-key comparison short-circuits on match in two of three copies"
NEW_HEADING = "### APD-CASCOR-005 — API-key comparison short-circuits on match in three of four copies"

OLD_ANCHOR = "[`APD-CASCOR-005`](#apd-cascor-005--api-key-comparison-short-circuits-on-match-in-two-of-three-copies)"
NEW_ANCHOR = "[`APD-CASCOR-005`](#apd-cascor-005--api-key-comparison-short-circuits-on-match-in-three-of-four-copies)"

_FIXED = (
    "**FIXED ([juniper-cascor#659](https://github.com/pcalnon/juniper-cascor/pull/659) + "
    "[juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974))** — juniper-data's explicit "
    "`matched`-flag loop ported into both forks, as ruled 2026-09-09; rejected in the same ruling was "
    "accepting and documenting the residual leak. Verified by CONTENT on `origin/main` in both repos, "
    "not by a MERGED badge. **The close carries a correction: this row said 2 of 3 copies, and there "
    "are FOUR.** `juniper-canopy/src/security.py:74` is a fourth copy, found by an independent census "
    "on 2026-09-21 that was denied this register. It is NOT fixed here, and the reason it was never "
    "seen is worth more than the miscount: `juniper-ml/tests/test_service_fork_drift.py` declares "
    "`_FORK_REPOS = (\"juniper-data\", \"juniper-cascor\")` and `test_every_guard_is_well_formed` "
    "asserts every site's repo is a member — so **no guard can reference canopy even in principle**, "
    "and the gate that exists to catch copy drift is blind to a quarter of the copies. canopy also "
    "lacks the `blank-api-key-filter` the other three carry (`:53` is a bare `set(api_keys)`); that "
    "one fails CLOSED rather than open, because its only caller turns `\"\"` into `None` via a "
    "truthiness test, so it is a divergence and not a bypass. Widening `_FORK_REPOS` is follow-up. — "
)

T_ROW_OLD = "| APD-CASCOR-005   | Key comparison short-circuits on match in 2 of 3 copies"
T_ROW_NEW = "| APD-CASCOR-005   | " + _FIXED + "Key comparison short-circuits on match in 3 of 4 copies"

T_51_ANCHOR = "whose handoff is `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`. |"
T_51_NEW = T_51_ANCHOR + (
    "\n| APD-CASCOR-005 | API-key comparison short-circuits on match — `any(hmac.compare_digest(...))` in the forks where juniper-data walks every key "
    "| [juniper-cascor#659](https://github.com/pcalnon/juniper-cascor/pull/659) + [juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974) "
    "| Both forks now carry the accumulate-then-return loop, verified by content on `origin/main` (`src/api/security.py:68,72`; "
    "`juniper-service-core/juniper_service_core/security.py:73,77`). **No behavioural test pins this, and none can** — `any(...)` and the flag loop "
    "return the same value for every input, so a test written to distinguish them passes against both and is vacuous (the §5.3 trap, in its sharpest "
    "form). The instrument is instead a SOURCE marker, `nonshortcircuit-key-compare` in `tests/test_service_fork_drift.py`, which was verified "
    "NON-VACUOUS before it was committed: run against the unported forks it failed with `absent markers: ['matched = False', 'return matched']` on "
    "juniper-cascor while passing on juniper-data. **Bounded close:** it closes the two copies the ruling named. `juniper-canopy/src/security.py:74` "
    "is a fourth copy, still short-circuiting, and the drift gate cannot express it — see the row. |"
)

T_S2A_OLD = "then (2026-09-04) `APD-DATA-018` — leaving **17 open** of the primer rows"
T_S2A_NEW = "then (2026-09-04) `APD-DATA-018`, and (2026-09-21) `APD-CASCOR-005` — leaving **16 open** of the primer rows"

T_S2B_OLD = "**Seventy-nine of the 96 have since been fixed**"
T_S2B_NEW = "**Eighty of the 96 have since been fixed**"

T_S2C_OLD = "— and seven are open — **24 open in all**, 17 primer + 7 post-primer."
T_S2C_NEW = "— and seven are open — **23 open in all**, 16 primer + 7 post-primer."

T_ROUTING_OLD = "**Do not unify the three copies unilaterally.**"
T_ROUTING_NEW = (
    "**SUPERSEDED 2026-09-21.** The routing below was correct while the row awaited a ruling. The owner "
    "ruled on 2026-09-09 (port the `matched`-flag loop; rejected: accept and document the residual leak) "
    "and it shipped as [juniper-cascor#659](https://github.com/pcalnon/juniper-cascor/pull/659) + "
    "[juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974). Note also that \"the three copies\" "
    "is itself wrong — there are four; see the row. The original instruction, left standing because it is "
    "what the ruling overrode: **Do not unify the three copies unilaterally.**"
)

T_RULING_OLD = "- `APD-CASCOR-005` — **RULED.** **Port juniper-data's explicit `matched`-flag loop** into cascor and"
T_RULING_NEW = (
    "- `APD-CASCOR-005` — **RULED, and SHIPPED 2026-09-21** by "
    "[juniper-cascor#659](https://github.com/pcalnon/juniper-cascor/pull/659) + "
    "[juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974), with the named guard the ruling "
    "asked for. The row is closed; the census taken while implementing it found a FOURTH copy "
    "(juniper-canopy) that the drift gate cannot express. Ruling as taken: "
    "**Port juniper-data's explicit `matched`-flag loop** into cascor and"
)

SIMPLE = (
    ("§3 heading (2 of 3 -> 3 of 4)", OLD_HEADING, NEW_HEADING),
    ("line 23 anchor link", OLD_ANCHOR, NEW_ANCHOR),
    ("§4 table row", T_ROW_OLD, T_ROW_NEW),
    ("§5.1 verification row", T_51_ANCHOR, T_51_NEW),
    ("§2 primer fixed-list + primer open count", T_S2A_OLD, T_S2A_NEW),
    ("§2 'Seventy-nine' -> 'Eighty'", T_S2B_OLD, T_S2B_NEW),
    ("§2 totals", T_S2C_OLD, T_S2C_NEW),
    ("§4.3 routing note", T_ROUTING_OLD, T_ROUTING_NEW),
    ("§4.9 ruling bullet", T_RULING_OLD, T_RULING_NEW),
)


def close_status_field(text: str) -> tuple[str, bool]:
    """Flip the §3 Status cell of APD-CASCOR-005 only.

    Located by walking forward from the (now corrected) heading to the FIRST Status row, so the
    padded ``| **Status**     | OPEN`` string -- which every open §3 entry carries -- cannot be
    matched against some other row's detail entry.
    """
    start = text.find(NEW_HEADING)
    if start < 0:
        return text, False
    window = text[start : start + 2000]
    match = re.search(r"\|\s\*\*Status\*\*\s+\|\sOPEN(\s+)\|", window)
    if not match:
        return text, False
    replacement = f"| **Status**     | **FIXED** (juniper-cascor#659 + juniper-ml#1974){match.group(1)}|"
    return text[:start] + window.replace(match.group(0), replacement, 1) + text[start + 2000 :], True


def main() -> int:
    text = REGISTER.read_text(encoding="utf-8")

    for label, old, _new in SIMPLE:
        count = text.count(old)
        if count != 1:
            print(f"REFUSED  {label}: anchor found {count} times, wanted exactly 1")
            print(f"         anchor: {old[:110]}")
            return 2

    for label, old, new in SIMPLE:
        text = text.replace(old, new, 1)
        print(f"applied  {label}")

    text, ok = close_status_field(text)
    if not ok:
        print("REFUSED  §3 Status field: could not locate the APD-CASCOR-005 Status row")
        return 2
    print("applied  §3 Status field")

    REGISTER.write_text(text, encoding="utf-8")
    print(f"\nwrote {REGISTER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

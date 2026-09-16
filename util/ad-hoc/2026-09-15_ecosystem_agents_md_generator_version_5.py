#!/usr/bin/env python3
"""Move the ecosystem data contract's generator_version statement to 5.0.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#404 (merged 2026-09-16, squash 1bbb6976)

``Juniper/AGENTS.md`` sits in the ecosystem parent, which is **not a git repository**: no PR, no
CI, no history, invisible to any other machine. Nothing enforces this statement, so it drifts
silently -- and it drifted the moment #404 merged. Round-2 lane A caught that the handoff had
called it stale prematurely (it was correct while #404 was open); this makes it correct again now
that #404 has landed.

The script exists rather than a hand edit precisely BECAUSE that file has no history: this is the
only record that the change was made, by whom, and against which merge.
"""

from __future__ import annotations

import sys
from pathlib import Path

AGENTS = Path("/home/pcalnon/Development/python/Juniper/AGENTS.md")

OLD = """- Generator `generator_version` is **`3.0.0`, except `equities` and `equities_seq`,
  which are at `4.0.0`** since 2026-09-11. It went `1.x -> 2.0.0` when `val` was added
  and `2.0.0 -> 3.0.0` when `*_full` was removed; the equities pair went to `4.0.0` for
  the owner rulings on causal share history and the feature set (juniper-data#395).
"""

NEW = """- Generator `generator_version` is **`3.0.0`, except `equities` and `equities_seq`,
  which are at `5.0.0`** since 2026-09-16. It went `1.x -> 2.0.0` when `val` was added
  and `2.0.0 -> 3.0.0` when `*_full` was removed; the equities pair went to `4.0.0` for
  the owner rulings on causal share history and the feature set (juniper-data#395), and
  to `5.0.0` because **#395 shipped a regression and the corrected values must not be
  served under the id that carried the wrong ones** (juniper-data#404). #395's causal
  median included the point it was judging, so a scale typo in a series' opening filings
  survived it: AIZ was delivered at 116,799,796,000 against a truth of 117,926,517 (990x)
  and EOG at 251,931,774,000 against 587,723,622 (428x), for four days. **Every artifact
  minted at `4.0.0` for a symbol with such a typo carries it** -- that is the whole reason
  the bump is not optional.
"""

text = AGENTS.read_text()
if NEW in text:
    print("  --  already applied")
    sys.exit(0)
if text.count(OLD) != 1:
    sys.exit(f"FAIL: found {text.count(OLD)} occurrences of the generator_version paragraph")

AGENTS.write_text(text.replace(OLD, NEW, 1))
print("  ok  Juniper/AGENTS.md generator_version -> 5.0.0")

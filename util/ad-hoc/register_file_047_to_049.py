#!/usr/bin/env python3
"""
File the three rows that juniper-data#395 produced rather than closed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#395; util/ad-hoc/register_close_data395.py

* `APD-DATA-047` -- the absolute share-count CEILING, added while implementing a ruling that named
  only a floor. It is not a defect in the product; it is an unratified decision, and it is filed so
  a successor either ratifies or removes it rather than inheriting it as settled. The verification
  row for `-043` already points here, which is what forced this row to exist.
* `APD-DATA-048` -- `adj_close` is now unreachable. The option was put to the owner as leaving the
  column requestable; there is no feature-column parameter, so the ruling as implemented removes a
  capability. This is the register recording that the framing was wrong, not just the outcome.
* `APD-DATA-049` -- the versioned cache key orphans 485 payloads. Correct for a shape change, and a
  cold re-fetch of that universe is slow and rate-limited by SEC's fair-access policy.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

text = REG.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} for:\n{old[:160]}")
    text = text.replace(old, new)
    print(f"  ok  {label}")


NEW_ROWS = (
    "| APD-DATA-047 | An absolute share-count **ceiling** (1e13) was added by [juniper-data#395](https://github.com/pcalnon/juniper-data/pull/395) while implementing a ruling that named only a floor. Making the outlier median causal removed the ability to catch a cover-page typo arriving early in a series — there is no prior basis to judge it against — so the ceiling replaced a look-ahead with a bound. Sited 588× above the largest genuine count in the bundled universe. **Not a product defect: an unratified decision**, filed so it is ratified or removed rather than inherited | M | `generators/equities/generator.py` (`_SHARES_ABSOLUTE_CEILING`) | — | High |\n"
    "| APD-DATA-048 | `adj_close` is no longer reachable at all. [juniper-data#395](https://github.com/pcalnon/juniper-data/pull/395) removed it from `EQUITIES_FEATURE_COLUMNS` under the 2026-09-09 ruling, which was put to the owner as leaving the column *requestable* — but `EquitiesParams` has no feature-column parameter, so the default list is the only list. The column is still computed and present in the conditioned frame; nothing can select it into a dataset. The ruling's framing was wrong, and the capability is gone until a parameter exists | M | `generators/equities/params.py` (no feature-column field), `generators/equities/defaults.py` (`EQUITIES_FEATURE_COLUMNS`) | — | High |\n"
    "| APD-DATA-049 | The versioned SEC shares cache key introduced by [juniper-data#395](https://github.com/pcalnon/juniper-data/pull/395) orphans the 485 payloads under the old CIK-only path. Correct for a shape change, but a cold rebuild re-fetches the whole universe under SEC's fair-access limit (`_SEC_MIN_INTERVAL = 0.12`s, <10 req/s), and the rescue ladder costs ~1.15 s and ~5 MB per miss. A one-time migration would avoid re-downloading data that has not changed | E | `generators/equities/generator.py` (`_SHARES_CACHE_VERSION`); cache `~/.cache/juniper_data/equities/shares/` | — | High |\n"
)
sub(
    "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared**",
    NEW_ROWS + "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared**",
    "three rows filed",
)

sub(
    "- `APD-DATA-046` — **filed 2026-09-09, deferred by the same ruling.**",
    "- `APD-DATA-047` — **owner decision owed: ratify or remove.** It was added by the session\n"
    "  implementing the `-043` ruling, not by a ruling, and a bound nobody chose is exactly the kind\n"
    "  of thing that becomes load-bearing by accident. Removing it re-opens the early-typo blind\n"
    "  spot the causal median created; keeping it needs the number owned.\n"
    "- `APD-DATA-048` — **actionable**, and the remedy is a feature-column parameter rather than\n"
    "  putting `adj_close` back in the defaults, which the owner ruled against for good reason.\n"
    "- `APD-DATA-049` — **actionable**: a one-time migration of the existing payloads into the\n"
    "  versioned path. Purely operational; no contract question.\n"
    "- `APD-DATA-046` — **filed 2026-09-09, deferred by the same ruling.**",
    "park sentences",
)

sub(
    "and three are open — **20 open in all**, 17 primer + 3 post-primer.",
    "and six are open — **23 open in all**, 17 primer + 6 post-primer. Three of those six (`APD-DATA-047` / `APD-DATA-048` / `APD-DATA-049`) were FILED BY the fix for the others, which is the ordinary cost of a contract change and is recorded rather than folded into the closes.",
    "§2 status line",
)

REG.write_text(text)

sys.path.insert(0, str(HERE))
from register_open_set import format_report, parse_register  # noqa: E402
from register_status_crosscheck import crosscheck  # noqa: E402

seen, fixed = parse_register(text)
print("\nopen-set:", format_report(seen, fixed).splitlines()[0])
raise SystemExit(crosscheck(text))

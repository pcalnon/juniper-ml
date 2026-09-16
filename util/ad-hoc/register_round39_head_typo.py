#!/usr/bin/env python3
"""Record the #395 head-typo regression on the defect register, and correct four rows it touches.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#404 (the fix), juniper-data#395 (which shipped the regression),
         round-39 validation lane B1 (which found it)

Edits, all in ``notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md``:

1. FILE ``APD-DATA-050`` -- the regression itself -- and close it against #404.
2. FILE ``APD-DATA-051`` -- the cache-derived figures quoted in the generator's comments cite a
   485-payload sweep whose numerators no obvious predicate reproduces.
3. CORRECT ``APD-DATA-047`` -- the ceiling is 1e11 as of #404, not 1e13, and it is now
   load-bearing (it is the only instrument that reaches EOG's first-filing typo). The decision
   owed is unchanged in kind and changed in subject.
4. CORRECT ``APD-DATA-048`` -- ``adj_close`` is not wholly unreachable: ``basis_price_field``
   still selects it for the cost basis. What is gone is its availability as a FEATURE COLUMN.
5. CORRECT ``APD-CASCOR-011`` -- the row is marked FIXED and the 2026-09-09 rulings block says
   "close the row", but its own text still ends "The row stays OPEN ... still owed a ruling".
6. CORRECT the ``APD-DATA-043`` close in 5.1 -- it names the 1e13 ceiling that #404 superseded.
7. UPDATE the 4.9 status sentence: twenty-two filed, not sixteen, with the new counts.
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


PR404 = "[juniper-data#404](https://github.com/pcalnon/juniper-data/pull/404)"
PR395 = "[juniper-data#395](https://github.com/pcalnon/juniper-data/pull/395)"

# ---------------------------------------------------------------- 1 + 2: the new rows
ROW_049_TAIL = "| E | `generators/equities/generator.py` (`_SHARES_CACHE_VERSION`); cache `~/.cache/juniper_data/equities/shares/` | — | High |\n"

NEW_ROWS = (
    f"| APD-DATA-050 | **FIXED ({PR404})** — the causal scale-typo filter {PR395} shipped judged every point "
    "against a median that **included that point**, so an outlier dominated its own basis and could never be rejected. "
    "No `min_periods` value repairs it — the problem is membership, not sample size — and the two real cases sit at "
    "opposite ends of what a relative test can reach: AIZ's typo is at position 1 and EOG's at position 0. Both were "
    "**delivered**: AIZ 116,799,796,000 against a truth of 117,926,517 (990×), EOG 251,931,774,000 against 587,723,622 "
    "(428×). The pre-#395 filter caught both, but only by consulting filings that had not happened yet — the look-ahead "
    "#395 was written to remove — so the row is a regression of the fix, not a case for reverting it | C | "
    "`generators/equities/generator.py` (`_fetch_shares`, the relative filter and `_SHARES_ABSOLUTE_CEILING`) | — | High |\n"
    "| APD-DATA-051 | Several comments in `generators/equities/generator.py` quote counts from a **485-payload sweep** "
    "against a cache that holds **486**, and the numerators cannot be reproduced: re-measuring with the generator's own "
    "parsing gives 183 CIKs carrying a restatement where the comment says 162, and 42 value-changing period-end "
    "collisions where it says 54. Bumping the denominator alone would leave every numerator asserting a measurement "
    "nobody redid, so #404 deliberately renumbered nothing. Either the predicates are recovered and the figures "
    "restated, or the comments stop quoting counts they cannot defend. "
    "`util/ad-hoc/2026-09-15_remeasure_shares_cache_figures.py` (juniper-data) is the instrument | E | "
    "`generators/equities/generator.py` (the comment blocks at `_SHARES_ABSOLUTE_CEILING`, `SHARES_QUALITY_STALE`, "
    "`_SHARES_FACTS_LADDER`, `_condition_one`'s dedup, and `_fetch_shares`' observation table) | — | High |\n"
)
sub(ROW_049_TAIL, ROW_049_TAIL + NEW_ROWS, "file APD-DATA-050 and APD-DATA-051")

# ---------------------------------------------------------------- 3: APD-DATA-047
sub(
    f"| APD-DATA-047 | An absolute share-count **ceiling** (1e13) was added by {PR395} while implementing a ruling "
    "that named only a floor. Making the outlier median causal removed the ability to catch a cover-page typo arriving "
    "early in a series — there is no prior basis to judge it against — so the ceiling replaced a look-ahead with a "
    "bound. Sited 588× above the largest genuine count in the bundled universe. **Not a product defect: an unratified "
    "decision**, filed so it is ratified or removed rather than inherited |",
    f"| APD-DATA-047 | An absolute share-count **ceiling** was added by {PR395} while implementing a ruling that named "
    "only a floor. Making the outlier median causal removed the ability to catch a cover-page typo arriving early in a "
    "series — there is no prior basis to judge it against — so the ceiling replaced a look-ahead with a bound. **Not a "
    "product defect: an unratified decision**, filed so it is ratified or removed rather than inherited. *(Updated "
    f"2026-09-15: the value is **1e11**, not the 1e13 this row was filed against — {PR404} re-sited it between the "
    "largest genuine count in the bundled universe (AAPL, 1.70e10) and the smallest demonstrated typo in the cache "
    "(AIZ, 1.168e11), 18 observations across 24 series having sat in the dead band above 1e11. The decision owed is "
    "unchanged in kind and changed in subject, and the stakes are higher: at 1e13 the bound was nearly inert, and at "
    "1e11 it is the **only** instrument that reaches a typo in a series' first filing — `APD-DATA-050`'s EOG case. "
    "Removing it now re-opens that hole outright.)* |",
    "correct APD-DATA-047 (ceiling value and stakes)",
)

# ---------------------------------------------------------------- 4: APD-DATA-048
sub(
    "The column is still computed and present in the conditioned frame; nothing can select it into a dataset. "
    "The ruling's framing was wrong, and the capability is gone until a parameter exists |",
    "The column is still computed and present in the conditioned frame; nothing can select it into a dataset. "
    "The ruling's framing was wrong, and the capability is gone until a parameter exists. *(Corrected 2026-09-15: "
    "`adj_close` is not wholly unreachable — `EquitiesParams.basis_price_field` is a "
    "`Literal[\"close\", \"adj_close\"]` and still selects it as the price the cost basis is struck at, so the column "
    "reaches the artifact through `cost_basis`. What is gone is its availability as a **feature column**, which is "
    "what the ruling was about and what this row is scoped to. The distinction matters for the remedy: a "
    "feature-column parameter, not a re-plumbing of the price field that already exists.)* |",
    "correct APD-DATA-048 (basis_price_field still reaches adj_close)",
)

# ---------------------------------------------------------------- 5: APD-CASCOR-011
sub(
    "so the inertness is no longer silent. The row stays OPEN because the parked question is *drop the flag or "
    "rewire the path*, and that is still owed a ruling.)*",
    "so the inertness is no longer silent. This row first added that it *stayed OPEN* pending a ruling on **drop the "
    "flag or rewire the path** — that ruling was taken the same day, in the block below: keep the flag as #640 shipped "
    "it, and close the row. Both alternatives were considered and rejected there. The sentence outlived the ruling by "
    "six days and is corrected here 2026-09-15; the row is FIXED, as its own marker already said.)*",
    "correct APD-CASCOR-011 (stale 'still owed a ruling')",
)

# ---------------------------------------------------------------- 6: the APD-DATA-043 close
sub(
    "An absolute ceiling at 1e13 was added in the same change and is NOT part of the ruling — see `APD-DATA-047`. |",
    f"An absolute ceiling was added in the same change and is NOT part of the ruling — see `APD-DATA-047`. **This close "
    f"was BOUNDED, and the bound broke:** the expanding median included the point it judged, so a typo in a series' "
    f"opening filings survived it and was delivered. That is `APD-DATA-050`, fixed by {PR404}, which also re-sited the "
    f"ceiling from 1e13 to 1e11. The ruling itself stands — the look-ahead is gone and stays gone. |",
    "correct the APD-DATA-043 close (bounded, and the bound broke)",
)

# ---------------------------------------------------------------- 7: the §4.9 status sentence
sub(
    "sixteen filed, of which (2026-09-09) `APD-DATA-037` / `APD-DATA-038`",
    "twenty-two filed, of which (2026-09-09) `APD-DATA-037` / `APD-DATA-038`",
    "4.9 count: sixteen -> twenty-two",
)
sub(
    "and six are open — **23 open in all**, 17 primer + 6 post-primer. Three of those six were FILED BY the fix for "
    "the others (an unratified bound, a capability the ruling's framing did not notice it removed, and an orphaned "
    "cache) — the ordinary cost of a contract change, recorded rather than folded into the closes.",
    f"and (2026-09-15) `APD-DATA-050` ({PR404}) — and seven are open — **24 open in all**, 17 primer + 7 post-primer. "
    "Four of those seven were FILED BY a fix for the others (an unratified bound, a capability the ruling's framing "
    "did not notice it removed, an orphaned cache, and comment figures that cannot be reproduced) — the ordinary cost "
    "of a contract change, recorded rather than folded into the closes. A fifth, `APD-DATA-050`, was filed **against** "
    "one of those fixes and is already closed: #395's causal median could not reject an outlier in a series' opening "
    "filings, and delivered two of them 990× and 428× too large until #404.",
    "4.9 open-count sentence",
)

# ---------------------------------------------------------------- the §5.1 close row
ANCHOR_51 = (
    "| APD-DATA-045 | Share counts go stale silently | "
    f"{PR395} | A series with more than 365 days of silence before its window ends is annotated `degraded` with the "
    "affected row count. Measured per SERIES: a first implementation measured per row, which flags the tail of every "
    "gap — an annual filer produces a 365-day gap by definition — and was caught when it made a deliberately-clean "
    "fixture dirty. |\n"
)
CLOSE_050 = (
    "| APD-DATA-050 | A scale typo in a series' opening filings survived the causal median and was delivered | "
    f"{PR404} | Two changes, and **neither is redundant — the two regressions prove it one each.** (1) Every point is "
    "judged against the median of what was already **accepted**, not of everything already **seen**, so a rejected "
    "typo cannot poison the judgement of its neighbours; this alone returns AIZ (position 1) to 117,926,517. "
    "`expanding().median().shift(1)` is the tempting one-liner and is wrong for the same family of reason as the "
    "unshifted median — after a typo in the second filing its basis for the third is `median(1e8, 5e10)`, deleting a "
    "genuine value. On the bundled cache the two agree on all 486 series, which is exactly why the one-liner would "
    "have looked fine. (2) `_SHARES_ABSOLUTE_CEILING` 1e13 → 1e11, because nothing relative reaches position 0 — "
    "EOG's case. Generator `4.0.0` → `5.0.0` on both `equities` and `equities_seq`: `generator_version` is hashed "
    "into `dataset_id`, so the corrected values must not be served under the ID that carried the wrong ones. "
    "**Bounded close:** Berkshire's two genuine share classes, 1,138× apart, are now filtered as a scale error — no "
    "relative test can tell that step from a typo. They survived before only because `min_periods=3` switched the "
    "filter off for opening points, which is the same hole. Pinned by its own test; the remedy is `APD-DATA-046`'s "
    "class-aware lookup. Three new regression tests, each verified to FAIL against the pre-fix generator; 1887 pass. |\n"
)
sub(ANCHOR_51, ANCHOR_51 + CLOSE_050, "file the APD-DATA-050 close in 5.1")

REGISTER.write_text(text)
print(f"\nregister updated: {REGISTER}")

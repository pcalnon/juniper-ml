#!/usr/bin/env python3
"""File the one ruled defect that had no register row: a caller cannot refuse truncation.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: round-39 validation lane B1 (which found the gap); owner ruling 2026-09-09

The register's own 4.9 preamble already names this as a gap rather than a decision: two findings
from the round-37/38 validation were written down ONLY in
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md``.
One of the two -- the ``val_ratio`` / ``INFRASTRUCTURE_FIELDS`` drift -- was closed by
juniper-canopy#605 and belongs to the canopy ledger. The other is open, was RULED on 2026-09-09,
and is the largest single unit of remaining work in this arc. A ruled item with no row is invisible
to every count the register produces and to anyone who does not read a superseded handoff.
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


# --------------------------------------------------------------- the row itself
ANCHOR = (
    "| APD-DATA-051 | Several comments in `generators/equities/generator.py` quote counts from a **485-payload sweep** "
)
ROW_052 = (
    "| APD-DATA-052 | **A caller cannot refuse truncation where the operator enabled it.** `allow_truncation` is a "
    "two-state `bool` whose absence and whose explicit `false` are indistinguishable downstream: the route binds "
    "deployment defaults before `generate`, and the three `or settings.*` sites then read the bound value, so an "
    "explicit `false` is overridden by the deployment on every apply. The asymmetry is deliberate and documented "
    "today (\"A client cannot opt out of the operator's choice\") and the owner **ruled on 2026-09-09 to reverse it**: "
    "`true | false | null`, with `null`/omitted deferring to the deployment. **Filed 2026-09-15**, six days after the "
    "ruling — it had been recorded only in the round-38 handoff, which §4.9's preamble already named as a gap; a "
    "ruled item with no row is invisible to every count this register produces | C | "
    "`api/routes/datasets.py` (the binder hook), `generators/csv_import/generator.py`, "
    "`generators/equities/generator.py` (two `or settings.*` sites), "
    "`tests/unit/test_csv_import_generator.py::test_request_cannot_opt_out_of_deployment_allow_truncation` | — | High |\n"
)
sub(ANCHOR, ROW_052 + ANCHOR, "file APD-DATA-052")

# --------------------------------------------------------------- its park sentence
PARK_ANCHOR = """- `APD-DATA-051` — **actionable, and cheap.** No contract question: either the predicates behind
  the quoted numerators are recovered and the figures restated against 486 payloads, or the
  comments stop quoting counts. What must not happen is a denominator bump on its own, which is
  why #404 renumbered nothing.
"""
PARK_052 = PARK_ANCHOR + """- `APD-DATA-052` — **RULED 2026-09-09: actionable**, and it is the largest single unit of work
  left in this arc. Tri-state `allow_truncation` (`true | false | null`), `null` deferring to the
  deployment. It **reverses a deliberate, documented, test-pinned design**, so the test whose name
  IS the old behaviour must be INVERTED rather than deleted — the half that survives is that an
  *omitted* flag still defers. Do not reach for a `model_fields_set` presence guard: the binder
  ends in `model_copy(update=...)`, which ADDS the updated keys to `model_fields_set`, so
  downstream of it an omitted flag and an explicit `false` are identical and the guard is
  constant-true. That was measured twice — round 38 "refuted" it and round-2 validation reversed
  the refutation.
"""
sub(PARK_ANCHOR, PARK_052, "park sentence for APD-DATA-052")

# --------------------------------------------------------------- the preamble that named the gap
sub(
    "**Two of them are in neither, and that is a gap, not a\ndecision** (noted 2026-09-09): the explicit-`allow_truncation: false`-on-every-apply defect and the\n`val_ratio` / `INFRASTRUCTURE_FIELDS` drift are so far written down only in\n",
    "**Two of them were in neither, and that was a gap, not a\ndecision** (noted 2026-09-09; **the gap is closed 2026-09-15** — the truncation defect is now\n`APD-DATA-052` below, and the `val_ratio` / `INFRASTRUCTURE_FIELDS` drift was closed by\njuniper-canopy#605 and belongs to the canopy ledger, so neither is handoff-only any more): the\nexplicit-`allow_truncation: false`-on-every-apply defect and the `val_ratio` /\n`INFRASTRUCTURE_FIELDS` drift were written down only in\n",
    "close the named gap in the 4.9 preamble",
)

# --------------------------------------------------------------- the counts
sub(
    "and seven are open — **24 open in all**, 17 primer + 7 post-primer.",
    "and eight are open — **25 open in all**, 17 primer + 8 post-primer.",
    "4.9 open count: 24 -> 25",
)

REGISTER.write_text(text)
print(f"\nregister updated: {REGISTER}")

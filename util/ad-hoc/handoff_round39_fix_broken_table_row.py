#!/usr/bin/env python3
"""Repair a table row this session's own edit script split across two lines.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1947 (the PR it reddened);
         [[handoff_round39_apply_laneB2]] (the script that introduced it)

``handoff_round39_apply_laneB2.py``'s "name the row and register at §4" hunk emitted a ``\\n``
inside a markdown TABLE CELL while wrapping a replacement to the file's line width. A table row is
one line; the break ended the table at that row, and the row after it began a new table with no
separator, so it rendered as paragraph text.

**`Documentation Links` caught it and nothing else did** -- not markdownlint, not the doc-link
validator, not any local test. ``util/markdown_structure_delta.py`` reported
``0 -> 1`` structural problems, ``table at line 334 has no separator row``, and the Quality Gate
failure was purely downstream of that one check. This is the screen doing exactly the job it was
built for; treat a structure-delta failure as a real rendering defect until proven otherwise.

The second fix here is lane A's, applied in the same pass because it is in the same table: the
``APD-DATA-030`` row claimed "two tests asserting it", and only ONE asserts ``Retry-After`` on the
auth-throttle 429. The second test asserts it on the RATE-LIMIT 429, which is a different mechanism.
"""

from __future__ import annotations

import sys
from pathlib import Path

HANDOFF = (
    Path(__file__).resolve().parents[2]
    / "prompts/thread-handoff_automated-prompts"
    / "HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md"
)

text = HANDOFF.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    if new in text and old not in text:
        print(f"  --  {label} (already applied)")
        return
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} occurrences of:\n{old[:200]}")
    text = text.replace(old, new, 1)
    print(f"  ok  {label}")


sub(
    'said "nothing can select it into a dataset"; corrected\n2026-09-15. |',
    'said "nothing can select it into a dataset"; corrected 2026-09-15. |',
    "rejoin the table row split across two lines",
)

sub(
    "`Retry-After` IS sent on the auth-throttle 429, with two tests asserting it.",
    "`Retry-After` IS sent on the auth-throttle 429 (`api/middleware.py:206`), asserted by "
    "`tests/unit/test_middleware.py:240`. A second test, `tests/integration/test_security_integration.py:138`, "
    "asserts it on the **rate-limit** 429 (`api/security.py:287`) — a different mechanism, so the honest "
    "count is one test per source, not two on one.",
    "APD-DATA-030 row: one test per source, not two",
)

HANDOFF.write_text(text)
print(f"\nhandoff repaired: {HANDOFF.name}")

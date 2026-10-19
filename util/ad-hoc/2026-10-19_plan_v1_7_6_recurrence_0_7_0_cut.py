#!/usr/bin/env python3
"""Plan v1.7.6: record that the W5.8 (B) service half merged and recurrence 0.7.0 was cut to its PyPI gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.5 -> v1.7.6);
         juniper-recurrence#212 (the service half), #213 (the 0.7.0 proposal); juniper-ml#2254 (the archive);
         util/ad-hoc/2026-10-19_plan_v1_7_5_w5_9_w5_8b_landed.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-19_plan_v1_7_6_recurrence_0_7_0_cut.py [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

CUT = "juniper-recurrence#212 merged as `5fb7dbff` once model 0.5.0 was on PyPI (its `requires_dist` equals 0.4.0's); proposal juniper-recurrence#213 merged as `5c576da4`; Release `juniper-recurrence-v0.7.0` cut at that commit, archive juniper-ml#2254, publish run 39194767443 approved by the owner and green — **0.7.0 is on PyPI and GHCR**"

EDITS: list[tuple[str, str]] = [
    ("- **Version**: 1.7.5", "- **Version**: 1.7.6"),
    # Status line.
    (
        "the consensus re-derivation's −0.195 reproduced). The v1.4.0 plan edits follow that record",
        f"the consensus re-derivation's −0.195 reproduced); **the service half merged and recurrence 0.7.0 is cut** (v1.7.6: {CUT}). The v1.4.0 plan edits follow that record",
    ),
    # W5.8 row header cell.
    (
        "**service half juniper-recurrence#212** (recurrence 0.7.0; floor `>=0.5.0`) — CHANGELOG \"Changed\" in both |",
        "**service half landed 2026-10-19** (juniper-recurrence#212, `5fb7dbff`; recurrence 0.7.0 cut via #213, `5c576da4`) — CHANGELOG \"Changed\" in both |",
    ),
    # P5 status row.
    (
        "the W5.8 (B) service half is juniper-recurrence#212 | 5 |",
        "**the W5.8 (B) service half Done** (juniper-recurrence#212, `5fb7dbff`); **recurrence 0.7.0 published** (#213, `5c576da4`) — **P5 Done**; W5.2 next | 5 |",
    ),
    # Progress block: one more bullet.
    (
        "  - **Next**: merge the service PR once 0.5.0 is on PyPI, then cut recurrence 0.7.0 (proposal → ceremony → the owner's `pypi` gate); W5.2 and W5.4 (round 3 of the CV-blowup note's review first); W5.7.",
        f"  - **Later the same session**: {CUT}. W5.2 designed (recorded in the handoff), not started.\n  - **Next**: the juniper-ml `[recurrence]` extras and the Compose pin (both admit `<0.7.0`) are owner rulings again; W5.2 and W5.4 (round 3 of the CV-blowup note's review first); W5.7.",
    ),
]

_ROW_ANCHOR = "the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.6.1 image. | Paul Calnon |\n"
_ROW = (
    f"| 2026-10-19 | 1.7.6 | **The W5.8 (B) service half merged and recurrence 0.7.0 is published; P5 is done**: {CUT}. "
    "Updated: Status line, W5.8 row, P5 status row, the Progress 2026-10-19 block. "
    "Owed: the juniper-ml `[recurrence]` extras ceiling (`<0.7.0`) and the Compose pin (owner rulings); W5.2 (designed), W5.4, W5.7; W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes. | Paul Calnon |\n"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = _PLAN.read_text(encoding="utf-8")
    pending = []
    done = 0
    for old, new in EDITS:
        if new in text:
            done += 1
            continue
        n = text.count(old)
        if n != 1:
            print(f"REFUSED: anchor matched {n} times (expected 1):\n  {old[:160]!r}")
            return 1
        pending.append((old, new))
    row_pending = _ROW not in text
    if row_pending and text.count(_ROW_ANCHOR) != 1:
        print(f"REFUSED: change-log anchor matched {text.count(_ROW_ANCHOR)} times (expected 1)")
        return 1
    if args.check:
        print(f"applied {done}, pending {len(pending)}, change-log row {'pending' if row_pending else 'present'}")
        return 0
    for old, new in pending:
        text = text.replace(old, new, 1)
    if row_pending:
        i = text.index(_ROW_ANCHOR) + len(_ROW_ANCHOR)
        text = text[:i] + _ROW + text[i:]
    _PLAN.write_text(text, encoding="utf-8")
    print(f"applied {done + len(pending)} edits; change-log row {'added' if row_pending else 'already present'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

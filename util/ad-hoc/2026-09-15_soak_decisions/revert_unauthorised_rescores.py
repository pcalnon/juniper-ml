#!/usr/bin/env python3
"""Remove two rescore appends that were made without the owner ruling that authorises them.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-16
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 7

Why
---
Section 7 of that note lists three owner questions. Item 1 is WHICH RETRIEVAL STANDARD BINDS;
item 2 is WHETHER THE SECTION 4 ROWS ARE RE-SCORED, and it says in terms that a downward
re-score "is a schema change, not a data edit". On 2026-09-15 the owner ruled item 1
(MECHANISM-CHECKED). I made the schema change AND the data edit on that authority. Only the
schema change was authorised.

Owner ruling 2026-09-16: keep the widening (the standard stays expressible and prospectively
binding), revert the two edits pending an explicit item-2 ruling.

Why a line removal rather than an append. `rescore` is append-only by design, and there is no
un-rescore verb -- `analyse` builds its `rescored` map from EVERY `kind == "rescore"` row with
no invalidation filter, so no appended record can neutralise one. Removing the two rows returns
the corpus to its authorised state; the full audit trail lives in this script, the PR, and the
note. The `invalidate` row (ruling 2, authorised) is deliberately NOT touched.

REFUSES unless it finds exactly the two expected rows, so a drifted ledger stops it.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEDGER = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"

# The two unauthorised rescore rows, by their own obs_id.
DROP = {
    "be968f2c-3f5e-492d-8a29-50704e80e6c2",   # rescores P21 b57a72bb (filename=1)
    "041f6c5f-2f69-4ded-998d-0a982c2d8ed8",   # rescores P24 eb3d9320 (foreign=2)
}
# Must survive untouched: the authorised ledger-leak invalidation (ruling 2).
KEEP = "327107a0-86a2-4f15-a960-54d64b5ddf6a"


def main() -> int:
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    keep_lines, dropped = [], []
    for ln in lines:
        if not ln.strip():
            continue
        rec = json.loads(ln)
        if rec.get("obs_id") in DROP:
            if rec.get("kind") != "rescore":
                print(f"REFUSING: {rec.get('obs_id')} is a {rec.get('kind')!r}, not a rescore",
                      file=sys.stderr)
                return 1
            dropped.append(rec)
        else:
            keep_lines.append(ln)

    if len(dropped) != len(DROP):
        print(f"REFUSING: expected {len(DROP)} rescore rows, found {len(dropped)}. "
              "The ledger has drifted; re-identify before removing anything.", file=sys.stderr)
        return 1
    if not any(json.loads(ln).get("obs_id") == KEEP for ln in keep_lines):
        print(f"REFUSING: the authorised invalidate row {KEEP} is not present after the filter",
              file=sys.stderr)
        return 1

    LEDGER.write_text("\n".join(keep_lines) + "\n", encoding="utf-8")
    for rec in dropped:
        print(f"removed rescore {rec['obs_id']}  "
              f"({rec.get('from_outcome')} -> {rec.get('to_outcome')} on {rec.get('rescores')})")
    print(f"kept {len(keep_lines)} rows; invalidate {KEEP} intact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
